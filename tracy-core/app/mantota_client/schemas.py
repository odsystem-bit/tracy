"""Schémas Pydantic pour les échanges avec l'API Mantota.

Ces modèles reflètent la structure des réponses de l'API bot Mantota.
Ils sont volontairement stricts (validation Pydantic) pour garantir
qu'aucune donnée non conforme ne circule dans Tracy Core.

Référence : docs/tracy/04-TOOLS.md (paramètres et réponses de chaque Tool).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ── Commerce ────────────────────────────────────────────────────────


class Product(BaseModel):
    id: str
    nom: str
    prix: float
    stock: int
    image_url: str | None = None
    store_id: str
    category: str | None = None
    description: str | None = None
    scope: str | None = None
    """local | country | other | unknown (proximité vendeur/client)."""
    shop_city: str | None = None
    distance_km: float | None = None
    delivers_to_you: bool | None = None


class ProductSearchResult(BaseModel):
    products: list[Product]
    total: int


class Store(BaseModel):
    id: str
    nom: str
    type: Literal["physique", "en_ligne"] = "en_ligne"
    note: float = 0.0
    ville: str | None = None
    logo_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    storefront_photo_url: str | None = None


class StoreCreateResult(BaseModel):
    store_id: str
    nom: str
    type: Literal["physique", "en_ligne"]
    statut: str = "active"


class StoreSearchResult(BaseModel):
    stores: list[Store]
    total: int


class CatalogCategory(BaseModel):
    id: str
    nom: str
    product_count: int = 0


class CatalogResult(BaseModel):
    store_id: str
    categories: list[CatalogCategory] = Field(default_factory=list)
    products: list[Product] = Field(default_factory=list)


# ── Configuration Boutique (règles de négociation) ─────────────────


class ShopConfig(BaseModel):
    store_id: str
    min_margin_percent: float = 10.0
    first_order_discount_percent: float = 0.0
    max_discount_percent: float = 15.0
    free_shipping_threshold: float | None = None
    auto_accept_below: float = 5.0  # auto-accepte si réduction demandée <= ce %
    custom_rules: str | None = None  # règles libres du vendeur
    currency: str = "XOF"
    address_form: str = "tu"  # "tu" ou "vous" — configurable par le vendeur


class ShopConfigResult(BaseModel):
    success: bool = True
    store_id: str
    message: str = "Configuration mise à jour"


# ── Devises ────────────────────────────────────────────────────────


class Currency(BaseModel):
    code: str
    name: str
    symbol: str
    rate_to_xof: float = 1.0
    country_codes: list[str] = Field(default_factory=list)


class CurrencyListResult(BaseModel):
    currencies: list[Currency]


# ── Commandes ───────────────────────────────────────────────────────


class Order(BaseModel):
    success: bool = True
    order_id: str
    reference: str | None = None
    payment_url: str | None = None
    tracking_url: str | None = None
    tracking_token: str | None = None
    delivery_pin: str | None = None
    amount: float | None = None

    @classmethod
    def model_validate(cls, obj: Any) -> "Order":
        if isinstance(obj, dict) and "order_id" in obj and isinstance(obj["order_id"], int):
            obj = {**obj, "order_id": str(obj["order_id"])}
        return super().model_validate(obj)


class OrderStatusHistory(BaseModel):
    statut: str
    date: str
    note: str | None = None


class OrderTrackingResult(BaseModel):
    order_id: str
    statut: str
    historique: list[OrderStatusHistory] = Field(default_factory=list)
    date_estimee_livraison: str | None = None


# ── Paiement ────────────────────────────────────────────────────────


class WalletTransaction(BaseModel):
    id: str
    type: str
    montant: float
    statut: str
    reference: str | None = None
    created_at: str | None = None


class Wallet(BaseModel):
    user_id: str
    solde_disponible: float
    solde_en_attente: float = 0.0
    dernieres_transactions: list[WalletTransaction] = Field(default_factory=list)


class PaymentResult(BaseModel):
    payment_id: str
    checkout_url: str | None = None
    statut: str
    reference: str | None = None


class WithdrawalResult(BaseModel):
    reference: str
    statut: str
    montant: float


# ── Marketing ───────────────────────────────────────────────────────


class Campaign(BaseModel):
    id: str
    nom: str
    statut: str
    audience: str | None = None
    vues: int = 0
    clics: int = 0
    conversions: int = 0


class Partner(BaseModel):
    id: str
    nom: str
    commissions_cumulees: float = 0.0
    code_parrainage: str | None = None


# ── Mémoire ─────────────────────────────────────────────────────────


class MemoryEntry(BaseModel):
    id: str | None = None
    scope: str
    entity_id: str
    key: str
    value: str
    source: str = "inferred"
    created_at: str | None = None
    updated_at: str | None = None
    expires_at: str | None = None


class MemorySearchResult(BaseModel):
    entries: list[MemoryEntry]
    total: int


# ── Abonnement Tracy ────────────────────────────────────────────────


class SubscriptionResult(BaseModel):
    statut: str
    date_expiration: str | None = None
    reference_transaction: str | None = None


# ── Restaurant ───────────────────────────────────────────────────────


class RestaurantSummary(BaseModel):
    id: str
    shop_name: str
    shop_logo: str | None = None
    shop_type: str = "restaurant_online"
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_open_now: bool = False
    rating: float = 0.0


class RestaurantListResult(BaseModel):
    restaurants: list[RestaurantSummary]


class MenuItemOptionValue(BaseModel):
    id: str
    name: str
    price_modifier: float = 0.0
    is_default: bool = False


class MenuItemOption(BaseModel):
    id: str
    name: str
    type: str = "single_choice"
    is_required: bool = False
    max_selections: int = 1
    values: list[MenuItemOptionValue] = []


class MenuItemSummary(BaseModel):
    id: str
    name: str
    description: str | None = None
    price: float
    image_url: str
    preparation_time_min: int = 15
    calories: int | None = None
    is_vegetarian: bool = False
    is_halal: bool = False
    options: list[MenuItemOption] = []


class MenuCategory(BaseModel):
    id: str
    name: str
    items: list[MenuItemSummary] = []


class RestaurantHour(BaseModel):
    day_of_week: int
    open_time: str
    close_time: str
    is_closed: bool = False


class RestaurantMenuResult(BaseModel):
    restaurant_id: str
    shop_name: str
    shop_logo: str | None = None
    is_open_now: bool = False
    address: str | None = None
    categories: list[MenuCategory] = []
    hours: list[RestaurantHour] = []


class RestaurantOrderItemInput(BaseModel):
    menu_item_id: str
    quantity: int = 1
    selected_options: list[dict] | None = None
    special_instructions: str | None = None


class RestaurantOrderResult(BaseModel):
    success: bool
    order_id: str
    order_number: str
    subtotal: float = 0.0
    delivery_fee: float = 0.0
    total: float = 0.0
    estimated_delivery_at: str | None = None
    error: str | None = None


class RestaurantOrderStatus(BaseModel):
    id: str
    order_number: str
    status: str = "pending"
    order_type: str = "delivery"
    total: float = 0.0
    estimated_delivery_at: str | None = None
    delivered_at: str | None = None
    items: list[dict] = []
