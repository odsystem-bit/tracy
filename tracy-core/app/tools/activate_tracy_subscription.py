"""Tool activate_tracy_subscription (docs/tracy/04-TOOLS.md).

Active ou renouvelle l'abonnement Tracy pour un vendeur, en débitant son
Wallet Mantota (même mécanisme que les autres abonnements Mantota).
Permissions : PaymentAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError
from app.mantota_client.schemas import SubscriptionResult
from app.tools.base import Tool, ToolContext, ToolResult


class ActivateTracySubscriptionTool(Tool[SubscriptionResult]):
    """Activation de l'abonnement Tracy via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "activate_tracy_subscription"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"PaymentAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        vendor_id: str,
        plan: str,
        **_extra: Any,
    ) -> ToolResult[SubscriptionResult]:
        if not vendor_id.strip():
            return ToolResult.fail(
                "INVALID_VENDOR_ID",
                "L'identifiant du vendeur ne peut pas être vide.",
                ctx.correlation_id,
            )
        if not plan.strip():
            return ToolResult.fail(
                "PLAN_NOT_AVAILABLE",
                "Le plan d'abonnement est requis.",
                ctx.correlation_id,
            )

        try:
            result = await self._mantota.activate_tracy_subscription(
                vendor_id=vendor_id,
                plan=plan,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(result, ctx.correlation_id)
