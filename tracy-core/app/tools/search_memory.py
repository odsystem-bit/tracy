"""Tool search_memory (docs/tracy/04-TOOLS.md).

Recherche une information mémorisée pertinente pour le contexte courant.
Permissions : MemoryAgent (consulté pour tous les autres agents via Tracy Core).

Aucune logique métier ici : validation des paramètres puis appel à Mantota.
"""

from __future__ import annotations

from typing import Any

from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError
from app.mantota_client.schemas import MemorySearchResult
from app.tools.base import Tool, ToolContext, ToolResult


class SearchMemoryTool(Tool[MemorySearchResult]):
    """Recherche dans la mémoire via l'API Mantota."""

    def __init__(self, mantota_client: MantotaClient) -> None:
        self._mantota = mantota_client

    @property
    def name(self) -> str:
        return "search_memory"

    @property
    def allowed_agents(self) -> frozenset[str]:
        return frozenset({"MemoryAgent", "CommercialAgent"})

    async def execute(
        self,
        ctx: ToolContext,
        *,
        scope: str,
        entity_id: str,
        query: str | None = None,
        **_extra: Any,
    ) -> ToolResult[MemorySearchResult]:
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

        try:
            result = await self._mantota.search_memory(
                scope=scope,
                entity_id=entity_id,
                query=query,
            )
        except MantotaNotFoundError:
            return ToolResult.fail(
                "NOT_FOUND",
                "Aucune mémoire trouvée pour cette recherche.",
                ctx.correlation_id,
            )
        except MantotaError as exc:
            return ToolResult.fail(exc.code, exc.message, ctx.correlation_id)

        return ToolResult.ok(result, ctx.correlation_id)
