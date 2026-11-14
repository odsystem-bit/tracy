"""Tool get_campaign (docs/tracy/04-TOOLS.md).

Retourne les détails ou performances d'une campagne.
Permissions : CampaignAgent, NegotiationAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.mantota_client.schemas import Campaign
from app.tools.base import Tool, ToolContext, ToolResult


class GetCampaignTool(Tool[Campaign]):
    """Consultation d'une campagne via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "get_campaign"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CampaignAgent", "NegotiationAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        campaign_id: str,
        **_extra: Any,
    ) -> ToolResult[Campaign]:
        if not campaign_id.strip():
            return ToolResult.fail(
                "INVALID_CAMPAIGN_ID",
                "L'identifiant de campagne ne peut pas être vide.",
                ctx.correlation_id,
            )

        try:
            campaign = await self._mantota.get_campaign(campaign_id=campaign_id)
        except MantotaNotFoundError:
            return ToolResult.fail(
                "CAMPAIGN_NOT_FOUND",
                f"Campagne introuvable : {campaign_id}",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(campaign, ctx.correlation_id)
