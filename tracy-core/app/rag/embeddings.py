"""app/rag/embeddings.py — Génération d'embeddings via OpenAI (text-embedding-3-small).

Rôle : générer un vecteur de 1536 dimensions à partir d'un texte,
pour alimenter la recherche pgvector côté Mantota.

RÈGLE FONDAMENTALE : le LLM reformule, il ne décide jamais.
Les embeddings servent uniquement à retrouver du texte pertinent pour
enrichir le prompt de reformulation. Aucune décision métier n'est prise ici.
"""

from __future__ import annotations

import asyncio
from typing import Any

from openai import AsyncOpenAI

from app.logging_config import get_logger

logger = get_logger(__name__)

# Modèle d'embedding OpenAI (1536 dimensions)
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


class EmbeddingError(Exception):
    """Erreur lors de la génération d'un embedding."""


class EmbeddingService:
    """Service de génération d'embeddings via OpenAI.

    Utilise text-embedding-3-small (1536 dimensions).
    Gère les retries avec backoff exponentiel.
    """

    def __init__(self, api_key: str, timeout: float = 30.0, retry_max: int = 3) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self._retry_max = retry_max
        self._retry_backoff = 0.5

    async def embed(self, text: str) -> list[float]:
        """Génère un embedding pour un texte donné.

        Args:
            text: Texte à embedder (non vide).

        Returns:
            Vecteur de 1536 dimensions (list[float]).

        Raises:
            EmbeddingError: si la génération échoue après tous les retries.
        """
        if not text.strip():
            raise EmbeddingError("Le texte ne peut pas être vide.")

        last_exc: Exception | None = None

        for attempt in range(1, self._retry_max + 1):
            try:
                response = await self._client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=text,
                )
                embedding = response.data[0].embedding
                logger.debug(
                    "embedding_generated",
                    model=EMBEDDING_MODEL,
                    dimensions=len(embedding),
                    attempt=attempt,
                )
                return embedding
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "embedding_failed",
                    attempt=attempt,
                    error=str(exc),
                )
                if attempt < self._retry_max:
                    await asyncio.sleep(self._retry_backoff * (2 ** (attempt - 1)))

        raise EmbeddingError(f"Échec de génération d'embedding après {self._retry_max} tentatives: {last_exc}")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Génère des embeddings pour une liste de textes.

        Args:
            texts: Liste de textes à embedder.

        Returns:
            Liste de vecteurs (chaque vecteur a 1536 dimensions).

        Raises:
            EmbeddingError: si la génération échoue.
        """
        if not texts:
            return []

        if not all(t.strip() for t in texts):
            raise EmbeddingError("Aucun texte ne peut être vide.")

        last_exc: Exception | None = None

        for attempt in range(1, self._retry_max + 1):
            try:
                response = await self._client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=texts,
                )
                # OpenAI retourne les embeddings dans l'ordre d'entrée
                embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
                logger.debug(
                    "embedding_batch_generated",
                    model=EMBEDDING_MODEL,
                    count=len(embeddings),
                    attempt=attempt,
                )
                return embeddings
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "embedding_batch_failed",
                    attempt=attempt,
                    error=str(exc),
                )
                if attempt < self._retry_max:
                    await asyncio.sleep(self._retry_backoff * (2 ** (attempt - 1)))

        raise EmbeddingError(f"Échec de génération d'embedments batch après {self._retry_max} tentatives: {last_exc}")
