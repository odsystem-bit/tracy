"""Schémas de message entrant/sortant de Tracy Core.

Ces modèles définissent l'interface publique de l'API Tracy Core
(docs/tracy/02-ARCHITECTURE.md §Tracy Core).

Règle (docs/tracy/07-DEVELOPMENT_RULES.md) : tout payload est validé
par un modèle Pydantic avant traitement.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProductCard(BaseModel):
    """Carte produit affichable dans la conversation."""

    id: str
    name: str
    price: str
    raw_price: float
    stock: int
    image_url: str | None = None
    store_id: str
    category: str | None = None
    description: str | None = None


class IncomingMessage(BaseModel):
    """Message entrant reçu par Tracy Core via la Gateway.

    Représente un message d'un client, vendeur ou partenaire, transmis
    par l'APK Mantota ou le webhook WhatsApp.
    """

    store_id: str = Field(description="Identifiant de la boutique concernée")
    customer_id: str = Field(description="Identifiant du client/vendeur/partenaire")
    text: str = Field(description="Contenu du message")
    conversation_id: str | None = Field(
        default=None,
        description="Identifiant de conversation (généré si absent)",
    )
    country_code: str | None = Field(
        default=None,
        description="Code pays ISO 2 lettres (ex: BJ, CI, NG) détecté via IP ou fourni par l'utilisateur",
    )
    city: str | None = Field(
        default=None,
        description="Ville du client (GPS inversé, profil ou saisie)",
    )
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    image: str | None = Field(
        default=None,
        description="Photo jointe au message (data URL base64 ou base64 brut)",
    )


class TracyReply(BaseModel):
    """Réponse de Tracy Core renvoyée à la Gateway."""

    text: str
    correlation_id: str
    agent: str | None = None
    tools_used: list[str] = Field(default_factory=list)
    cards: list[ProductCard] | None = None
    data: dict[str, str] | None = Field(
        default=None,
        description="Données additionnelles pour le client (ex: vendor_conversation_id pour deep-link APK)",
    )


class IntentClassification(BaseModel):
    """Résultat de la classification d'intention (docs/tracy/03-AGENTS.md §Principe de sélection)."""

    intent: Literal[
        "product_search",
        "store_search",
        "negotiation",
        "catalog_management",
        "store_creation",
        "shop_config",
        "order",
        "payment",
        "support",
        "campaign",
        "memory",
        "restaurant",
        "delivery",
        "app_download",
        "vendor_onboarding",
        "vendor_stats",
        "unknown",
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    selected_agent: str
    reason: str = ""
