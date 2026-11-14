"""Tool create_payment (docs/tracy/04-TOOLS.md).

Initie un paiement pour une commande via Moneroo (par Mantota).
Permissions : PaymentAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError
from app.mantota_client.schemas import PaymentResult
from app.tools.base import Tool, ToolContext, ToolResult


class CreatePaymentTool(Tool[PaymentResult]):
    """Initiation d'un paiement via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "create_payment"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"PaymentAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        order_id: str,
        amount: float,
        currency: str,
        method: str,
        **_extra: Any,
    ) -> ToolResult[PaymentResult]:
        if not order_id.strip():
            return ToolResult.fail(
                "INVALID_ORDER_ID",
                "L'identifiant de commande ne peut pas être vide.",
                ctx.correlation_id,
            )
        if amount <= 0:
            return ToolResult.fail(
                "AMOUNT_MISMATCH",
                "Le montant doit être supérieur à zéro.",
                ctx.correlation_id,
            )
        if not method.strip():
            return ToolResult.fail(
                "PAYMENT_METHOD_UNAVAILABLE",
                "La méthode de paiement est requise.",
                ctx.correlation_id,
            )

        try:
            result = await self._mantota.create_payment(
                order_id=order_id,
                amount=amount,
                currency=currency,
                method=method,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(result, ctx.correlation_id)
