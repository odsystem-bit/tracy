"""app/rag/retriever.py — Retriever RAG pour Tracy Core.

Rôle : rechercher des chunks de connaissances pertinents via pgvector
sur le PostgreSQL de Mantota. La recherche se fait en deux étapes :
  1. Générer l'embedding de la requête (via OpenAI text-embedding-3-small).
  2. Envoyer l'embedding à l'API Mantota qui exécute la recherche pgvector.

RÈGLE FONDAMENTALE : le LLM reformule, il ne décide jamais.
Les chunks récupérés sont injectés dans le prompt de reformulation finale.
Ils ne déclenchent jamais d'action métier (prix, commande, paiement).
"""

from __future__ import annotations

from typing import Literal

from app.logging_config import get_logger
from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError
from app.rag.embeddings import EmbeddingService

logger = get_logger(__name__)

RelevanceLevel = Literal["correct", "ambiguous", "incorrect"]


def classify_relevance(
    chunks: list[KnowledgeChunk],
    score_correct: float = 0.85,
    score_ambiguous: float = 0.6,
) -> RelevanceLevel:
    """Classe la pertinence des chunks récupérés selon le meilleur score de similarité.

    La classification est purement numérique (score cosinus) — jamais par le LLM.

    Args:
        chunks: Liste de KnowledgeChunk triés par score décroissant.
        score_correct: Seuil au-dessus duquel les chunks sont considérés comme pertinents.
        score_ambiguous: Seuil en-dessous duquel les chunks sont considérés comme non pertinents.
            Entre score_ambiguous et score_correct : zone ambiguë.

    Returns:
        "correct" si le meilleur score >= score_correct,
        "ambiguous" si le meilleur score >= score_ambiguous,
        "incorrect" sinon (ou si la liste est vide).
    """
    if not chunks:
        return "incorrect"

    best_score = chunks[0].score

    if best_score >= score_correct:
        return "correct"
    elif best_score >= score_ambiguous:
        return "ambiguous"
    else:
        return "incorrect"


class KnowledgeChunk:
    """Un chunk de connaissance récupéré par le RAG."""

    def __init__(
        self,
        id: int,
        content: str,
        score: float,
        title: str,
        category: str,
        country_id: int | None,
    ) -> None:
        self.id = id
        self.content = content
        self.score = score
        self.title = title
        self.category = category
        self.country_id = country_id

    def __repr__(self) -> str:
        return f"KnowledgeChunk(id={self.id}, score={self.score:.4f}, title='{self.title}')"


class KnowledgeRetriever:
    """Retriever RAG : génère l'embedding de la requête et interroge Mantota.

    Utilise le MantotaClient pour communiquer avec l'endpoint /bot/knowledge/search
    qui exécute la recherche pgvector côté PostgreSQL.
    """

    def __init__(self, embedding_service: EmbeddingService, mantota_client: MantotaClient) -> None:
        self._embeddings = embedding_service
        self._mantota = mantota_client

    async def search_knowledge(
        self,
        query: str,
        country_id: int | None = None,
        category: str | None = None,
        top_k: int = 5,
    ) -> list[KnowledgeChunk]:
        """Recherche les chunks de connaissances les plus pertinents.

        Args:
            query: Texte de la requête (message du client ou question).
            country_id: ID du pays pour filtrer (None = tous les pays).
            category: Catégorie de document pour filtrer (None = toutes).
            top_k: Nombre maximum de résultats à retourner.

        Returns:
            Liste de KnowledgeChunk triés par score décroissant.
        """
        if not query.strip():
            logger.warning("rag_empty_query")
            return []

        # Étape 1 : générer l'embedding de la requête
        try:
            embedding = await self._embeddings.embed(query)
        except Exception as exc:
            logger.error("rag_embedding_failed", query=query[:100], error=str(exc))
            return []

        # Étape 2 : interroger Mantota pour la recherche pgvector
        try:
            result = await self._mantota.search_knowledge(
                embedding=embedding,
                country_id=country_id,
                category=category,
                top_k=top_k,
            )
        except MantotaError as exc:
            logger.error("rag_search_failed", error=str(exc), code=exc.code)
            return []
        except Exception as exc:
            logger.error("rag_search_unexpected_error", error=str(exc))
            return []

        # Étape 3 : mapper les résultats en KnowledgeChunk
        chunks = [
            KnowledgeChunk(
                id=item["id"],
                content=item["content"],
                score=item["score"],
                title=item["title"],
                category=item["category"],
                country_id=item.get("country_id"),
            )
            for item in result.get("results", [])
        ]

        logger.info(
            "rag_search_completed",
            query=query[:100],
            results_count=len(chunks),
            top_score=chunks[0].score if chunks else None,
        )

        return chunks

    def format_chunks_for_prompt(self, chunks: list[KnowledgeChunk]) -> str:
        """Formate les chunks pour injection dans le prompt de reformulation du LLM.

        Args:
            chunks: Liste de KnowledgeChunk à formater.

        Returns:
            Texte formaté prêt à être injecté dans un prompt.
        """
        if not chunks:
            return ""

        lines = ["CONTEXTE DE CONNAISSANCE (à utiliser pour reformuler, ne pas citer mot pour mot) :"]
        for chunk in chunks:
            lines.append(f"--- {chunk.title} ({chunk.category}) ---")
            lines.append(chunk.content)
            lines.append("")

        return "\n".join(lines)
