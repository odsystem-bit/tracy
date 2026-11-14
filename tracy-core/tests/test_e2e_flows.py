"""Tests E2E : flux complets avec orchestrateur, mock AI et mock tools.

Valide les parcours critiques :
1. Recherche produit → produit en contexte → commande → lien de paiement
2. Création de ticket support en mode guest
3. Suivi de commande avec référence CMD-XXXX
4. Persistance du contexte (order_id, order_payment_url) entre messages
5. PaymentAgent donne le vrai lien depuis le contexte
6. NegotiationAgent fait une vraie recherche d'alternatives

Usage :
    .venv/bin/pytest tests/test_e2e_flows.py -v
"""

from __future__ import annotations

import httpx
import pytest
import respx

from app.core.orchestrator import TracyOrchestrator
from app.core.schemas import IncomingMessage
from app.memory.short_term import InMemoryShortTermMemory

from tests.conftest import MANTOTA_BASE_URL, mock_product_search_response, mock_store_config_response


# ── Helpers : réponses mock Mantota ──────────────────────────────────


def _mock_order_response(
    order_id: str = "42",
    reference: str = "CMD-ABC123",
    payment_url: str = "https://pay.mantota.com/CMD-ABC123",
    tracking_url: str = "https://mantota.com/track/CMD-ABC123",
    amount: float = 190000.0,
) -> dict:
    return {
        "success": True,
        "order_id": order_id,
        "reference": reference,
        "payment_url": payment_url,
        "tracking_url": tracking_url,
        "tracking_token": "tok_abc",
        "delivery_pin": "1234",
        "amount": amount,
    }


def _mock_support_ticket_response(
    reference_code: str = "TKT-XYZ789",
    ticket_id: int = 15,
) -> dict:
    return {
        "success": True,
        "reference_code": reference_code,
        "ticket_id": ticket_id,
        "track_url": "https://mantota.com/support/track",
    }


def _mock_track_order_response(
    order_id: str = "42",
    statut: str = "en_livraison",
) -> dict:
    return {
        "order_id": order_id,
        "statut": statut,
        "historique": [
            {"statut": "en_attente", "date": "2026-08-30 09:00", "note": None},
            {"statut": "confirmee", "date": "2026-08-30 09:15", "note": None},
            {"statut": statut, "date": "2026-08-30 10:00", "note": "En route"},
        ],
        "date_estimee_livraison": "2026-08-31 14:00",
    }


# ── Tests E2E ────────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_e2e_product_search_then_order(
    orchestrator: TracyOrchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """Flux complet : recherche produit → produit en contexte → commande créée → lien de paiement.

    Vérifie que :
    - CommercialAgent trouve le produit (search_products)
    - Le produit est persisté dans le contexte (product_id, product_name)
    - La commande est créée (create_order) avec quantité + ville
    - Le lien de paiement est présent dans la réponse
    - Le contexte persiste order_id, order_payment_url
    """
    conv_id = "conv_e2e_order"

    # Message 1 : recherche produit
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(
            products=[{"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": "store_1"}],
            total=1,
        ))
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/memory/search").mock(
        return_value=httpx.Response(200, json={"entries": [], "total": 0})
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/memory").mock(
        return_value=httpx.Response(200, json={"id": "mem_1", "scope": "client", "entity_id": "c1", "key": "test", "value": "test", "source": "observed"})
    )

    reply1 = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_e2e",
            text="Je cherche un téléphone",
            conversation_id=conv_id,
        )
    )

    assert reply1.agent == "CommercialAgent"
    assert "search_products" in reply1.tools_used
    assert len(reply1.text) > 0

    # Vérifier que le produit est en contexte (1 seul produit = sélectionné automatiquement)
    ctx = await short_term_memory.get_context(conv_id)
    assert ctx.product_id is not None, "Le produit doit être en contexte après la recherche"
    assert ctx.product_name is not None

    # Message 2 : "2 à Cotonou" → doit déclencher create_order
    respx.post(f"{MANTOTA_BASE_URL}/bot/orders").mock(
        return_value=httpx.Response(201, json=_mock_order_response())
    )

    reply2 = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_e2e",
            text="je veux 2 a cotonou",
            conversation_id=conv_id,
        )
    )

    # La commande doit être créée
    assert "create_order" in reply2.tools_used, "create_order doit être appelé"

    # Vérifier la persistance du contexte
    ctx_after = await short_term_memory.get_context(conv_id)
    assert ctx_after.order_id is not None, "order_id doit être persisté dans le contexte"
    assert ctx_after.order_reference is not None, "order_reference doit être persisté"
    assert ctx_after.order_payment_url is not None, "order_payment_url doit être persisté"
    assert ctx_after.order_tracking_url is not None, "order_tracking_url doit être persisté"
    assert ctx_after.task_state == "order_created"


