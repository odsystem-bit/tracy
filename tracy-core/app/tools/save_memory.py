"""Tool save_memory (docs/tracy/04-TOOLS.md).

Enregistre durablement une information validée (voir critères dans 06-MEMORY.md).
Permissions : MemoryAgent.

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaValidationError
from app.mantota_client.schemas import MemoryEntry
from app.tools.base import Tool, ToolContext, ToolResult


class SaveMemoryTool(Tool[MemoryEntry]):
    """Enregistrement d'une mémoire via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "save_memory"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"MemoryAgent", "CommercialAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        scope: str,
        entity_id: str,
        key: str,
        value: str,
        source: str = "inferred",
        **_extra: Any,
    ) -> ToolResult[MemoryEntry]:
        if scope not in ("client", "store", "conversation"):
            return ToolResult.fail(
                "INVALID_SCOPE",
                f"Scope invalide : {scope}. Valeurs acceptées : client, store, conversation.",
                ctx.correlation_id,
            )
        if not entity_id.strip():
            return ToolResult.fail(
                "INVALID_ENTITY_ID",
                "L'identifiant d'entité ne peut pas être vide.",
                ctx.correlation_id,
            )
        if not key.strip():
            return ToolResult.fail(
                "INVALID_KEY",
                "La clé de mémoire ne peut pas être vide.",
                ctx.correlation_id,
            )

        try:
            entry = await self._mantota.save_memory(
                scope=scope,
                entity_id=entity_id,
                key=key,
                value=value,
                source=source,
            )
        except MantotaValidationError as exc:
            return ToolResult.fail("NOT_CONFIRMED", exc.message, ctx.correlation_id)
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(entry, ctx.correlation_id)
