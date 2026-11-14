"""Contrat commun à tous les agents (docs/tracy/03-AGENTS.md).

Règles communes (docs/tracy/03-AGENTS.md §Règles communes) :
- Un agent ne communique jamais directement avec l'utilisateur final : il passe
  toujours par Tracy Core.
- Un agent ne possède pas de base de données propre.
- Un agent ne contourne jamais Mantota pour exécuter une action.
- Un agent signale à Tracy Core lorsqu'il atteint les limites de son rôle.

Règles de développement (docs/tracy/07-DEVELOPMENT_RULES.md) :
- Architecture DDD, SOLID, dépendances injectées.
- Pydantic obligatoire pour les entrées/sorties.
- Type hints obligatoires.
- 100% asynchrone.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.ai_gateway.base import AIGateway, ChatMessage
from app.core.schemas import ProductCard
from app.memory.short_term import ConversationContext
from app.tools.registry import ToolRegistry

_INFO_QUESTION_RE = re.compile(
    r"\?|^\s*(?:o[ùu]|comment|quel(?:le)?s?|quand|pourquoi|c'est quoi|qu'est[- ]ce)\b|"
    r"\bmarch[ée]s?\b|\bquartiers?\b|\bmoyens? de paiement\b|\bmobile money\b|\bmomo\b|"
    r"\bd[ée]lais?\b|\bfrais\b|\bgarantie\b|\bretour\b|\bproc[ée]dure\b|\bhoraires?\b",
    re.IGNORECASE,
)


class AgentInput(BaseModel):
    """Entrée standard d'un agent.

    Transmise par l'orchestrateur (Tracy Core) à l'agent sélectionné.
    """

    message: str
    store_id: str
    correlation_id: str
    customer_id: str | None = None
    conversation_id: str | None = None
    conversation_history: list[str] = Field(default_factory=list)
    country_code: str | None = None
    user_city: str | None = None
    user_latitude: float | None = None
    user_longitude: float | None = None
    conversation_context: ConversationContext | None = None
    image: str | None = None


class AgentOutput(BaseModel):
    """Sortie standard d'un agent.

    Retournée par l'agent à l'orchestrateur (Tracy Core).
    """

    reply: str
    handled: bool
    escalate: bool = False
    tools_used: list[str] = Field(default_factory=list)
    cards: list[ProductCard] | None = None
    data: dict[str, str] | None = None


AgentAutonomy = Literal[
    "full",
    "conversation_only",
    "within_margin",
    "confirmation_required",
    "always_validated",
    "propose_only",
]


class BaseAgent(ABC):
    """Interface abstraite d'un agent Tracy.

    Chaque agent déclare :
    - son nom unique (docs/tracy/03-AGENTS.md),
    - son niveau d'autonomie,
    - son system prompt (docs/tracy/05-AI_BEHAVIOR.md),
    - les Tools qu'il est autorisé à utiliser (via ToolRegistry).

    L'agent ne fait jamais d'action directe : il appelle toujours un Tool
    déclaré, qui lui-même appelle l'API Mantota.
    """

    def __init__(
        self,
        ai_gateway: AIGateway,
        tool_registry: ToolRegistry,
        address_form: str = "tu",
    ) -> None:
        self._ai_gateway = ai_gateway
        self._tool_registry = tool_registry
        self._address_form = address_form

    def set_address_form(self, address_form: str) -> None:
        """Définit dynamiquement la forme d'adresse (par boutique)."""
        self._address_form = address_form

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom unique de l'agent (ex: CommercialAgent)."""

    @property
    @abstractmethod
    def autonomy(self) -> AgentAutonomy:
        """Niveau d'autonomie de l'agent (docs/tracy/03-AGENTS.md)."""

    @property
    @abstractmethod
    def _raw_system_prompt(self) -> str:
        """System prompt brut sans la directive d'adresse."""

    @property
    def system_prompt(self) -> str:
        """System prompt final avec la directive d'adresse injectée."""
        if self._address_form == "vous":
            address_directive = (
                "\n\nFORME D'ADRESSE : Vouvoiement obligatoire. "
                "Utilise toujours « vous » pour t'adresser au client. "
                "Jamais de tutoiement."
            )
        else:
            address_directive = (
                "\n\nFORME D'ADRESSE : Tutoiement obligatoire. "
                "Utilise toujours « tu » pour t'adresser au client. "
                "Jamais de vouvoiement."
            )
        return self._raw_system_prompt + address_directive

    @property
    def allowed_tools(self) -> list[str]:
        """Liste des Tools autorisés pour cet agent (définie par le registre)."""
        return self._tool_registry.list_tools_for_agent(self.name)

    @abstractmethod
    async def handle(self, input_data: AgentInput) -> AgentOutput:
        """Traite le message d'entrée et retourne une réponse.

        Args:
            input_data: Message du client/vendeur, contexte boutique, historique.

        Returns:
            AgentOutput contenant la réponse et le statut de traitement.
        """

    async def _knowledge_context(self, ctx: Any, message: str) -> str:
        """Contexte RAG vérifié pour une question informative (lieux, marchés, paiement, délais...).

        Retourne "" si le message n'est pas une question informative, si l'outil
        `search_knowledge` n'est pas disponible pour cet agent, ou en cas d'erreur :
        le RAG enrichit la réponse, il ne doit jamais la bloquer.
        """
        if not _INFO_QUESTION_RE.search(message):
            return ""
        if "search_knowledge" not in self.allowed_tools:
            return ""
        try:
            result = await self._tool_registry.execute("search_knowledge", ctx, query=message)
        except Exception:  # noqa: BLE001 — le RAG est optionnel
            return ""
        if not result.success or result.data is None:
            return ""
        return "Base de connaissances Mantota :\n" + result.data.formatted_context  # type: ignore[union-attr]

    async def _call_ai(self, messages: list[ChatMessage], max_tokens: int | None = None) -> str:
        """Appelle l'AI Gateway avec une liste de messages et retourne le texte généré."""
        response = await self._ai_gateway.complete(messages, max_tokens=max_tokens)
        return response.content
