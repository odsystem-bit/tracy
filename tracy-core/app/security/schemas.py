"""Schémas Pydantic pour le module security.

Module préparé. Aucune implémentation dans la V1.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Permission(BaseModel):
    """Permission d'accès à une ressource ou action."""

    resource: str = Field(description="Ressource concernée (ex: catalog, orders, wallet)")
    action: Literal["read", "write", "delete", "execute"] = "read"
    scope: str = Field(default="store", description="Portée (store, global, conversation)")


class Role(BaseModel):
    """Rôle utilisateur avec permissions associées."""

    name: str = Field(description="Nom du rôle (ex: client, vendor, partner, admin)")
    permissions: list[Permission] = Field(default_factory=list)


class Session(BaseModel):
    """Session utilisateur active."""

    session_id: str
    user_id: str
    store_id: str | None = None
    role: str = "client"
    created_at: str
    expires_at: str
    metadata: dict[str, str] = Field(default_factory=dict)


class DeviceInfo(BaseModel):
    """Informations sur un appareil connecté."""

    device_id: str
    user_id: str
    platform: str | None = None
    app_version: str | None = None
    last_seen: str | None = None
    trusted: bool = False


class TokenInfo(BaseModel):
    """Informations sur un token d'authentification."""

    token_id: str
    user_id: str
    token_type: Literal["api_key", "jwt", "session"] = "api_key"
    issued_at: str
    expires_at: str | None = None
    revoked: bool = False


class FraudSignal(BaseModel):
    """Signal de fraude détecté par le FraudDetector.

    Le FraudDetector analyse les patterns comportementaux et signale
    les activités suspectes. La décision finale appartient toujours à Mantota.
    """

    signal_id: str
    user_id: str
    signal_type: str = Field(description="Type de signal (ex: rapid_requests, unusual_location)")
    severity: Literal["low", "medium", "high"] = "low"
    description: str
    correlation_id: str
    detected_at: str
