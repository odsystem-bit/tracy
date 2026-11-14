"""Tests LogisticsAgent : intent de livraison et couverture par ville."""

from __future__ import annotations

import pytest

from app.agents.location import extract_city_after_preposition
from app.core.intent import classify_intent
from app.tools.base import ToolContext
from app.tools.get_delivery_info import GetDeliveryInfoTool


@pytest.mark.parametrize(
    ("text", "agent"),
    [
        ("tu livres à Parakou ?", "LogisticsAgent"),
        ("quels sont les frais de livraison", "LogisticsAgent"),
        ("où est ma livraison CMD-123", "OrderAgent"),
        ("livraison repas pizza", "RestaurantAgent"),
        ("je veux des baskets", "CommercialAgent"),
    ],
)
def test_delivery_intent_routing(text: str, agent: str) -> None:
    assert classify_intent(text).selected_agent == agent


def test_city_after_preposition() -> None:
    assert extract_city_after_preposition("tu livres à Parakou ?") == "Parakou"
    assert extract_city_after_preposition("tu livres à la maison") is None


class _FakeClient:
    def __init__(self, data: dict) -> None:
        self._data = data

    async def get_delivery_quartiers(self, store_id: str) -> dict:
        return self._data


def _ctx() -> ToolContext:
    return ToolContext(agent_name="LogisticsAgent", correlation_id="c", store_id="1")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("data", "city", "expected"),
    [
        ({"delivery_mode": "national"}, "Parakou", True),
        ({"delivery_mode": "pickup_only"}, "Parakou", False),
        ({"delivery_mode": "multi_city", "delivery_cities": ["Cotonou"]}, "cotonou", True),
        ({"delivery_mode": "multi_city", "delivery_cities": ["Cotonou"]}, "Parakou", False),
        (
            {"delivery_mode": "quartiers", "quartiers": [{"name": "Ganhi", "ville": {"name": "Cotonou"}}]},
            "Cotonou",
            True,
        ),
        ({"delivery_mode": "national"}, None, None),
    ],
)
async def test_delivery_coverage(data: dict, city: str | None, expected: bool | None) -> None:
    tool = GetDeliveryInfoTool(_FakeClient(data))  # type: ignore[arg-type]
    result = await tool.execute(_ctx(), store_id="1", city=city)
    assert result.success
    assert result.data.covers_city is expected


@pytest.mark.asyncio
async def test_public_store_rejected() -> None:
    tool = GetDeliveryInfoTool(_FakeClient({}))  # type: ignore[arg-type]
    result = await tool.execute(_ctx(), store_id="public")
    assert not result.success
