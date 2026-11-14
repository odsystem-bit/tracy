"""Tests des nouveaux agents (docs/tracy/03-AGENTS.md, 09-TEST_SCENARIOS.md).

Couvre : OrderAgent, PaymentAgent, SupportAgent, CampaignAgent, MemoryAgent.
Valide que chaque agent répond correctement et utilise les bons tools.
"""

from __future__ import annotations

import httpx
import respx

from app.agents.base import AgentInput
from app.agents.campaign_agent import CampaignAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.order_agent import OrderAgent
from app.agents.payment_agent import PaymentAgent
from app.agents.support_agent import SupportAgent

from tests.conftest import MANTOTA_BASE_URL


# ── OrderAgent ────────────────────────────────────────────────────


@respx.mock
async def test_order_agent_track_order(order_agent: OrderAgent) -> None:
    """OrderAgent suit une commande via track_order."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/orders/order_123/track").mock(
        return_value=httpx.Response(
            200,
            json={
                "order_id": "order_123",
                "statut": "shipped",
                "historique": [
                    {"statut": "pending", "date": "2025-01-01"},
                    {"statut": "shipped", "date": "2025-01-02"},
                ],
                "date_estimee_livraison": "2025-01-05",
            },
        )
    )

    result = await order_agent.handle(
        AgentInput(
            message="Où en est ma commande order_123 ?",
            store_id="store_1",
            customer_id="client_1",
            correlation_id="test-order-track",
        )
    )

    assert result.handled
    assert "track_order" in result.tools_used
    assert len(result.reply) > 0


async def test_order_agent_cancel_request(order_agent: OrderAgent) -> None:
    """OrderAgent demande confirmation pour une annulation."""
    result = await order_agent.handle(
        AgentInput(
            message="Je veux annuler ma commande",
            store_id="store_1",
            customer_id="client_1",
            correlation_id="test-order-cancel",
        )
    )

    assert result.handled
    assert len(result.reply) > 0


async def test_order_agent_create_request(order_agent: OrderAgent) -> None:
    """OrderAgent demande les infos manquantes pour créer une commande."""
    result = await order_agent.handle(
        AgentInput(
            message="Je veux commander un téléphone",
            store_id="store_1",
            customer_id="client_1",
            correlation_id="test-order-create",
        )
    )

    assert result.handled
    assert len(result.reply) > 0


# ── PaymentAgent ──────────────────────────────────────────────────


@respx.mock
async def test_payment_agent_get_wallet(payment_agent: PaymentAgent) -> None:
    """PaymentAgent consulte le wallet."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/wallet/vendor_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "user_id": "vendor_1",
                "solde_disponible": 150000,
                "solde_en_attente": 25000,
                "dernieres_transactions": [
                    {"id": "tx1", "type": "sale", "montant": 50000, "statut": "completed"},
                ],
            },
        )
    )

    result = await payment_agent.handle(
        AgentInput(
            message="Combien d'argent sur mon wallet ?",
            store_id="store_1",
            customer_id="vendor_1",
            correlation_id="test-payment-wallet",
        )
    )

    assert result.handled
    assert "get_wallet" in result.tools_used
    assert len(result.reply) > 0


async def test_payment_agent_withdrawal_request(payment_agent: PaymentAgent) -> None:
    """PaymentAgent demande les infos pour un retrait."""
    result = await payment_agent.handle(
        AgentInput(
            message="Je veux faire un retrait de mes gains",
            store_id="store_1",
            customer_id="vendor_1",
            correlation_id="test-payment-withdraw",
        )
    )

    assert result.handled
    assert len(result.reply) > 0


async def test_payment_agent_subscription_request(payment_agent: PaymentAgent) -> None:
    """PaymentAgent gère une demande d'abonnement."""
    result = await payment_agent.handle(
        AgentInput(
            message="Je veux activer mon abonnement Tracy",
            store_id="store_1",
            customer_id="vendor_1",
            correlation_id="test-payment-sub",
        )
    )

    assert result.handled
    assert len(result.reply) > 0


# ── SupportAgent ──────────────────────────────────────────────────


