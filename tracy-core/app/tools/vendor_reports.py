"""Tools de comptes-rendus vendeur : send_vendor_report, get_vendor_reports, get_vendor_stats.

- send_vendor_report : Tracy prévient le vendeur (résumé de discussion, demande de contact).
- get_vendor_reports / get_vendor_stats : lecture pour le VendorCopilot.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError
from app.tools.base import Tool, ToolContext, ToolResult

REPORT_KINDS = {"negotiation", "sale", "contact_request", "summary"}


class SendVendorReportTool(Tool[dict[str, Any]]):
    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "send_vendor_report"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CommercialAgent", "NegotiationAgent", "SupportAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        vendor_id: str,
        kind: str,
        summary: str,
        customer_name: str | None = None,
        customer_phone: str | None = None,
        product_name: str | None = None,
        conversation_id: str | None = None,
        **_extra: Any,
    ) -> ToolResult[dict[str, Any]]:
        if not str(vendor_id).isdigit():
            return ToolResult.fail("INVALID_VENDOR", "Vendeur invalide.", ctx.correlation_id)
        if kind not in REPORT_KINDS or not summary.strip():
            return ToolResult.fail("INVALID_REPORT", "Rapport invalide.", ctx.correlation_id)
        try:
            result = await self._mantota.send_vendor_report(
                vendor_id=str(vendor_id),
                kind=kind,
                summary=summary.strip()[:1500],
                customer_name=customer_name,
                customer_phone=customer_phone,
                product_name=product_name,
                conversation_id=conversation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)
        return ToolResult.ok(result, ctx.correlation_id)


class GetVendorReportsTool(Tool[dict[str, Any]]):
    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "get_vendor_reports"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"VendorCopilot"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        vendor_id: str | None = None,
        limit: int = 10,
        **_extra: Any,
    ) -> ToolResult[dict[str, Any]]:
        vid = vendor_id or ctx.store_id
        if not vid or not str(vid).isdigit():
            return ToolResult.fail("INVALID_VENDOR", "Vendeur invalide.", ctx.correlation_id)
        try:
            result = await self._mantota.get_vendor_reports(str(vid), limit=limit)
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)
        return ToolResult.ok(result, ctx.correlation_id)


class ConnectVendorTool(Tool[dict[str, Any]]):
    """Met un client de l'app en relation directe avec le vendeur (conversation in-app)."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "connect_client_vendor"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CommercialAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        vendor_id: str,
        client_user_id: str,
        summary: str | None = None,
        product_name: str | None = None,
        **_extra: Any,
    ) -> ToolResult[dict[str, Any]]:
        if not str(vendor_id).isdigit() or not str(client_user_id).isdigit():
            return ToolResult.fail("INVALID_CONNECT", "Vendeur ou client invalide.", ctx.correlation_id)
        try:
            result = await self._mantota.connect_client_vendor(
                vendor_id=str(vendor_id),
                client_user_id=str(client_user_id),
                summary=summary,
                product_name=product_name,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)
        return ToolResult.ok(result, ctx.correlation_id)


class ScheduleFollowUpTool(Tool[dict[str, Any]]):
    """Planifie une relance proactive au client (post-négociation, 2-3h)."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "schedule_follow_up"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CommercialAgent", "NegotiationAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        vendor_id: str,
        customer_id: str,
        channel: str,
        message: str,
        context_key: str | None = None,
        send_at_minutes: int = 120,
        **_extra: Any,
    ) -> ToolResult[dict[str, Any]]:
        if not str(vendor_id).isdigit() or not str(customer_id).strip():
            return ToolResult.fail("INVALID_FOLLOW_UP", "Vendeur ou client invalide.", ctx.correlation_id)
        if channel not in {"whatsapp", "app"}:
            return ToolResult.fail("INVALID_CHANNEL", "Canal de relance invalide.", ctx.correlation_id)
        try:
            result = await self._mantota.schedule_follow_up(
                vendor_id=str(vendor_id),
                customer_id=str(customer_id),
                channel=channel,
                message=message[:1500],
                context_key=context_key,
                send_at_minutes=int(send_at_minutes),
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)
        return ToolResult.ok(result, ctx.correlation_id)


class GetVendorStatsTool(Tool[dict[str, Any]]):
    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "get_vendor_stats"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"VendorCopilot"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        vendor_id: str | None = None,
        **_extra: Any,
    ) -> ToolResult[dict[str, Any]]:
        vid = vendor_id or ctx.store_id
        if not vid or not str(vid).isdigit():
            return ToolResult.fail("INVALID_VENDOR", "Vendeur invalide.", ctx.correlation_id)
        try:
            result = await self._mantota.get_vendor_stats(str(vid))
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)
        return ToolResult.ok(result, ctx.correlation_id)
