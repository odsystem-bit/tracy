"""Endpoints API pour les modules vision de Tracy Core.

Endpoints:
    POST /vision/identify-product     — Identifie un produit depuis une photo client
    POST /vision/compute-embedding    — Calcule et stocke l'embedding d'un produit
    POST /vision/check-authenticity   — Vérifie l'authenticité d'une photo produit
    POST /vision/check-conformity     — Vérifie la conformité post-livraison
    GET  /vision/shop-quality/{id}    — Récupère le score de qualité d'une boutique
    POST /vision/shop-quality/signal  — Enregistre un signal de qualité
"""

from __future__ import annotations

import base64
import io
from typing import Any

from fastapi import APIRouter, Depends, UploadFile, File, Form
from PIL import Image
from pydantic import BaseModel, Field

from app.gateway.auth import verify_gateway_api_key
from app.logging_config import get_logger
from app.vision import (
    get_product_vision_engine,
    get_authenticity_engine,
    get_conformity_engine,
    get_shop_quality_engine,
    IdentifyResult,
    ProductEmbedding,
    AuthenticityCheck,
    ConformityCheck,
    ConformityVerdict,
    QualitySignal,
    QualitySignalType,
    ShopQualityScore,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/vision", tags=["vision"], dependencies=[Depends(verify_gateway_api_key)])


# ── Schémas de requêtes ───────────────────────────────────────────────


class IdentifyRequest(BaseModel):
    """Requête d'identification produit."""
    image_base64: str = Field(description="Image encodée en base64")
    store_id: str = Field(description="ID de la boutique du vendeur")
    catalog_embeddings: list[ProductEmbedding] = Field(
        default_factory=list,
        description="Embeddings des produits du vendeur (avec augmentations)",
    )


class ComputeEmbeddingRequest(BaseModel):
    """Requête de calcul d'embedding pour un produit."""
    image_base64: str = Field(description="Image encodée en base64")
    product_id: str
    store_id: str
    image_url: str = ""
    augment: bool = Field(default=True, description="Générer aussi les embeddings augmentés")


class ComputeEmbeddingResult(BaseModel):
    """Résultat du calcul d'embedding."""
    product_id: str
    store_id: str
    image_url: str
    embeddings: list[ProductEmbedding] = Field(description="Embedding original + augmentés")
    count: int


class CheckAuthenticityRequest(BaseModel):
    """Requête de vérification d'authenticité."""
    image_base64: str = Field(description="Image encodée en base64")
    product_id: str
    store_id: str
    known_hashes: dict[str, str] = Field(
        default_factory=dict,
        description="Hashes perceptuels des autres produits du vendeur {product_id: hash}",
    )


class CheckConformityRequest(BaseModel):
    """Requête de vérification de conformité post-livraison."""
    order_id: str
    product_id: str
    store_id: str
    verdict: ConformityVerdict
    received_photo_base64: str | None = Field(default=None, description="Photo du produit reçu par le client")
    catalog_photo_base64: str | None = Field(default=None, description="Photo du catalogue")


class QualitySignalRequest(BaseModel):
    """Requête d'enregistrement d'un signal de qualité."""
    store_id: str
    signal_type: QualitySignalType
    product_id: str | None = None
    order_id: str | None = None
    description: str = ""


class ShopQualityRequest(BaseModel):
    """Requête de calcul de score de qualité."""
    store_id: str
    signals: list[QualitySignal] = Field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────


def _decode_base64_image(b64_string: str) -> Image.Image:
    """Décode une string base64 en image PIL."""
    # Supporter les data URLs (data:image/jpeg;base64,...)
    if "," in b64_string and b64_string.startswith("data:"):
        b64_string = b64_string.split(",", 1)[1]
    raw = base64.b64decode(b64_string)
    return Image.open(io.BytesIO(raw))


# ── Endpoints ─────────────────────────────────────────────────────────


@router.post("/identify-product", response_model=IdentifyResult)
async def identify_product(request: IdentifyRequest) -> IdentifyResult:
    """Identifie un produit à partir d'une photo envoyée par un client.

    Pipeline:
        1. YOLOv8 détecte et crop l'objet principal
        2. CLIP génère l'embedding du crop
        3. Comparaison cosinus avec les embeddings du catalogue
        4. Retourne le top 3 avec scores de confiance

    Utilisé quand un client quitte un live TikTok et envoie une capture
    au numéro WhatsApp du vendeur.
    """
    logger.info("identify_product_request", store_id=request.store_id, candidates=len(request.catalog_embeddings))

    image = _decode_base64_image(request.image_base64)
    engine = get_product_vision_engine()
    result = engine.identify_product(image, request.catalog_embeddings)

    logger.info(
        "identify_product_response",
        store_id=request.store_id,
        matched=result.matched,
        needs_confirmation=result.needs_confirmation,
        not_found=result.not_found,
        elapsed_ms=result.processing_time_ms,
    )

    return result


@router.post("/compute-embedding", response_model=ComputeEmbeddingResult)
async def compute_embedding(request: ComputeEmbeddingRequest) -> ComputeEmbeddingResult:
    """Calcule l'embedding CLIP d'un produit (à l'upload).

    Si augment=True, génère aussi les embeddings des variantes augmentées
    (rotation, luminosité, flou, crop, saturation) pour robustifier
    l'identification future.
    """
    logger.info("compute_embedding_request", product_id=request.product_id, augment=request.augment)

    image = _decode_base64_image(request.image_base64)
    engine = get_product_vision_engine()

    embeddings: list[ProductEmbedding] = []

    if request.augment:
        # Embeddings originaux + augmentés
        variants = engine.augment_image(image)
        for i, variant in enumerate(variants):
            emb = engine.compute_embedding(variant)
            embeddings.append(ProductEmbedding(
                product_id=request.product_id,
                store_id=request.store_id,
                embedding=emb,
                image_url=request.image_url,
                augmented=i > 0,
            ))
    else:
        emb = engine.compute_embedding(image)
        embeddings.append(ProductEmbedding(
            product_id=request.product_id,
            store_id=request.store_id,
            embedding=emb,
            image_url=request.image_url,
            augmented=False,
        ))

    logger.info("compute_embedding_done", product_id=request.product_id, count=len(embeddings))

    return ComputeEmbeddingResult(
        product_id=request.product_id,
        store_id=request.store_id,
        image_url=request.image_url,
        embeddings=embeddings,
        count=len(embeddings),
    )


@router.post("/check-authenticity", response_model=AuthenticityCheck)
async def check_authenticity(request: CheckAuthenticityRequest) -> AuthenticityCheck:
    """Vérifie l'authenticité d'une photo produit uploadée par un vendeur.

    Détections:
    - Watermark/logo (photo volée sur internet)
    - Duplication (même photo pour plusieurs produits)
    - Photo trop professionnelle (fond blanc = catalogue volé)
    - Résolution/upscale suspects

    À appeler à chaque upload de photo produit.
    """
    logger.info("check_authenticity_request", product_id=request.product_id, store_id=request.store_id)

    image = _decode_base64_image(request.image_base64)
    engine = get_authenticity_engine()
    result = engine.check_photo(
        image=image,
        known_hashes=request.known_hashes,
        current_product_id=request.product_id,
    )

    logger.info(
        "check_authenticity_done",
        product_id=request.product_id,
        trust_score=result.trust_score,
        flags=result.flags,
    )

    return result


@router.post("/check-conformity", response_model=ConformityCheck)
async def check_conformity(request: CheckConformityRequest) -> ConformityCheck:
    """Vérifie la conformité d'un produit livré vs sa photo catalogue.

    À appeler après la livraison quand Tracy demande au client
    "Le produit correspond à la photo ?" et reçoit la réponse.

    Si le client envoie une photo du produit reçu, Tracy compare
    avec la photo du catalogue via CLIP.
    """
    logger.info("check_conformity_request", order_id=request.order_id, verdict=request.verdict.value)

    received_photo = None
    catalog_photo = None

    if request.received_photo_base64:
        received_photo = _decode_base64_image(request.received_photo_base64)
    if request.catalog_photo_base64:
        catalog_photo = _decode_base64_image(request.catalog_photo_base64)

    engine = get_conformity_engine()
    result = engine.process_client_verdict(
        order_id=request.order_id,
        product_id=request.product_id,
        store_id=request.store_id,
        verdict=request.verdict,
        received_photo=received_photo,
        catalog_photo=catalog_photo,
    )

    logger.info(
        "check_conformity_done",
        order_id=request.order_id,
        verdict=request.verdict.value,
        similarity=result.photo_similarity,
        signal=result.signal_type.value if result.signal_type else None,
        admin_notified=result.admin_notification is not None,
    )

    return result


@router.get("/shop-quality/{store_id}", response_model=ShopQualityScore)
async def get_shop_quality(store_id: str, signals: list[QualitySignal] | None = None) -> ShopQualityScore:
    """Récupère le score de qualité d'une boutique.

    Le score est calculé à partir des signaux des 30 derniers jours.
    Niveaux: excellent (≥80), good (≥60), warning (≥40), risk (≥20), suspended (<20).
    """
    logger.info("get_shop_quality_request", store_id=store_id)

    engine = get_shop_quality_engine()
    result = engine.compute_score(store_id, signals or [])

    return result


@router.post("/shop-quality/signal", response_model=QualitySignal)
async def create_quality_signal(request: QualitySignalRequest) -> QualitySignal:
    """Enregistre un signal de qualité pour une boutique.

    Signaux positifs: photo_confirmed, good_rating, repeat_customer, fast_delivery
    Signaux négatifs: photo_non_conform, watermark_detected, duplicate_photo, etc.
    """
    logger.info("create_signal_request", store_id=request.store_id, signal_type=request.signal_type.value)

    engine = get_shop_quality_engine()
    signal = engine.create_signal(
        store_id=request.store_id,
        signal_type=request.signal_type,
        product_id=request.product_id,
        order_id=request.order_id,
        description=request.description,
    )

    return signal


@router.post("/shop-quality/compute", response_model=ShopQualityScore)
async def compute_shop_quality(request: ShopQualityRequest) -> ShopQualityScore:
    """Calcule le score de qualité d'une boutique à partir de ses signaux.

    Endpoint utilisé par l'admin panel pour visualiser le score et les actions automatiques.
    """
    logger.info("compute_shop_quality_request", store_id=request.store_id, signals_count=len(request.signals))

    engine = get_shop_quality_engine()
    result = engine.compute_score(request.store_id, request.signals)

    return result
