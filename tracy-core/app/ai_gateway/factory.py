"""Factory de l'AI Gateway (docs/tracy/02-ARCHITECTURE.md §AI Gateway).

Responsabilités :
- instancier le fournisseur par défaut selon la configuration,
- instancier un fournisseur de repli (fallback) en cas d'indisponibilité,
- créer une AIGateway avec fallback automatique.

Règle (docs/tracy/02-ARCHITECTURE.md §Résilience) :
Si l'AI Gateway est indisponible pour un fournisseur, elle bascule automatiquement
sur un fournisseur de repli déclaré.
"""

from __future__ import annotations

from app.ai_gateway.base import AIGateway, AIProvider
from app.config import Settings
from app.logging_config import get_logger

logger = get_logger(__name__)


def create_ai_gateway(settings: Settings) -> AIGateway:
    """Crée une AIGateway à partir de la configuration.

    Args:
        settings: Configuration de Tracy Core.

    Returns:
        AIGateway avec fournisseur principal et fallback.
    """
    primary = _create_provider(settings.default_ai_provider, settings)

    fallback_name = settings.fallback_ai_provider
    fallback: AIProvider | None = None
    if fallback_name != "none":
        fallback = _create_provider(fallback_name, settings)

    return AIGateway(primary=primary, fallback=fallback)


def _create_provider(provider_name: str, settings: Settings) -> AIProvider:
    """Instancie un fournisseur IA par son nom."""
    if provider_name == "openai":
        from app.ai_gateway.openai_provider import OpenAIProvider

        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model, timeout=settings.ai_timeout)

    if provider_name == "ollama":
        from app.ai_gateway.ollama_provider import OllamaProvider

        return OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)

    if provider_name == "anthropic":
        from app.ai_gateway.anthropic_provider import AnthropicProvider

        return AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.anthropic_model, timeout=settings.ai_timeout)

    if provider_name == "deepseek":
        from app.ai_gateway.deepseek_provider import DeepSeekProvider

        return DeepSeekProvider(api_key=settings.deepseek_api_key, model=settings.deepseek_model, timeout=settings.ai_timeout)

    raise ValueError(f"Fournisseur IA non supporté : {provider_name}")
