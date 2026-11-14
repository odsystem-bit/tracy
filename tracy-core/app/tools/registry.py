"""Registre central des Tools (docs/tracy/04-TOOLS.md, 07-DEVELOPMENT_RULES.md).

Le registre :
- centralise tous les Tools disponibles,
- vérifie les permissions (un agent ne peut appeler qu'un Tool qui l'autorise),
- journalise chaque exécution (agent, tool, paramètres, durée, résultat).

Aucun Tool n'est instancié en dehors de ce registre.
"""

from __future__ import annotations

import time
from typing import Any

from app.logging_config import bind_context, get_logger
from app.tools.base import Tool, ToolContext, ToolResult

logger = get_logger(__name__)


class ToolPermissionError(Exception):
    """Levée quand un agent tente d'appeler un Tool non autorisé."""

    def __init__(self, agent_name: str, tool_name: str) -> None:
        self.agent_name = agent_name
        self.tool_name = tool_name
        super().__init__(
            f"Agent '{agent_name}' n'est pas autorisé à utiliser le Tool '{tool_name}'."
        )


class ToolNotFoundError(Exception):
    """Levée quand un Tool demandé n'existe pas dans le registre."""

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' introuvable dans le registre.")


class ToolRegistry:
    """Registre central des Tools avec vérification des permissions."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool[Any]] = {}

    def register(self, tool: Tool[Any]) -> None:
        """Enregistre un Tool dans le registre.

        Raises:
            ValueError: si un Tool avec le même nom est déjà enregistré.
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' est déjà enregistré.")
        self._tools[tool.name] = tool
        logger.info("tool_registered", tool=tool.name, allowed_agents=list(tool.allowed_agents))

    def get(self, tool_name: str) -> Tool[Any]:
        """Récupère un Tool par son nom.

        Raises:
            ToolNotFoundError: si le Tool n'existe pas.
        """
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ToolNotFoundError(tool_name)
        return tool

    def list_tools(self) -> list[str]:
        """Retourne la liste des noms de Tools enregistrés."""
        return list(self._tools.keys())

    def list_tools_for_agent(self, agent_name: str) -> list[str]:
        """Retourne les Tools autorisés pour un agent donné."""
        return [name for name, tool in self._tools.items() if tool.is_allowed(agent_name)]

    async def execute(
        self,
        tool_name: str,
        ctx: ToolContext,
        **kwargs: Any,
    ) -> ToolResult[Any]:
        """Exécute un Tool après vérification des permissions.

        Args:
            tool_name: Nom du Tool à exécuter.
            ctx: Contexte d'exécution (agent, correlation_id, store_id).
            **kwargs: Paramètres du Tool.

        Returns:
            ToolResult contenant les données ou l'erreur.

        Raises:
            ToolNotFoundError: si le Tool n'existe pas.
            ToolPermissionError: si l'agent n'est pas autorisé.
        """
        tool = self.get(tool_name)

        if not tool.is_allowed(ctx.agent_name):
            logger.warning(
                "tool_permission_denied",
                agent=ctx.agent_name,
                tool=tool_name,
                correlation_id=ctx.correlation_id,
            )
            raise ToolPermissionError(ctx.agent_name, tool_name)

        bind_context(tool=tool_name, agent=ctx.agent_name)
        start = time.monotonic()

        logger.info(
            "tool_execution_started",
            tool=tool_name,
            agent=ctx.agent_name,
            correlation_id=ctx.correlation_id,
            params=kwargs,
        )

        try:
            result = await tool.execute(ctx, **kwargs)
        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            logger.error(
                "tool_execution_exception",
                tool=tool_name,
                agent=ctx.agent_name,
                correlation_id=ctx.correlation_id,
                duration_ms=round(duration_ms, 2),
                error=str(exc),
            )
            raise

        duration_ms = (time.monotonic() - start) * 1000
        logger.info(
            "tool_execution_completed",
            tool=tool_name,
            agent=ctx.agent_name,
            correlation_id=ctx.correlation_id,
            duration_ms=round(duration_ms, 2),
            success=result.success,
            error_code=result.error.code if result.error else None,
        )

        return result
