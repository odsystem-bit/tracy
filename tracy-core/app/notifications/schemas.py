"""Schémas Pydantic pour le module notifications.

Module préparé. Aucune implémentation dans la V1.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


NotificationChannelType = Literal["fcm", "apns", "web_push", "email", "sms", "whatsapp"]


class NotificationChannel(BaseModel):
    """Canal de notification (ex: fcm, apns, email, sms)."""

    type: NotificationChannelType
    target: str = Field(description="Identifiant du destinataire (token FCM, email, numéro SMS, etc.)")
    metadata: dict[str, str] = Field(default_factory=dict)


class NotificationEvent(BaseModel):
    """Événement déclencheur d'une notification.

    Représente l'occurrence métier qui justifie l'envoi d'une notification
    (ex: commande confirmée, paiement reçu, relance panier abandonné).
    """

    event_type: str = Field(description="Type d'événement (ex: order_confirmed, payment_received)")
    entity_id: str = Field(description="Identifiant de l'entité concernée (order_id, customer_id, etc.)")
    store_id: str
    correlation_id: str
    payload: dict[str, str] = Field(default_factory=dict)


class NotificationTemplate(BaseModel):
    """Modèle de notification pour un canal donné.

    Définit le squelette du message à envoyer, avec des variables
    à remplacer par les données de l'événement.
    """

    template_id: str
    channel: NotificationChannelType
    locale: str = "fr"
    title_template: str = ""
    body_template: str = Field(description="Corps du message avec variables {{var}}")
    variables: list[str] = Field(default_factory=list, description="Variables attendues dans le template")


class NotificationMessage(BaseModel):
    """Message de notification prêt à être envoyé à un provider."""

    channel: NotificationChannel
    title: str
    body: str
    data: dict[str, str] = Field(default_factory=dict)
    correlation_id: str
    priority: Literal["normal", "high"] = "normal"


class NotificationResult(BaseModel):
    """Résultat de l'envoi d'une notification."""

    success: bool
    channel: NotificationChannelType
    provider_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    correlation_id: str
