"""Tests de préservation du contexte de conversation (fix bug context loss).

Valide que:
- ConversationContext est enrichi après une recherche produit
- Les follow-ups ("oui", "combien", "comment je paie") sont routés contextuellement
- L'intent app_download est reconnu
- Le contexte produit est extrait depuis les cards retournées
- Le changement de sujet réinitialise le contexte produit
"""

from __future__ import annotations

import httpx
import pytest
import respx

from app.core.orchestrator import TracyOrchestrator
from app.core.schemas import IncomingMessage
from app.memory.short_term import InMemoryShortTermMemory, ConversationContext

from tests.conftest import MANTOTA_BASE_URL, mock_product_search_response, mock_store_config_response


@respx.mock
async def test_context_enriched_after_product_search(
    orchestrator: TracyOrchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """Après une recherche produit, le contexte est enrichi avec product_name, product_id, etc."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(
            products=[{"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": "store_1"}],
        ))
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/memory/search").mock(
        return_value=httpx.Response(200, json={"entries": [], "total": 0})
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/memory").mock(
        return_value=httpx.Response(200, json={"id": "mem_1", "scope": "client", "entity_id": "client_1", "key": "test", "value": "test", "source": "observed"})
    )

    conv_id = "conv_ctx_test_1"
    await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_1",
            text="Je veux un téléphone",
            conversation_id=conv_id,
        )
    )

    context = await short_term_memory.get_context(conv_id)
    assert context is not None
    assert context.product_name is not None
    assert context.product_id is not None
    assert context.last_intent == "product_search"
    assert context.last_agent == "CommercialAgent"
    assert context.task_state in ("product_found", "products_proposed")


@respx.mock
async def test_followup_routing_unknown_intent(
    orchestrator: TracyOrchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """Un follow-up court avec intent 'unknown' est routé vers le dernier agent."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response())
    )

    conv_id = "conv_followup_1"
    # MSG1: recherche produit
    await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_1",
            text="Je veux un téléphone",
            conversation_id=conv_id,
        )
    )

    # MSG2: follow-up "oui" (intent unknown)
    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_1",
            text="oui",
            conversation_id=conv_id,
        )
    )

    # Doit être routé vers CommercialAgent (dernier agent)
    assert reply.agent == "CommercialAgent"

    context = await short_term_memory.get_context(conv_id)
    assert context.last_user_confirmation == "yes"


@respx.mock
async def test_ok_after_counter_offer_freezes_negotiated_price(
    orchestrator: TracyOrchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """« ok » après une contre-offre fige le dernier prix annoncé (pas une nouvelle relance)."""
    conv_id = "conv_nego_ok"
    ctx = await short_term_memory.get_context(conv_id)
    ctx.last_agent = "NegotiationAgent"
    ctx.last_intent = "negotiation"
    ctx.product_id = "p1"
    ctx.product_name = "Téléphone"
    ctx.product_price = 10000.0
    ctx.negotiation_product_id = "p1"
    ctx.negotiation_rounds = 2
    ctx.negotiation_last_ask = 9000.0
    await short_term_memory.update_context(conv_id, ctx)

    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_1",
            text="ok",
            conversation_id=conv_id,
        )
    )

    assert reply.agent == "CommercialAgent"
    after = await short_term_memory.get_context(conv_id)
    assert after.negotiated_price == 9000.0


