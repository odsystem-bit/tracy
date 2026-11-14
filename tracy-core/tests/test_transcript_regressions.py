"""Régressions tirées de conversations réelles (transcripts du chat web).

Chaque test reproduit un message client qui a mal tourné en production :
- « jai 100k je veux un telpehone » : budget ignoré
- « techno ou samsung ou iphone » : une seule marque cherchée
- « donne moi les coodoner de la boutisue » : refus de donner l'adresse
- photo + « tu as ca » : image ignorée, Tracy faisait semblant d'avoir vu
- produits en rupture proposés avant les produits disponibles
"""

from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest
import respx

from app.agents.base import AgentInput
from app.agents.commercial_agent import CommercialAgent
from app.agents.location import sort_by_scope
from app.ai_gateway.base import AIGateway, AIProvider, ChatMessage, ChatResponse
from app.core.orchestrator import TracyOrchestrator
from app.core.schemas import IncomingMessage, ProductCard
from app.memory.short_term import ConversationContext
from app.tools.registry import ToolRegistry

from tests.conftest import MANTOTA_BASE_URL, FakeAIGateway, mock_product_search_response

_TINY_JPEG = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2w=="


def _queries(route: respx.Route) -> list[str]:
    return [call.request.url.params.get("query", "") for call in route.calls]


# ── Budget « 100k » ──────────────────────────────────────────────────


@respx.mock
async def test_budget_k_suffix_filters_search(commercial_agent: CommercialAgent) -> None:
    route = respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response())
    )

    await commercial_agent.handle(
        AgentInput(
            message="jai 100k je veux un telpehone propose moi",
            store_id="public",
            correlation_id="reg-budget",
            customer_id="c1",
        )
    )

    max_prices = [
        float(c.request.url.params["max_price"])
        for c in route.calls
        if "max_price" in c.request.url.params
    ]
    assert max_prices, "le budget 100k doit être transmis à la recherche"
    assert all(100_000 <= p <= 110_001 for p in max_prices)


# ── Plusieurs marques « A ou B ou C » ────────────────────────────────


@respx.mock
async def test_multi_brand_or_searches_each_brand(commercial_agent: CommercialAgent) -> None:
    route = respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response())
    )

    await commercial_agent.handle(
        AgentInput(
            message="techno ou samsung ou iphone",
            store_id="public",
            correlation_id="reg-multibrand",
            customer_id="c1",
        )
    )

    queries = " | ".join(_queries(route)).lower()
    for brand in ("tecno", "samsung", "iphone"):
        assert brand in queries, f"{brand} doit être cherché (requêtes : {queries})"


# ── Coordonnées de la boutique ───────────────────────────────────────


@respx.mock
async def test_store_coordinates_uses_last_card_store(commercial_agent: CommercialAgent) -> None:
    info_route = respx.get(f"{MANTOTA_BASE_URL}/bot/stores/42/info").mock(
        return_value=httpx.Response(200, json={
            "id": "42",
            "nom": "Tech Ganhi",
            "ville": "Cotonou, Ganhi",
            "logo_url": None,
            "latitude": 6.3654,
            "longitude": 2.4183,
        })
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response())
    )
    card = ProductCard(
        id="p1", name="iPhone 12 Pro", price="350 000 F",
        raw_price=350000, stock=2, store_id="42",
    )

    result = await commercial_agent.handle(
        AgentInput(
            message="ok merci donne moi les coodoner de la boutisue",
            store_id="public",
            correlation_id="reg-coords",
            customer_id="c1",
            conversation_context=ConversationContext(last_cards=[card]),
        )
    )

    assert info_route.called, "la fiche de la boutique du produit affiché doit être consultée"
    assert "search_store" in result.tools_used
    assert "google.com/maps?q=6.3654,2.4183" in result.reply


# ── Photos ───────────────────────────────────────────────────────────


