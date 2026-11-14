"""Tests du repli LLM d'intention : valide, invalide, panne, confiance faible."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.llm_intent import classify_with_llm


class _Gateway:
    def __init__(self, content: str | None = None, error: Exception | None = None) -> None:
        self._content = content
        self._error = error

    async def complete(self, messages, temperature=0.7, max_tokens=None):  # noqa: ANN001
        if self._error:
            raise self._error
        return SimpleNamespace(content=self._content)


@pytest.mark.asyncio
async def test_valid_json_maps_to_agent() -> None:
    gw = _Gateway('{"intent": "delivery", "confidence": 0.9}')
    result = await classify_with_llm(gw, "ça arrive quand chez moi")  # type: ignore[arg-type]
    assert result is not None
    assert result.selected_agent == "LogisticsAgent"


@pytest.mark.asyncio
async def test_json_wrapped_in_text() -> None:
    gw = _Gateway('Voici : {"intent": "support", "confidence": 0.8} merci')
    result = await classify_with_llm(gw, "x")  # type: ignore[arg-type]
    assert result is not None and result.intent == "support"


@pytest.mark.parametrize(
    "content",
    [
        '{"intent": "unknown", "confidence": 0.9}',
        '{"intent": "delivery", "confidence": 0.3}',
        '{"intent": "hack", "confidence": 0.99}',
        '{"intent": "delivery", "confidence": 7}',
        "pas de json",
    ],
)
@pytest.mark.asyncio
async def test_rejected_outputs_return_none(content: str) -> None:
    assert await classify_with_llm(_Gateway(content), "x") is None  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_gateway_failure_returns_none() -> None:
    gw = _Gateway(error=RuntimeError("down"))
    assert await classify_with_llm(gw, "x") is None  # type: ignore[arg-type]
