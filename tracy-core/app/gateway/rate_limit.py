"""Rate limiting de la Gateway (docs/tracy/02-ARCHITECTURE.md §Gateway).

Responsabilité : limitation de débit pour protéger Tracy Core.

V1 : rate limiting simple en mémoire (par adresse IP ou store_id).
V2 : migration vers Redis pour un rate limiting distribué.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Rate limiter simple en mémoire.

    Suit le nombre de requêtes par clé (IP ou store_id) sur une fenêtre
    glissante d'une minute.
    """

    def __init__(self, max_requests_per_minute: int = 60) -> None:
        self._max = max_requests_per_minute
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        """Vérifie si la clé a dépassé le quota.

        Args:
            key: Clé de rate limiting (ex: IP ou store_id).

        Raises:
            HTTPException: 429 si le quota est dépassé.
        """
        now = time.monotonic()
        window_start = now - 60.0

        # Nettoyer les anciennes entrées
        self._requests[key] = [t for t in self._requests[key] if t > window_start]

        if len(self._requests[key]) >= self._max:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Trop de requêtes. Réessayez dans un instant.",
                headers={"Retry-After": "60"},
            )

        self._requests[key].append(now)


# Instance globale — sera configurée dans main.py
_rate_limiter: InMemoryRateLimiter | None = None


def configure_rate_limiter(max_requests_per_minute: int) -> None:
    """Configure le rate limiter global."""
    global _rate_limiter
    _rate_limiter = InMemoryRateLimiter(max_requests_per_minute)


async def check_rate_limit(request: Request) -> None:
    """Dépendance FastAPI pour vérifier le rate limiting.

    Utilise l'IP du client comme clé de rate limiting.
    """
    if _rate_limiter is None:
        return

    client_ip = request.client.host if request.client else "unknown"
    _rate_limiter.check(client_ip)
