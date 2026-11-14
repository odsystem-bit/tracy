"""Module de vision produit pour Tracy Core.

Identifie un produit à partir d'une photo envoyée par un client (ex: screenshot de live TikTok).
Utilise CLIP pour les embeddings + YOLOv8 pour la détection d'objet (crop du produit).

Flow:
    1. Image client reçue
    2. YOLOv8 détecte l'objet principal → crop
    3. CLIP génère l'embedding du crop
    4. Comparaison cosinus avec les embeddings des produits du vendeur
    5. Retourne le top 3 avec scores de confiance

100% local, aucun coût API externe.
"""

from __future__ import annotations

import io
import base64
from typing import Any

import numpy as np
from PIL import Image
from pydantic import BaseModel, Field

from app.logging_config import get_logger

logger = get_logger(__name__)


# ── Schémas Pydantic ──────────────────────────────────────────────────


class ProductMatch(BaseModel):
    """Un produit identifié avec son score de confiance."""
    product_id: str
    product_name: str
    price: float
    image_url: str | None = None
    confidence: float = Field(description="Score de similarité cosinus [0..1]")
    store_id: str


class IdentifyResult(BaseModel):
    """Résultat de l'identification produit."""
    matched: bool = Field(description="True si au moins un produit dépasse le seuil de confirmation")
    needs_confirmation: bool = Field(description="True si le meilleur match est entre seuil_confirmation et seuil_match")
    not_found: bool = Field(description="True si aucun produit ne dépasse le seuil minimum")
    top_matches: list[ProductMatch] = Field(default_factory=list)
    message: str = ""
    processing_time_ms: float = 0.0


class ProductEmbedding(BaseModel):
    """Embedding CLIP d'un produit, stocké en DB."""
    product_id: str
    store_id: str
    embedding: list[float]
    image_url: str
    augmented: bool = Field(default=False, description="True si généré par augmentation de données")


# ── Seuils de confiance ───────────────────────────────────────────────

CONFIDENCE_MATCH = 0.75       # Match direct, Tracy propose sans demander confirmation
CONFIDENCE_ASK = 0.50         # Match probable, Tracy demande "C'est bien celui-ci ?"
CONFIDENCE_MIN = 0.30         # En dessous: produit non trouvé


# ── Engine de vision produit ──────────────────────────────────────────


