"""Configuration des logs structurés (JSON).

Règles (docs/tracy/07-DEVELOPMENT_RULES.md) :
- Aucun `print` dans le projet.
- Chaque log contient un contexte exploitable (ID de corrélation, agent, tool, durée, résultat).
- Format structuré JSON (structlog).

L'ID de corrélation est propagé via structlog contextvars pour tracer
une conversation de bout en bout (docs/tracy/02-ARCHITECTURE.md §Observabilité).
"""

from __future__ import annotations

import logging
import sys

import structlog

# Niveaux de log par environnement
_LOG_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def configure_logging(environment: str = "development", log_level: str = "INFO") -> None:
    """Configure structlog pour émettre des logs JSON structurés sur stdout.

    Args:
        environment: development, staging ou production.
        log_level: niveau de log (DEBUG, INFO, WARNING, ERROR).
    """
    level = _LOG_LEVELS.get(log_level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Retourne un logger structlog lié au module appelant."""
    return structlog.get_logger(name)


def bind_correlation_id(correlation_id: str) -> None:
    """Lie un ID de corrélation au contexte structlog courant.

    Toutes les logs émises dans ce contexte incluront automatiquement
    le correlation_id, garantissant la traçabilité de bout en bout.
    """
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def clear_correlation_id() -> None:
    """Nettoie le contexte structlog (à appeler en fin de requête)."""
    structlog.contextvars.clear_contextvars()


def bind_context(**kwargs: object) -> None:
    """Ajoute des paires clé/valeur au contexte structlog courant."""
    structlog.contextvars.bind_contextvars(**kwargs)
