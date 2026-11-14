"""Tool request_withdrawal (docs/tracy/04-TOOLS.md).

Soumet une demande de retrait de fonds depuis le wallet.
Permissions : PaymentAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError
from app.mantota_client.schemas import WithdrawalResult
from app.tools.base import Tool, ToolContext, ToolResult


class RequestWithdrawalTool(Tool[WithdrawalResult]):
    """Demande de retrait via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "request_withdrawal"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"PaymentAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        user_id: str,
        amount: float,
        payout_method: str,
        phone: str,
        country: str,
        **_extra: Any,
    ) -> ToolResult[WithdrawalResult]:
        if not user_id.strip():
            return ToolResult.fail(
                "INVALID_USER_ID",
                "L'identifiant utilisateur ne peut pas être vide.",
                ctx.correlation_id,
            )
        if amount <= 0:
            return ToolResult.fail(
                "INSUFFICIENT_BALANCE",
                "Le montant du retrait doit être supérieur à zéro.",
                ctx.correlation_id,
            )
        if not phone.strip():
            return ToolResult.fail(
                "INVALID_PHONE",
                "Le numéro de téléphone est requis.",
                ctx.correlation_id,
            )

        try:
            result = await self._mantota.request_withdrawal(
                user_id=user_id,
                amount=amount,
                payout_method=payout_method,
                phone=phone,
                country=country,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(result, ctx.correlation_id)
