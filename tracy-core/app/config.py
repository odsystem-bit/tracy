"""Configuration centralisée de Tracy Core (Pydantic Settings).

Sources de vérité :
- docs/tracy/02-ARCHITECTURE.md (environnements, composants)
- docs/tracy/07-DEVELOPMENT_RULES.md (secrets, async, Python 3.12)

Toutes les valeurs sont injectées par variables d'environnement ou fichier .env.
Aucun secret n'est jamais codé en dur (règle 07-DEVELOPMENT_RULES.md).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Environnement ──────────────────────────────────────────────
    environment: Literal["development", "staging", "production"] = "development"
    port: int = 8000
    log_level: str = "INFO"

    # ── Mantota API ────────────────────────────────────────────────
    # Base URL de l'API Mantota (Laravel). En staging : od-system-staging.
    mantota_api_url: str = "https://mantota.test/api"
    mantota_api_key: str = Field(default="", description="Clé X-Bot-Api-Key pour l'API bot Mantota")
    mantota_timeout: float = 10.0
    mantota_retry_max: int = 3
    mantota_retry_backoff: float = 0.5

    # ── AI Gateway ─────────────────────────────────────────────────
    # Fournisseurs supportés (docs/tracy/02-ARCHITECTURE.md §AI Gateway)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Fournisseur par défaut et fournisseur de repli (fallback)
    default_ai_provider: Literal["openai", "anthropic", "deepseek", "ollama"] = "openai"
    fallback_ai_provider: Literal["openai", "anthropic", "deepseek", "ollama", "none"] = "ollama"

    ai_temperature: float = 0.7
    ai_timeout: float = 30.0
    ai_retry_max: int = 2

    # ── Comportement conversationnel ───────────────────────────────
    # Forme d'adresse : "tu" (tutoiement) ou "vous" (vouvoiement)
    address_form: Literal["tu", "vous"] = "tu"

    # ── Redis (mémoire courte, sessions, cache) ────────────────────
    redis_url: str = "redis://localhost:6379/0"
    short_term_memory_ttl: int = 3600  # secondes (1h par défaut)

    # ── Gateway (auth, rate limiting) ──────────────────────────────
    # Clés API acceptées par la Gateway, séparées par des virgules
    gateway_api_keys: str = ""
    rate_limit_per_minute: int = 60

    # ── Orchestrateur ──────────────────────────────────────────────
    max_conversation_history: int = 20
    # Repli LLM quand les regex ne comprennent pas le message (désactivé par défaut)
    llm_intent_fallback: bool = False
    # Classifieur d'intention actif :
    #   keyword = regex seuls (défaut V1)
    #   llm     = le LLM décide, regex en repli (timeout 1.5 s)
    #   shadow  = regex décident, LLM vote en fond et logue les divergences
    intent_classifier: Literal["keyword", "llm", "shadow"] = "keyword"

    # ── Liens officiels Mantota ────────────────────────────────────
    # Liens de téléchargement de l'app et site web officiels
    mantota_play_store_url: str = "https://play.google.com/store/apps/details?id=com.mantota.app"
    mantota_app_store_url: str = "https://apps.apple.com/app/mantota/id000000000"
    mantota_apk_url: str = "https://mantota.com/download/mantota.apk"
    mantota_web_url: str = "https://mantota.com"

    @property
    def gateway_api_key_set(self) -> set[str]:
        """Ensemble des clés API valides pour la Gateway."""
        return {key.strip() for key in self.gateway_api_keys.split(",") if key.strip()}

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Retourne une instance unique de Settings (singleton)."""
    return Settings()


def reset_settings_cache() -> None:
    """Invalide le cache de Settings (pour les tests)."""
    get_settings.cache_clear()
