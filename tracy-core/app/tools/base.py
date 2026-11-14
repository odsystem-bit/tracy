"""Contrat standard d'un Tool (docs/tracy/04-TOOLS.md).

Tout Tool respecte la même enveloppe de réponse, quel que soit le résultat.
Aucun Tool ne contient de logique métier : il valide les paramètres, appelle
Mantota, retransmet le résultat.

Règles (docs/tracy/07-DEVELOPMENT_RULES.md) :
- Tout Tool est typé (Pydantic) en entrée et sortie.
- Chaque exécution est journalisée (agent appelant, paramètres, résultat, durée).
- Un Tool ne modifie jamais de règle métier : il exécute ce que Mantota autorise.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ToolError(BaseModel):
    """Erreur typée retournée par un Tool en cas d'échec."""

    code: str
    message: str


class ToolResult(BaseModel, Generic[T]):
    """Enveloppe standard de réponse d'un Tool (docs/tracy/04-TOOLS.md).

    Succès :
        {"success": true, "data": {...}, "error": null, "correlation_id": "..."}
    Échec :
        {"success": false, "data": null, "error": {"code": "...", "message": "..."}, "correlation_id": "..."}
    """

    success: bool
    data: T | None = None
    error: ToolError | None = None
    correlation_id: str

    @classmethod
    def ok(cls, data: T, correlation_id: str) -> ToolResult[T]:
        return cls(success=True, data=data, error=None, correlation_id=correlation_id)

    @classmethod
    def fail(cls, code: str, message: str, correlation_id: str) -> ToolResult[T]:
        return cls(
            success=False,
            data=None,
            error=ToolError(code=code, message=message),
            correlation_id=correlation_id,
        )


class ToolContext(BaseModel):
    """Contexte transmis à chaque Tool : identifie l'agent appelant et la conversation."""

    agent_name: str
    correlation_id: str
    store_id: str | None = None


class Tool(ABC, Generic[T]):
    """Interface abstraite d'un Tool.

    Chaque Tool déclare :
    - son nom unique (docs/tracy/04-TOOLS.md),
    - les agents autorisés à l'appeler (permissions),
    - une méthode execute() qui valide, appelle Mantota, et retourne un ToolResult.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom unique du Tool (ex: search_products)."""

    @property
    @abstractmethod
    def allowed_agents(self) -> frozenset[str]:
        """Ensemble figé des agents autorisés à appeler ce Tool."""

    @abstractmethod
    async def execute(self, ctx: ToolContext, **kwargs: object) -> ToolResult[T]:
        """Exécute le Tool avec les paramètres fournis.

        Args:
            ctx: Contexte d'exécution (agent, correlation_id, store_id).
            **kwargs: Paramètres spécifiques au Tool.

        Returns:
            ToolResult typé contenant les données ou une erreur.
        """

    def is_allowed(self, agent_name: str) -> bool:
        """Vérifie si un agent est autorisé à appeler ce Tool."""
        return agent_name in self.allowed_agents
