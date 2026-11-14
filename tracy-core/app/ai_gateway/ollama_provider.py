"""Connecteur Ollama pour l'AI Gateway.

Fournisseur local pour la confidentialité, la latence et le coût
(docs/tracy/02-ARCHITECTURE.md §AI Gateway, docs/tracy/08-ROADMAP.md V3).

Ollama expose une API REST locale compatible avec le format OpenAI.
"""

from __future__ import annotations

import httpx

from app.ai_gateway.base import AIProvider, ChatMessage, ChatResponse
from app.logging_config import get_logger

logger = get_logger(__name__)


class OllamaProvider(AIProvider):
    """Fournisseur IA Ollama (modèles locaux)."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2") -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=60.0,
            headers={"Content-Type": "application/json"},
        )

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    async def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        logger.debug(
            "ai_ollama_request",
            model=self._model,
            message_count=len(messages),
        )

        options: dict = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "options": options,
            "stream": False,
        }

        response = await self._client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()

        content = data.get("message", {}).get("content", "")
        tokens = data.get("eval_count")

        logger.debug(
            "ai_ollama_response",
            model=self._model,
            tokens_used=tokens,
        )

        return ChatResponse(
            content=content,
            provider=self.name,
            model=self._model,
            tokens_used=tokens,
        )

    async def aclose(self) -> None:
        await self._client.aclose()
