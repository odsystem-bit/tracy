"""Tests des tools OrderAgent (docs/tracy/04-TOOLS.md, 09-TEST_SCENARIOS.md).

Couvre : create_order, cancel_order, track_order.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from app.mantota_client.client import MantotaClient
from app.tools.base import ToolContext
from app.tools.cancel_order import CancelOrderTool
from app.tools.create_order import CreateOrderTool
from app.tools.track_order import TrackOrderTool

from tests.conftest import MANTOTA_BASE_URL


@pytest.fixture
def ctx() -> ToolContext:
    return ToolContext(
        agent_name="OrderAgent",
        correlation_id="test-order",
        store_id="store_1",
    )


# ── create_order ──────────────────────────────────────────────────


@respx.mock
async def test_create_order_success(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """create_order réussit avec des paramètres valides."""
    respx.post(f"{MANTOTA_BASE_URL}/bot/orders").mock(
        return_value=httpx.Response(
            201,
            json={
                "success": True,
                "order_id": "order_123",
                "reference": "CMD-TEST123",
                "payment_url": "https://pay.mantota.test/123",
                "tracking_url": "https://mantota.test/track/123",
                "tracking_token": "tok123",
                "delivery_pin": "1234",
                "amount": 95000,
            },
        )
    )

    tool = CreateOrderTool(mantota_client)
    result = await tool.execute(
        ctx,
        vendor_id="2",
        product_id="1",
        customer_name="Client Test",
        customer_phone="+22997000099",
        customer_whatsapp="+22997000099",
        country="BJ",
        city="Cotonou",
    )

    assert result.success
    assert result.data is not None
    assert result.data.order_id == "order_123"
    assert result.data.amount == 95000


async def test_create_order_empty_product(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """create_order échoue si product_id est vide."""
    tool = CreateOrderTool(mantota_client)
    result = await tool.execute(
        ctx,
        vendor_id="2",
        product_id="",
        customer_name="Client Test",
        customer_phone="+22997000099",
        customer_whatsapp="+22997000099",
        country="BJ",
        city="Cotonou",
    )

    assert not result.success
    assert result.error is not None
    assert "INVALID_PRODUCT" in result.error.code


async def test_create_order_empty_customer_name(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """create_order échoue si le nom du client est vide."""
    tool = CreateOrderTool(mantota_client)
    result = await tool.execute(
        ctx,
        vendor_id="2",
        product_id="1",
        customer_name="  ",
        customer_phone="+22997000099",
        customer_whatsapp="+22997000099",
        country="BJ",
        city="Cotonou",
    )

    assert not result.success
    assert result.error is not None
    assert "INVALID_CUSTOMER" in result.error.code


async def test_create_order_permission_denied(
    mantota_client: MantotaClient,
) -> None:
    """create_order refuse un agent non autorisé."""
    from app.tools.registry import ToolRegistry, ToolPermissionError

    registry = ToolRegistry()
    registry.register(CreateOrderTool(mantota_client))

    ctx = ToolContext(
        agent_name="NegotiationAgent",
        correlation_id="test-perm",
        store_id="store_1",
    )

    with pytest.raises(ToolPermissionError):
        await registry.execute(
            "create_order",
            ctx,
            vendor_id="2",
            product_id="1",
            customer_name="Client Test",
            customer_phone="+22997000099",
            customer_whatsapp="+22997000099",
            country="BJ",
            city="Dakar",
        )


# ── cancel_order ──────────────────────────────────────────────────


@respx.mock
async def test_cancel_order_success(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """cancel_order réussit avec un order_id et une raison valides."""
    respx.post(f"{MANTOTA_BASE_URL}/bot/orders/order_123/cancel").mock(
        return_value=httpx.Response(
            200,
            json={"cancelled": True, "refund_status": "pending"},
        )
    )

    tool = CancelOrderTool(mantota_client)
    result = await tool.execute(ctx, order_id="order_123", reason="Client a changé d'avis")

    assert result.success
    assert result.data is not None
    assert result.data.cancelled is True


async def test_cancel_order_empty_reason(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """cancel_order échoue sans raison."""
    tool = CancelOrderTool(mantota_client)
    result = await tool.execute(ctx, order_id="order_123", reason="")

    assert not result.success
    assert result.error is not None
    assert "INVALID_REASON" in result.error.code


@respx.mock
async def test_cancel_order_not_found(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """cancel_order retourne ORDER_NOT_FOUND si la commande n'existe pas."""
    respx.post(f"{MANTOTA_BASE_URL}/bot/orders/unknown/cancel").mock(
        return_value=httpx.Response(404)
    )

    tool = CancelOrderTool(mantota_client)
    result = await tool.execute(ctx, order_id="unknown", reason="Test")

    assert not result.success
    assert result.error is not None
    assert "ORDER_NOT_FOUND" in result.error.code


# ── track_order ───────────────────────────────────────────────────


@respx.mock
async def test_track_order_success(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """track_order retourne le statut et l'historique."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/orders/order_123/track").mock(
        return_value=httpx.Response(
            200,
            json={
                "order_id": "order_123",
                "statut": "shipped",
                "historique": [
                    {"statut": "pending", "date": "2025-01-01T10:00:00Z"},
                    {"statut": "shipped", "date": "2025-01-02T08:00:00Z"},
                ],
                "date_estimee_livraison": "2025-01-05",
            },
        )
    )

    tool = TrackOrderTool(mantota_client)
    result = await tool.execute(ctx, order_id="order_123")

    assert result.success
    assert result.data is not None
    assert result.data.statut == "shipped"
    assert len(result.data.historique) == 2


@respx.mock
async def test_track_order_not_found(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """track_order retourne ORDER_NOT_FOUND."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/orders/unknown/track").mock(
        return_value=httpx.Response(404)
    )

    tool = TrackOrderTool(mantota_client)
    result = await tool.execute(ctx, order_id="unknown")

    assert not result.success
    assert result.error is not None
    assert "ORDER_NOT_FOUND" in result.error.code
