#!/usr/bin/env python3
"""scripts/ingest_knowledge.py — Script d'ingestion RAG pour Tracy Core.

Rôle : prend un document `approved` en base (via l'API Mantota), le découpe en
chunks sémantiques (par section/paragraphe), génère les embeddings via OpenAI
(text-embedding-3-small), et les insère dans la table knowledge_chunks via
l'API Mantota.

Le découpage est sémantique : par section/paragraphe, pas de découpage à taille
fixe arbitraire. On utilise les séparateurs naturels (double saut de ligne,
titres avec ---, etc.).

Le script est idempotent : relancer sur le même document ne duplique pas les
chunks (upsert par document_id + chunk_index).

Usage:
    python scripts/ingest_knowledge.py --document-id 1
    python scripts/ingest_knowledge.py --all-approved

RÈGLE FONDAMENTALE : le LLM reformule, il ne décide jamais.
Ce script prépare les données pour la reformulation, il ne prend aucune décision.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from typing import Any

import httpx

# Ajoute le répertoire parent au path pour les imports
sys.path.insert(0, ".")

from app.config import get_settings
from app.logging_config import configure_logging, get_logger
from app.rag.embeddings import EmbeddingService

logger = get_logger(__name__)


def chunk_document(content: str, max_chunk_size: int = 1000) -> list[str]:
    """Découpe un document en chunks sémantiques.

    Stratégie :
    1. Découper par sections (séparées par '---' ou titres markdown '#')
    2. Si une section est trop longue, la découper par paragraphes (double saut de ligne)
    3. Si un paragraphe est trop long, le découper par phrases

    Args:
        content: Texte du document à découper.
        max_chunk_size: Taille maximale d'un chunk en caractères.

    Returns:
        Liste de chunks (texte).
    """
    # Étape 1 : découper par sections (--- ou titres #)
    sections = re.split(r"\n---\n|\n#{1,3}\s", content)
    sections = [s.strip() for s in sections if s.strip()]

    chunks: list[str] = []

    for section in sections:
        if len(section) <= max_chunk_size:
            chunks.append(section)
            continue

        # Étape 2 : découper par paragraphes (double saut de ligne)
        paragraphs = re.split(r"\n\n+", section)
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= max_chunk_size:
                current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # Si le paragraphe seul est trop long, découper par phrases
                if len(para) > max_chunk_size:
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    current_chunk = ""
                    for sent in sentences:
                        if len(current_chunk) + len(sent) + 1 <= max_chunk_size:
                            current_chunk = f"{current_chunk} {sent}" if current_chunk else sent
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sent
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

    return chunks


async def ingest_document(
    document_id: int,
    mantota_base_url: str,
    mantota_api_key: str,
    embedding_service: EmbeddingService,
) -> int:
    """Ingère un document : récupère le contenu, découpe, embedde, et upsert les chunks.

    Args:
        document_id: ID du document à ingérer.
        mantota_base_url: URL de base de l'API Mantota.
        mantota_api_key: Clé API bot Mantota.
        embedding_service: Service d'embedding OpenAI.

    Returns:
        Nombre de chunks insérés.
    """
    async with httpx.AsyncClient(
        base_url=mantota_base_url,
        headers={
            "X-Bot-Api-Key": mantota_api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=30.0,
    ) as client:
        # Récupère le document via l'API bot
        resp = await client.get(f"/bot/knowledge/documents/{document_id}")
        resp.raise_for_status()
        doc_data = resp.json()["data"]

        if doc_data["status"] != "approved":
            logger.warning(
                "ingest_document_not_approved",
                document_id=document_id,
                status=doc_data["status"],
            )
            return 0

        title = doc_data["title"]
        content = doc_data["content"]
        country_id = doc_data.get("country_id")
        category = doc_data["category"]

        logger.info("ingest_document_start", document_id=document_id, title=title)

        # Découpe en chunks sémantiques
        chunk_texts = chunk_document(content)
        logger.info("ingest_chunks_created", document_id=document_id, chunk_count=len(chunk_texts))

        # Génère les embeddings en batch
        embeddings = await embedding_service.embed_batch(chunk_texts)

        # Prépare les chunks pour l'upsert
        chunks_payload = []
        for i, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
            chunks_payload.append({
                "document_id": document_id,
                "chunk_index": i,
                "content": chunk_text,
                "embedding": embedding,
                "metadata": {
                    "country_id": country_id,
                    "category": category,
                    "title": title,
                },
            })

        # Upsert via l'API bot (endpoint dédié à l'ingestion)
        # On utilise un endpoint bot qui fait upsert par (document_id, chunk_index)
        resp = await client.post(
            f"/bot/knowledge/documents/{document_id}/chunks",
            json={"chunks": chunks_payload},
        )
        resp.raise_for_status()

        result = resp.json()
        inserted = result.get("inserted", len(chunks_payload))

        logger.info(
            "ingest_document_complete",
            document_id=document_id,
            title=title,
            chunks_inserted=inserted,
        )

        return inserted


async def ingest_all_approved(
    mantota_base_url: str,
    mantota_api_key: str,
    embedding_service: EmbeddingService,
) -> int:
    """Ingère tous les documents approved non encore indexés.

    Args:
        mantota_base_url: URL de base de l'API Mantota.
        mantota_api_key: Clé API bot Mantota.
        embedding_service: Service d'embedding OpenAI.

    Returns:
        Nombre total de chunks insérés.
    """
    async with httpx.AsyncClient(
        base_url=mantota_base_url,
        headers={
            "X-Bot-Api-Key": mantota_api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=30.0,
    ) as client:
        resp = await client.get("/bot/knowledge/documents", params={"per_page": 100})
        resp.raise_for_status()
        docs = resp.json()["data"]

        total_chunks = 0
        for doc in docs:
            total_chunks += await ingest_document(
                document_id=doc["id"],
                mantota_base_url=mantota_base_url,
                mantota_api_key=mantota_api_key,
                embedding_service=embedding_service,
            )

        logger.info("ingest_all_complete", total_documents=len(docs), total_chunks=total_chunks)
        return total_chunks


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestion RAG — Tracy Core")
    parser.add_argument("--document-id", type=int, help="ID du document à ingérer")
    parser.add_argument("--all-approved", action="store_true", help="Ingérer tous les documents approved")
    args = parser.parse_args()

    if not args.document_id and not args.all_approved:
        parser.error("Spécifier --document-id ou --all-approved")

    settings = get_settings()
    configure_logging(settings.environment, settings.log_level)

    if not settings.openai_api_key:
        logger.error("OPENAI_API_KEY manquant — impossible de générer les embeddings")
        sys.exit(1)

    embedding_service = EmbeddingService(
        api_key=settings.openai_api_key,
        timeout=settings.ai_timeout,
        retry_max=settings.ai_retry_max,
    )

    if args.document_id:
        count = await ingest_document(
            document_id=args.document_id,
            mantota_base_url=settings.mantota_api_url,
            mantota_api_key=settings.mantota_api_key,
            embedding_service=embedding_service,
        )
        print(f"✓ Document {args.document_id} ingéré : {count} chunks insérés")
    elif args.all_approved:
        count = await ingest_all_approved(
            mantota_base_url=settings.mantota_api_url,
            mantota_api_key=settings.mantota_api_key,
            embedding_service=embedding_service,
        )
        print(f"✓ Ingestion complète : {count} chunks insérés")


if __name__ == "__main__":
    asyncio.run(main())
