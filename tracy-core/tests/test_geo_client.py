"""Tests unitaires — Méthodes géographiques du MantotaClient.

Couvre :
  - resolve_geo (quartier trouvé, ville fallback, non trouvé)
  - get_ville_quartiers
  - get_delivery_quartiers
  - set_delivery_quartiers (par IDs, par ville, avec exclusion)
  - remove_delivery_quartier
"""

from __future__ import annotations

import pytest
import respx
import httpx

from app.mantota_client.client import MantotaClient, MantotaNotFoundError

MANTOTA_BASE_URL = "https://mantota.test/api"


@pytest.fixture
def client() -> MantotaClient:
    return MantotaClient(
        base_url=MANTOTA_BASE_URL,
        api_key="test-bot-key",
        retry_max=1,
        retry_backoff=0.01,
    )


# ── resolve_geo ──────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_resolve_geo_quartier_found(client: MantotaClient):
    respx.get(f"{MANTOTA_BASE_URL}/api/geo/resolve").mock(
        return_value=httpx.Response(200, json={
            "found": True,
            "type": "quartier",
            "id": 1,
            "name": "Ganhi",
            "arrondissement": "Cotonou I",
            "ville_id": 1,
            "ville_name": "Cotonou",
            "department": "Littoral",
        })
    )

    result = await client.resolve_geo("Ganhi")

    assert result["found"] is True
    assert result["type"] == "quartier"
    assert result["name"] == "Ganhi"
    assert result["ville_name"] == "Cotonou"


@pytest.mark.asyncio
@respx.mock
async def test_resolve_geo_ville_fallback(client: MantotaClient):
    respx.get(f"{MANTOTA_BASE_URL}/api/geo/resolve").mock(
        return_value=httpx.Response(200, json={
            "found": True,
            "type": "ville",
            "id": 5,
            "name": "Parakou",
            "department": "Borgou",
            "country_id": 1,
        })
    )

    result = await client.resolve_geo("parakou")

    assert result["found"] is True
    assert result["type"] == "ville"
    assert result["name"] == "Parakou"


@pytest.mark.asyncio
@respx.mock
async def test_resolve_geo_not_found(client: MantotaClient):
    respx.get(f"{MANTOTA_BASE_URL}/api/geo/resolve").mock(
        return_value=httpx.Response(404, json={
            "found": False,
            "query": "VilleInexistante",
            "message": "Aucun quartier ou ville trouvé.",
        })
    )

    result = await client.resolve_geo("VilleInexistante")

    assert result["found"] is False
    assert result["query"] == "VilleInexistante"


# ── get_ville_quartiers ──────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_get_ville_quartiers(client: MantotaClient):
    respx.get(f"{MANTOTA_BASE_URL}/api/villes/1/quartiers").mock(
        return_value=httpx.Response(200, json={
            "ville": {"id": 1, "name": "Cotonou", "department": "Littoral"},
            "quartiers": [
                {"id": 1, "name": "Ganhi", "arrondissement_name": "Cotonou I"},
                {"id": 2, "name": "Dantokpa", "arrondissement_name": "Cotonou I"},
            ],
        })
    )

    result = await client.get_ville_quartiers(1)

    assert result["ville"]["name"] == "Cotonou"
    assert len(result["quartiers"]) == 2
    assert result["quartiers"][0]["name"] == "Ganhi"


# ── get_delivery_quartiers ───────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_get_delivery_quartiers(client: MantotaClient):
    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/store_1/delivery-quartiers").mock(
        return_value=httpx.Response(200, json={
            "store_id": "store_1",
            "delivery_mode": "quartiers",
            "quartiers": [
                {"id": 1, "name": "Ganhi", "arrondissement_name": "Cotonou I", "ville_id": 1},
            ],
        })
    )

    result = await client.get_delivery_quartiers("store_1")

    assert result["store_id"] == "store_1"
    assert result["delivery_mode"] == "quartiers"
    assert len(result["quartiers"]) == 1


# ── set_delivery_quartiers ───────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_set_delivery_quartiers_by_ids(client: MantotaClient):
    respx.post(f"{MANTOTA_BASE_URL}/bot/stores/store_1/delivery-quartiers").mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "store_id": "store_1",
            "added": 3,
            "total": 3,
            "message": "Quartiers de livraison mis à jour.",
        })
    )

    result = await client.set_delivery_quartiers("store_1", quartier_ids=[1, 2, 3])

    assert result["success"] is True
    assert result["added"] == 3


@pytest.mark.asyncio
@respx.mock
async def test_set_delivery_quartiers_whole_city(client: MantotaClient):
    respx.post(f"{MANTOTA_BASE_URL}/bot/stores/store_1/delivery-quartiers").mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "store_id": "store_1",
            "added": 20,
            "total": 20,
            "message": "Quartiers de livraison mis à jour.",
        })
    )

    result = await client.set_delivery_quartiers("store_1", ville_id=1)

    assert result["success"] is True
    assert result["total"] == 20


@pytest.mark.asyncio
@respx.mock
async def test_set_delivery_quartiers_city_with_exclusion(client: MantotaClient):
    respx.post(f"{MANTOTA_BASE_URL}/bot/stores/store_1/delivery-quartiers").mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "store_id": "store_1",
            "added": 19,
            "total": 19,
            "message": "Quartiers de livraison mis à jour.",
        })
    )

    result = await client.set_delivery_quartiers(
        "store_1",
        ville_id=1,
        exclude_quartier_ids=[5],
    )

    assert result["success"] is True
    assert result["total"] == 19


# ── remove_delivery_quartier ─────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_remove_delivery_quartier(client: MantotaClient):
    respx.delete(f"{MANTOTA_BASE_URL}/bot/stores/store_1/delivery-quartiers/5").mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "store_id": "store_1",
            "removed_quartier_id": 5,
            "remaining": 2,
        })
    )

    result = await client.remove_delivery_quartier("store_1", 5)

    assert result["success"] is True
    assert result["removed_quartier_id"] == 5
    assert result["remaining"] == 2


@pytest.mark.asyncio
@respx.mock
async def test_remove_delivery_quartier_not_found(client: MantotaClient):
    respx.delete(f"{MANTOTA_BASE_URL}/bot/stores/store_1/delivery-quartiers/999").mock(
        return_value=httpx.Response(404, json={"message": "Quartier non dans la liste."})
    )

    with pytest.raises(MantotaNotFoundError):
        await client.remove_delivery_quartier("store_1", 999)
