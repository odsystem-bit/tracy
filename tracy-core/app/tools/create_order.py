"""Tool create_order (docs/tracy/04-TOOLS.md).

Crée une commande à partir d'un panier confirmé.
Permissions : OrderAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError
from app.mantota_client.schemas import Order
from app.tools.base import Tool, ToolContext, ToolResult


class CreateOrderTool(Tool[Order]):
    """Création d'une commande via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "create_order"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"OrderAgent", "CommercialAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        vendor_id: str,
        product_id: str,
        customer_name: str,
        customer_phone: str,
        customer_whatsapp: str,
        country: str,
        city: str,
        customer_email: str | None = None,
        landmark_indication: str | None = None,
        agreed_price: float | None = None,
        **_extra: Any,
    ) -> ToolResult[Order]:
        if not product_id:
            return ToolResult.fail(
                "INVALID_PRODUCT",
                "Un product_id est requis pour créer une commande.",
                ctx.correlation_id,
            )
        if not customer_name.strip():
            return ToolResult.fail(
                "INVALID_CUSTOMER",
                "Le nom du client ne peut pas être vide.",
                ctx.correlation_id,
            )
        if not customer_phone.strip() or customer_phone.strip() == "N/A":
            # En chat public, le client peut ne pas avoir encore donné son numéro
            customer_phone = customer_phone.strip() or "N/A"

        extra: dict[str, Any] = {}
        if agreed_price is not None:
            extra["agreed_price"] = agreed_price

        try:
            order = await self._mantota.create_order(
                vendor_id=vendor_id,
                product_id=product_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_whatsapp=customer_whatsapp,
                country=country,
                city=city,
                customer_email=customer_email,
                landmark_indication=landmark_indication,
                **extra,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(order, ctx.correlation_id)
