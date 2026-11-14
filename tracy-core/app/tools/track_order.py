"""Tool track_order (docs/tracy/04-TOOLS.md).

Retourne le statut actuel d'une commande.
Permissions : OrderAgent, SupportAgent, DeliveryAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.mantota_client.schemas import OrderTrackingResult
from app.tools.base import Tool, ToolContext, ToolResult


class TrackOrderTool(Tool[OrderTrackingResult]):
    """Suivi d'une commande via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "track_order"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"OrderAgent", "SupportAgent", "DeliveryAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        order_id: str,
        **_extra: Any,
    ) -> ToolResult[OrderTrackingResult]:
        if not order_id.strip():
            return ToolResult.fail(
                "INVALID_ORDER_ID",
                "L'identifiant de commande ne peut pas être vide.",
                ctx.correlation_id,
            )

        try:
            result = await self._mantota.track_order(order_id=order_id)
        except MantotaNotFoundError:
            return ToolResult.fail(
                "ORDER_NOT_FOUND",
                f"Commande introuvable : {order_id}",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(result, ctx.correlation_id)
