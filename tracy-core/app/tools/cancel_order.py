"""Tool cancel_order (docs/tracy/04-TOOLS.md).

Annule une commande existante si elle n'est pas encore expédiée.
Permissions : OrderAgent, SupportAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.tools.base import Tool, ToolContext, ToolResult


class CancelOrderResult(BaseModel):
    """Résultat de l'annulation d'une commande."""

    order_id: str
    cancelled: bool
    refund_status: str | None = None


class CancelOrderTool(Tool[CancelOrderResult]):
    """Annulation d'une commande via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "cancel_order"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"OrderAgent", "SupportAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        order_id: str,
        reason: str,
        **_extra: Any,
    ) -> ToolResult[CancelOrderResult]:
        if not order_id.strip():
            return ToolResult.fail(
                "INVALID_ORDER_ID",
                "L'identifiant de commande ne peut pas être vide.",
                ctx.correlation_id,
            )
        if not reason.strip():
            return ToolResult.fail(
                "INVALID_REASON",
                "La raison de l'annulation est requise.",
                ctx.correlation_id,
            )

        try:
            data = await self._mantota.cancel_order(order_id=order_id, reason=reason)
        except MantotaNotFoundError:
            return ToolResult.fail(
                "ORDER_NOT_FOUND",
                f"Commande introuvable : {order_id}",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        result = CancelOrderResult(
            order_id=order_id,
            cancelled=True,
            refund_status=data.get("refund_status"),
        )
        return ToolResult.ok(result, ctx.correlation_id)
