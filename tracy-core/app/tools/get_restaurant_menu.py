"""Tool get_restaurant_menu — Récupère le menu d'un restaurant.

Permissions : RestaurantAgent, CommercialAgent.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.mantota_client.schemas import RestaurantMenuResult
from app.tools.base import Tool, ToolContext, ToolResult


class GetRestaurantMenuTool(Tool[RestaurantMenuResult]):
    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "get_restaurant_menu"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"RestaurantAgent", "CommercialAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        restaurant_id: str,
        **_extra: Any,
    ) -> ToolResult[RestaurantMenuResult]:
        if not restaurant_id.strip():
            return ToolResult.fail(
                "INVALID_RESTAURANT_ID",
                "L'identifiant du restaurant est requis.",
                ctx.correlation_id,
            )

        try:
            result = await self._mantota.get_restaurant_menu(restaurant_id)
        except MantotaNotFoundError:
            return ToolResult.fail(
                "RESTAURANT_NOT_FOUND",
                "Restaurant introuvable.",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(result, ctx.correlation_id)
