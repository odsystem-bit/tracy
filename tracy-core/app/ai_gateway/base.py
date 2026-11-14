"""Interface commune de l'AI Gateway (docs/tracy/02-ARCHITECTURE.md §AI Gateway).

Permet de changer de fournisseur (GPT, Claude, DeepSeek, Llama, Ollama) sans
modifier le code des agents. L'AI Gateway route chaque requête IA vers le
fournisseur adapté et bascule sur un fournisseur de repli en cas d'indisponibilité.

Règles :
- 100% asynchrone (docs/tracy/07-DEVELOPMENT_RULES.md règle 13).
- Chaque appel est typé (Pydantic) et journalisé.
- Aucune logique métier dans l'AI Gateway.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field

from app.logging_config import get_logger

logger = get_logger(__name__)


class ChatMessage(BaseModel):
    """Message de conversation au format standard pour tous les fournisseurs IA."""

    role: Literal["system", "user", "assistant"]
    content: str
    images: list[str] = Field(
        default_factory=list,
        description="Images jointes (data URL base64) — multimodal si le provider le supporte",
    )


class ChatResponse(BaseModel):
    """Réponse d'un fournisseur IA."""

    content: str
    provider: str
    model: str
    tokens_used: int | None = None


class AIProvider(ABC):
    """Interface abstraite d'un fournisseur IA.

    Chaque fournisseur (OpenAI, Anthropic, DeepSeek, Ollama) implémente cette
    interface. L'AI Gateway utilise ces fournisseurs sans connaître leur implémentation.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom du fournisseur (ex: openai, ollama)."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Modèle utilisé (ex: gpt-4o-mini, llama3.2)."""

    @property
    def supports_vision(self) -> bool:
        """True si le fournisseur transmet réellement `ChatMessage.images` au modèle."""
        return False

    @abstractmethod
    async def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        """Génère une réponse à partir d'une liste de messages.

        Args:
            messages: Liste des messages de conversation (system, user, assistant).
            temperature: Température de génération (0.0 = déterministe, 1.0 = créatif).
            max_tokens: Limite de tokens à générer (None = pas de limite).

        Returns:
            ChatResponse contenant le texte généré et les métadonnées.
        """


class AIGateway:
    """Gateway IA avec fallback automatique.

    Le fournisseur principal est utilisé par défaut. En cas d'erreur, le
    fournisseur de repli est sollicité. Si aucun fallback n'est configuré,
    l'erreur du fournisseur principal est propagée.

    Règle (docs/tracy/02-ARCHITECTURE.md §Résilience) :
    Si l'AI Gateway est indisponible pour un fournisseur, elle bascule automatiquement
    sur un fournisseur de repli déclaré.
    """

    def __init__(self, primary: AIProvider, fallback: AIProvider | None = None) -> None:
        self._primary = primary
        self._fallback = fallback

    async def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        try:
            return await self._primary.complete(messages, temperature=temperature, max_tokens=max_tokens)
        except Exception as exc:
            logger.warning(
                "ai_gateway_primary_failed",
                provider=self._primary.name,
                model=self._primary.model,
                error=str(exc),
            )

            if self._fallback is None:
                raise

            logger.info(
                "ai_gateway_fallback_activated",
                fallback_provider=self._fallback.name,
                fallback_model=self._fallback.model,
            )
            return await self._fallback.complete(messages, temperature=temperature, max_tokens=max_tokens)

    async def complete_vision(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        """Comme `complete`, mais uniquement via des fournisseurs capables de vision.

        Un fournisseur « aveugle » recevrait le texte sans l'image et inventerait
        une description : on lève une erreur plutôt que de l'utiliser.
        """
        providers = [p for p in (self._primary, self._fallback) if p is not None and p.supports_vision]
        if not providers:
            raise RuntimeError("Aucun fournisseur IA capable de vision n'est configuré")
        last_exc: Exception | None = None
        for provider in providers:
            try:
                return await provider.complete(messages, temperature=temperature, max_tokens=max_tokens)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "ai_gateway_vision_failed",
                    provider=provider.name,
                    model=provider.model,
                    error=str(exc),
                )
        assert last_exc is not None
        raise last_exc
