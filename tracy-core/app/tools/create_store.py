"""Tool create_store (docs/tracy/04-TOOLS.md).

Crée une boutique sur Mantota.
- Si type == "physique" → latitude, longitude et storefront_photo_url sont obligatoires.
- Si type == "en_ligne" → pas besoin de GPS ni de photo.
Permissions : CatalogAgent.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError
from app.mantota_client.schemas import StoreCreateResult
from app.tools.base import Tool, ToolContext, ToolResult


class CreateStoreTool(Tool[StoreCreateResult]):
    """Crée une boutique physique ou en ligne sur Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "create_store"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CatalogAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        vendor_id: str,
        nom: str,
        store_type: str,
        category: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        storefront_photo_url: str | None = None,
        logo_url: str | None = None,
        **_extra: Any,
    ) -> ToolResult[StoreCreateResult]:
        if not nom.strip():
            return ToolResult.fail(
                "INVALID_NAME",
                "Le nom de la boutique ne peut pas être vide.",
                ctx.correlation_id,
            )

        if store_type not in ("physique", "en_ligne"):
            return ToolResult.fail(
                "INVALID_STORE_TYPE",
                "Le type doit être 'physique' ou 'en_ligne'.",
                ctx.correlation_id,
            )

        # Boutique physique → GPS + photo obligatoires
        if store_type == "physique":
            if latitude is None or longitude is None:
                return ToolResult.fail(
                    "MISSING_GPS",
                    "Une boutique physique nécessite les coordonnées GPS (latitude, longitude).",
                    ctx.correlation_id,
                )
            if storefront_photo_url is None:
                return ToolResult.fail(
                    "MISSING_STOREFRONT_PHOTO",
                    "Une boutique physique nécessite une photo de la devanture.",
                    ctx.correlation_id,
                )

        try:
            result = await self._mantota.create_store(
                vendor_id=vendor_id,
                nom=nom,
                store_type=store_type,
                category=category,
                latitude=latitude,
                longitude=longitude,
                storefront_photo_url=storefront_photo_url,
                logo_url=logo_url,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(result, ctx.correlation_id)
