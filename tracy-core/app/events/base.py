"""Schémas et interfaces pour le module events.

Module préparé. Aucune implémentation dans la V1.

L'EventBus est le point central de communication interne entre
les composants de Tracy Core. Il permet un couplage faible :
- l'orchestrateur publie des événements (message reçu, agent sélectionné, etc.),
- les modules (audit, notifications, security) s'abonnent aux événements qui les concernent,
- aucun module ne connaît les autres directement.

Règle (docs/tracy/07-DEVELOPMENT_RULES.md) : 100% asynchrone.
Les handlers d'événements doivent être des coroutines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T", bound="BaseEvent")


class BaseEvent(BaseModel):
    """Événement de base pour le système d'événements interne.

    Tous les événements de Tracy héritent de cette classe.
    Chaque événement est immuable, horodaté et tracé par correlation_id.

    Exemples d'événements futurs :
    - MessageReceivedEvent (message client/vendeur reçu)
    - IntentClassifiedEvent (intention classifiée)
    - AgentSelectedEvent (agent sélectionné)
    - ToolExecutedEvent (tool exécuté)
    - OrderCreatedEvent (commande créée)
    - PaymentInitiatedEvent (paiement initié)
    - ConversationStartedEvent / ConversationEndedEvent
    - AuditEventEmitted (événement d'audit émis)
    """

    event_id: str = Field(description="Identifiant unique de l'événement")
    event_type: str = Field(description="Type d'événement (ex: message_received, tool_executed)")
    timestamp: str = Field(description="Horodatage ISO 8601")
    correlation_id: str
    store_id: str | None = None
    user_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


# Type alias pour les handlers d'événements
EventHandler = Callable[[BaseEvent], Awaitable[None]]


class EventPublisher(ABC):
    """Interface pour publier des événements sur l'EventBus.

    Utilisée par l'orchestrateur, les agents et les tools pour
    émettre des événements sans connaître les subscribers.
    """

    @abstractmethod
    async def publish(self, event: BaseEvent) -> None:
        """Publie un événement sur le bus.

        Args:
            event: Événement à publier.
        """


class EventSubscriber(ABC):
    """Interface pour s'abonner à des événements sur l'EventBus.

    Utilisée par les modules (audit, notifications, security) pour
    réagir aux événements émis par le reste de Tracy.
    """

    @abstractmethod
    async def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """S'abonne à un type d'événement.

        Args:
            event_type: Type d'événement à écouter (ex: "message_received").
            handler: Coroutine appelée quand l'événement est publié.
        """

    @abstractmethod
    async def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """Se désabonne d'un type d'événement."""


class EventBus(EventPublisher, EventSubscriber, ABC):
    """Bus d'événements interne de Tracy Core.

    Centralise la publication et la distribution des événements.
    En V1 : implémentation en mémoire (synchrone, in-process).
    En V2 : implémentation avec Redis Pub/Sub pour distribution multi-process.
    En V3 : implémentation avec RabbitMQ pour persistance et retry.

    Règles :
    - 100% asynchrone (handlers = coroutines).
    - Un handler ne doit jamais lever une exception qui casse le bus.
    - Les handlers sont exécutés en parallèle (asyncio.gather).
    - Si un handler échoue, l'erreur est loggée mais ne propage pas.
    """

    @abstractmethod
    async def publish(self, event: BaseEvent) -> None:
        """Publie un événement et notifie tous les subscribers."""

    @abstractmethod
    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Abonne un handler à un type d'événement."""

    @abstractmethod
    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Désabonne un handler."""

    @abstractmethod
    async def get_subscriber_count(self, event_type: str) -> int:
        """Retourne le nombre de subscribers pour un type d'événement."""

    @abstractmethod
    async def aclose(self) -> None:
        """Nettoie les ressources du bus."""
