"""Tool get_shop_config (docs/tracy/04-TOOLS.md).

Récupère les règles de négociation d'une boutique.
Utilisé par le NegotiationAgent pour connaître les marges autorisées
avant de négocier avec un client.

Permissions : CatalogAgent, NegotiationAgent, CommercialAgent.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError
from app.mantota_client.schemas import ShopConfig
from app.tools.base import Tool, ToolContext, ToolResult


class GetShopConfigTool(Tool[ShopConfig]):
    """Récupère la configuration commerciale d'une boutique."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "get_shop_config"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CatalogAgent", "NegotiationAgent", "CommercialAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        store_id: str | None = None,
        **_extra: Any,
    ) -> ToolResult[ShopConfig]:
        resolved_store_id = store_id or ctx.store_id
        if not resolved_store_id:
            return ToolResult.fail(
                "MISSING_STORE_ID",
                "L'identifiant de la boutique est requis.",
                ctx.correlation_id,
            )

        try:
            result = await self._mantota.get_shop_config(resolved_store_id)
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(result, ctx.correlation_id)