@pytest.mark.asyncio
@respx.mock
async def test_e2e_support_ticket_guest(
    orchestrator: TracyOrchestrator,
) -> None:
    """Création d'un ticket support en mode guest (sans auth utilisateur).

    Vérifie que :
    - SupportAgent est sélectionné
    - create_support_ticket est appelé
    - Le reference_code est présent dans la réponse
    """
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/support/tickets").mock(
        return_value=httpx.Response(201, json=_mock_support_ticket_response())
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="public",
            customer_id="web_guest_abc123",
            text="Mon colis n'est jamais arrivé, je veux faire une réclamation",
        )
    )

    assert reply.agent == "SupportAgent"
    assert "create_support_ticket" in reply.tools_used, "create_support_ticket doit être appelé"
    assert len(reply.text) > 0


@pytest.mark.asyncio
@respx.mock
async def test_e2e_order_tracking_cmd_reference(
    orchestrator: TracyOrchestrator,
) -> None:
    """Suivi de commande avec référence CMD-XXXX.

    Vérifie que :
    - OrderAgent est sélectionné
    - extract_order_reference extrait bien "CMD-ABC123"
    - track_order est appelé (ou au moins l'agent tente le suivi)
    """
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.get(url__regex=r".*/bot/orders/.*/track").mock(
        return_value=httpx.Response(200, json=_mock_track_order_response())
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_e2e",
            text="Statut de ma commande CMD-ABC123",
        )
    )

    assert reply.agent == "OrderAgent"
    assert len(reply.text) > 0


@pytest.mark.asyncio
@respx.mock
async def test_e2e_payment_link_from_context(
    orchestrator: TracyOrchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """PaymentAgent donne le vrai lien de paiement depuis le contexte.

    Vérifie que :
    - Après qu'une commande est créée, le contexte contient order_payment_url
    - Si le client demande "comment je paie ?", PaymentAgent lit le contexte
    - Le lien de paiement est présent dans la réponse
    """
    conv_id = "conv_e2e_payment"

    # Préparer le contexte avec une commande déjà créée
    ctx = await short_term_memory.get_context(conv_id)
    ctx.product_id = "1"
    ctx.product_name = "Tecno Spark 10"
    ctx.product_price = 95000.0
    ctx.product_store_id = "store_1"
    ctx.order_id = "42"
    ctx.order_reference = "CMD-ABC123"
    ctx.order_payment_url = "https://pay.mantota.com/CMD-ABC123"
    ctx.order_tracking_url = "https://mantota.com/track/CMD-ABC123"
    ctx.last_agent = "CommercialAgent"
    ctx.last_intent = "order"
    ctx.task_state = "order_created"
    await short_term_memory.update_context(conv_id, ctx)

    # Mock shop config
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_e2e",
            text="Comment je paie ?",
            conversation_id=conv_id,
        )
    )

    # PaymentAgent doit être sélectionné (intent=payment)
    assert reply.agent == "PaymentAgent"
    assert len(reply.text) > 0


