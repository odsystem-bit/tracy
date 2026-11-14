"""Middleware de corrélation ID (docs/tracy/02-ARCHITECTURE.md §Observabilité).

Responsabilité :
- Génère ou propage un ID de corrélation unique pour chaque requête.
- L'ID est injecté dans les headers de réponse pour traçabilité côté client.
- L'ID est lié au contexte structlog pour que toutes les logs de la requête
  incluent automatiquement le correlation_id.

Règle (docs/tracy/02-ARCHITECTURE.md) : chaque appel est traçable
(ID de corrélation) de bout en bout.
"""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.logging_config import bind_correlation_id, clear_correlation_id

CORRELATION_ID_HEADER = "X-Correlation-Id"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware qui génère/propage un ID de corrélation pour chaque requête.

    Si le client fournit un X-Correlation-Id dans la requête, il est réutilisé.
    Sinon, un nouvel UUID est généré.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())

        # Lier au contexte structlog pour toutes les logs de cette requête
        bind_correlation_id(correlation_id)

        try:
            response = await call_next(request)
        finally:
            # Nettoyer le contexte à la fin de la requête
            clear_correlation_id()

        # Injecter le correlation_id dans la réponse
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
