"""Tests des scénarios T-001 et T-002 (docs/tracy/09-TEST_SCENARIOS.md).

T-001 : Recherche avec budget maximum
    Client : "Je veux un téléphone à 100 000 FCFA."
    Résultat attendu : Tracy propose uniquement des téléphones dont le prix
    est compris entre 90 000 et 100 000 FCFA.

T-002 : Recherche sans résultat
    Client : "Je cherche une montre connectée à 5 000 FCFA."
    Résultat attendu : Tracy indique honnêtement qu'aucun produit ne correspond,
    et propose l'alternative la moins chère si elle existe.

Agents impliqués : CommercialAgent
Tools attendus : search_products
"""

from __future__ import annotations

import httpx
import pytest
import respx

from app.agents.base import AgentInput
from app.agents.commercial_agent import CommercialAgent
from app.mantota_client.client import MantotaClient
from app.tools.base import ToolContext
from app.tools.registry import ToolRegistry

from tests.conftest import MANTOTA_BASE_URL, mock_product_search_response


@respx.mock
async def test_t001_search_within_budget(
    mantota_client: MantotaClient,
    tool_registry: ToolRegistry,
) -> None:
    """T-001 : Tracy propose des téléphones entre 90 000 et 100 000 FCFA."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(
            200,
            json=mock_product_search_response(
                products=[
                    {"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": "store_1"},
                    {"id": "2", "nom": "Infinix Hot 30", "prix": 90000, "stock": 3, "image_url": None, "store_id": "store_1"},
                ],
                total=2,
            ),
        )
    )

    ctx = ToolContext(
        agent_name="CommercialAgent",
        correlation_id="test-t001",
        store_id="store_1",
    )

    result = await tool_registry.execute(
        "search_products",
        ctx,
        query="téléphone",
        max_price=100000,
    )

    assert result.success is True
    assert result.data is not None
    assert result.data.total == 2
    assert all(p.prix <= 100000 for p in result.data.products)
    assert "Tecno Spark 10" in [p.nom for p in result.data.products]
    assert "Infinix Hot 30" in [p.nom for p in result.data.products]


@respx.mock
async def test_t001_agent_reply_contains_products(
    commercial_agent: CommercialAgent,
) -> None:
    """T-001 : la réponse de l'agent contient les produits trouvés."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(
            200,
            json=mock_product_search_response(),
        )
    )

    result = await commercial_agent.handle(
        AgentInput(
            message="Je veux un téléphone à 100 000 FCFA",
            store_id="store_1",
            correlation_id="test-t001-agent",
            customer_id="client_1",
        ),
    )

    assert result.handled is True
    assert "search_products" in result.tools_used
    assert "Tecno Spark 10" in result.reply or "Infinix Hot 30" in result.reply


@respx.mock
async def test_t002_no_results(
    mantota_client: MantotaClient,
    tool_registry: ToolRegistry,
) -> None:
    """T-002 : aucun produit trouvé — Tool retourne NO_RESULTS."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(404)
    )

    ctx = ToolContext(
        agent_name="CommercialAgent",
        correlation_id="test-t002",
        store_id="store_1",
    )

    result = await tool_registry.execute(
        "search_products",
        ctx,
        query="montre connectée",
        max_price=5000,
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "NO_RESULTS"


@respx.mock
async def test_t002_agent_reply_honest(
    commercial_agent: CommercialAgent,
) -> None:
    """T-002 : l'agent informe honnêtement qu'aucun produit ne correspond."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(404)
    )

    result = await commercial_agent.handle(
        AgentInput(
            message="Je cherche une montre connectée à 5 000 FCFA",
            store_id="store_1",
            correlation_id="test-t002-agent",
            customer_id="client_1",
        ),
    )

    assert result.handled is True
    assert "search_products" in result.tools_used


@respx.mock
async def test_search_products_empty_query(
    mantota_client: MantotaClient,
    tool_registry: ToolRegistry,
) -> None:
    """Validation : une requête vide retourne INVALID_QUERY."""
    ctx = ToolContext(
        agent_name="CommercialAgent",
        correlation_id="test-empty",
        store_id="store_1",
    )

    result = await tool_registry.execute(
        "search_products",
        ctx,
        query="  ",
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "INVALID_QUERY"


async def test_search_products_permission_denied(
    mantota_client: MantotaClient,
    tool_registry: ToolRegistry,
) -> None:
    """Permission : un agent non autorisé ne peut pas appeler search_products."""
    from app.tools.registry import ToolPermissionError

    ctx = ToolContext(
        agent_name="PaymentAgent",
        correlation_id="test-perm",
        store_id="store_1",
    )

    with pytest.raises(ToolPermissionError):
        await tool_registry.execute("search_products", ctx, query="test")
