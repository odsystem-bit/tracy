"""Connecteur OpenAI (GPT) pour l'AI Gateway.

Fournisseur par défaut pour le raisonnement général et la rédaction
(docs/tracy/02-ARCHITECTURE.md §AI Gateway).
"""

from __future__ import annotations

from openai import AsyncOpenAI

from app.ai_gateway.base import AIProvider, ChatMessage, ChatResponse
from app.logging_config import get_logger

logger = get_logger(__name__)


class OpenAIProvider(AIProvider):
    """Fournisseur IA OpenAI (GPT)."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout: float = 30.0) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self._model = model

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model

    @property
    def supports_vision(self) -> bool:
        return True

    async def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        logger.debug(
            "ai_openai_request",
            model=self._model,
            message_count=len(messages),
        )

        def _to_api(m: ChatMessage) -> dict:
            if not m.images:
                return {"role": m.role, "content": m.content}
            return {
                "role": m.role,
                "content": [
                    {"type": "text", "text": m.content},
                    *[
                        {"type": "image_url", "image_url": {"url": url}}
                        for url in m.images
                    ],
                ],
            }

        kwargs: dict = {
            "model": self._model,
            "messages": [_to_api(m) for m in messages],
            "temperature": temperature,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        response = await self._client.chat.completions.create(**kwargs)

        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else None

        logger.debug(
            "ai_openai_response",
            model=self._model,
            tokens_used=tokens,
        )

        return ChatResponse(
            content=content,
            provider=self.name,
            model=self._model,
            tokens_used=tokens,
        )
