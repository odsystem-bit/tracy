"""Tool search_restaurants — Recherche de restaurants.

Permissions : RestaurantAgent, CommercialAgent.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.mantota_client.schemas import RestaurantListResult
from app.tools.base import Tool, ToolContext, ToolResult


class SearchRestaurantsTool(Tool[RestaurantListResult]):
    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "search_restaurants"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"RestaurantAgent", "CommercialAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        lat: float | None = None,
        lng: float | None = None,
        **_extra: Any,
    ) -> ToolResult[RestaurantListResult]:
        try:
            result = await self._mantota.search_restaurants(lat=lat, lng=lng)
        except MantotaNotFoundError:
            return ToolResult.fail(
                "NO_RESTAURANTS",
                "Aucun restaurant disponible pour le moment.",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        if not result.restaurants:
            return ToolResult.fail(
                "NO_RESTAURANTS",
                "Aucun restaurant disponible pour le moment.",
                ctx.correlation_id,
            )

        return ToolResult.ok(result, ctx.correlation_id)
