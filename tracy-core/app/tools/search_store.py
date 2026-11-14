"""Tool search_store (docs/tracy/04-TOOLS.md).

Recherche une boutique par nom, secteur ou localisation.
Permissions : CommercialAgent, CatalogAgent.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.mantota_client.schemas import StoreSearchResult
from app.tools.base import Tool, ToolContext, ToolResult


class SearchStoreTool(Tool[StoreSearchResult]):
    """Recherche de boutique via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "search_store"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CommercialAgent", "CatalogAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        query: str = "",
        city: str | None = None,
        store_id: str | None = None,
        **_extra: Any,
    ) -> ToolResult[StoreSearchResult]:
        # Si store_id est fourni, on récupère directement la boutique par ID
        if store_id:
            try:
                store_info = await self._mantota.get_store_info(store_id)
                # Construit un StoreSearchResult à partir des infos
                from app.mantota_client.schemas import Store
                store = Store(
                    id=store_info.get("id", ""),
                    nom=store_info.get("nom", ""),
                    ville=store_info.get("ville"),
                    logo_url=store_info.get("logo_url"),
                    latitude=store_info.get("latitude"),
                    longitude=store_info.get("longitude"),
                )
                result = StoreSearchResult(stores=[store], total=1)
                return ToolResult.ok(result, ctx.correlation_id)
            except MantotaNotFoundError:
                return ToolResult.fail(
                    "NO_RESULTS",
                    "Boutique non trouvée.",
                    ctx.correlation_id,
                )
            except MantotaError as exc:
                return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        if not query:
            return ToolResult.fail(
                "INVALID_QUERY",
                "La requête ne peut pas être vide.",
                ctx.correlation_id,
            )

        try:
            result = await self._mantota.search_store(query=query, city=city)
        except MantotaNotFoundError:
            return ToolResult.fail(
                "NO_RESULTS",
                "Aucune boutique trouvée pour cette recherche.",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        if not result.stores:
            return ToolResult.fail(
                "NO_RESULTS",
                "Aucune boutique trouvée pour cette recherche.",
                ctx.correlation_id,
            )

        return ToolResult.ok(result, ctx.correlation_id)
