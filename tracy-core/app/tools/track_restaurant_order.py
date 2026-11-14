"""Tool track_restaurant_order — Suit le statut d'une commande restaurant.

Permissions : RestaurantAgent, OrderAgent, SupportAgent.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.mantota_client.schemas import RestaurantOrderStatus
from app.tools.base import Tool, ToolContext, ToolResult


class TrackRestaurantOrderTool(Tool[RestaurantOrderStatus]):
    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "track_restaurant_order"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"RestaurantAgent", "OrderAgent", "SupportAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        order_id: str,
        **_extra: Any,
    ) -> ToolResult[RestaurantOrderStatus]:
        if not order_id.strip():
            return ToolResult.fail(
                "INVALID_ORDER_ID",
                "L'identifiant de la commande est requis.",
                ctx.correlation_id,
            )

        try:
            result = await self._mantota.get_restaurant_order_status(order_id)
        except MantotaNotFoundError:
            return ToolResult.fail(
                "ORDER_NOT_FOUND",
                "Commande introuvable.",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(result, ctx.correlation_id)
