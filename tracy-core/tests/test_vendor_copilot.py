"""Tests VendorCopilot, comptes-rendus vendeur et mise en relation."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.agents.base import AgentInput
from app.agents.vendor_copilot import VendorCopilot
from app.core.orchestrator import TracyOrchestrator
from app.core.schemas import IncomingMessage
from app.memory.short_term import ConversationContext, InMemoryShortTermMemory
from app.negotiation.reporting import resolve_vendor_id, wants_vendor_contact

from tests.conftest import MANTOTA_BASE_URL


def test_wants_vendor_contact_detection():
    assert wants_vendor_contact("je veux parler au vendeur")
    assert wants_vendor_contact("Passe-moi le vendeur stp")
    assert wants_vendor_contact("tu peux me donner le numéro du vendeur ?")
    assert not wants_vendor_contact("combien coûte ce téléphone ?")
    assert not wants_vendor_contact("je veux vendre sur mantota")


def test_resolve_vendor_id():
    conv = ConversationContext(product_store_id="42")
    assert resolve_vendor_id("7", None) == "7"
    assert resolve_vendor_id("public", conv) == "42"
    assert resolve_vendor_id("public", None) is None
    assert resolve_vendor_id("store_x", None) is None


async def test_copilot_refuses_outside_vendor_mode(vendor_copilot: VendorCopilot):
    out = await vendor_copilot.handle(
        AgentInput(message="mes ventes", store_id="public", correlation_id="c1")
    )
    assert out.handled and out.tools_used == []
    assert "vendeur" in out.reply.lower()


@respx.mock
async def test_copilot_reads_stats_and_reports(vendor_copilot: VendorCopilot):
    stats = respx.get(f"{MANTOTA_BASE_URL}/bot/vendors/7/stats").mock(
        return_value=httpx.Response(200, json={"stats": {"total_orders": 3}})
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/vendors/7/reports").mock(
        return_value=httpx.Response(200, json={"reports": [
            {"kind": "contact_request", "summary": "Un client veut vous parler", "customer_phone": "+22990000000"},
        ]})
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(200, json={"store_id": "7", "categories": [], "products": []})
    )
    out = await vendor_copilot.handle(
        AgentInput(message="fais-moi le point du jour", store_id="7", correlation_id="c2")
    )
    assert stats.called
    assert "get_vendor_stats" in out.tools_used
    assert "get_vendor_reports" in out.tools_used


@respx.mock
async def test_vendor_contact_request_notifies_vendor(
    orchestrator: TracyOrchestrator,
    short_term_memory: InMemoryShortTermMemory,
):
    report = respx.post(f"{MANTOTA_BASE_URL}/bot/vendors/7/reports").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="7",
            customer_id="22990000000",
            text="je veux parler au vendeur",
            conversation_id="conv_handoff",
        )
    )
    assert report.called
    body = report.calls[0].request.content.decode()
    assert "contact_request" in body
    assert reply.agent == "CommercialAgent"
    ctx = await short_term_memory.get_context("conv_handoff")
    assert len(ctx.vendor_reports_sent) == 1


@respx.mock
async def test_vendor_contact_apk_creates_conversation(
    orchestrator: TracyOrchestrator,
    short_term_memory: InMemoryShortTermMemory,
):
    """APK (conversation_id 'app:{user}:{salon}') → vraie mise en relation, pas de rapport simple."""
    connect = respx.post(f"{MANTOTA_BASE_URL}/bot/vendors/7/connect").mock(
        return_value=httpx.Response(200, json={"success": True, "conversation_id": "5"})
    )
    report = respx.post(f"{MANTOTA_BASE_URL}/bot/vendors/7/reports").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="7",
            customer_id="12",
            text="je veux parler au vendeur",
            conversation_id="app:12:tracy",
        )
    )
    assert connect.called
    assert not report.called
    assert "mis en relation" in reply.text.lower() or "messages" in reply.text.lower()
    assert reply.data is not None
    assert reply.data["vendor_conversation_id"] == "5"


@respx.mock
async def test_vendor_contact_whatsapp_notifies_only(
    orchestrator: TracyOrchestrator,
):
    """WhatsApp (numéro, pas de préfixe 'app:') → notification au vendeur, pas de connect."""
    connect = respx.post(f"{MANTOTA_BASE_URL}/bot/vendors/7/connect").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    report = respx.post(f"{MANTOTA_BASE_URL}/bot/vendors/7/reports").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    await orchestrator.handle_message(
        IncomingMessage(
            store_id="7",
            customer_id="22990000000",
            text="je veux parler au vendeur",
            conversation_id="wa_22990000000",
        )
    )
    assert not connect.called
    assert report.called


@respx.mock
async def test_vendor_report_not_duplicated(orchestrator: TracyOrchestrator):
    report = respx.post(f"{MANTOTA_BASE_URL}/bot/vendors/7/reports").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    for _ in range(2):
        await orchestrator.handle_message(
            IncomingMessage(
                store_id="7",
                customer_id="22990000000",
                text="je veux parler au vendeur",
                conversation_id="conv_dedupe",
            )
        )
    assert report.call_count == 1