class ProductVisionEngine:
    """Moteur de vision produit: CLIP + YOLOv8 pour l'identification.

    Les modèles sont chargés en lazy (au premier appel) pour ne pas ralentir le démarrage.
    """

    def __init__(self) -> None:
        self._clip_model: Any = None
        self._clip_processor: Any = None
        self._yolo_model: Any = None
        self._device: str = "cpu"
        self._initialized = False

    def _initialize(self) -> None:
        """Charge les modèles CLIP et YOLOv8 (lazy loading)."""
        if self._initialized:
            return

        logger.info("product_vision_loading_models")

        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info("product_vision_device", device=self._device)

            self._clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self._clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self._clip_model.to(self._device)
            self._clip_model.eval()

            logger.info("clip_model_loaded")
        except Exception as e:
            logger.error("clip_load_failed", error=str(e))
            raise

        try:
            from ultralytics import YOLO

            self._yolo_model = YOLO("yolov8n.pt")
            logger.info("yolo_model_loaded")
        except Exception as e:
            logger.warning("yolo_load_failed", error=str(e), fallback="clip_only")
            self._yolo_model = None

        self._initialized = True
        logger.info("product_vision_ready")

    def _detect_and_crop(self, image: Image.Image) -> Image.Image:
        """Détecte l'objet principal avec YOLOv8 et crop l'image.

        Si YOLO n'est pas disponible ou ne détecte rien, retourne l'image originale.
        """
        if self._yolo_model is None:
            return image

        try:
            import numpy as np

            img_array = np.array(image.convert("RGB"))
            results = self._yolo_model(img_array, verbose=False)

            if not results or len(results) == 0:
                return image

            boxes = results[0].boxes
            if boxes is None or len(boxes) == 0:
                return image

            # Prendre la plus grande boîte (l'objet le plus visible)
            areas = (boxes.xyxy[:, 2] - boxes.xyxy[:, 0]) * (boxes.xyxy[:, 3] - boxes.xyxy[:, 1])
            largest_idx = int(areas.argmax().item())
            x1, y1, x2, y2 = boxes.xyxy[largest_idx].tolist()

            # Ajouter un padding de 10%
            w, h = x2 - x1, y2 - y1
            pad_w, pad_h = w * 0.1, h * 0.1
            x1 = max(0, int(x1 - pad_w))
            y1 = max(0, int(y1 - pad_h))
            x2 = min(image.width, int(x2 + pad_w))
            y2 = min(image.height, int(y2 + pad_h))

            cropped = image.crop((x1, y1, x2, y2))
            logger.info("product_vision_cropped", box=[x1, y1, x2, y2])
            return cropped
        except Exception as e:
            logger.warning("yolo_detection_failed", error=str(e))
            return image

    def compute_embedding(self, image: Image.Image) -> list[float]:
        """Calcule l'embedding CLIP d'une image.

        Args:
            image: Image PIL à encoder.

        Returns:
            Vecteur de dimension 512 (CLIP ViT-B/32).
        """
        import torch

        self._initialize()

        with torch.no_grad():
            inputs = self._clip_processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            features = self._clip_model.get_image_features(**inputs)
            features = features / features.norm(dim=-1, keepdim=True)

        return features.cpu().numpy().flatten().tolist()

    def compute_embedding_from_bytes(self, image_bytes: bytes) -> list[float]:
        """Calcule l'embedding CLIP à partir de bytes d'image."""
        image = Image.open(io.BytesIO(image_bytes))
        return self.compute_embedding(image)

    def compute_embedding_from_base64(self, b64_string: str) -> list[float]:
        """Calcule l'embedding CLIP à partir d'une string base64."""
        raw = base64.b64decode(b64_string)
        return self.compute_embedding_from_bytes(raw)

    def augment_image(self, image: Image.Image) -> list[Image.Image]:
        """Génère des variantes augmentées d'une image pour robustifier la comparaison.

        Variantes générées:
        - Rotation ±15°
        - Luminosité ±30%
        - Flou léger
        - Crop central (zoom 1.2x)
        - Saturation ±20%
        """
        from PIL import ImageFilter, ImageEnhance, ImageOps
        import random

        variants = [image]  # Original toujours inclus

        # Rotation
        for angle in [-15, 15]:
            rotated = image.convert("RGBA").rotate(angle, expand=False, fillcolor=(0, 0, 0, 0))
            # Crée un fond blanc
            bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
            bg.paste(rotated, mask=rotated)
            variants.append(bg.convert("RGB"))

        # Luminosité
        for factor in [0.7, 1.3]:
            enhancer = ImageEnhance.Brightness(image)
            variants.append(enhancer.enhance(factor))

        # Flou léger
        variants.append(image.filter(ImageFilter.GaussianBlur(radius=1.5)))

        # Crop central (zoom)
        w, h = image.size
        crop_w, crop_h = int(w * 0.8), int(h * 0.8)
        left = (w - crop_w) // 2
        top = (h - crop_h) // 2
        zoomed = image.crop((left, top, left + crop_w, top + crop_h))
        variants.append(zoomed.resize((w, h)))

        # Saturation
        for factor in [0.8, 1.2]:
            enhancer = ImageEnhance.Color(image)
            variants.append(enhancer.enhance(factor))

        return variants

    def compute_augmented_embeddings(self, image: Image.Image) -> list[list[float]]:
        """Calcule les embeddings de l'image + ses variantes augmentées.

        Returns:
            Liste d'embeddings (original + variantes).
        """
        variants = self.augment_image(image)
        return [self.compute_embedding(v) for v in variants]

    def identify_product(
        self,
        query_image: Image.Image,
        catalog_embeddings: list[ProductEmbedding],
    ) -> IdentifyResult:
        """Identifie le produit dans l'image du client parmi le catalogue du vendeur.

        Pipeline:
            1. YOLOv8 crop l'objet principal
            2. CLIP génère l'embedding du crop
            3. Comparaison cosinus avec tous les embeddings du catalogue
            4. Retourne le top 3 avec scores

        Args:
            query_image: Image envoyée par le client (PIL Image).
            catalog_embeddings: Embeddings des produits du vendeur (avec augmentations).

        Returns:
            IdentifyResult avec les matches et le statut.
        """
        import time
        import torch

        start = time.time()
        self._initialize()

        # 1. Crop avec YOLO
        cropped = self._detect_and_crop(query_image)

        # 2. Embedding CLIP de l'image query
        with torch.no_grad():
            inputs = self._clip_processor(images=cropped, return_tensors="pt")
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            query_features = self._clip_model.get_image_features(**inputs)
            query_features = query_features / query_features.norm(dim=-1, keepdim=True)
            query_vec = query_features.cpu().numpy().flatten()

        # 3. Comparaison cosinus avec le catalogue
        # On groupe les embeddings par product_id (un produit peut avoir plusieurs embeddings: original + augmentés)
        product_scores: dict[str, list[float]] = {}
        product_info: dict[str, ProductEmbedding] = {}

        for pe in catalog_embeddings:
            ref_vec = np.array(pe.embedding)
            similarity = float(np.dot(query_vec, ref_vec))
            product_scores.setdefault(pe.product_id, []).append(similarity)
            if pe.product_id not in product_info or not pe.augmented:
                product_info[pe.product_id] = pe

        # Score final = max des similarités (best match parmi les variantes)
        scored: list[tuple[str, float, ProductEmbedding]] = []
        for pid, scores in product_scores.items():
            best_score = max(scores)
            scored.append((pid, best_score, product_info[pid]))

        scored.sort(key=lambda x: x[1], reverse=True)

        elapsed_ms = (time.time() - start) * 1000

        # 4. Construire le résultat
        top_matches: list[ProductMatch] = []
        for pid, score, pe in scored[:3]:
            top_matches.append(ProductMatch(
                product_id=pid,
                product_name=pe.image_url,  # Sera remplacé par le vrai nom via Mantota
                price=0.0,  # Sera rempli via Mantota
                image_url=pe.image_url,
                confidence=round(score, 4),
                store_id=pe.store_id,
            ))

        best_score = top_matches[0].confidence if top_matches else 0.0

        if best_score >= CONFIDENCE_MATCH:
            result = IdentifyResult(
                matched=True,
                needs_confirmation=False,
                not_found=False,
                top_matches=top_matches,
                message=f"Produit identifié avec {best_score:.0%} de confiance",
                processing_time_ms=round(elapsed_ms, 1),
            )
        elif best_score >= CONFIDENCE_ASK:
            result = IdentifyResult(
                matched=False,
                needs_confirmation=True,
                not_found=False,
                top_matches=top_matches,
                message=f"Produit probablement identifié ({best_score:.0%}), confirmation requise",
                processing_time_ms=round(elapsed_ms, 1),
            )
        elif best_score >= CONFIDENCE_MIN:
            result = IdentifyResult(
                matched=False,
                needs_confirmation=True,
                not_found=False,
                top_matches=top_matches,
                message=f"Correspondance faible ({best_score:.0%}), demande de clarification",
                processing_time_ms=round(elapsed_ms, 1),
            )
        else:
            result = IdentifyResult(
                matched=False,
                needs_confirmation=False,
                not_found=True,
                top_matches=top_matches,
                message="Produit non trouvé dans le catalogue",
                processing_time_ms=round(elapsed_ms, 1),
            )

        logger.info(
            "product_identified",
            best_score=best_score,
            matched=result.matched,
            needs_confirmation=result.needs_confirmation,
            not_found=result.not_found,
            candidates=len(catalog_embeddings),
            elapsed_ms=round(elapsed_ms, 1),
        )

        return result


# ── Singleton ─────────────────────────────────────────────────────────

_engine: ProductVisionEngine | None = None


def get_product_vision_engine() -> ProductVisionEngine:
    """Retourne l'instance unique du moteur de vision produit."""
    global _engine
    if _engine is None:
        _engine = ProductVisionEngine()
    return _engine
