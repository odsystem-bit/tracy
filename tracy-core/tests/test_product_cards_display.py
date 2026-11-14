"""Tests pour le fix d'affichage des cartes produit (bug cards manquantes).

Valide que:
1. Les cards sont toujours présentes quand le texte mentionne des produits
2. L'intention "afficher catalogue/image" avec produits récents renvoie les cards
3. _is_boutique_q ne classe pas "catalogue" comme non-produit quand il y a un contexte produit
4. _is_boutique_q garde le comportement actuel sans contexte produit (non-régression)
5. Les follow-ups (combien, disponible) attachent les cards du contexte
6. Le fallback GPT final attache les cards du contexte
"""

from __future__ import annotations

import httpx
import pytest
import respx

from app.agents.base import AgentInput
from app.agents.commercial_agent import CommercialAgent
from app.core.schemas import IncomingMessage, ProductCard
from app.memory.short_term import ConversationContext, InMemoryShortTermMemory

from tests.conftest import MANTOTA_BASE_URL, mock_product_search_response


# ── Helpers ────────────────────────────────────────────────────────────


def _make_cards(n: int = 2) -> list[ProductCard]:
    return [
        ProductCard(
            id=str(i),
            name=f"Produit Test {i}",
            price=f"{95000 + i * 5000:,}".replace(",", " ") + " F",
            raw_price=95000.0 + i * 5000,
            stock=5,
            image_url=f"https://example.com/img{i}.jpg" if i % 2 == 0 else None,
            store_id="store_1",
            category="Téléphones",
        )
        for i in range(1, n + 1)
    ]


def _make_ctx_with_cards(cards: list[ProductCard] | None = None) -> ConversationContext:
    ctx = ConversationContext()
    ctx.last_cards = cards or _make_cards()
    ctx.product_name = cards[0].name if cards else "Produit Test 1"
    ctx.product_id = cards[0].id if cards else "1"
    ctx.product_price = cards[0].raw_price if cards else 95000.0
    ctx.product_store_id = "store_1"
    ctx.task_state = "products_proposed"
    ctx.current_task = "product_search"
    return ctx


# ── 1. Show-products intent: "voir" / "montre" / "catalogue" with recent cards ──


@pytest.mark.asyncio
async def test_show_products_intent_voir(commercial_agent: CommercialAgent) -> None:
    """Client dit "voir" avec cartes récentes → cards renvoyées."""
    ctx = _make_ctx_with_cards()
    inp = AgentInput(
        message="je veux voir",
        store_id="public",
        correlation_id="test-voir",
        customer_id="c1",
        conversation_context=ctx,
    )
    out = await commercial_agent.handle(inp)
    assert out.cards is not None
    assert len(out.cards) == len(ctx.last_cards)
    assert out.handled is True


@pytest.mark.asyncio
async def test_show_products_intent_catalogue(commercial_agent: CommercialAgent) -> None:
    """Client dit "catalogue" avec cartes récentes → cards renvoyées, pas de boucle."""
    ctx = _make_ctx_with_cards()
    inp = AgentInput(
        message="je veux voir le catalogue",
        store_id="public",
        correlation_id="test-cat",
        customer_id="c1",
        conversation_context=ctx,
    )
    out = await commercial_agent.handle(inp)
    assert out.cards is not None
    assert len(out.cards) == len(ctx.last_cards)


@pytest.mark.asyncio
async def test_show_products_intent_image(commercial_agent: CommercialAgent) -> None:
    """Client dit "image" avec cartes récentes → cards renvoyées."""
    ctx = _make_ctx_with_cards()
    inp = AgentInput(
        message="où sont les images",
        store_id="public",
        correlation_id="test-img",
        customer_id="c1",
        conversation_context=ctx,
    )
    out = await commercial_agent.handle(inp)
    assert out.cards is not None
    assert len(out.cards) == len(ctx.last_cards)


