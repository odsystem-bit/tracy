"""Tests du scénario T-005 (docs/tracy/09-TEST_SCENARIOS.md).

T-005 : Envoi du catalogue
    Client : "Envoie-moi le catalogue."
    Résultat attendu : Tracy envoie les produits de la boutique concernée
    uniquement — jamais le catalogue d'une autre boutique.

Agents impliqués : CommercialAgent
Tools attendus : send_catalog
"""

from __future__ import annotations

import httpx
import respx

from app.agents.base import AgentInput
from app.agents.catalog_agent import CatalogAgent
from app.mantota_client.client import MantotaClient
from app.tools.base import ToolContext
from app.tools.registry import ToolRegistry

from tests.conftest import MANTOTA_BASE_URL, mock_catalog_response


@respx.mock
async def test_t005_send_catalog(
    mantota_client: MantotaClient,
    tool_registry: ToolRegistry,
) -> None:
    """T-005 : send_catalog envoie le catalogue de la boutique concernée."""
    respx.post(f"{MANTOTA_BASE_URL}/bot/catalog/send").mock(
        return_value=httpx.Response(
            200,
            json={"sent": True, "store_id": "store_1", "channel": "whatsapp"},
        )
    )

    ctx = ToolContext(
        agent_name="CommercialAgent",
        correlation_id="test-t005",
        store_id="store_1",
    )

    result = await tool_registry.execute(
        "send_catalog",
        ctx,
        store_id="store_1",
        channel="whatsapp",
    )

    assert result.success is True
    assert result.data is not None
    assert result.data.sent is True
    assert result.data.store_id == "store_1"


@respx.mock
async def test_t005_send_catalog_specific_products(
    mantota_client: MantotaClient,
    tool_registry: ToolRegistry,
) -> None:
    """T-005 : send_catalog avec une sélection de produits."""
    respx.post(f"{MANTOTA_BASE_URL}/bot/catalog/send").mock(
        return_value=httpx.Response(
            200,
            json={"sent": True},
        )
    )

    ctx = ToolContext(
        agent_name="CommercialAgent",
        correlation_id="test-t005-products",
        store_id="store_1",
    )

    result = await tool_registry.execute(
        "send_catalog",
        ctx,
        store_id="store_1",
        product_ids=["1", "2", "3"],
        channel="whatsapp",
    )

    assert result.success is True
    assert result.data is not None
    assert result.data.product_count == 3


async def test_t005_send_catalog_no_store_id(
    mantota_client: MantotaClient,
    tool_registry: ToolRegistry,
) -> None:
    """T-005 edge case : pas de store_id — retourne STORE_REQUIRED."""
    ctx = ToolContext(
        agent_name="CommercialAgent",
        correlation_id="test-t005-no-store",
        store_id=None,
    )

    result = await tool_registry.execute(
        "send_catalog",
        ctx,
        channel="whatsapp",
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "STORE_REQUIRED"


@respx.mock
async def test_t005_catalog_agent_reply(
    catalog_agent: CatalogAgent,
) -> None:
    """T-005 : CatalogAgent répond avec le catalogue de la boutique."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(
            200,
            json=mock_catalog_response(
                products=[
                    {"id": "1", "nom": "Sac à main", "prix": 15000, "stock": 10, "image_url": None, "store_id": "store_1"},
                ],
            ),
        )
    )

    result = await catalog_agent.handle(
        AgentInput(
            message="Affiche-moi le catalogue",
            store_id="store_1",
            correlation_id="test-t005-agent",
            customer_id="vendor_1",
        ),
    )

    assert result.handled is True
    assert "search_catalog" in result.tools_used