@respx.mock
async def test_payment_followup_stays_on_commercial(
    orchestrator: TracyOrchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """Un follow-up 'comment je paie' avec produit en contexte reste sur CommercialAgent."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(
            products=[{"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": "store_1"}],
        ))
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/memory/search").mock(
        return_value=httpx.Response(200, json={"entries": [], "total": 0})
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/memory").mock(
        return_value=httpx.Response(200, json={"id": "mem_1", "scope": "client", "entity_id": "client_1", "key": "test", "value": "test", "source": "observed"})
    )

    conv_id = "conv_payment_1"
    # MSG1: recherche produit
    await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_1",
            text="Je veux un téléphone",
            conversation_id=conv_id,
        )
    )

    # MSG2: "comment je paie" — intent payment mais produit en contexte
    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_1",
            text="comment je paie",
            conversation_id=conv_id,
        )
    )

    # Doit rester sur CommercialAgent, pas PaymentAgent
    assert reply.agent == "CommercialAgent"


@respx.mock
async def test_context_persists_across_messages(
    orchestrator: TracyOrchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """Le contexte persiste entre messages dans la même conversation."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(
            products=[{"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": "store_1"}],
        ))
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/memory/search").mock(
        return_value=httpx.Response(200, json={"entries": [], "total": 0})
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/memory").mock(
        return_value=httpx.Response(200, json={"id": "mem_1", "scope": "client", "entity_id": "client_1", "key": "test", "value": "test", "source": "observed"})
    )

    conv_id = "conv_persist_1"
    # MSG1
    await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_1",
            text="Je veux un téléphone",
            conversation_id=conv_id,
        )
    )

    # Vérifie le contexte après MSG1
    ctx1 = await short_term_memory.get_context(conv_id)
    assert ctx1.product_name is not None

    # MSG2 (follow-up)
    await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_1",
            text="oui",
            conversation_id=conv_id,
        )
    )

    # Le contexte produit doit toujours être là
    ctx2 = await short_term_memory.get_context(conv_id)
    assert ctx2.product_name == ctx1.product_name
    assert ctx2.last_user_confirmation == "yes"


@respx.mock
async def test_different_conversations_isolated(
    orchestrator: TracyOrchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """Deux conversations différentes ont des contextes isolés."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(
            products=[{"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": "store_1"}],
        ))
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/memory/search").mock(
        return_value=httpx.Response(200, json={"entries": [], "total": 0})
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/memory").mock(
        return_value=httpx.Response(200, json={"id": "mem_1", "scope": "client", "entity_id": "client_a", "key": "test", "value": "test", "source": "observed"})
    )

    conv_a = "conv_iso_a"
    conv_b = "conv_iso_b"

    await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_a",
            text="Je veux un téléphone",
            conversation_id=conv_a,
        )
    )

    await orchestrator.handle_message(
        IncomingMessage(
            store_id="public",
            customer_id="client_b",
            text="merci",
            conversation_id=conv_b,
        )
    )

    ctx_a = await short_term_memory.get_context(conv_a)
    ctx_b = await short_term_memory.get_context(conv_b)

    # Conv A a un produit, Conv B n'en a pas
    assert ctx_a.product_name is not None
    assert ctx_b.product_name is None


def test_app_download_intent_classification() -> None:
    """L'intent app_download est reconnu par le classificateur."""
    from app.core.intent import classify_intent

    test_messages = [
        "télécharger l app mantota",
        "ou telecharger l app",
        "download mantota app",
        "installer l application",
        "play store mantota",
        "je veux l app mantota",
    ]

    for msg in test_messages:
        result = classify_intent(msg)
        assert result.intent == "app_download", f"Failed for: {msg}"
        assert result.selected_agent == "CommercialAgent"


def test_app_download_in_intent_enum() -> None:
    """app_download est dans l'énumération des intents (schemas.py)."""
    from app.core.schemas import IntentClassification
    from typing import get_type_hints

    hints = get_type_hints(IntentClassification)
    intent_type = hints.get("intent")
    # Le type Literal doit contenir "app_download"
    assert hasattr(intent_type, "__args__")
    assert "app_download" in intent_type.__args__


def test_conversation_context_fields() -> None:
    """ConversationContext contient tous les champs enrichis."""
    ctx = ConversationContext()
    assert ctx.product_id is None
    assert ctx.product_name is None
    assert ctx.product_price is None
    assert ctx.product_store_id is None
    assert ctx.current_task is None
    assert ctx.task_state is None
    assert ctx.pending_action is None
    assert ctx.last_tool_result is None
    assert ctx.last_user_confirmation is None
    assert ctx.language is None
    assert ctx.last_agent is None
    assert ctx.last_intent is None
