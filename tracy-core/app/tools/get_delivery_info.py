"""Tool get_delivery_info — Couverture de livraison d'une boutique vers une ville.

Permissions : LogisticsAgent, CommercialAgent.

Aucune logique de tarification ici : Mantota ne fournit ni frais ni délai
par zone, l'outil ne répond donc QUE sur la couverture (livre / ne livre pas /
retrait sur place). Les frais et délais sont confirmés par le vendeur.
"""

from __future__ import annotations

import unicodedata
from typing import Any

from pydantic import BaseModel, Field

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.tools.base import Tool, ToolContext, ToolResult


def _norm(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    return "".join(c for c in text if not unicodedata.combining(c)).strip().lower()


class DeliveryInfo(BaseModel):
    store_id: str
    delivery_mode: str
    pickup_available: bool
    shop_address: str | None = None
    city: str | None = None
    covers_city: bool | None = None
    """True / False si la ville est connue, None sinon."""
    quartiers_in_city: list[str] = Field(default_factory=list)
    delivery_cities: list[str] = Field(default_factory=list)


class GetDeliveryInfoTool(Tool[DeliveryInfo]):
    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "get_delivery_info"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"LogisticsAgent", "CommercialAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        store_id: str,
        city: str | None = None,
        **_extra: Any,
    ) -> ToolResult[DeliveryInfo]:
        if not store_id or store_id == "public":
            return ToolResult.fail("INVALID_STORE", "Boutique non précisée.", ctx.correlation_id)

        try:
            data = await self._mantota.get_delivery_quartiers(store_id)
        except MantotaNotFoundError:
            return ToolResult.fail("STORE_NOT_FOUND", "Boutique introuvable.", ctx.correlation_id)
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        mode = str(data.get("delivery_mode") or "pickup_only")
        cities = [str(c) for c in (data.get("delivery_cities") or [])]
        city_n = _norm(city)

        quartiers_in_city: list[str] = []
        for q in data.get("quartiers") or []:
            ville = q.get("ville") or {}
            if city_n and _norm(ville.get("name")) == city_n:
                quartiers_in_city.append(str(q.get("name")))

        covers: bool | None = None
        if city_n:
            if mode in ("national", "international"):
                covers = True
            elif mode == "multi_city":
                covers = city_n in {_norm(c) for c in cities}
            elif mode == "quartiers":
                covers = bool(quartiers_in_city)
            else:
                covers = False

        return ToolResult.ok(
            DeliveryInfo(
                store_id=str(store_id),
                delivery_mode=mode,
                pickup_available=bool(data.get("pickup_available", True)),
                shop_address=data.get("shop_address"),
                city=city,
                covers_city=covers,
                quartiers_in_city=quartiers_in_city[:10],
                delivery_cities=cities[:10],
            ),
            ctx.correlation_id,
        )
