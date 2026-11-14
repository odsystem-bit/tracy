"""Tool delete_memory (docs/tracy/04-TOOLS.md).

Supprime une information mémorisée (droit à l'oubli, expiration).
Permissions : MemoryAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.tools.base import Tool, ToolContext, ToolResult


class DeleteMemoryResult(BaseModel):
    """Résultat de la suppression d'une mémoire."""

    memory_id: str
    deleted: bool


class DeleteMemoryTool(Tool[DeleteMemoryResult]):
    """Suppression d'une mémoire via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "delete_memory"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"MemoryAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        memory_id: str,
        reason: str,
        **_extra: Any,
    ) -> ToolResult[DeleteMemoryResult]:
        if not memory_id.strip():
            return ToolResult.fail(
                "INVALID_MEMORY_ID",
                "L'identifiant de mémoire ne peut pas être vide.",
                ctx.correlation_id,
            )

        try:
            await self._mantota.delete_memory(memory_id=memory_id, reason=reason)
        except MantotaNotFoundError:
            return ToolResult.fail(
                "MEMORY_NOT_FOUND",
                f"Mémoire introuvable : {memory_id}",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        result = DeleteMemoryResult(memory_id=memory_id, deleted=True)
        return ToolResult.ok(result, ctx.correlation_id)
