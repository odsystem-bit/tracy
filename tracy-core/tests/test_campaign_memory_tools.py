"""Tests des tools CampaignAgent et MemoryAgent (docs/tracy/04-TOOLS.md).

Couvre : get_campaign, search_partner, save_memory, search_memory,
update_memory, delete_memory.
"""

from __future__ import annotations

import httpx
import pytest
import respx

pytestmark = pytest.mark.skip_common_mocks

from app.mantota_client.client import MantotaClient
from app.tools.base import ToolContext
from app.tools.delete_memory import DeleteMemoryTool
from app.tools.get_campaign import GetCampaignTool
from app.tools.save_memory import SaveMemoryTool
from app.tools.search_memory import SearchMemoryTool
from app.tools.search_partner import SearchPartnerTool
from app.tools.update_memory import UpdateMemoryTool

from tests.conftest import MANTOTA_BASE_URL


# ── get_campaign ──────────────────────────────────────────────────


@respx.mock
async def test_get_campaign_success(mantota_client: MantotaClient) -> None:
    """get_campaign retourne les détails d'une campagne."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/campaigns/camp_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "camp_1",
                "nom": "Soldes Janvier",
                "statut": "active",
                "audience": "all",
                "vues": 1500,
                "clics": 300,
                "conversions": 45,
            },
        )
    )

    ctx = ToolContext(
        agent_name="CampaignAgent",
        correlation_id="test-campaign",
        store_id="store_1",
    )

    tool = GetCampaignTool(mantota_client)
    result = await tool.execute(ctx, campaign_id="camp_1")

    assert result.success
    assert result.data is not None
    assert result.data.nom == "Soldes Janvier"
    assert result.data.conversions == 45


@respx.mock
async def test_get_campaign_not_found(mantota_client: MantotaClient) -> None:
    """get_campaign retourne CAMPAIGN_NOT_FOUND."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/campaigns/unknown").mock(
        return_value=httpx.Response(404)
    )

    ctx = ToolContext(
        agent_name="CampaignAgent",
        correlation_id="test-campaign",
        store_id="store_1",
    )

    tool = GetCampaignTool(mantota_client)
    result = await tool.execute(ctx, campaign_id="unknown")

    assert not result.success
    assert "CAMPAIGN_NOT_FOUND" in result.error.code  # type: ignore[union-attr]


# ── search_partner ────────────────────────────────────────────────


@respx.mock
async def test_search_partner_success(mantota_client: MantotaClient) -> None:
    """search_partner retourne un partenaire."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/partners/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "partner_1",
                "nom": "Awa Diallo",
                "commissions_cumulees": 75000,
                "code_parrainage": "AWA2025",
            },
        )
    )

    ctx = ToolContext(
        agent_name="CampaignAgent",
        correlation_id="test-partner",
        store_id="store_1",
    )

    tool = SearchPartnerTool(mantota_client)
    result = await tool.execute(ctx, query="Awa")

    assert result.success
    assert result.data is not None
    assert result.data.nom == "Awa Diallo"
    assert result.data.code_parrainage == "AWA2025"


async def test_search_partner_empty_query(mantota_client: MantotaClient) -> None:
    """search_partner échoue avec une requête vide."""
    ctx = ToolContext(
        agent_name="CampaignAgent",
        correlation_id="test-partner",
        store_id="store_1",
    )

    tool = SearchPartnerTool(mantota_client)
    result = await tool.execute(ctx, query="")

    assert not result.success
    assert "INVALID_QUERY" in result.error.code  # type: ignore[union-attr]


# ── save_memory ───────────────────────────────────────────────────


@respx.mock
async def test_save_memory_success(mantota_client: MantotaClient) -> None:
    """save_memory enregistre une entrée avec des paramètres valides."""
    respx.post(f"{MANTOTA_BASE_URL}/bot/memory").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "mem_1",
                "scope": "client",
                "entity_id": "client_1",
                "key": "preferred_category",
                "value": "électronique",
                "source": "inferred",
                "created_at": "2025-01-01T10:00:00Z",
            },
        )
    )

    ctx = ToolContext(
        agent_name="MemoryAgent",
        correlation_id="test-memory",
        store_id="store_1",
    )

    tool = SaveMemoryTool(mantota_client)
    result = await tool.execute(
        ctx,
        scope="client",
        entity_id="client_1",
        key="preferred_category",
        value="électronique",
    )

    assert result.success
    assert result.data is not None
    assert result.data.id == "mem_1"


async def test_save_memory_invalid_scope(mantota_client: MantotaClient) -> None:
    """save_memory échoue avec un scope invalide."""
    ctx = ToolContext(
        agent_name="MemoryAgent",
        correlation_id="test-memory",
        store_id="store_1",
    )

    tool = SaveMemoryTool(mantota_client)
    result = await tool.execute(
        ctx,
        scope="invalid",
        entity_id="client_1",
        key="test",
        value="test",
    )

    assert not result.success
    assert "INVALID_SCOPE" in result.error.code  # type: ignore[union-attr]


# ── search_memory ─────────────────────────────────────────────────


@respx.mock
async def test_search_memory_success(mantota_client: MantotaClient) -> None:
    """search_memory retourne des entrées."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/memory/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "entries": [
                    {
                        "id": "mem_1",
                        "scope": "client",
                        "entity_id": "client_1",
                        "key": "preferred_category",
                        "value": "électronique",
                        "source": "inferred",
                    },
                ],
                "total": 1,
            },
        )
    )

    ctx = ToolContext(
        agent_name="MemoryAgent",
        correlation_id="test-memory",
        store_id="store_1",
    )

    tool = SearchMemoryTool(mantota_client)
    result = await tool.execute(
        ctx,
        scope="client",
        entity_id="client_1",
        query="préférence",
    )

    assert result.success
    assert result.data is not None
    assert result.data.total == 1
    assert result.data.entries[0].key == "preferred_category"