class _VisionGateway(FakeAIGateway):
    def __init__(self, caption: str) -> None:
        super().__init__()
        self.caption = caption
        self.vision_messages: list[ChatMessage] = []

    async def complete_vision(self, messages, temperature=0.2, max_tokens=None) -> ChatResponse:
        self.vision_messages.extend(messages)
        return ChatResponse(content=self.caption, provider="fake", model="vision")


class _BlindGateway(FakeAIGateway):
    async def complete_vision(self, messages, temperature=0.2, max_tokens=None) -> ChatResponse:
        raise RuntimeError("Aucun fournisseur IA capable de vision n'est configuré")


@respx.mock
async def test_image_is_described_then_searched(tool_registry: ToolRegistry) -> None:
    gateway = _VisionGateway("téléphone Samsung Galaxy A15 noir")
    agent = CommercialAgent(ai_gateway=gateway, tool_registry=tool_registry)
    route = respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response())
    )

    result = await agent.handle(
        AgentInput(
            message="tu as ca",
            store_id="public",
            correlation_id="reg-image",
            customer_id="c1",
            image=_TINY_JPEG,
        )
    )

    assert gateway.vision_messages and gateway.vision_messages[0].images == [_TINY_JPEG]
    assert _queries(route) == ["téléphone Samsung Galaxy A15 noir"]
    assert result.cards


@respx.mock
async def test_image_without_vision_is_honest(tool_registry: ToolRegistry) -> None:
    agent = CommercialAgent(ai_gateway=_BlindGateway(), tool_registry=tool_registry)
    route = respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response())
    )

    result = await agent.handle(
        AgentInput(
            message="tu as ca",
            store_id="public",
            correlation_id="reg-image-blind",
            customer_id="c1",
            image=_TINY_JPEG,
        )
    )

    assert not route.called, "aucune recherche inventée sans analyse de l'image"
    assert "n'arrive pas à identifier" in result.reply
    assert not result.cards


@respx.mock
async def test_image_always_routes_to_commercial_agent(orchestrator: TracyOrchestrator) -> None:
    respx.get(url__regex=rf"{MANTOTA_BASE_URL}/.*").mock(return_value=httpx.Response(404))

    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="public", customer_id="c1",
            text="je veux payer", image=_TINY_JPEG,
        )
    )

    assert reply.agent == "CommercialAgent"


class _Provider(AIProvider):
    def __init__(self, name: str, vision: bool) -> None:
        self._name = name
        self._vision = vision

    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> str:
        return f"{self._name}-model"

    @property
    def supports_vision(self) -> bool:
        return self._vision

    async def complete(self, messages, temperature=0.7, max_tokens=None) -> ChatResponse:
        return ChatResponse(content=self._name, provider=self._name, model=self.model)


async def test_complete_vision_skips_blind_providers() -> None:
    gateway = AIGateway(primary=_Provider("ollama", vision=False), fallback=_Provider("openai", vision=True))
    response = await gateway.complete_vision([ChatMessage(role="user", content="?", images=[_TINY_JPEG])])
    assert response.provider == "openai"


async def test_complete_vision_refuses_when_no_vision_provider() -> None:
    gateway = AIGateway(primary=_Provider("ollama", vision=False))
    with pytest.raises(RuntimeError):
        await gateway.complete_vision([ChatMessage(role="user", content="?", images=[_TINY_JPEG])])


# ── Rupture de stock ─────────────────────────────────────────────────


def test_out_of_stock_sorted_after_available_same_scope() -> None:
    a15 = SimpleNamespace(nom="Samsung A15", stock=0, scope="other")
    iphone = SimpleNamespace(nom="iPhone 12", stock=3, scope="other")
    local = SimpleNamespace(nom="Tecno local", stock=0, scope="local")

    ordered = [p.nom for p in sort_by_scope([a15, iphone, local])]

    assert ordered == ["Tecno local", "iPhone 12", "Samsung A15"]
