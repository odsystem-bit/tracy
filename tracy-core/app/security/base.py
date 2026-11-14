"""Interfaces abstraites pour le module security.

Module préparé. Aucune implémentation dans la V1.

Chaque composant est une interface abstraite (ABC) destinée à être
implémentée dans les versions ultérieures. Aucune logique métier ici.

Règle (docs/tracy/07-DEVELOPMENT_RULES.md) : Tracy ne décide jamais.
Le PermissionEngine vérifie les permissions mais la décision finale
d'autorisation appartient toujours à Mantota.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.security.schemas import (
    DeviceInfo,
    FraudSignal,
    Permission,
    Role,
    Session,
    TokenInfo,
)


class PermissionEngine(ABC):
    """Moteur de vérification des permissions.

    Vérifie qu'un utilisateur (identifié par son rôle) a le droit
    d'exécuter une action sur une ressource. Les règles de permissions
    sont définies côté Mantota — Tracy ne fait que vérifier.

    TODO V2: Implémenter avec cache Redis pour les règles de permissions.
    """

    @abstractmethod
    async def check_permission(
        self,
        user_id: str,
        permission: Permission,
        store_id: str | None = None,
    ) -> bool:
        """Vérifie si un utilisateur a une permission donnée.

        Args:
            user_id: Identifiant de l'utilisateur.
            permission: Permission à vérifier (resource, action, scope).
            store_id: Boutique concernée (pour isolation multi-tenant).

        Returns:
            True si l'utilisateur a la permission, False sinon.
        """

    @abstractmethod
    async def get_role(self, user_id: str) -> Role:
        """Récupère le rôle d'un utilisateur depuis Mantota."""


class RoleChecker(ABC):
    """Vérificateur de rôles.

    Détermine le rôle d'un utilisateur (client, vendeur, partenaire)
    et fournit les permissions associées.

    TODO V2: Implémenter avec cache local + invalidation via events.
    """

    @abstractmethod
    async def get_user_role(self, user_id: str, store_id: str | None = None) -> Role:
        """Retourne le rôle d'un utilisateur dans le contexte d'une boutique."""

    @abstractmethod
    async def is_vendor(self, user_id: str, store_id: str) -> bool:
        """Vérifie si l'utilisateur est le vendeur de la boutique."""

    @abstractmethod
    async def is_client(self, user_id: str) -> bool:
        """Vérifie si l'utilisateur est un client."""


class SessionManager(ABC):
    """Gestionnaire de sessions.

    Crée, valide et invalide les sessions utilisateur. Les sessions
    sont stockées en Redis (court terme) avec TTL configurable.

    TODO V2: Implémenter avec Redis.
    """

    @abstractmethod
    async def create_session(self, user_id: str, store_id: str | None = None) -> Session:
        """Crée une nouvelle session."""

    @abstractmethod
    async def get_session(self, session_id: str) -> Session | None:
        """Récupère une session par son ID."""

    @abstractmethod
    async def revoke_session(self, session_id: str) -> None:
        """Révoque une session."""

    @abstractmethod
    async def refresh_session(self, session_id: str) -> Session | None:
        """Prolonge la durée de vie d'une session."""


class DeviceManager(ABC):
    """Gestionnaire d'appareils connectés.

    Suit les appareils utilisés par chaque utilisateur pour des
    fins de sécurité et de notifications push.

    TODO V2: Implémenter avec stockage Mantota.
    """

    @abstractmethod
    async def register_device(self, device: DeviceInfo) -> None:
        """Enregistre un nouvel appareil."""

    @abstractmethod
    async def get_devices(self, user_id: str) -> list[DeviceInfo]:
        """Retourne les appareils d'un utilisateur."""

    @abstractmethod
    async def revoke_device(self, device_id: str) -> None:
        """Révoque un appareil."""

    @abstractmethod
    async def trust_device(self, device_id: str) -> None:
        """Marque un appareil comme de confiance."""


class TokenManager(ABC):
    """Gestionnaire de tokens d'authentification.

    Gère les tokens API, JWT et tokens de session. Inclut la
    révocation et la rotation.

    TODO V2: Implémenter avec stockage Redis + invalidation.
    """

    @abstractmethod
    async def issue_token(self, user_id: str, token_type: str = "api_key") -> TokenInfo:
        """Émet un nouveau token."""

    @abstractmethod
    async def validate_token(self, token: str) -> TokenInfo | None:
        """Valide un token et retourne ses infos."""

    @abstractmethod
    async def revoke_token(self, token_id: str) -> None:
        """Révoque un token."""

    @abstractmethod
    async def rotate_token(self, token_id: str) -> TokenInfo:
        """Rotations un token (révoque l'ancien, émet un nouveau)."""


class EncryptionService(ABC):
    """Service de chiffrement pour les données sensibles.

    Utilisé pour chiffrer les données en transit et au repos (si
    Tracy Core doit temporairement stocker des données sensibles).

    TODO V2: Implémenter avec cryptography (AES-256-GCM).
    """

    @abstractmethod
    async def encrypt(self, plaintext: str, context: str = "") -> str:
        """Chiffre un texte et retourne le ciphertext encodé en base64.

        Args:
            plaintext: Texte à chiffrer.
            context: Contexte de chiffrement (ex: user_id) pour AEAD.
        """

    @abstractmethod
    async def decrypt(self, ciphertext: str, context: str = "") -> str:
        """Déchiffre un ciphertext et retourne le plaintext."""

    @abstractmethod
    async def hash_secret(self, secret: str) -> str:
        """Hash un secret de manière irréversible (bcrypt/argon2)."""


class SecretManager(ABC):
    """Gestionnaire de secrets.

    Centralise la gestion des secrets (clés API, tokens) avec
    rotation automatique et accès sécurisé.

    TODO V2: Implémenter avec vault (HashiCorp Vault) ou AWS Secrets Manager.
    TODO V1: Utiliser les variables d'environnement (déjà en place via config.py).
    """

    @abstractmethod
    async def get_secret(self, key: str) -> str:
        """Récupère un secret par sa clé."""

    @abstractmethod
    async def set_secret(self, key: str, value: str) -> None:
        """Définit un secret."""

    @abstractmethod
    async def rotate_secret(self, key: str) -> str:
        """Rotations un secret et retourne la nouvelle valeur."""


class FraudDetector(ABC):
    """Détecteur de fraude (placeholder).

    Analyse les patterns comportementaux pour détecter des activités
    suspectes. Les signaux sont remontés à Mantota qui prend la
    décision finale.

    IMPORTANT : Tracy ne bloque jamais une action seule — elle signale
    et Mantota décide (docs/tracy/07-DEVELOPMENT_RULES.md règle fondamentale).

    TODO V3: Implémenter avec règles + ML.
    """

    @abstractmethod
    async def analyze_request(
        self,
        user_id: str,
        action: str,
        correlation_id: str,
    ) -> FraudSignal | None:
        """Analyse une requête et retourne un signal de fraude si détecté.

        Returns:
            FraudSignal si une activité suspecte est détectée, None sinon.
        """

    @abstractmethod
    async def get_signals(self, user_id: str) -> list[FraudSignal]:
        """Retourne les signaux de fraude actifs pour un utilisateur."""
