"""Tool create_support_ticket.

Crée un ticket support (guest ou connecté) via l'API Mantota.
Permissions : CommercialAgent, SupportAgent.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError
from app.tools.base import Tool, ToolContext, ToolResult


class CreateSupportTicketTool(Tool[dict[str, Any]]):
    """Création d'un ticket support."""

    CATEGORIES = {"bug", "paiement", "question", "litige", "signalement", "autre"}

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "create_support_ticket"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"CommercialAgent", "SupportAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        subject: str,
        category: str,
        message: str,
        guest_name: str | None = None,
        guest_email: str | None = None,
        customer_id: str | None = None,
        **_extra: Any,
    ) -> ToolResult[dict[str, Any]]:
        category = category.lower().strip()
        if category not in self.CATEGORIES:
            return ToolResult.fail(
                "INVALID_CATEGORY",
                f"Catégorie invalide. Valeurs acceptées : {', '.join(sorted(self.CATEGORIES))}.",
                ctx.correlation_id,
            )

        if not subject.strip() or not message.strip():
            return ToolResult.fail(
                "MISSING_FIELDS",
                "Le sujet et le message sont obligatoires.",
                ctx.correlation_id,
            )

        try:
            result = await self._mantota.create_support_ticket(
                subject=subject,
                category=category,
                message=message,
                guest_name=guest_name,
                guest_email=guest_email,
                customer_id=customer_id,
                store_id=ctx.store_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(result, ctx.correlation_id)
