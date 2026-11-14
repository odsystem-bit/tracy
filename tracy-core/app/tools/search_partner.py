"""Tool search_partner (docs/tracy/04-TOOLS.md).

Recherche un partenaire par nom ou identifiant de code de parrainage.
Permissions : CampaignAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.mantota_client.schemas import Partner
from app.tools.base import Tool, ToolContext, ToolResult


class SearchPartnerTool(Tool[Partner]):
    """Recherche d'un partenaire via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "search_partner"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CampaignAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        query: str,
        **_extra: Any,
    ) -> ToolResult[Partner]:
        if not query.strip():
            return ToolResult.fail(
                "INVALID_QUERY",
                "La requête ne peut pas être vide.",
                ctx.correlation_id,
            )

        try:
            partner = await self._mantota.search_partner(query=query)
        except MantotaNotFoundError:
            return ToolResult.fail(
                "PARTNER_NOT_FOUND",
                f"Partenaire introuvable : {query}",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(partner, ctx.correlation_id)
