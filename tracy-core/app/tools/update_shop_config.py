"""Tool update_shop_config (docs/tracy/04-TOOLS.md).

Met à jour les règles de négociation d'une boutique.
- Marge minimale de négociation
- Réduction premier achat
- Réduction maximum autorisée
- Seuil de livraison gratuite
- Seuil d'auto-acceptation
- Règles personnalisées (texte libre du vendeur)
- Devise de la boutique

Permissions : CatalogAgent, NegotiationAgent.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError
from app.mantota_client.schemas import ShopConfigResult
from app.tools.base import Tool, ToolContext, ToolResult


class UpdateShopConfigTool(Tool[ShopConfigResult]):
    """Met à jour la configuration commerciale d'une boutique."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "update_shop_config"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CatalogAgent", "NegotiationAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        store_id: str | None = None,
        min_margin_percent: float | None = None,
        first_order_discount_percent: float | None = None,
        max_discount_percent: float | None = None,
        free_shipping_threshold: float | None = None,
        auto_accept_below: float | None = None,
        custom_rules: str | None = None,
        currency: str | None = None,
        **_extra: Any,
    ) -> ToolResult[ShopConfigResult]:
        resolved_store_id = store_id or ctx.store_id
        if not resolved_store_id:
            return ToolResult.fail(
                "MISSING_STORE_ID",
                "L'identifiant de la boutique est requis.",
                ctx.correlation_id,
            )

        try:
            result = await self._mantota.update_shop_config(
                store_id=resolved_store_id,
                min_margin_percent=min_margin_percent,
                first_order_discount_percent=first_order_discount_percent,
                max_discount_percent=max_discount_percent,
                free_shipping_threshold=free_shipping_threshold,
                auto_accept_below=auto_accept_below,
                custom_rules=custom_rules,
                currency=currency,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(result, ctx.correlation_id)
