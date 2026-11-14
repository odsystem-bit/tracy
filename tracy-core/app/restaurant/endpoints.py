"""Endpoints API restaurant pour Tracy Core.

Tracy gère les restaurants de bout en bout :
    POST /restaurant/chat          — Chat restaurant (proxy vers l'orchestrateur)
    GET  /restaurant/list          — Liste des restaurants
    GET  /restaurant/menu/{id}     — Menu d'un restaurant
    POST /restaurant/order         — Créer une commande restaurant
    GET  /restaurant/order/{id}    — Statut d'une commande restaurant
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.gateway.auth import verify_gateway_api_key
from app.logging_config import get_logger
from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError, MantotaNotFoundError

logger = get_logger(__name__)

router = APIRouter(prefix="/restaurant", tags=["restaurant"])


# ── Schemas ──────────────────────────────────────────────────────────


class RestaurantListItem(BaseModel):
    id: str
    shop_name: str
    shop_logo: str | None = None
    shop_type: str = "restaurant_online"
    address: str | None = None
    is_open_now: bool = False
    rating: float = 0.0


class RestaurantListResponse(BaseModel):
    restaurants: list[RestaurantListItem]


class OrderItemInput(BaseModel):
    menu_item_id: str
    quantity: int = 1
    selected_options: list[dict[str, Any]] | None = None
    special_instructions: str | None = None


class CreateOrderRequest(BaseModel):
    restaurant_id: str
    customer_id: str
    order_type: str = "delivery"
    items: list[OrderItemInput]
    delivery_address: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    notes: str | None = None


class CreateOrderResponse(BaseModel):
    success: bool
    order_id: str
    order_number: str
    subtotal: float = 0.0
    delivery_fee: float = 0.0
    total: float = 0.0
    estimated_delivery_at: str | None = None
    error: str | None = None


class OrderStatusResponse(BaseModel):
    id: str
    order_number: str
    status: str = "pending"
    order_type: str = "delivery"
    total: float = 0.0
    estimated_delivery_at: str | None = None
    delivered_at: str | None = None
    items: list[dict[str, Any]] = []


# ── Endpoints ────────────────────────────────────────────────────────


@router.get("/list", response_model=RestaurantListResponse)
async def list_restaurants(
    request: Request,
    _auth: None = Depends(verify_gateway_api_key),
) -> RestaurantListResponse:
    """Liste tous les restaurants disponibles."""
    mantota: MantotaClient = request.app.state.mantota_client
    try:
        result = await mantota.search_restaurants()
    except MantotaError as exc:
        logger.error("restaurant_list_error", error=str(exc))
        return RestaurantListResponse(restaurants=[])
    return RestaurantListResponse(
        restaurants=[
            RestaurantListItem(
                id=r.id,
                shop_name=r.shop_name,
                shop_logo=r.shop_logo,
                shop_type=r.shop_type,
                address=r.address,
                is_open_now=r.is_open_now,
                rating=r.rating,
            )
            for r in result.restaurants
        ]
    )


@router.get("/menu/{restaurant_id}")
async def get_menu(
    restaurant_id: str,
    request: Request,
    _auth: None = Depends(verify_gateway_api_key),
) -> dict[str, Any]:
    """Récupère le menu complet d'un restaurant."""
    mantota: MantotaClient = request.app.state.mantota_client
    try:
        result = await mantota.get_restaurant_menu(restaurant_id)
    except MantotaNotFoundError:
        return {"error": "Restaurant introuvable"}
    except MantotaError as exc:
        logger.error("restaurant_menu_error", error=str(exc))
        return {"error": exc.message}
    return result.model_dump()


@router.post("/order", response_model=CreateOrderResponse)
async def create_order(
    body: CreateOrderRequest,
    request: Request,
    _auth: None = Depends(verify_gateway_api_key),
) -> CreateOrderResponse:
    """Crée une commande restaurant (panier multi-plats)."""
    mantota: MantotaClient = request.app.state.mantota_client
    try:
        result = await mantota.create_restaurant_order(
            restaurant_id=body.restaurant_id,
            customer_id=body.customer_id,
            order_type=body.order_type,
            items=[item.model_dump() for item in body.items],
            delivery_address=body.delivery_address,
            delivery_latitude=body.delivery_latitude,
            delivery_longitude=body.delivery_longitude,
            notes=body.notes,
        )
    except MantotaError as exc:
        logger.error("restaurant_order_error", error=str(exc))
        return CreateOrderResponse(
            success=False,
            order_id="",
            order_number="",
            error=exc.message,
        )
    return CreateOrderResponse(
        success=result.success,
        order_id=result.order_id,
        order_number=result.order_number,
        subtotal=result.subtotal,
        delivery_fee=result.delivery_fee,
        total=result.total,
        estimated_delivery_at=result.estimated_delivery_at,
        error=result.error,
    )


@router.get("/order/{order_id}", response_model=OrderStatusResponse)
async def get_order_status(
    order_id: str,
    request: Request,
    _auth: None = Depends(verify_gateway_api_key),
) -> OrderStatusResponse:
    """Récupère le statut d'une commande restaurant."""
    mantota: MantotaClient = request.app.state.mantota_client
    try:
        result = await mantota.get_restaurant_order_status(order_id)
    except MantotaNotFoundError:
        return OrderStatusResponse(
            id="",
            order_number="",
            status="not_found",
        )
    except MantotaError as exc:
        logger.error("restaurant_order_status_error", error=str(exc))
        return OrderStatusResponse(
            id="",
            order_number="",
            status="error",
        )
    return OrderStatusResponse(
        id=result.id,
        order_number=result.order_number,
        status=result.status,
        order_type=result.order_type,
        total=result.total,
        estimated_delivery_at=result.estimated_delivery_at,
        delivered_at=result.delivered_at,
        items=result.items,
    )
