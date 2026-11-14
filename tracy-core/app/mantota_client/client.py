"""Client HTTP asynchrone et typé vers l'API Mantota.

Règle (docs/tracy/07-DEVELOPMENT_RULES.md) : c'est le SEUL point de contact entre
Tracy Core et Mantota. Aucun Tool n'utilise httpx directement, il passe par ce client.

Le client gère :
- l'authentification via header X-Bot-Api-Key,
- les retries avec backoff exponentiel sur erreurs réseau,
- le mapping des codes HTTP vers une hiérarchie d'exceptions typée,
- la validation Pydantic des réponses.

Note : les chemins d'endpoints suivent la convention documentée dans
docs/tracy/04-TOOLS.md. Ils sont à ajuster dès que les endpoints réels
de l'API "bot" de Mantota sont exposés côté od-system-staging.
"""

from __future__ import annotations

import asyncio
from types import TracebackType
from typing import Any

import httpx

from app.logging_config import get_logger
from app.mantota_client.exceptions import (
    MantotaApiError,
    MantotaAuthenticationError,
    MantotaConnectionError,
    MantotaNotFoundError,
    MantotaTimeoutError,
    MantotaValidationError,
)
from app.mantota_client.schemas import (
    Campaign,
    CatalogResult,
    CurrencyListResult,
    MemoryEntry,
    MemorySearchResult,
    Order,
    OrderTrackingResult,
    Partner,
    PaymentResult,
    ProductSearchResult,
    RestaurantListResult,
    RestaurantMenuResult,
    RestaurantOrderResult,
    RestaurantOrderStatus,
    ShopConfig,
    ShopConfigResult,
    StoreCreateResult,
    StoreSearchResult,
    SubscriptionResult,
    Wallet,
    WithdrawalResult,
)

logger = get_logger(__name__)


