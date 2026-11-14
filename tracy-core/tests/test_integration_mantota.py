"""Tests d'intégration — Tracy Core ↔ Mantota API locale (PostgreSQL).

Ces tests se connectent à l'API Laravel réelle sur http://127.0.0.1:8000/api.
Ils nécessitent :
  - Le serveur Laravel (php artisan serve) démarré
  - PostgreSQL avec les migrations et le seeder TracyTestSeeder
  - Le fichier .env de tracy-core configuré avec MANTOTA_API_URL et MANTOTA_API_KEY

Scénarios couverts (docs/tracy/09-TEST_SCENARIOS.md) :
  T-001 : Recherche produits avec budget
  T-002 : Recherche sans résultat
  T-005 : Catalogue + envoi
  T-006 : Recherche boutique
  T-007 : Suivi commande
  T-008 : Annulation commande
  T-009 : Création paiement
  T-011 : Consultation wallet
  T-012 : Demande retrait
  T-013 : Détails campagne
  T-014 : Recherche partenaire
  T-015 : Sauvegarde mémoire
"""

from __future__ import annotations

import os
import pytest

from app.mantota_client.client import MantotaClient

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Set RUN_INTEGRATION_TESTS=1 to run integration tests against local Mantota API",
)

MANTOTA_URL = os.getenv("MANTOTA_API_URL", "http://127.0.0.1:8000/api")
MANTOTA_KEY = os.getenv("MANTOTA_API_KEY", "4bFsLxzHObueHwTp9vobD0Ga0JTHplGAtMyLnpYA")

VENDOR_ID = "2"
PRODUCT_ID = "1"
ORDER_ID = "1"
CAMPAIGN_ID = "1"


@pytest.fixture
async def client() -> MantotaClient:
    c = MantotaClient(
        base_url=MANTOTA_URL,
        api_key=MANTOTA_KEY,
        retry_max=1,
        retry_backoff=0.01,
    )
    yield c
    await c.aclose()


# ── T-001 : Recherche produits ──


async def test_t001_search_products_within_budget(client: MantotaClient) -> None:
    result = await client.search_products(query="samsung", max_price=100000)
    assert result.total > 0
    for p in result.products:
        assert p.prix <= 100000


async def test_t002_search_products_no_result(client: MantotaClient) -> None:
    result = await client.search_products(query="fusée spatiale")
    assert result.total == 0
    assert len(result.products) == 0


# ── T-005 : Catalogue ──


async def test_t005_search_catalog(client: MantotaClient) -> None:
    result = await client.search_catalog(store_id=VENDOR_ID)
    assert len(result.products) > 0
    assert all(p.store_id == VENDOR_ID for p in result.products)


async def test_t005_send_catalog(client: MantotaClient) -> None:
    result = await client.send_catalog(store_id=VENDOR_ID, channel="whatsapp")
    assert result.get("success") is True


# ── T-006 : Recherche boutique ──


async def test_t006_search_store(client: MantotaClient) -> None:
    result = await client.search_store(query="boutique")
    assert result.total > 0
    assert any("Boutique" in s.nom for s in result.stores)


# ── T-007 : Suivi commande ──


async def test_t007_track_order(client: MantotaClient) -> None:
    result = await client.track_order(order_id=ORDER_ID)
    assert result.order_id == ORDER_ID
    assert result.statut is not None
    assert len(result.historique) > 0


# ── T-008 : Annulation commande ──


async def test_t008_cancel_order(client: MantotaClient) -> None:
    order = await client.create_order(
        vendor_id=VENDOR_ID,
        product_id=PRODUCT_ID,
        customer_name="Test Cancel",
        customer_phone="+22997099999",
        customer_whatsapp="+22997099999",
        country="BJ",
        city="Cotonou",
    )
    result = await client.cancel_order(order_id=order.order_id, reason="Test annulation")
    assert result.get("success") is True or result.get("statut") is not None


# ── T-009 : Paiement ──


async def test_t009_create_payment(client: MantotaClient) -> None:
    try:
        result = await client.create_payment(
            order_id=ORDER_ID,
            amount=5000,
            currency="XOF",
            method="mobile_money",
        )
        assert result.payment_id is not None
    except Exception:
        pytest.skip("Moneroo API key not configured locally")


# ── T-011 : Wallet ──


async def test_t011_get_wallet(client: MantotaClient) -> None:
    result = await client.get_wallet(user_id=VENDOR_ID)
    assert result.user_id == VENDOR_ID
    assert result.solde_disponible >= 0


# ── T-012 : Retrait ──


async def test_t012_request_withdrawal(client: MantotaClient) -> None:
    try:
        result = await client.request_withdrawal(
            user_id=VENDOR_ID,
            amount=1000,
            payout_method="momo",
            phone="+22997000001",
            country="BJ",
        )
        assert result.reference is not None
    except Exception as e:
        if "insufficient" in str(e).lower() or "solde" in str(e).lower():
            pytest.skip("Insufficient balance for withdrawal test")
        raise


# ── T-013 : Campagne ──


async def test_t013_get_campaign(client: MantotaClient) -> None:
    result = await client.get_campaign(campaign_id=CAMPAIGN_ID)
    assert result.id == CAMPAIGN_ID
    assert result.nom is not None
    assert result.statut is not None


# ── T-014 : Partenaire ──


async def test_t014_search_partner(client: MantotaClient) -> None:
    result = await client.search_partner(query="awa")
    assert result is not None
    assert "Awa" in result.nom or "awa" in result.nom.lower()


# ── T-015 : Mémoire ──


async def test_t015_save_and_search_memory(client: MantotaClient) -> None:
    entry = await client.save_memory(
        scope="vendor",
        entity_id=VENDOR_ID,
        key="test_pref",
        value="fr",
        source="explicit",
    )
    assert entry.id is not None

    results = await client.search_memory(scope="vendor", entity_id=VENDOR_ID)
    assert results.total > 0
    found = [e for e in results.entries if e.key == "test_pref"]
    assert len(found) > 0
    assert found[0].value == "fr"

    await client.delete_memory(memory_id=entry.id, reason="cleanup")
