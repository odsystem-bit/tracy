"""Tool update_memory (docs/tracy/04-TOOLS.md).

Met à jour une information mémorisée existante.
Permissions : MemoryAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.tools.base import Tool, ToolContext, ToolResult


class UpdateMemoryResult(BaseModel):
    """Résultat de la mise à jour d'une mémoire."""

    memory_id: str
    updated: bool


class UpdateMemoryTool(Tool[UpdateMemoryResult]):
    """Mise à jour d'une mémoire via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "update_memory"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"MemoryAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        memory_id: str,
        value: str,
        **_extra: Any,
    ) -> ToolResult[UpdateMemoryResult]:
        if not memory_id.strip():
            return ToolResult.fail(
                "INVALID_MEMORY_ID",
                "L'identifiant de mémoire ne peut pas être vide.",
                ctx.correlation_id,
            )

        try:
            await self._mantota.update_memory(memory_id=memory_id, value=value)
        except MantotaNotFoundError:
            return ToolResult.fail(
                "MEMORY_NOT_FOUND",
                f"Mémoire introuvable : {memory_id}",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        result = UpdateMemoryResult(memory_id=memory_id, updated=True)
        return ToolResult.ok(result, ctx.correlation_id)