class MantotaClient:
    """Client HTTP typé vers l'API bot Mantota.

    Cycle de vie : utiliser en context manager ou appeler aclose() explicitement.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 10.0,
        retry_max: int = 3,
        retry_backoff: float = 0.5,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={
                "X-Bot-Api-Key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        self._retry_max = retry_max
        self._retry_backoff = retry_backoff

    async def __aenter__(self) -> MantotaClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    # ── Support / Litiges ───────────────────────────────────────────

    async def create_support_ticket(
        self,
        subject: str,
        category: str,
        message: str,
        guest_name: str | None = None,
        guest_email: str | None = None,
        customer_id: str | None = None,
        store_id: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "subject": subject,
            "category": category,
            "message": message,
            "guest_name": guest_name,
            "guest_email": guest_email,
            "customer_id": customer_id,
            "store_id": store_id,
        }
        return await self._post("/bot/support/tickets", json={k: v for k, v in payload.items() if v is not None})

    async def create_dispute(
        self,
        order_reference: str,
        reason: str,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "order_reference": order_reference,
            "reason": reason,
            "customer_id": customer_id,
        }
        return await self._post("/bot/disputes", json={k: v for k, v in payload.items() if v is not None})

    # ── Vendeur : comptes-rendus et statistiques ────────────────────

    async def send_vendor_report(
        self,
        vendor_id: str,
        kind: str,
        summary: str,
        customer_name: str | None = None,
        customer_phone: str | None = None,
        product_name: str | None = None,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "kind": kind,
            "summary": summary,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "product_name": product_name,
            "conversation_id": conversation_id,
        }
        return await self._post(
            f"/bot/vendors/{vendor_id}/reports",
            json={k: v for k, v in payload.items() if v is not None},
        )

    async def get_vendor_reports(self, vendor_id: str, limit: int = 10) -> dict[str, Any]:
        return await self._get(f"/bot/vendors/{vendor_id}/reports", params={"limit": limit})

    async def get_vendor_stats(self, vendor_id: str) -> dict[str, Any]:
        return await self._get(f"/bot/vendors/{vendor_id}/stats")

    async def connect_client_vendor(
        self,
        vendor_id: str,
        client_user_id: str,
        summary: str | None = None,
        product_name: str | None = None,
    ) -> dict[str, Any]:
        """Crée une vraie conversation in-app client↔vendeur (APK uniquement)."""
        payload = {
            "client_user_id": client_user_id,
            "summary": summary,
            "product_name": product_name,
        }
        return await self._post(
            f"/bot/vendors/{vendor_id}/connect",
            json={k: v for k, v in payload.items() if v is not None},
        )

    async def schedule_follow_up(
        self,
        vendor_id: str,
        customer_id: str,
        channel: str,
        message: str,
        context_key: str | None = None,
        send_at_minutes: int = 120,
    ) -> dict[str, Any]:
        """Planifie une relance proactive au client (post-négociation).

        Laravel stocke la relance dans `tracy_follow_ups` (dédup par context_key)
        et la commande planifiée l'envoie sur le bon canal à l'heure prévue.
        """
        payload = {
            "vendor_id": int(vendor_id),
            "customer_id": customer_id,
            "channel": channel,
            "message": message,
            "context_key": context_key,
            "send_at_minutes": send_at_minutes,
        }
        return await self._post(
            "/bot/follow-ups",
            json={k: v for k, v in payload.items() if v is not None},
        )

    # ── Méthode interne : GET avec retry ────────────────────────────

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def _post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("POST", path, json=json)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        last_exc: Exception | None = None

        for attempt in range(1, self._retry_max + 1):
            try:
                response = await self._client.request(method, path, params=params, json=json)
            except httpx.TimeoutException as exc:
                last_exc = MantotaTimeoutError(str(exc))
                logger.warning("mantota_timeout", path=path, attempt=attempt)
            except httpx.RequestError as exc:
                last_exc = MantotaConnectionError(str(exc))
                logger.warning("mantota_connection_error", path=path, attempt=attempt, error=str(exc))
            else:
                return self._handle_response(response, path)

            if attempt < self._retry_max:
                await asyncio.sleep(self._retry_backoff * (2 ** (attempt - 1)))

        assert last_exc is not None
        raise last_exc

    def _handle_response(self, response: httpx.Response, path: str) -> dict[str, Any]:
        status = response.status_code

        if status == 200 or status == 201:
            return response.json()

        if status == 404:
            raise MantotaNotFoundError("Ressource", path)

        if status in (401, 403):
            raise MantotaAuthenticationError()

        if status == 422:
            detail = response.text
            raise MantotaValidationError(detail)

        if status >= 500:
            logger.error("mantota_server_error", path=path, status=status, body=response.text)
            raise MantotaApiError(
                "MANTOTA_SERVER_ERROR",
                f"HTTP {status}",
                status_code=status,
            )

        # Autres 4xx
        raise MantotaApiError(
            "MANTOTA_ERROR",
            f"HTTP {status}: {response.text}",
            status_code=status,
        )

    # ── Commerce ───────────────────────────────────────────────────

    async def search_products(
        self,
        query: str,
        store_id: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        limit: int = 10,
        country: str | None = None,
        city: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> ProductSearchResult:
        params: dict[str, str | float | int] = {"query": query, "limit": limit}
        if city:
            params["city"] = city
        if latitude is not None and longitude is not None:
            params["lat"] = latitude
            params["lng"] = longitude
        if store_id is not None:
            params["store_id"] = store_id
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if country is not None:
            params["country"] = country

        data = await self._get("/bot/products/search", params=params)
        return ProductSearchResult.model_validate(data)

    async def search_catalog(
        self,
        store_id: str,
        category: str | None = None,
    ) -> CatalogResult:
        params: dict[str, str] = {"store_id": store_id}
        if category is not None:
            params["category"] = category

        data = await self._get("/bot/catalog/search", params=params)
        return CatalogResult.model_validate(data)

    async def search_store(
        self,
        query: str,
        city: str | None = None,
    ) -> StoreSearchResult:
        params: dict[str, str] = {"query": query}
        if city is not None:
            params["city"] = city

        data = await self._get("/bot/stores/search", params=params)
        return StoreSearchResult.model_validate(data)

    async def get_store_info(
        self,
        store_id: str,
    ) -> dict[str, Any]:
        """Récupère les infos d'une boutique par son ID."""
        return await self._get(f"/bot/stores/{store_id}/info")

    async def create_store(
        self,
        vendor_id: str,
        nom: str,
        store_type: str,
        category: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        storefront_photo_url: str | None = None,
        logo_url: str | None = None,
    ) -> StoreCreateResult:
        payload: dict[str, Any] = {
            "vendor_id": vendor_id,
            "nom": nom,
            "type": store_type,
        }
        if category is not None:
            payload["category"] = category
        if latitude is not None:
            payload["latitude"] = latitude
        if longitude is not None:
            payload["longitude"] = longitude
        if storefront_photo_url is not None:
            payload["storefront_photo_url"] = storefront_photo_url
        if logo_url is not None:
            payload["logo_url"] = logo_url
        data = await self._post("/bot/stores", json=payload)
        return StoreCreateResult.model_validate(data)

    # ── Configuration Boutique ────────────────────────────────────

    async def get_shop_config(self, store_id: str) -> ShopConfig:
        data = await self._get(f"/bot/stores/{store_id}/config")
        return ShopConfig.model_validate(data)

    async def update_shop_config(
        self,
        store_id: str,
        min_margin_percent: float | None = None,
        first_order_discount_percent: float | None = None,
        max_discount_percent: float | None = None,
        free_shipping_threshold: float | None = None,
        auto_accept_below: float | None = None,
        custom_rules: str | None = None,
        currency: str | None = None,
    ) -> ShopConfigResult:
        payload: dict[str, Any] = {"store_id": store_id}
        if min_margin_percent is not None:
            payload["min_margin_percent"] = min_margin_percent
        if first_order_discount_percent is not None:
            payload["first_order_discount_percent"] = first_order_discount_percent
        if max_discount_percent is not None:
            payload["max_discount_percent"] = max_discount_percent
        if free_shipping_threshold is not None:
            payload["free_shipping_threshold"] = free_shipping_threshold
        if auto_accept_below is not None:
            payload["auto_accept_below"] = auto_accept_below
        if custom_rules is not None:
            payload["custom_rules"] = custom_rules
        if currency is not None:
            payload["currency"] = currency
        data = await self._post(f"/bot/stores/{store_id}/config", json=payload)
        return ShopConfigResult.model_validate(data)

    # ── Référentiel géographique ────────────────────────────────────

    async def resolve_geo(self, query: str) -> dict[str, Any]:
        """Résout un nom de lieu (quartier ou ville) dans le référentiel géographique.

        GET /api/geo/resolve?query=X
        Retourne {'found': bool, 'type': 'quartier'|'ville', ...} ou {'found': False}
        """
        try:
            return await self._get("/api/geo/resolve", params={"query": query})
        except MantotaNotFoundError:
            return {"found": False, "query": query}
        except httpx.RequestError as e:
            logger.error(f"Network error during geo resolve: {e}")
            raise

    async def get_ville_quartiers(self, ville_id: int) -> dict[str, Any]:
        """Récupère la liste des quartiers d'une ville.

        GET /api/villes/{id}/quartiers
        """
        data = await self._get(f"/api/villes/{ville_id}/quartiers")
        return data

    # ── Quartiers de livraison ──────────────────────────────────────

    async def get_delivery_quartiers(self, store_id: str) -> dict[str, Any]:
        """Récupère les quartiers de livraison d'une boutique.

        GET /bot/stores/{store_id}/delivery-quartiers
        """
        data = await self._get(f"/bot/stores/{store_id}/delivery-quartiers")
        return data

    async def set_delivery_quartiers(
        self,
        store_id: str,
        quartier_ids: list[int] | None = None,
        ville_id: int | None = None,
        exclude_quartier_ids: list[int] | None = None,
        replace: bool = False,
    ) -> dict[str, Any]:
        """Définit les quartiers de livraison d'une boutique.

        POST /bot/stores/{store_id}/delivery-quartiers
        - quartier_ids : liste d'IDs de quartiers précis
        - ville_id : pré-coche tous les quartiers de la ville
        - exclude_quartier_ids : quartiers à exclure (mode "sauf [quartier]")
        - replace : si True, remplace toute la liste existante
        """
        payload: dict[str, Any] = {}
        if quartier_ids is not None:
            payload["quartier_ids"] = quartier_ids
        if ville_id is not None:
            payload["ville_id"] = ville_id
        if exclude_quartier_ids is not None:
            payload["exclude_quartier_ids"] = exclude_quartier_ids
        if replace:
            payload["replace"] = True

        data = await self._post(f"/bot/stores/{store_id}/delivery-quartiers", json=payload)
        return data

    async def remove_delivery_quartier(self, store_id: str, quartier_id: int) -> dict[str, Any]:
        """Retire un quartier précis de la liste de livraison.

        DELETE /bot/stores/{store_id}/delivery-quartiers/{quartier_id}
        """
        try:
            return await self._request("DELETE", f"/bot/stores/{store_id}/delivery-quartiers/{quartier_id}")
        except MantotaNotFoundError:
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error removing delivery quartier: {e}")
            raise

    # ── Devises ─────────────────────────────────────────────────────

    async def get_currencies(self) -> CurrencyListResult:
        data = await self._get("/bot/currencies")
        return CurrencyListResult.model_validate(data)

    # ── Commandes ──────────────────────────────────────────────────

    async def create_order(
        self,
        vendor_id: str,
        product_id: str,
        customer_name: str,
        customer_phone: str,
        customer_whatsapp: str,
        country: str,
        city: str,
        customer_email: str | None = None,
        landmark_indication: str | None = None,
        agreed_price: float | None = None,
    ) -> Order:
        payload: dict[str, Any] = {
            "vendor_id": vendor_id,
            "product_id": product_id,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "customer_whatsapp": customer_whatsapp,
            "country": country,
            "city": city,
        }
        if customer_email is not None:
            payload["customer_email"] = customer_email
        if landmark_indication is not None:
            payload["landmark_indication"] = landmark_indication
        if agreed_price is not None:
            payload["agreed_price"] = agreed_price
        data = await self._post("/bot/orders", json=payload)
        return Order.model_validate(data)

    async def cancel_order(self, order_id: str, reason: str) -> dict[str, Any]:
        payload = {"reason": reason}
        data = await self._post(f"/bot/orders/{order_id}/cancel", json=payload)
        return data

    async def track_order(self, order_id: str) -> OrderTrackingResult:
        data = await self._get(f"/bot/orders/{order_id}/track")
        return OrderTrackingResult.model_validate(data)

    # ── Paiement ───────────────────────────────────────────────────

    async def create_payment(
        self,
        order_id: str,
        amount: float,
        currency: str,
        method: str,
    ) -> PaymentResult:
        payload = {
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "method": method,
        }
        data = await self._post("/bot/payments", json=payload)
        return PaymentResult.model_validate(data)

    async def get_wallet(self, user_id: str) -> Wallet:
        data = await self._get(f"/bot/wallet/{user_id}")
        return Wallet.model_validate(data)

    async def request_withdrawal(
        self,
        user_id: str,
        amount: float,
        payout_method: str,
        phone: str,
        country: str,
    ) -> WithdrawalResult:
        payload = {
            "user_id": user_id,
            "amount": amount,
            "payout_method": payout_method,
            "phone": phone,
            "country": country,
        }
        data = await self._post("/bot/wallet/withdraw", json=payload)
        return WithdrawalResult.model_validate(data)

    async def send_payment_link(self, order_id: str, channel: str) -> dict[str, Any]:
        payload = {"order_id": order_id, "channel": channel}
        data = await self._post("/bot/payments/send-link", json=payload)
        return data

    # ── Marketing ──────────────────────────────────────────────────

    async def get_campaign(self, campaign_id: str) -> Campaign:
        data = await self._get(f"/bot/campaigns/{campaign_id}")
        return Campaign.model_validate(data)

    async def search_partner(self, query: str) -> Partner:
        params = {"query": query}
        data = await self._get("/bot/partners/search", params=params)
        return Partner.model_validate(data)

    async def send_catalog(
        self,
        store_id: str,
        product_ids: list[str] | None = None,
        channel: str = "whatsapp",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"store_id": store_id, "channel": channel}
        if product_ids is not None:
            payload["product_ids"] = product_ids
        data = await self._post("/bot/catalog/send", json=payload)
        return data

    # ── Mémoire ────────────────────────────────────────────────────

    async def save_memory(
        self,
        scope: str,
        entity_id: str,
        key: str,
        value: str,
        source: str = "inferred",
    ) -> MemoryEntry:
        payload = {
            "scope": scope,
            "entity_id": entity_id,
            "key": key,
            "value": value,
            "source": source,
        }
        data = await self._post("/bot/memory", json=payload)
        return MemoryEntry.model_validate(data)

    async def search_memory(
        self,
        scope: str,
        entity_id: str,
        query: str | None = None,
    ) -> MemorySearchResult:
        params: dict[str, str] = {"scope": scope, "entity_id": entity_id}
        if query is not None:
            params["query"] = query
        data = await self._get("/bot/memory/search", params=params)
        return MemorySearchResult.model_validate(data)

    async def update_memory(self, memory_id: str, value: str) -> dict[str, Any]:
        payload = {"value": value}
        data = await self._patch(f"/bot/memory/{memory_id}", json=payload)
        return data

    async def delete_memory(self, memory_id: str, reason: str) -> dict[str, Any]:
        payload = {"reason": reason}
        data = await self._request("DELETE", f"/bot/memory/{memory_id}", json=payload)
        return data

    async def _patch(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("PATCH", path, json=json)

    # ── Abonnement Tracy ───────────────────────────────────────────

    async def activate_tracy_subscription(
        self,
        vendor_id: str,
        plan: str,
    ) -> SubscriptionResult:
        payload = {"vendor_id": vendor_id, "plan": plan}
        data = await self._post("/bot/subscriptions/tracy", json=payload)
        return SubscriptionResult.model_validate(data)

    # ── Restaurant ─────────────────────────────────────────────────

    async def search_restaurants(
        self,
        lat: float | None = None,
        lng: float | None = None,
    ) -> RestaurantListResult:
        params: dict[str, float] = {}
        if lat is not None:
            params["lat"] = lat
        if lng is not None:
            params["lng"] = lng
        data = await self._get("/bot/restaurant/search", params=params or None)
        return RestaurantListResult.model_validate(data)

    async def get_restaurant_menu(self, restaurant_id: str) -> RestaurantMenuResult:
        data = await self._get(f"/bot/restaurant/menu/{restaurant_id}")
        # Adapt the response to match our schema
        rest = data.get("restaurant", {})
        return RestaurantMenuResult(
            restaurant_id=str(rest.get("id", restaurant_id)),
            shop_name=rest.get("shop_name", "Restaurant"),
            shop_logo=rest.get("shop_logo"),
            is_open_now=rest.get("is_open_now", False),
            address=rest.get("address"),
            categories=data.get("categories", []),
            hours=data.get("hours", []),
        )

    async def create_restaurant_order(
        self,
        restaurant_id: str,
        customer_id: str,
        order_type: str,
        items: list[dict[str, Any]],
        delivery_address: str | None = None,
        delivery_latitude: float | None = None,
        delivery_longitude: float | None = None,
        notes: str | None = None,
    ) -> RestaurantOrderResult:
        payload: dict[str, Any] = {
            "restaurant_id": restaurant_id,
            "customer_id": customer_id,
            "order_type": order_type,
            "items": items,
        }
        if delivery_address is not None:
            payload["delivery_address"] = delivery_address
        if delivery_latitude is not None:
            payload["delivery_latitude"] = delivery_latitude
        if delivery_longitude is not None:
            payload["delivery_longitude"] = delivery_longitude
        if notes is not None:
            payload["notes"] = notes
        data = await self._post("/bot/restaurant/orders", json=payload)
        return RestaurantOrderResult.model_validate(data)

    async def get_restaurant_order_status(self, order_id: str) -> RestaurantOrderStatus:
        data = await self._get(f"/bot/restaurant/orders/{order_id}/status")
        return RestaurantOrderStatus.model_validate(data)

    async def update_restaurant_order_status(
        self,
        order_id: str,
        status: str,
    ) -> dict[str, Any]:
        payload = {"status": status}
        data = await self._request("PATCH", f"/bot/restaurant/orders/{order_id}/status", json=payload)
        return data

    # ── Knowledge RAG ────────────────────────────────────────────────

    async def search_knowledge(
        self,
        embedding: list[float],
        country_id: int | None = None,
        category: str | None = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Recherche vectorielle dans la base de connaissances (pgvector).

        Args:
            embedding: Vecteur de 1536 dimensions (text-embedding-3-small).
            country_id: ID du pays pour filtrer (None = tous).
            category: Catégorie de document (None = toutes).
            top_k: Nombre de résultats à retourner.

        Returns:
            Dict contenant la clé "results" avec une liste de chunks.
        """
        payload: dict[str, Any] = {
            "embedding": embedding,
            "top_k": top_k,
        }
        if country_id is not None:
            payload["country_id"] = country_id
        if category is not None:
            payload["category"] = category
        data = await self._post("/bot/knowledge/search", json=payload)
        return data

    async def log_knowledge_gap(
        self,
        query_text: str,
        query_embedding: list[float],
        country_id: int | None = None,
        category_guess: str | None = None,
    ) -> dict[str, Any]:
        """Enregistre ou incrémente une lacune de connaissance (RAG Correctif).

        Appelle POST /bot/knowledge/gaps/log côté Mantota. Le endpoint cherche
        un gap existant par similarité cosinus (seuil > 0.92) et incrémente
        occurrence_count si trouvé, sinon crée un nouveau gap.

        Args:
            query_text: Texte de la requête qui n'a pas trouvé de réponse pertinente.
            query_embedding: Embedding de la requête (1536 dimensions).
            country_id: ID du pays si connu.
            category_guess: Catégorie devinée (ex: nom de l'intent en cours).

        Returns:
            Dict avec "action" ("created" ou "incremented") et "gap_id".
        """
        payload: dict[str, Any] = {
            "query_text": query_text,
            "query_embedding": query_embedding,
        }
        if country_id is not None:
            payload["country_id"] = country_id
        if category_guess is not None:
            payload["category_guess"] = category_guess
        data = await self._post("/bot/knowledge/gaps/log", json=payload)
        return data
