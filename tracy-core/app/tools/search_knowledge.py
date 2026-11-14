"""Tool search_knowledge (28e tool) — Recherche RAG dans la base de connaissances.

Rôle : rechercher du contexte pertinent (quartiers, marchés, moyens de paiement,
procédures, FAQ) via pgvector pour enrichir la reformulation du LLM.

Permissions : CommercialAgent, SupportAgent uniquement.
OrderAgent et PaymentAgent ne doivent PAS chercher du contexte — ils exécutent
des actions transactionnelles.

RAG Correctif : la pertinence est classée numériquement (score cosinus), jamais
par le LLM. Quand relevance == "incorrect", le tool logge la lacune en
arrière-plan (async, ne bloque pas) et retourne un contexte de repli honnête
pour que le LLM produise un comportement de repli plutôt qu'une réponse inventée.

RÈGLE FONDAMENTALE : le LLM reformule, il ne décide jamais.
Le résultat de ce tool est injecté dans le prompt de reformulation finale.
Il ne déclenche jamais d'action métier (prix, commande, paiement).
"""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel

from app.logging_config import get_logger
from app.rag.retriever import KnowledgeRetriever, classify_relevance
from app.tools.base import Tool, ToolContext, ToolResult

logger = get_logger(__name__)


class KnowledgeSearchResult(BaseModel):
    """Résultat d'une recherche dans la base de connaissances RAG."""
    chunks: list[dict[str, Any]]
    formatted_context: str
    relevance: str  # "correct", "ambiguous", "incorrect"


class SearchKnowledgeTool(Tool[KnowledgeSearchResult]):
    """Recherche sémantique dans la base de connaissances via pgvector."""

    def __init__(self, retriever: KnowledgeRetriever) -> None:
        self._retriever = retriever

    @property
    def name(self) -> str:
        return "search_knowledge"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CommercialAgent", "SupportAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        query: str,
        country_id: int | None = None,
        category: str | None = None,
        top_k: int = 5,
        **_extra: Any,
    ) -> ToolResult[KnowledgeSearchResult]:
        if not query.strip():
            return ToolResult.fail(
                "INVALID_QUERY",
                "La requête ne peut pas être vide.",
                ctx.correlation_id,
            )

        chunks = await self._retriever.search_knowledge(
            query=query,
            country_id=country_id,
            category=category,
            top_k=top_k,
        )

        # Classification de pertinence (purement numérique, jamais par le LLM)
        relevance = classify_relevance(chunks)

        logger.info(
            "rag_relevance_classified",
            query=query[:100],
            relevance=relevance,
            top_score=chunks[0].score if chunks else None,
        )

        if relevance == "incorrect":
            # Aucune information fiable : logge la lacune en arrière-plan
            # (fire-and-forget, ne bloque pas la réponse)
            asyncio.create_task(
                self._log_gap(
                    query=query,
                    country_id=country_id,
                    category_guess=category,
                    correlation_id=ctx.correlation_id,
                )
            )

            # Retourne un succès avec un contexte de repli honnête
            # pour que le LLM produise un comportement de repli
            fallback_context = (
                "AUCUNE INFORMATION FIABLE TROUVÉE dans la base de connaissances.\n"
                "Vous ne disposez pas de contexte vérifié pour répondre à cette question.\n"
                "Comportement attendu :\n"
                "- Si vous êtes CommercialAgent : indiquez honnêtement que vous n'êtes pas sûre "
                "et que vous allez vérifier, puis proposez d'escalader vers un humain si nécessaire.\n"
                "- Si vous êtes SupportAgent : indiquez que l'information n'est pas disponible "
                "et proposez de créer un ticket ou d'escalader vers un humain.\n"
                "- N'inventez JAMAIS une information. Ne fabriquez pas de réponse à partir de "
                "connaissances générales non vérifiées dans le contexte local.\n"
                "- Le LLM reformule, il ne décide jamais."
            )

            result = KnowledgeSearchResult(
                chunks=[],
                formatted_context=fallback_context,
                relevance="incorrect",
            )
            return ToolResult.ok(result, ctx.correlation_id)

        # relevance == "correct" ou "ambiguous" : on utilise les chunks
        formatted = self._retriever.format_chunks_for_prompt(chunks)

        if relevance == "ambiguous":
            # Ajoute une note de prudence en amont du contexte
            formatted = (
                "ATTENTION : les informations ci-dessous ont une pertinence limitée "
                "(score de similarité moyen). Utilisez-les avec prudence et nuancez votre réponse.\n\n"
                + formatted
            )

        result = KnowledgeSearchResult(
            chunks=[
                {
                    "id": c.id,
                    "content": c.content,
                    "score": c.score,
                    "title": c.title,
                    "category": c.category,
                }
                for c in chunks
            ],
            formatted_context=formatted,
            relevance=relevance,
        )

        return ToolResult.ok(result, ctx.correlation_id)

    async def _log_gap(
        self,
        query: str,
        country_id: int | None,
        category_guess: str | None,
        correlation_id: str,
    ) -> None:
        """Logge une lacune de connaissance en arrière-plan (fire-and-forget).

        Génère l'embedding de la requête et l'envoie à Mantota via log_knowledge_gap.
        Cette méthode ne lève jamais — elle logge seulement en cas d'erreur.
        """
        try:
            embedding_service = self._retriever._embeddings
            mantota_client = self._retriever._mantota

            embedding = await embedding_service.embed(query)

            await mantota_client.log_knowledge_gap(
                query_text=query,
                query_embedding=embedding,
                country_id=country_id,
                category_guess=category_guess,
            )

            logger.info(
                "rag_gap_logged",
                query=query[:100],
                category_guess=category_guess,
                correlation_id=correlation_id,
            )
        except Exception as exc:
            logger.warning(
                "rag_gap_log_failed",
                query=query[:100],
                error=str(exc),
                correlation_id=correlation_id,
            )
