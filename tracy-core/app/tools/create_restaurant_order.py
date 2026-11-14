"""Tool create_restaurant_order — Crée une commande restaurant (panier multi-plats).

Permissions : RestaurantAgent, OrderAgent.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaValidationError
from app.mantota_client.schemas import RestaurantOrderResult
from app.tools.base import Tool, ToolContext, ToolResult


class CreateRestaurantOrderTool(Tool[RestaurantOrderResult]):
    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "create_restaurant_order"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"RestaurantAgent", "OrderAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        restaurant_id: str,
        customer_id: str,
        order_type: str = "delivery",
        items: list[dict[str, Any]] | None = None,
        delivery_address: str | None = None,
        delivery_latitude: float | None = None,
        delivery_longitude: float | None = None,
        notes: str | None = None,
        **_extra: Any,
    ) -> ToolResult[RestaurantOrderResult]:
        if not restaurant_id.strip():
            return ToolResult.fail(
                "INVALID_RESTAURANT_ID",
                "L'identifiant du restaurant est requis.",
                ctx.correlation_id,
            )

        if not items:
            return ToolResult.fail(
                "EMPTY_CART",
                "Le panier est vide. Ajoutez au moins un plat.",
                ctx.correlation_id,
            )

        if order_type not in ("delivery", "pickup"):
            return ToolResult.fail(
                "INVALID_ORDER_TYPE",
                "Le type de commande doit être 'delivery' ou 'pickup'.",
                ctx.correlation_id,
            )

        try:
            result = await self._mantota.create_restaurant_order(
                restaurant_id=restaurant_id,
                customer_id=customer_id,
                order_type=order_type,
                items=items,
                delivery_address=delivery_address,
                delivery_latitude=delivery_latitude,
                delivery_longitude=delivery_longitude,
                notes=notes,
            )
        except MantotaValidationError as exc:
            return ToolResult.fail(
                "VALIDATION_ERROR",
                str(exc),
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        if not result.success:
            return ToolResult.fail(
                "ORDER_FAILED",
                result.error or "La commande n'a pas pu être créée.",
                ctx.correlation_id,
            )

        return ToolResult.ok(result, ctx.correlation_id)
