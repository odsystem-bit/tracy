"""Tool send_payment_link (docs/tracy/04-TOOLS.md).

Envoie un lien de paiement au client via le canal de conversation.
Permissions : PaymentAgent, CommercialAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError
from app.tools.base import Tool, ToolContext, ToolResult


class SendPaymentLinkResult(BaseModel):
    """Résultat de l'envoi d'un lien de paiement."""

    order_id: str
    sent: bool
    channel: str


class SendPaymentLinkTool(Tool[SendPaymentLinkResult]):
    """Envoi d'un lien de paiement via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "send_payment_link"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"PaymentAgent", "CommercialAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        order_id: str,
        channel: str = "whatsapp",
        **_extra: Any,
    ) -> ToolResult[SendPaymentLinkResult]:
        if not order_id.strip():
            return ToolResult.fail(
                "INVALID_ORDER_ID",
                "L'identifiant de commande ne peut pas être vide.",
                ctx.correlation_id,
            )

        try:
            await self._mantota.send_payment_link(order_id=order_id, channel=channel)
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        result = SendPaymentLinkResult(
            order_id=order_id,
            sent=True,
            channel=channel,
        )
        return ToolResult.ok(result, ctx.correlation_id)
