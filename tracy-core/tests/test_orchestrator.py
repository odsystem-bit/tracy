"""Tests de l'orchestrateur Tracy Core (docs/tracy/02-ARCHITECTURE.md).

Valide le flux complet : message → classification → agent → réponse,
avec mémoire courte et traçabilité (correlation_id).
"""

from __future__ import annotations

import httpx
import respx

from app.core.orchestrator import TracyOrchestrator
from app.core.schemas import IncomingMessage
from app.memory.short_term import InMemoryShortTermMemory

from tests.conftest import MANTOTA_BASE_URL, mock_product_search_response, mock_catalog_response, mock_store_config_response


@respx.mock
async def test_orchestrator_routes_to_commercial(
    orchestrator: TracyOrchestrator,
) -> None:
    """L'orchestrateur route une recherche produit vers CommercialAgent."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response())
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/memory/search").mock(
        return_value=httpx.Response(200, json={"entries": [], "total": 0})
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/memory").mock(
        return_value=httpx.Response(200, json={"id": "mem_1", "scope": "client", "entity_id": "client_1", "key": "test", "value": "test", "source": "observed"})
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_1",
            text="Je veux un téléphone à 100 000 FCFA",
        )
    )

    assert reply.correlation_id
    assert reply.agent == "CommercialAgent"
    assert "search_products" in reply.tools_used
    assert len(reply.text) > 0


@respx.mock
async def test_orchestrator_routes_to_negotiation(
    orchestrator: TracyOrchestrator,
) -> None:
    """L'orchestrateur route une négociation vers NegotiationAgent."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
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
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(200, json=mock_catalog_response())
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_1",
            text="Je négocie, c'est possible d'avoir un meilleur prix ?",
        )
    )

    assert reply.agent == "NegotiationAgent"
    assert "search_catalog" in reply.tools_used


@respx.mock
async def test_orchestrator_routes_to_catalog(
    orchestrator: TracyOrchestrator,
) -> None:
    """L'orchestrateur route une gestion de catalogue vers CatalogAgent."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(200, json=mock_catalog_response())
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/memory/search").mock(
        return_value=httpx.Response(200, json={"entries": [], "total": 0})
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/memory").mock(
        return_value=httpx.Response(200, json={"id": "mem_1", "scope": "client", "entity_id": "vendor_1", "key": "test", "value": "test", "source": "observed"})
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="vendor_1",
            text="Augmente le prix du riz à 650 FCFA",
        )
    )

    assert reply.agent == "CatalogAgent"
    assert "search_catalog" in reply.tools_used


@respx.mock
async def test_orchestrator_routes_to_order(
    orchestrator: TracyOrchestrator,
) -> None:
    """L'orchestrateur route une commande vers OrderAgent."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_1",
            text="Je confirme, je prends celui-là",
        )
    )

    assert reply.agent == "OrderAgent"
    assert len(reply.text) > 0


@respx.mock
async def test_orchestrator_short_term_memory(
    orchestrator: TracyOrchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """L'orchestrateur sauvegarde les messages dans la mémoire courte."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response())
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/memory/search").mock(
        return_value=httpx.Response(200, json={"entries": [], "total": 0})
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/memory").mock(
        return_value=httpx.Response(200, json={"id": "mem_1", "scope": "client", "entity_id": "client_1", "key": "test", "value": "test", "source": "observed"})
    )

    await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_1",
            text="Je veux un téléphone",
            conversation_id="conv_test_1",
        )
    )

    history = await short_term_memory.get_history("conv_test_1")
    assert len(history) == 2  # user + assistant
    assert history[0].role == "user"
    assert history[0].content == "Je veux un téléphone"
    assert history[1].role == "assistant"
