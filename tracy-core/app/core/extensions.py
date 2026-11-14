"""Points d'extension pour les futures intégrations (docs/tracy/08-ROADMAP.md).

Ce module définit les interfaces abstraites pour les fonctionnalités futures
de Tracy Core. Aucune implémentation n'est fournie en V1 — uniquement les
contrats d'extension pour permettre un développement futur sans modification
de l'architecture existante.

Modules futurs concernés :
- Notifications : échéances, paiements, statuts de commande, campagnes.
- Contracts : paiement échelonné, réservation, contrats universels Mantota.
- Livraison : suivi, statut, itinéraire, contact livreur.
- Créateurs de contenu : génération de posts, descriptions produits, visuels.
- Live Shopping : diffusion en direct, interaction client en temps réel.

Règle : ces interfaces ne contiennent aucune logique métier. Elles définissent
uniquement le contrat d'extension. L'implémentation future respectera l'architecture
existante (Tools → Mantota, Agents → AI Gateway + Tools).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class NotificationEvent(BaseModel):
    """Événement de notification (futur module Notifications).

    Représente un événement déclenché par Mantota ou Tracy Core
    qui doit être notifié au client, vendeur ou partenaire.
    """

    event_type: str = Field(description="Type d'événement (e.g. 'payment_received', 'order_shipped')")
    recipient_id: str = Field(description="Identifiant du destinataire")
    store_id: str = Field(description="Identifiant de la boutique")
    channel: str = Field(default="whatsapp", description="Canal de notification (whatsapp, sms, in_app)")
    payload: dict[str, Any] = Field(default_factory=dict, description="Données spécifiques à l'événement")


class NotificationSender(ABC):
    """Interface d'envoi de notifications (futur module Notifications).

    V2+ : implémentation via le module notifications de Tracy Core.
    V1 : non implémenté. L'orchestrateur n'appelle pas cette interface.
    """

    @abstractmethod
    async def send(self, event: NotificationEvent) -> bool:
        """Envoie une notification. Retourne True si l'envoi a réussi."""


class ContractNotifier(ABC):
    """Interface pour les notifications de contrat (futur module Contracts).

    V2 : implémentation via le module Contracts de Mantota.
    V1 : non implémenté. Voir docs/mantota/09-CONTRACTS.md.
    """

    @abstractmethod
    async def notify_installment_due(self, contract_id: str, customer_id: str, amount: float) -> bool:
        """Notifie qu'une échéance de contrat est due."""

    @abstractmethod
    async def notify_payment_received(self, contract_id: str, customer_id: str, amount: float) -> bool:
        """Notifie qu'un paiement de contrat a été reçu."""

    @abstractmethod
    async def notify_contract_completed(self, contract_id: str, customer_id: str) -> bool:
        """Notifie qu'un contrat est entièrement payé."""


class DeliveryTracker(ABC):
    """Interface pour le suivi de livraison (futur module Livraison).

    V2+ : implémentation via l'API Mantota Livraison.
    V1 : non implémenté.
    """

    @abstractmethod
    async def get_delivery_status(self, order_id: str) -> dict[str, Any]:
        """Retourne le statut de livraison d'une commande."""

    @abstractmethod
    async def get_delivery_eta(self, order_id: str) -> str | None:
        """Retourne l'estimation de livraison d'une commande."""


class ContentGenerator(ABC):
    """Interface pour la génération de contenu (futur module Créateurs de contenu).

    V2+ : implémentation via l'AI Gateway + Mantota.
    V1 : non implémenté.
    """

    @abstractmethod
    async def generate_product_description(self, product_id: str, store_id: str) -> str:
        """Génère une description de produit optimisée pour la vente."""

    @abstractmethod
    async def generate_social_post(self, store_id: str, campaign_id: str | None = None) -> str:
        """Génère un post pour les réseaux sociaux."""


class LiveShoppingHandler(ABC):
    """Interface pour le Live Shopping (futur module Live Shopping).

    V3+ : implémentation via l'API Mantota Live Shopping.
    V1 : non implémenté.
    """

    @abstractmethod
    async def handle_live_message(self, session_id: str, customer_id: str, message: str) -> str:
        """Traite un message pendant une session de Live Shopping."""


class ExtensionRegistry:
    """Registre des points d'extension.

    Permet à V2+ d'enregistrer des implémentations pour les interfaces
    d'extension sans modifier l'orchestrateur ou les agents existants.

    V1 : le registre est vide. Aucune extension n'est enregistrée.
    L'orchestrateur vérifie l'existence d'une extension avant de l'appeler.
    """

    def __init__(self) -> None:
        self._extensions: dict[str, Any] = {}

    def register(self, name: str, implementation: Any) -> None:
        if name in self._extensions:
            raise ValueError(f"Extension '{name}' est déjà enregistrée.")
        self._extensions[name] = implementation

    def get(self, name: str) -> Any | None:
        return self._extensions.get(name)

    def has(self, name: str) -> bool:
        return name in self._extensions
