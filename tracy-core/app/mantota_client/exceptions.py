"""Hiérarchie d'exceptions du client Mantota.

Règle (docs/tracy/07-DEVELOPMENT_RULES.md) : Mantota est la seule source de vérité.
Toute erreur Mantota doit être typée et propagée de manière structurée pour que
les agents puissent informer honnêtement l'utilisateur (docs/tracy/02-ARCHITECTURE.md
§Résilience).
"""

from __future__ import annotations


class MantotaError(Exception):
    """Erreur de base du client Mantota."""

    def __init__(self, code: str, message: str, status_code: int | None = None) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(f"[{code}] {message}")


class MantotaConnectionError(MantotaError):
    """Erreur réseau — Mantota injoignable."""

    def __init__(self, message: str) -> None:
        super().__init__("GATEWAY_ERROR", f"Mantota injoignable : {message}")


class MantotaTimeoutError(MantotaError):
    """Délai d'attente dépassé."""

    def __init__(self, message: str) -> None:
        super().__init__("TIMEOUT", f"Délai dépassé : {message}")


class MantotaApiError(MantotaError):
    """Erreur retournée par l'API Mantota (HTTP 4xx/5xx)."""

    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(code, message, status_code)


class MantotaNotFoundError(MantotaError):
    """Ressource introuvable (HTTP 404)."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            "NOT_FOUND",
            f"{resource} introuvable : {identifier}",
            status_code=404,
        )


class MantotaAuthenticationError(MantotaError):
    """Clé API invalide ou expirée (HTTP 401/403)."""

    def __init__(self, message: str = "Authentification Mantota échouée") -> None:
        super().__init__("AUTH_ERROR", message, status_code=401)


class MantotaValidationError(MantotaError):
    """Validation refusée côté Mantota (HTTP 422)."""

    def __init__(self, message: str) -> None:
        super().__init__("VALIDATION_ERROR", message, status_code=422)
