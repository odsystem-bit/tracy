"""Tool get_currencies — Récupère la liste des devises supportées.

Permissions : CommercialAgent, PaymentAgent, CatalogAgent.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError
from app.mantota_client.schemas import CurrencyListResult
from app.tools.base import Tool, ToolContext, ToolResult


class GetCurrenciesTool(Tool[CurrencyListResult]):
    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "get_currencies"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CommercialAgent", "PaymentAgent", "CatalogAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        **_extra: Any,
    ) -> ToolResult[CurrencyListResult]:
        try:
            result = await self._mantota.get_currencies()
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        if not result.currencies:
            return ToolResult.fail(
                "NO_CURRENCIES",
                "Aucune devise disponible.",
                ctx.correlation_id,
            )

        return ToolResult.ok(result, ctx.correlation_id)