@pytest.mark.asyncio
async def test_show_products_intent_montre_moi(commercial_agent: CommercialAgent) -> None:
    """Client dit "montre-moi" avec cartes récentes → cards renvoyées."""
    ctx = _make_ctx_with_cards()
    inp = AgentInput(
        message="montre-moi les produits",
        store_id="public",
        correlation_id="test-montre",
        customer_id="c1",
        conversation_context=ctx,
    )
    out = await commercial_agent.handle(inp)
    assert out.cards is not None
    assert len(out.cards) == len(ctx.last_cards)


# ── 2. Non-régression: "catalogue" sans contexte produit → comportement inchangé ──


@pytest.mark.asyncio
async def test_catalogue_without_recent_cards_no_loop(commercial_agent: CommercialAgent) -> None:
    """"catalogue" sans cartes récentes → pas de show-products intent, comportement normal."""
    inp = AgentInput(
        message="tu as quoi comme catalogue",
        store_id="public",
        correlation_id="test-no-ctx",
        customer_id="c1",
        conversation_context=None,
    )
    out = await commercial_agent.handle(inp)
    # Pas de crash, réponse générée
    assert out.handled is True
    assert out.reply


# ── 3. Follow-up question attache les cards du contexte ──


@pytest.mark.asyncio
async def test_followup_question_attaches_cards(commercial_agent: CommercialAgent) -> None:
    """Follow-up "combien" avec produit en contexte → cards attachées."""
    ctx = _make_ctx_with_cards()
    inp = AgentInput(
        message="combien ça coûte",
        store_id="public",
        correlation_id="test-fu-q",
        customer_id="c1",
        conversation_context=ctx,
    )
    out = await commercial_agent.handle(inp)
    assert out.cards is not None
    assert len(out.cards) == len(ctx.last_cards)


@pytest.mark.asyncio
async def test_followup_confirm_attaches_cards(commercial_agent: CommercialAgent) -> None:
    """Follow-up "oui" avec produit en contexte → cards attachées."""
    ctx = _make_ctx_with_cards()
    inp = AgentInput(
        message="oui",
        store_id="public",
        correlation_id="test-fu-c",
        customer_id="c1",
        conversation_context=ctx,
    )
    out = await commercial_agent.handle(inp)
    assert out.cards is not None
    assert len(out.cards) == len(ctx.last_cards)


@pytest.mark.asyncio
async def test_followup_disponible_attaches_cards(commercial_agent: CommercialAgent) -> None:
    """Follow-up "disponible" avec produit en contexte → cards attachées."""
    ctx = _make_ctx_with_cards()
    inp = AgentInput(
        message="c'est disponible",
        store_id="public",
        correlation_id="test-fu-d",
        customer_id="c1",
        conversation_context=ctx,
    )
    out = await commercial_agent.handle(inp)
    assert out.cards is not None
    assert len(out.cards) == len(ctx.last_cards)


# ── 4. Fallback GPT final attache les cards du contexte ──


@pytest.mark.asyncio
async def test_fallback_gpt_attaches_cards(commercial_agent: CommercialAgent) -> None:
    """Message non-reconnu avec contexte produit → fallback GPT attache les cards."""
    ctx = _make_ctx_with_cards()
    inp = AgentInput(
        message="je ne sais pas quoi choisir",
        store_id="public",
        correlation_id="test-fb",
        customer_id="c1",
        conversation_context=ctx,
    )
    out = await commercial_agent.handle(inp)
    assert out.cards is not None
    assert len(out.cards) == len(ctx.last_cards)


# ── 5. Intégration: recherche produit → puis "voir" renvoie les mêmes cards ──


