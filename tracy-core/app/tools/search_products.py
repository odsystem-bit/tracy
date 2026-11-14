"""Tool search_products (docs/tracy/04-TOOLS.md).

Recherche des produits selon des critères (nom, catégorie, prix, disponibilité).
Permissions : CommercialAgent, CatalogAgent, NegotiationAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.mantota_client.schemas import ProductSearchResult
from app.tools.base import Tool, ToolContext, ToolResult


class SearchProductsTool(Tool[ProductSearchResult]):
    """Recherche de produits via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "search_products"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CommercialAgent", "CatalogAgent", "NegotiationAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        query: str,
        store_id: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        limit: int = 10,
        country: str | None = None,
        city: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        **_extra: Any,
    ) -> ToolResult[ProductSearchResult]:
        if not query.strip():
            return ToolResult.fail(
                "INVALID_QUERY",
                "La requête ne peut pas être vide.",
                ctx.correlation_id,
            )

        effective_store_id = store_id or ctx.store_id
        if effective_store_id == "public":
            effective_store_id = None

        # Mantota classe les résultats (local > pays > ailleurs) ; chaque produit porte
        # son `scope` pour que l'agent annonce honnêtement quand c'est dans une autre zone.
        try:
            result = await self._mantota.search_products(
                query=query,
                store_id=effective_store_id,
                min_price=min_price,
                max_price=max_price,
                limit=limit,
                country=country,
                city=city,
                latitude=latitude,
                longitude=longitude,
            )
        except MantotaNotFoundError:
            return ToolResult.fail(
                "NO_RESULTS",
                "Aucun produit trouvé pour cette recherche.",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        if not result.products:
            return ToolResult.fail(
                "NO_RESULTS",
                "Aucun produit trouvé pour cette recherche.",
                ctx.correlation_id,
            )

        return ToolResult.ok(result, ctx.correlation_id)
