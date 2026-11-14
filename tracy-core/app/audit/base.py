"""Interfaces abstraites pour le module audit.

Module préparé. Aucune implémentation dans la V1.

L'audit log est distinct des logs structurés (structlog) :
- structlog = logs techniques pour debugging et observabilité.
- audit = journal d'audit pour traçabilité métier et conformité.

Règle (docs/tracy/07-DEVELOPMENT_RULES.md) : Tracy ne stocke aucune
donnée durable. L'AuditRepository délègue le stockage à Mantota.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.audit.schemas import AuditContext, AuditEvent, AuditEventType


class AuditRepository(ABC):
    """Dépôt de stockage des événements d'audit.

    V1 : implémentation en mémoire (optionnelle, pour tests).
    V2 : implémentation via API Mantota (endpoint /bot/audit).
    V3 : implémentation via base dédiée (Elasticsearch, ClickHouse).

    Règle : Tracy ne stocke jamais d'audit en local de manière durable.
    Le dépôt Mantota est la source de vérité.
    """

    @abstractmethod
    async def save(self, event: AuditEvent) -> None:
        """Persiste un événement d'audit."""

    @abstractmethod
    async def query(
        self,
        event_type: AuditEventType | None = None,
        user_id: str | None = None,
        store_id: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Requête les événements d'audit avec filtres.

        Args:
            event_type: Filtrer par type d'événement.
            user_id: Filtrer par utilisateur.
            store_id: Filtrer par boutique.
            start_time: Horodatage de début (ISO 8601).
            end_time: Horodatage de fin (ISO 8601).
            limit: Nombre maximum de résultats.

        Returns:
            Liste des événements correspondants, triés par timestamp décroissant.
        """

    @abstractmethod
    async def get_by_id(self, event_id: str) -> AuditEvent | None:
        """Récupère un événement par son ID."""


class AuditLogger(ABC):
    """Logger d'audit de haut niveau.

    Interface utilisée par les agents, tools et l'orchestrateur pour
    émettre des événements d'audit. Le logger construit l'AuditEvent
    à partir du contexte courant et le persiste via l'AuditRepository.

    Usage futur :
        await audit_logger.log(
            event_type="commande",
            context=audit_ctx,
            description="Commande créée",
            after_state={"order_id": "123", "total": "50000"},
        )
    """

    @abstractmethod
    async def log(
        self,
        event_type: AuditEventType,
        context: AuditContext,
        description: str,
        *,
        before_state: dict[str, str] | None = None,
        after_state: dict[str, str] | None = None,
        severity: str = "info",
    ) -> AuditEvent:
        """Enregistre un événement d'audit.

        Args:
            event_type: Type d'événement (connexion, commande, paiement, etc.).
            context: Contexte d'audit (qui, où, correlation_id).
            description: Description lisible.
            before_state: État avant l'action (pour modifications).
            after_state: État après l'action (pour modifications).
            severity: Niveau de gravité (info, warning, critical).

        Returns:
            L'AuditEvent créé et persisté.
        """

    @abstractmethod
    async def log_error(
        self,
        context: AuditContext,
        description: str,
        error_code: str,
        error_detail: str,
    ) -> AuditEvent:
        """Enregistre une erreur technique dans l'audit.

        Raccourci pour log(event_type="erreur", severity="critical").
        """