@respx.mock
@pytest.mark.asyncio
async def test_integration_search_then_show(
    orchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """Recherche produit → "voir" renvoie les cards de la recherche précédente."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json={
            "store_id": "store_1",
            "min_margin_percent": 10.0,
            "first_order_discount_percent": 0.0,
            "max_discount_percent": 15.0,
            "free_shipping_threshold": None,
            "auto_accept_below": 5.0,
            "custom_rules": None,
            "currency": "XOF",
        })
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(
            products=[
                {"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": "https://example.com/tecno.jpg", "store_id": "store_1"},
                {"id": "2", "nom": "Infinix Hot 30", "prix": 90000, "stock": 3, "image_url": None, "store_id": "store_1"},
            ],
        ))
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/memory/search").mock(
        return_value=httpx.Response(200, json={"entries": [], "total": 0})
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/memory").mock(
        return_value=httpx.Response(200, json={"id": "mem_1", "scope": "client", "entity_id": "c1", "key": "test", "value": "test", "source": "observed"})
    )

    conv_id = "conv_show_test"

    # MSG1: recherche produit
    reply1 = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="c1",
            text="Je veux un téléphone",
            conversation_id=conv_id,
        )
    )
    assert reply1.cards is not None
    assert len(reply1.cards) == 2

    # MSG2: "voir" → doit renvoyer les mêmes cards
    reply2 = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="c1",
            text="je veux voir",
            conversation_id=conv_id,
        )
    )
    assert reply2.cards is not None
    assert len(reply2.cards) == 2
    assert reply2.cards[0].id == reply1.cards[0].id


# ── 6. Intégration: "catalogue" après recherche ne boucle pas ──


@respx.mock
@pytest.mark.asyncio
async def test_integration_catalogue_after_search_no_loop(
    orchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """Recherche produit → "catalogue" renvoie les cards, pas une réponse générique."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json={
            "store_id": "store_1",
            "min_margin_percent": 10.0,
            "first_order_discount_percent": 0.0,
            "max_discount_percent": 15.0,
            "free_shipping_threshold": None,
            "auto_accept_below": 5.0,
            "custom_rules": None,
            "currency": "XOF",
        })
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(
            products=[
                {"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": "store_1"},
            ],
        ))
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/memory/search").mock(
        return_value=httpx.Response(200, json={"entries": [], "total": 0})
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/memory").mock(
        return_value=httpx.Response(200, json={"id": "mem_1", "scope": "client", "entity_id": "c1", "key": "test", "value": "test", "source": "observed"})
    )

    conv_id = "conv_cat_loop_test"

    # MSG1: recherche produit
    reply1 = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="c1",
            text="Je cherche un téléphone",
            conversation_id=conv_id,
        )
    )
    assert reply1.cards is not None

    # MSG2: "catalogue" → doit renvoyer les cards, pas boucler
    reply2 = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="c1",
            text="montre-moi le catalogue",
            conversation_id=conv_id,
        )
    )
    assert reply2.cards is not None
    assert len(reply2.cards) >= 1


# ── 7. last_cards sauvegardé dans le contexte par l'orchestrateur ──


@respx.mock
@pytest.mark.asyncio
async def test_last_cards_saved_in_context(
    orchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """Après une recherche produit, last_cards est sauvegardé dans le contexte."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json={
            "store_id": "store_1",
            "min_margin_percent": 10.0,
            "first_order_discount_percent": 0.0,
            "max_discount_percent": 15.0,
            "free_shipping_threshold": None,
            "auto_accept_below": 5.0,
            "custom_rules": None,
            "currency": "XOF",
        })
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(
            products=[
                {"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": "https://example.com/t.jpg", "store_id": "store_1"},
            ],
        ))
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/memory/search").mock(
        return_value=httpx.Response(200, json={"entries": [], "total": 0})
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/memory").mock(
        return_value=httpx.Response(200, json={"id": "mem_1", "scope": "client", "entity_id": "c1", "key": "test", "value": "test", "source": "observed"})
    )

    conv_id = "conv_last_cards_test"

    await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="c1",
            text="Je veux un téléphone",
            conversation_id=conv_id,
        )
    )

    context = await short_term_memory.get_context(conv_id)
    assert context.last_cards is not None
    assert len(context.last_cards) == 1
    assert context.last_cards[0].name == "Tecno Spark 10"
    assert context.last_cards[0].image_url == "https://example.com/t.jpg"
