"""Connecteur DeepSeek pour l'AI Gateway.

Fournisseur pour les tâches économiques à fort volume
(docs/tracy/02-ARCHITECTURE.md §AI Gateway).
"""

from __future__ import annotations

import httpx

from app.ai_gateway.base import AIProvider, ChatMessage, ChatResponse
from app.logging_config import get_logger

logger = get_logger(__name__)


class DeepSeekProvider(AIProvider):
    """Fournisseur IA DeepSeek."""

    def __init__(self, api_key: str, model: str = "deepseek-chat", timeout: float = 30.0) -> None:
        self._api_key = api_key
        self._model = model
        self._client = httpx.AsyncClient(
            base_url="https://api.deepseek.com/v1",
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    @property
    def name(self) -> str:
        return "deepseek"

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
            "ai_deepseek_request",
            model=self._model,
            message_count=len(messages),
        )

        payload: dict = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        tokens = data.get("usage", {}).get("total_tokens")

        return ChatResponse(
            content=content,
            provider=self.name,
            model=self._model,
            tokens_used=tokens,
        )

    async def aclose(self) -> None:
        await self._client.aclose()
