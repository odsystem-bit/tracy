"""Tests de la Gateway : authentification et rate limiting
(docs/tracy/02-ARCHITECTURE.md §Gateway, §Sécurité).
"""

from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.config import reset_settings_cache
from app.gateway.auth import verify_gateway_api_key
from app.gateway.rate_limit import InMemoryRateLimiter


def test_auth_valid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Une clé API valide passe l'authentification."""
    from app.config import Settings

    monkeypatch.setenv("GATEWAY_API_KEYS", "valid-key-1,valid-key-2")
    reset_settings_cache()

    app = FastAPI()

    @app.get("/protected")
    async def protected(_auth: None = Depends(verify_gateway_api_key)):
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/protected", headers={"X-Api-Key": "valid-key-1"})
    assert response.status_code == 200


def test_auth_invalid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Une clé API invalide est rejetée avec 401."""
    monkeypatch.setenv("GATEWAY_API_KEYS", "valid-key-1")
    reset_settings_cache()

    app = FastAPI()

    @app.get("/protected")
    async def protected(_auth: None = Depends(verify_gateway_api_key)):
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/protected", headers={"X-Api-Key": "wrong-key"})
    assert response.status_code == 401


def test_auth_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """L'absence de clé API est rejetée avec 401."""
    monkeypatch.setenv("GATEWAY_API_KEYS", "valid-key-1")
    reset_settings_cache()

    app = FastAPI()

    @app.get("/protected")
    async def protected(_auth: None = Depends(verify_gateway_api_key)):
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/protected")
    assert response.status_code == 401


def test_auth_no_keys_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Si aucune clé n'est configurée, la Gateway retourne 503."""
    monkeypatch.setenv("GATEWAY_API_KEYS", "")
    reset_settings_cache()

    app = FastAPI()

    @app.get("/protected")
    async def protected(_auth: None = Depends(verify_gateway_api_key)):
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/protected", headers={"X-Api-Key": "any-key"})
    assert response.status_code == 503


def test_rate_limiter_allows_under_limit() -> None:
    """Le rate limiter autorise les requêtes sous la limite."""
    limiter = InMemoryRateLimiter(max_requests_per_minute=5)
    for _ in range(5):
        limiter.check("192.168.1.1")


def test_rate_limiter_blocks_over_limit() -> None:
    """Le rate limiter bloque les requêtes au-dessus de la limite."""
    limiter = InMemoryRateLimiter(max_requests_per_minute=3)
    for _ in range(3):
        limiter.check("10.0.0.1")

    with pytest.raises(HTTPException) as exc_info:
        limiter.check("10.0.0.1")
    assert exc_info.value.status_code == 429


def test_rate_limiter_independent_keys() -> None:
    """Le rate limiter traite les clés indépendamment."""
    limiter = InMemoryRateLimiter(max_requests_per_minute=2)
    limiter.check("ip_a")
    limiter.check("ip_a")
    limiter.check("ip_b")  # ip_b n'est pas affecté par ip_a
