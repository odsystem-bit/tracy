"""Tool search_catalog (docs/tracy/04-TOOLS.md).

Explore le catalogue complet d'une boutique (catégories, collections).
Permissions : CommercialAgent, CatalogAgent, NegotiationAgent, CampaignAgent.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.mantota_client.schemas import CatalogResult
from app.tools.base import Tool, ToolContext, ToolResult


class SearchCatalogTool(Tool[CatalogResult]):
    """Exploration du catalogue d'une boutique via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "search_catalog"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CommercialAgent", "CatalogAgent", "NegotiationAgent", "CampaignAgent", "VendorCopilot"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        store_id: str | None = None,
        category: str | None = None,
        **_extra: Any,
    ) -> ToolResult[CatalogResult]:
        effective_store_id = store_id or ctx.store_id
        if not effective_store_id:
            return ToolResult.fail(
                "STORE_REQUIRED",
                "Un store_id est requis pour explorer le catalogue.",
                ctx.correlation_id,
            )

        try:
            result = await self._mantota.search_catalog(
                store_id=effective_store_id,
                category=category,
            )
        except MantotaNotFoundError:
            return ToolResult.fail(
                "STORE_NOT_FOUND",
                f"Boutique introuvable : {effective_store_id}",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(result, ctx.correlation_id)
