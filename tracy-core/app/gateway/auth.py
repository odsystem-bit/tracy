"""Authentification de la Gateway (docs/tracy/02-ARCHITECTURE.md §Gateway).

Responsabilités :
- Authentification et vérification des tokens (clés API).
- Aucune requête n'atteint Tracy Core sans passer par cette vérification.

Règle (docs/tracy/02-ARCHITECTURE.md §Sécurité) : chaque requête entrante
(WhatsApp, APK) est vérifiée par la Gateway avant d'atteindre Tracy Core.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.config import get_settings


async def verify_gateway_api_key(x_api_key: str = Header(default="")) -> None:
    """Vérifie que la clé API fournie dans le header X-Api-Key est valide.

    Args:
        x_api_key: Valeur du header X-Api-Key.

    Raises:
        HTTPException: 401 si la clé est manquante ou invalide.
    """
    settings = get_settings()

    if not settings.gateway_api_key_set:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Aucune clé API configurée sur la Gateway. Service indisponible.",
        )

    if x_api_key not in settings.gateway_api_key_set:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou manquante.",
            headers={"WWW-Authenticate": "X-Api-Key"},
        )
