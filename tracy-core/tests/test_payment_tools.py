"""Tests des tools PaymentAgent (docs/tracy/04-TOOLS.md, 09-TEST_SCENARIOS.md).

Couvre : create_payment, get_wallet, request_withdrawal, send_payment_link,
activate_tracy_subscription.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from app.mantota_client.client import MantotaClient
from app.tools.base import ToolContext
from app.tools.activate_tracy_subscription import ActivateTracySubscriptionTool
from app.tools.create_payment import CreatePaymentTool
from app.tools.get_wallet import GetWalletTool
from app.tools.request_withdrawal import RequestWithdrawalTool
from app.tools.send_payment_link import SendPaymentLinkTool

from tests.conftest import MANTOTA_BASE_URL


@pytest.fixture
def ctx() -> ToolContext:
    return ToolContext(
        agent_name="PaymentAgent",
        correlation_id="test-payment",
        store_id="store_1",
    )


# ── create_payment ────────────────────────────────────────────────


@respx.mock
async def test_create_payment_success(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """create_payment réussit avec des paramètres valides."""
    respx.post(f"{MANTOTA_BASE_URL}/bot/payments").mock(
        return_value=httpx.Response(
            201,
            json={
                "payment_id": "pay_123",
                "checkout_url": "https://pay.moneroo.com/abc",
                "statut": "pending",
                "reference": "REF-001",
            },
        )
    )

    tool = CreatePaymentTool(mantota_client)
    result = await tool.execute(
        ctx,
        order_id="order_123",
        amount=95000,
        currency="XOF",
        method="wave",
    )

    assert result.success
    assert result.data is not None
    assert result.data.payment_id == "pay_123"
    assert result.data.checkout_url is not None


async def test_create_payment_zero_amount(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """create_payment échoue si le montant est <= 0."""
    tool = CreatePaymentTool(mantota_client)
    result = await tool.execute(
        ctx,
        order_id="order_123",
        amount=0,
        currency="XOF",
        method="wave",
    )

    assert not result.success
    assert "AMOUNT" in result.error.code  # type: ignore[union-attr]


async def test_create_payment_empty_method(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """create_payment échoue sans méthode de paiement."""
    tool = CreatePaymentTool(mantota_client)
    result = await tool.execute(
        ctx,
        order_id="order_123",
        amount=5000,
        currency="XOF",
        method="",
    )

    assert not result.success
    assert "PAYMENT_METHOD" in result.error.code  # type: ignore[union-attr]


# ── get_wallet ────────────────────────────────────────────────────


@respx.mock
async def test_get_wallet_success(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """get_wallet retourne le solde et l'historique."""
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

    tool = GetWalletTool(mantota_client)
    result = await tool.execute(ctx, user_id="vendor_1")

    assert result.success
    assert result.data is not None
    assert result.data.solde_disponible == 150000


@respx.mock
async def test_get_wallet_not_found(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """get_wallet retourne WALLET_NOT_FOUND."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/wallet/unknown").mock(
        return_value=httpx.Response(404)
    )

    tool = GetWalletTool(mantota_client)
    result = await tool.execute(ctx, user_id="unknown")

    assert not result.success
    assert "WALLET_NOT_FOUND" in result.error.code  # type: ignore[union-attr]


# ── request_withdrawal ────────────────────────────────────────────


@respx.mock
async def test_request_withdrawal_success(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """request_withdrawal réussit avec des paramètres valides."""
    respx.post(f"{MANTOTA_BASE_URL}/bot/wallet/withdraw").mock(
        return_value=httpx.Response(
            201,
            json={
                "reference": "WD-001",
                "statut": "pending",
                "montant": 50000,
            },
        )
    )

    tool = RequestWithdrawalTool(mantota_client)
    result = await tool.execute(
        ctx,
        user_id="vendor_1",
        amount=50000,
        payout_method="wave",
        phone="+22170000000",
        country="SN",
    )

    assert result.success
    assert result.data is not None
    assert result.data.reference == "WD-001"


async def test_request_withdrawal_zero_amount(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """request_withdrawal échoue si le montant est <= 0."""
    tool = RequestWithdrawalTool(mantota_client)
    result = await tool.execute(
        ctx,
        user_id="vendor_1",
        amount=0,
        payout_method="wave",
        phone="+22170000000",
        country="SN",
    )

    assert not result.success
    assert "INSUFFICIENT" in result.error.code  # type: ignore[union-attr]


async def test_request_withdrawal_empty_phone(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """request_withdrawal échoue sans numéro de téléphone."""
    tool = RequestWithdrawalTool(mantota_client)
    result = await tool.execute(
        ctx,
        user_id="vendor_1",
        amount=50000,
        payout_method="wave",
        phone="",
        country="SN",
    )

    assert not result.success
    assert "INVALID_PHONE" in result.error.code  # type: ignore[union-attr]


# ── send_payment_link ─────────────────────────────────────────────


@respx.mock
async def test_send_payment_link_success(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """send_payment_link réussit."""
    respx.post(f"{MANTOTA_BASE_URL}/bot/payments/send-link").mock(
        return_value=httpx.Response(200, json={"sent": True})
    )

    tool = SendPaymentLinkTool(mantota_client)
    result = await tool.execute(ctx, order_id="order_123", channel="whatsapp")

    assert result.success
    assert result.data is not None
    assert result.data.sent is True


async def test_send_payment_link_empty_order(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """send_payment_link échoue sans order_id."""
    tool = SendPaymentLinkTool(mantota_client)
    result = await tool.execute(ctx, order_id="", channel="whatsapp")

    assert not result.success
    assert "INVALID_ORDER_ID" in result.error.code  # type: ignore[union-attr]


# ── activate_tracy_subscription ───────────────────────────────────


@respx.mock
async def test_activate_subscription_success(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """activate_tracy_subscription réussit."""
    respx.post(f"{MANTOTA_BASE_URL}/bot/subscriptions/tracy").mock(
        return_value=httpx.Response(
            201,
            json={
                "statut": "active",
                "date_expiration": "2025-12-31",
                "reference_transaction": "SUB-001",
            },
        )
    )

    tool = ActivateTracySubscriptionTool(mantota_client)
    result = await tool.execute(ctx, vendor_id="vendor_1", plan="monthly")

    assert result.success
    assert result.data is not None
    assert result.data.statut == "active"


async def test_activate_subscription_empty_vendor(
    mantota_client: MantotaClient,
    ctx: ToolContext,
) -> None:
    """activate_tracy_subscription échoue sans vendor_id."""
    tool = ActivateTracySubscriptionTool(mantota_client)
    result = await tool.execute(ctx, vendor_id="", plan="monthly")

    assert not result.success
    assert "INVALID_VENDOR" in result.error.code  # type: ignore[union-attr]
