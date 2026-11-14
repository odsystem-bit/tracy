"""Tool create_dispute.

Crée un litige sur une commande via l'API Mantota.
Permissions : CommercialAgent, SupportAgent.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.tools.base import Tool, ToolContext, ToolResult


class CreateDisputeTool(Tool[dict[str, Any]]):
    """Création d'un litige."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "create_dispute"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CommercialAgent", "SupportAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        order_reference: str,
        reason: str,
        customer_id: str | None = None,
        **_extra: Any,
    ) -> ToolResult[dict[str, Any]]:
        if not order_reference.strip() or not reason.strip():
            return ToolResult.fail(
                "MISSING_FIELDS",
                "La référence commande et la raison sont obligatoires.",
                ctx.correlation_id,
            )

        try:
            result = await self._mantota.create_dispute(
                order_reference=order_reference,
                reason=reason,
                customer_id=customer_id,
            )
        except MantotaNotFoundError:
            return ToolResult.fail(
                "ORDER_NOT_FOUND",
                "Je n'ai pas trouvé cette commande. Vérifie la référence (ex: CMD-XXXX).",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(result, ctx.correlation_id)