@respx.mock
async def test_support_agent_track_complaint(support_agent: SupportAgent) -> None:
    """SupportAgent vérifie le statut d'une commande lors d'une réclamation."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/orders/order_123/track").mock(
        return_value=httpx.Response(
            200,
            json={
                "order_id": "order_123",
                "statut": "delivered",
                "historique": [
                    {"statut": "pending", "date": "2025-01-01"},
                    {"statut": "delivered", "date": "2025-01-03"},
                ],
                "date_estimee_livraison": "2025-01-03",
            },
        )
    )

    result = await support_agent.handle(
        AgentInput(
            message="Ma commande order_123 n'est jamais arrivée",
            store_id="store_1",
            customer_id="client_1",
            correlation_id="test-support-track",
        )
    )

    assert result.handled
    assert "track_order" in result.tools_used
    assert len(result.reply) > 0


async def test_support_agent_refund_request(support_agent: SupportAgent) -> None:
    """SupportAgent gère une demande de remboursement sans promettre."""
    result = await support_agent.handle(
        AgentInput(
            message="Je veux être remboursé de ma commande",
            store_id="store_1",
            customer_id="client_1",
            correlation_id="test-support-refund",
        )
    )

    assert result.handled
    assert len(result.reply) > 0


# ── CampaignAgent ─────────────────────────────────────────────────


@respx.mock
async def test_campaign_agent_get_campaign(campaign_agent: CampaignAgent) -> None:
    """CampaignAgent consulte les performances d'une campagne."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/campaigns/camp_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "camp_1",
                "nom": "Soldes Janvier",
                "statut": "active",
                "vues": 1500,
                "clics": 300,
                "conversions": 45,
            },
        )
    )

    result = await campaign_agent.handle(
        AgentInput(
            message="Quelles sont les performances de ma campagne camp_1 ?",
            store_id="store_1",
            customer_id="vendor_1",
            correlation_id="test-campaign-get",
        )
    )

    assert result.handled
    assert "get_campaign" in result.tools_used
    assert len(result.reply) > 0


@respx.mock
async def test_campaign_agent_search_partner(campaign_agent: CampaignAgent) -> None:
    """CampaignAgent recherche un partenaire."""
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

    result = await campaign_agent.handle(
        AgentInput(
            message="Trouve le partenaire Awa",
            store_id="store_1",
            customer_id="vendor_1",
            correlation_id="test-campaign-partner",
        )
    )

    assert result.handled
    assert "search_partner" in result.tools_used
    assert len(result.reply) > 0


async def test_campaign_agent_relance(campaign_agent: CampaignAgent) -> None:
    """CampaignAgent propose une stratégie de relance."""
    result = await campaign_agent.handle(
        AgentInput(
            message="Relance les paniers abandonnés",
            store_id="store_1",
            customer_id="vendor_1",
            correlation_id="test-campaign-relance",
        )
    )

    assert result.handled
    assert len(result.reply) > 0


# ── MemoryAgent ───────────────────────────────────────────────────


@respx.mock
async def test_memory_agent_search(memory_agent: MemoryAgent) -> None:
    """MemoryAgent recherche dans la mémoire."""
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

    result = await memory_agent.handle(
        AgentInput(
            message="Tu te souviens de mes préférences ?",
            store_id="store_1",
            customer_id="client_1",
            correlation_id="test-memory-search",
        )
    )

    assert result.handled
    assert "search_memory" in result.tools_used
    assert len(result.reply) > 0


async def test_memory_agent_forget_request(memory_agent: MemoryAgent) -> None:
    """MemoryAgent gère une demande de droit à l'oubli."""
    result = await memory_agent.handle(
        AgentInput(
            message="Oublie toutes mes informations",
            store_id="store_1",
            customer_id="client_1",
            correlation_id="test-memory-forget",
        )
    )

    assert result.handled
    assert len(result.reply) > 0


async def test_memory_agent_save_request(memory_agent: MemoryAgent) -> None:
    """MemoryAgent gère une demande de mémorisation."""
    result = await memory_agent.handle(
        AgentInput(
            message="Retiens que je préfère la livraison express",
            store_id="store_1",
            customer_id="client_1",
            correlation_id="test-memory-save",
        )
    )

    assert result.handled
    assert len(result.reply) > 0