# ── update_memory ─────────────────────────────────────────────────


@respx.mock
async def test_update_memory_success(mantota_client: MantotaClient) -> None:
    """update_memory met à jour une entrée."""
    respx.patch(f"{MANTOTA_BASE_URL}/bot/memory/mem_1").mock(
        return_value=httpx.Response(200, json={"updated": True})
    )

    ctx = ToolContext(
        agent_name="MemoryAgent",
        correlation_id="test-memory",
        store_id="store_1",
    )

    tool = UpdateMemoryTool(mantota_client)
    result = await tool.execute(ctx, memory_id="mem_1", value="nouvelle valeur")

    assert result.success
    assert result.data is not None
    assert result.data.updated is True


@respx.mock
async def test_update_memory_not_found(mantota_client: MantotaClient) -> None:
    """update_memory retourne MEMORY_NOT_FOUND."""
    respx.patch(f"{MANTOTA_BASE_URL}/bot/memory/unknown").mock(
        return_value=httpx.Response(404)
    )

    ctx = ToolContext(
        agent_name="MemoryAgent",
        correlation_id="test-memory",
        store_id="store_1",
    )

    tool = UpdateMemoryTool(mantota_client)
    result = await tool.execute(ctx, memory_id="unknown", value="test")

    assert not result.success
    assert "MEMORY_NOT_FOUND" in result.error.code  # type: ignore[union-attr]


# ── delete_memory ─────────────────────────────────────────────────


@respx.mock
async def test_delete_memory_success(mantota_client: MantotaClient) -> None:
    """delete_memory supprime une entrée."""
    respx.route(method="DELETE", url=f"{MANTOTA_BASE_URL}/bot/memory/mem_1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )

    ctx = ToolContext(
        agent_name="MemoryAgent",
        correlation_id="test-memory",
        store_id="store_1",
    )

    tool = DeleteMemoryTool(mantota_client)
    result = await tool.execute(ctx, memory_id="mem_1", reason="droit à l'oubli")

    assert result.success
    assert result.data is not None
    assert result.data.deleted is True


@respx.mock
async def test_delete_memory_not_found(mantota_client: MantotaClient) -> None:
    """delete_memory retourne MEMORY_NOT_FOUND."""
    respx.route(method="DELETE", url=f"{MANTOTA_BASE_URL}/bot/memory/unknown").mock(
        return_value=httpx.Response(404)
    )

    ctx = ToolContext(
        agent_name="MemoryAgent",
        correlation_id="test-memory",
        store_id="store_1",
    )

    tool = DeleteMemoryTool(mantota_client)
    result = await tool.execute(ctx, memory_id="unknown", reason="test")

    assert not result.success
    assert "MEMORY_NOT_FOUND" in result.error.code  # type: ignore[union-attr]
