"""Interfaces abstraites pour le module notifications.

Module préparé. Aucune implémentation dans la V1.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.notifications.schemas import (
    NotificationEvent,
    NotificationMessage,
    NotificationResult,
    NotificationTemplate,
)


class NotificationProvider(ABC):
    """Interface abstraite d'un provider de notification.

    Chaque provider (FCM, APNS, Web Push, Email, SMS, WhatsApp) implémente
    cette interface. Le NotificationDispatcher route les messages vers le
    provider adapté selon le canal.
    """

    @property
    @abstractmethod
    def channel(self) -> str:
        """Type de canal géré par ce provider (ex: fcm, apns, email)."""

    @abstractmethod
    async def send(self, message: NotificationMessage) -> NotificationResult:
        """Envoie un message via ce provider.

        Args:
            message: Message à envoyer (canal, destinataire, contenu).

        Returns:
            NotificationResult indiquant le succès ou l'échec.
        """

    @abstractmethod
    async def aclose(self) -> None:
        """Nettoie les ressources du provider (connexions HTTP, etc.)."""


class NotificationQueue(ABC):
    """File d'attente pour les notifications asynchrones.

    Permet de découpler l'émission d'une notification de son envoi effectif.
    V1 : implémentation en mémoire (optionnelle).
    V2 : implémentation Redis ou RabbitMQ.
    """

    @abstractmethod
    async def enqueue(self, message: NotificationMessage) -> str:
        """Ajoute un message à la file d'attente.

        Returns:
            Identifiant unique du message en file.
        """

    @abstractmethod
    async def dequeue(self) -> NotificationMessage | None:
        """Récupère le prochain message à envoyer (bloquant ou non).

        Returns:
            Le message ou None si la file est vide.
        """

    @abstractmethod
    async def size(self) -> int:
        """Retourne le nombre de messages en file."""


class NotificationService(ABC):
    """Service de haut niveau pour l'envoi de notifications.

    Interface utilisée par les agents et l'orchestrateur pour émettre
    des notifications sans connaître les détails des providers.
    """

    @abstractmethod
    async def notify(
        self,
        event: NotificationEvent,
        template: NotificationTemplate,
    ) -> NotificationResult:
        """Notifie un destinataire à partir d'un événement et d'un template.

        Args:
            event: Événement déclencheur (type, entité, payload).
            template: Modèle de notification à utiliser.

        Returns:
            NotificationResult indiquant le résultat de l'envoi.
        """

    @abstractmethod
    async def register_provider(self, provider: NotificationProvider) -> None:
        """Enregistre un provider de notification."""


class NotificationDispatcher(ABC):
    """Dispatcher qui route les messages vers le bon provider.

    Le dispatcher maintient un registre des providers par canal et
    délègue l'envoi au provider approprié. Il gère également le
    fallback si un provider est indisponible.
    """

    @abstractmethod
    async def dispatch(self, message: NotificationMessage) -> NotificationResult:
        """Route un message vers le provider de son canal.

        Args:
            message: Message à envoyer.

        Returns:
            NotificationResult du provider.
        """

    @abstractmethod
    async def register_provider(self, provider: NotificationProvider) -> None:
        """Enregistre un provider dans le dispatcher."""