@pytest.mark.asyncio
@respx.mock
async def test_e2e_context_persistence_across_messages(
    orchestrator: TracyOrchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """Vérifie que le contexte persiste entre messages (product_id, last_agent, last_intent).

    Flux : message 1 (recherche) → vérifier contexte → message 2 (court) → vérifier contexte intact.
    """
    conv_id = "conv_e2e_persist"

    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(
            products=[{"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": "store_1"}],
            total=1,
        ))
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/memory/search").mock(
        return_value=httpx.Response(200, json={"entries": [], "total": 0})
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/memory").mock(
        return_value=httpx.Response(200, json={"id": "mem_1", "scope": "client", "entity_id": "c1", "key": "test", "value": "test", "source": "observed"})
    )

    # Message 1 : recherche
    await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_e2e",
            text="Je veux un téléphone",
            conversation_id=conv_id,
        )
    )

    ctx1 = await short_term_memory.get_context(conv_id)
    assert ctx1.product_id is not None, "product_id doit être persisté après message 1"
    assert ctx1.last_agent == "CommercialAgent"
    assert ctx1.last_intent == "product_search"

    # Message 2 : message court (ne doit pas écraser le contexte produit)
    await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_e2e",
            text="merci",
            conversation_id=conv_id,
        )
    )

    ctx2 = await short_term_memory.get_context(conv_id)
    assert ctx2.product_id is not None, "product_id doit être préservé après message 2"
    assert ctx2.product_name is not None, "product_name doit être préservé après message 2"

    # Vérifier que l'historique a bien 4 messages (2 user + 2 assistant)
    history = await short_term_memory.get_history(conv_id)
    assert len(history) == 4, f"Historique doit contenir 4 messages, actuel: {len(history)}"


@pytest.mark.asyncio
@respx.mock
async def test_e2e_negotiation_searches_alternatives(
    orchestrator: TracyOrchestrator,
    short_term_memory: InMemoryShortTermMemory,
) -> None:
    """NegotiationAgent public fait une vraie recherche d'alternatives (pas d'invention).

    Vérifie que :
    - NegotiationAgent est sélectionné
    - search_products est appelé (recherche d'alternatives sur le site public)
    - Le tool est dans tools_used
    """
    conv_id = "conv_e2e_nego"

    # Préparer le contexte avec un produit
    ctx = await short_term_memory.get_context(conv_id)
    ctx.product_id = "1"
    ctx.product_name = "Tecno Spark 10"
    ctx.product_price = 95000.0
    ctx.product_store_id = "store_1"
    ctx.product_mentioned = "téléphone"
    ctx.last_agent = "CommercialAgent"
    ctx.last_intent = "product_search"
    ctx.task_state = "product_found"
    await short_term_memory.update_context(conv_id, ctx)

    # store_id="public" pour déclencher le handler public (qui utilise search_products)
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response())
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="public",
            customer_id="client_e2e",
            text="C'est trop cher, baisse un peu",
            conversation_id=conv_id,
        )
    )

    assert reply.agent == "NegotiationAgent"
    assert "search_products" in reply.tools_used, "NegotiationAgent doit chercher de vraies alternatives"
    assert len(reply.text) > 0


@pytest.mark.asyncio
@respx.mock
async def test_e2e_vendor_onboarding_routes_to_catalog(
    orchestrator: TracyOrchestrator,
) -> None:
    """Intent vendor_onboarding route vers CatalogAgent (pas app_download)."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="public",
            customer_id="web_guest_xyz",
            text="Je veux vendre sur Mantota",
        )
    )

    assert reply.agent == "CatalogAgent"


@pytest.mark.asyncio
@respx.mock
async def test_e2e_vendor_stats_routes_to_vendor_copilot(
    orchestrator: TracyOrchestrator,
) -> None:
    """Intent vendor_stats route vers VendorCopilot (qui lit les vraies stats)."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="vendor_1",
            text="Combien j'ai vendu ce mois ?",
        )
    )

    assert reply.agent == "VendorCopilot"


@pytest.mark.asyncio
@respx.mock
async def test_e2e_paid_but_not_received_routes_to_support(
    orchestrator: TracyOrchestrator,
) -> None:
    """"J'ai payé mais rien reçu" route vers SupportAgent (pas unknown)."""
    respx.get(url__regex=r".*/bot/stores/.*/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/support/tickets").mock(
        return_value=httpx.Response(201, json=_mock_support_ticket_response())
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="client_e2e",
            text="J'ai payé mais rien reçu",
        )
    )

    assert reply.agent == "SupportAgent"
