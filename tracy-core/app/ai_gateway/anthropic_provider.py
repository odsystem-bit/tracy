"""Connecteur Anthropic (Claude) pour l'AI Gateway.

Fournisseur pour l'analyse longue et les tâches nuancées
(docs/tracy/02-ARCHITECTURE.md §AI Gateway).
"""

from __future__ import annotations

import httpx

from app.ai_gateway.base import AIProvider, ChatMessage, ChatResponse
from app.logging_config import get_logger

logger = get_logger(__name__)


class AnthropicProvider(AIProvider):
    """Fournisseur IA Anthropic (Claude)."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", timeout: float = 30.0) -> None:
        self._api_key = api_key
        self._model = model
        self._client = httpx.AsyncClient(
            base_url="https://api.anthropic.com/v1",
            timeout=timeout,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    @property
    def supports_vision(self) -> bool:
        return True

    @staticmethod
    def _to_api(m: ChatMessage) -> dict[str, object]:
        if not m.images:
            return {"role": m.role, "content": m.content}
        blocks: list[dict[str, object]] = []
        for url in m.images:
            # Data URL attendue : data:image/jpeg;base64,XXXX
            header, _, data = url.partition(",")
            media_type = header.removeprefix("data:").split(";")[0] or "image/jpeg"
            blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": data},
            })
        blocks.append({"type": "text", "text": m.content})
        return {"role": m.role, "content": blocks}

    async def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        logger.debug(
            "ai_anthropic_request",
            model=self._model,
            message_count=len(messages),
        )

        system_msg = next((m for m in messages if m.role == "system"), None)
        conversation = [m for m in messages if m.role != "system"]

        payload: dict[str, object] = {
            "model": self._model,
            "messages": [self._to_api(m) for m in conversation],
            "max_tokens": max_tokens if max_tokens is not None else 1024,
            "temperature": temperature,
        }
        if system_msg:
            payload["system"] = system_msg.content

        response = await self._client.post("/messages", json=payload)
        response.raise_for_status()
        data = response.json()

        content = data.get("content", [{}])[0].get("text", "")
        tokens = data.get("usage", {}).get("output_tokens")

        return ChatResponse(
            content=content,
            provider=self.name,
            model=self._model,
            tokens_used=tokens,
        )

    async def aclose(self) -> None:
        await self._client.aclose()
