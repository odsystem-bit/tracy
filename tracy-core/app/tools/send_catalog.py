"""Tool send_catalog (docs/tracy/04-TOOLS.md).

Envoie le catalogue (ou une sélection) au client ou à un partenaire.
Permissions : CommercialAgent, CampaignAgent.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError
from app.tools.base import Tool, ToolContext, ToolResult


class SendCatalogResult(BaseModel):
    """Résultat de l'envoi du catalogue."""

    sent: bool
    store_id: str
    channel: str
    product_count: int = 0


class SendCatalogTool(Tool[SendCatalogResult]):
    """Envoi du catalogue via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "send_catalog"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CommercialAgent", "CampaignAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        store_id: str | None = None,
        product_ids: list[str] | None = None,
        channel: str = "whatsapp",
        **_extra: Any,
    ) -> ToolResult[SendCatalogResult]:
        effective_store_id = store_id or ctx.store_id
        if not effective_store_id:
            return ToolResult.fail(
                "STORE_REQUIRED",
                "Un store_id est requis pour envoyer le catalogue.",
                ctx.correlation_id,
            )

        try:
            await self._mantota.send_catalog(
                store_id=effective_store_id,
                product_ids=product_ids,
                channel=channel,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        result = SendCatalogResult(
            sent=True,
            store_id=effective_store_id,
            channel=channel,
            product_count=len(product_ids) if product_ids else 0,
        )
        return ToolResult.ok(result, ctx.correlation_id)
