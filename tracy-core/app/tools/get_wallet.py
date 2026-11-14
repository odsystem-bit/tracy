"""Tool get_wallet (docs/tracy/04-TOOLS.md).

Retourne le solde et l'historique récent du portefeuille d'un vendeur ou partenaire.
Permissions : PaymentAgent, SupportAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.mantota_client.schemas import Wallet
from app.tools.base import Tool, ToolContext, ToolResult


class GetWalletTool(Tool[Wallet]):
    """Consultation du wallet via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "get_wallet"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"PaymentAgent", "SupportAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        user_id: str,
        **_extra: Any,
    ) -> ToolResult[Wallet]:
        if not user_id.strip():
            return ToolResult.fail(
                "INVALID_USER_ID",
                "L'identifiant utilisateur ne peut pas être vide.",
                ctx.correlation_id,
            )

        try:
            wallet = await self._mantota.get_wallet(user_id=user_id)
        except MantotaNotFoundError:
            return ToolResult.fail(
                "WALLET_NOT_FOUND",
                f"Portefeuille introuvable : {user_id}",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(wallet, ctx.correlation_id)
