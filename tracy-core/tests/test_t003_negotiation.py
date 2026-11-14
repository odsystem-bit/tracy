"""Tests des scénarios T-003 et T-004 (docs/tracy/09-TEST_SCENARIOS.md).

T-003 : Négociation dans la marge autorisée
    Client : "Je négocie, c'est possible d'avoir un meilleur prix ?"
    Contexte : marge de négociation maximale = 10%.
    Résultat attendu : Tracy propose une contre-offre ne dépassant pas 10% de remise.

T-004 : Négociation hors marge autorisée
    Client : "Fais-moi 50% de réduction."
    Résultat attendu : Tracy refuse clairement, explique la raison, propose une alternative.

Agents impliqués : NegotiationAgent
Tools attendus : search_catalog
"""

from __future__ import annotations

import httpx
import respx

from app.agents.base import AgentInput
from app.agents.negotiation_agent import NegotiationAgent
from app.tools.base import ToolContext
from app.tools.registry import ToolRegistry

from tests.conftest import MANTOTA_BASE_URL, mock_catalog_response


@respx.mock
async def test_t003_negotiation_within_margin(
    negotiation_agent: NegotiationAgent,
) -> None:
    """T-003 : Tracy propose une contre-offre dans la marge."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json={
            "store_id": "store_1",
            "min_margin_percent": 10.0,
            "first_order_discount_percent": 0.0,
            "max_discount_percent": 10.0,
            "free_shipping_threshold": None,
            "auto_accept_below": 5.0,
            "custom_rules": None,
            "currency": "XOF",
        })
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(
            200,
            json=mock_catalog_response(
                products=[
                    {"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": "store_1"},
                ],
            ),
        )
    )

    result = await negotiation_agent.handle(
        AgentInput(
            message="Je négocie, c'est possible d'avoir un meilleur prix ?",
            store_id="store_1",
            correlation_id="test-t003",
            customer_id="client_1",
        ),
    )

    assert result.handled is True
    assert "search_catalog" in result.tools_used


@respx.mock
async def test_t004_negotiation_outside_margin(
    negotiation_agent: NegotiationAgent,
) -> None:
    """T-004 : Tracy refuse une réduction hors marge."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json={
            "store_id": "store_1",
            "min_margin_percent": 10.0,
            "first_order_discount_percent": 0.0,
            "max_discount_percent": 10.0,
            "free_shipping_threshold": None,
            "auto_accept_below": 5.0,
            "custom_rules": None,
            "currency": "XOF",
        })
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(
            200,
            json=mock_catalog_response(
                products=[
                    {"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": "store_1"},
                ],
            ),
        )
    )

    result = await negotiation_agent.handle(
        AgentInput(
            message="Fais-moi 50% de réduction",
            store_id="store_1",
            correlation_id="test-t004",
            customer_id="client_1",
        ),
    )

    assert result.handled is True
    assert "search_catalog" in result.tools_used


@respx.mock
async def test_negotiation_final_offer_schedules_client_followup(
    negotiation_agent: NegotiationAgent,
) -> None:
    """Prix final annoncé sans accord → relance client planifiée via POST /bot/follow-ups.

    WhatsApp : conversation_id 'wa_{phone}_{vendor}' → channel whatsapp, customer_id = phone.
    """
    from app.memory.short_term import ConversationContext

    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/7/config").mock(
        return_value=httpx.Response(200, json={
            "store_id": "7",
            "min_margin_percent": 10.0,
            "first_order_discount_percent": 0.0,
            "max_discount_percent": 10.0,
            "free_shipping_threshold": None,
            "auto_accept_below": 5.0,
            "custom_rules": None,
            "currency": "XOF",
        })
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(
            200,
            json=mock_catalog_response(
                products=[
                    {"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": "7"},
                ],
            ),
        )
    )
    follow_ups = respx.post(f"{MANTOTA_BASE_URL}/bot/follow-ups").mock(
        return_value=httpx.Response(200, json={"success": True, "follow_up_id": 1})
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/vendors/7/reports").mock(
        return_value=httpx.Response(200, json={"success": True})
    )

    conv = ConversationContext()
    conv.product_id = "1"
    conv.product_name = "Tecno Spark 10"
    conv.product_price = 95000.0
    conv.negotiation_product_id = "1"
    conv.negotiation_rounds = 2
    conv.negotiation_last_ask = 90000.0
    conv.negotiation_last_price_asks = 1

    result = await negotiation_agent.handle(
        AgentInput(
            message="c'est quoi ton dernier prix ?",
            store_id="7",
            correlation_id="test-followup",
            customer_id="22990000000",
            conversation_id="wa_22990000000_7",
            conversation_context=conv,
        ),
    )

    assert result.handled is True
    assert follow_ups.called
    body = follow_ups.calls[0].request.read().decode()
    assert '"whatsapp"' in body
    assert "22990000000" in body


@respx.mock
async def test_t003_catalog_unavailable(
    negotiation_agent: NegotiationAgent,
) -> None:
    """T-003 edge case : catalogue indisponible — l'agent informe le client."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json={
            "store_id": "store_1",
            "min_margin_percent": 10.0,
            "first_order_discount_percent": 0.0,
            "max_discount_percent": 10.0,
            "free_shipping_threshold": None,
            "auto_accept_below": 5.0,
            "custom_rules": None,
            "currency": "XOF",
        })
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(500)
    )

    result = await negotiation_agent.handle(
        AgentInput(
            message="Je négocie",
            store_id="store_1",
            correlation_id="test-t003-unavailable",
            customer_id="client_1",
        ),
    )

    assert result.handled is True


@respx.mock
async def test_search_catalog_permission_denied(
    mantota_client: MantotaClient,
    tool_registry: ToolRegistry,
) -> None:
    """Permission : OrderAgent ne peut pas appeler search_catalog."""
    import pytest

    from app.tools.registry import ToolPermissionError

    ctx = ToolContext(
        agent_name="OrderAgent",
        correlation_id="test-perm-catalog",
        store_id="store_1",
    )

    with pytest.raises(ToolPermissionError):
        await tool_registry.execute("search_catalog", ctx, store_id="store_1")
