"""Module de vérification d'authenticité des photos produit.

Détecte:
- Watermarks / logos sur les photos (photo volée sur internet)
- Photos dupliquées (même photo utilisée pour plusieurs produits)
- Photos "trop professionnelles" (studio, fond blanc parfait)
- Résolution/taille suspecte (photo agrandie)

100% local, aucun coût API externe.
"""

from __future__ import annotations

import io
import hashlib
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageStat
from pydantic import BaseModel, Field

from app.logging_config import get_logger

logger = get_logger(__name__)


# ── Schémas ───────────────────────────────────────────────────────────


class AuthenticityCheck(BaseModel):
    """Résultat d'un check d'authenticité sur une photo produit."""
    has_watermark: bool = False
    is_duplicate: bool = False
    duplicate_of: str | None = Field(default=None, description="product_id si duplicata détecté")
    is_too_professional: bool = False
    resolution_suspicious: bool = False
    is_upscaled: bool = False
    trust_score: float = Field(default=100.0, description="Score de confiance [0..100], 100 = totalement authentique")
    flags: list[str] = Field(default_factory=list, description="Liste des problèmes détectés")
    recommendation: str = ""


class DuplicateCheck(BaseModel):
    """Résultat de la vérification de duplication."""
    is_duplicate: bool
    duplicate_of: str | None = None
    hash_similarity: float = Field(description="Similarité du hash perceptuel [0..1]")


# ── Engine d'authenticité ─────────────────────────────────────────────


class AuthenticityEngine:
    """Vérifie l'authenticité des photos produit uploadées par les vendeurs.

    Détections:
    1. Watermark: détecte les logos/textes superposés (photo volée)
    2. Duplication: même photo utilisée pour plusieurs produits
    3. Trop professionnel: fond blanc parfait = photo de catalogue volée
    4. Upscaled: photo agrandie (basse résolution d'origine)
    """

    # Seuils
    WATERMARK_EDGE_RATIO = 0.15      # Si > 15% des bords ont du texte/logo
    WHITE_BG_THRESHOLD = 245         # Valeur RGB > 245 = blanc
    WHITE_BG_RATIO = 0.85            # Si > 85% des pixels de fond sont blancs
    MIN_RESOLUTION = 300             # Largeur/hauteur minimum
    UPSCALE_ARTIFACT_THRESHOLD = 0.3 # Ratio d'artefacts de redimensionnement
    DUPLICATE_HASH_THRESHOLD = 0.95  # Similarité de hash pour duplication

    def __init__(self) -> None:
        self._initialized = False

    def _initialize(self) -> None:
        """Initialise les modèles si nécessaire."""
        if self._initialized:
            return
        # Pas de modèle lourd nécessaire ici — analyse pixel-level
        self._initialized = True
        logger.info("authenticity_engine_ready")

    def compute_perceptual_hash(self, image: Image.Image, hash_size: int = 16) -> str:
        """Calcule un hash perceptuel de l'image pour la détection de duplication.

        Plus robuste qu'un hash MD5 car insensible aux légères modifications
        (compression, redimensionnement, légère couleur).
        """
        self._initialize()

        # Convertir en niveaux de gris et redimensionner
        gray = image.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        pixels = list(gray.getdata())

        # Hash moyen: compare chaque pixel à la moyenne
        avg = sum(pixels) / len(pixels)
        bits = "".join("1" if p > avg else "0" for p in pixels)
        return bits

    def _hash_similarity(self, hash1: str, hash2: str) -> float:
        """Calcule la similarité entre deux hashes perceptuels [0..1]."""
        if len(hash1) != len(hash2):
            return 0.0
        matching = sum(1 for a, b in zip(hash1, hash2) if a == b)
        return matching / len(hash1)

    def check_duplicate(
        self,
        image: Image.Image,
        known_hashes: dict[str, str],
    ) -> DuplicateCheck:
        """Vérifie si une image est duplicata d'une image connue.

        Args:
            image: Image à vérifier.
            known_hashes: Dict {product_id: perceptual_hash} des images connues du vendeur.

        Returns:
            DuplicateCheck avec le résultat.
        """
        self._initialize()
        query_hash = self.compute_perceptual_hash(image)

        best_similarity = 0.0
        best_match: str | None = None

        for pid, ref_hash in known_hashes.items():
            sim = self._hash_similarity(query_hash, ref_hash)
            if sim > best_similarity:
                best_similarity = sim
                best_match = pid

        is_dup = best_similarity >= self.DUPLICATE_HASH_THRESHOLD

        if is_dup:
            logger.info("duplicate_detected", duplicate_of=best_match, similarity=best_similarity)

        return DuplicateCheck(
            is_duplicate=is_dup,
            duplicate_of=best_match if is_dup else None,
            hash_similarity=round(best_similarity, 4),
        )

    def check_watermark(self, image: Image.Image) -> bool:
        """Détecte la présence d'un watermark/logo sur l'image.

        Méthode: analyse des bords de l'image pour des patterns semi-transparents
        typiques des watermarks. Utilise la détection de variance dans les coins.
        """
        self._initialize()

        try:
            import cv2

            img_array = np.array(image.convert("RGB"))
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

            h, w = gray.shape
            # Analyser les 4 coins (zones typiques des watermarks)
            corner_size = min(h, w) // 6
            corners = [
                gray[:corner_size, :corner_size],           # Top-left
                gray[:corner_size, -corner_size:],           # Top-right
                gray[-corner_size:, :corner_size],           # Bottom-left
                gray[-corner_size:, -corner_size:],          # Bottom-right
            ]

            # Un watermark a généralement une variance élevée dans les coins
            # (texte/logo semi-transparent), contrairement à une photo normale
            corner_variances = [float(np.std(c)) for c in corners]
            avg_variance = sum(corner_variances) / len(corner_variances)

            # Comparer avec la variance du centre
            center = gray[h//4:3*h//4, w//4:3*w//4]
            center_variance = float(np.std(center))

            # Si les coins ont une variance anormalement élevée vs le centre
            ratio = avg_variance / max(center_variance, 1.0)
            has_wm = ratio > 2.0 and avg_variance > 30

            if has_wm:
                logger.info("watermark_detected", corner_variance=avg_variance, center_variance=center_variance, ratio=ratio)

            return has_wm
        except ImportError:
            # Fallback sans OpenCV: analyse PIL
            return self._check_watermark_pil(image)

    def _check_watermark_pil(self, image: Image.Image) -> bool:
        """Fallback de détection de watermark avec PIL uniquement."""
        self._initialize()
        gray = image.convert("L")
        w, h = gray.size
        corner_size = min(w, h) // 6

        corners = [
            gray.crop((0, 0, corner_size, corner_size)),
            gray.crop((w - corner_size, 0, w, corner_size)),
            gray.crop((0, h - corner_size, corner_size, h)),
            gray.crop((w - corner_size, h - corner_size, w, h)),
        ]

        corner_vars = [float(ImageStat.Stat(c).stddev[0]) for c in corners]
        avg_var = sum(corner_vars) / len(corner_vars)

        center = gray.crop((w // 4, h // 4, 3 * w // 4, 3 * h // 4))
        center_var = float(ImageStat.Stat(center).stddev[0])

        ratio = avg_var / max(center_var, 1.0)
        return ratio > 2.0 and avg_var > 30

    def check_too_professional(self, image: Image.Image) -> bool:
        """Détecte si une photo ressemble à une photo de catalogue professionnelle.

        Indicateurs:
        - Fond majoritairement blanc (> 85% des pixels de bordure)
        - Éclairage uniforme (faible variance dans les bords)
        """
        self._initialize()

        rgb = image.convert("RGB")
        w, h = rgb.size

        # Analyser les bords (zone de fond)
        border_width = min(w, h) // 8
        border_pixels = []

        # Top border
        for x in range(0, w, max(1, w // 100)):
            for y in range(border_width):
                border_pixels.append(rgb.getpixel((x, y)))
        # Bottom border
        for x in range(0, w, max(1, w // 100)):
            for y in range(h - border_width, h):
                border_pixels.append(rgb.getpixel((x, y)))
        # Left border
        for y in range(0, h, max(1, h // 100)):
            for x in range(border_width):
                border_pixels.append(rgb.getpixel((x, y)))
        # Right border
        for y in range(0, h, max(1, h // 100)):
            for x in range(w - border_width, w):
                border_pixels.append(rgb.getpixel((x, y)))

        if not border_pixels:
            return False

        white_count = sum(1 for r, g, b in border_pixels if r > self.WHITE_BG_THRESHOLD and g > self.WHITE_BG_THRESHOLD and b > self.WHITE_BG_THRESHOLD)
        white_ratio = white_count / len(border_pixels)

        is_pro = white_ratio > self.WHITE_BG_RATIO

        if is_pro:
            logger.info("professional_photo_detected", white_ratio=white_ratio)

        return is_pro

    def check_resolution(self, image: Image.Image) -> tuple[bool, bool]:
        """Vérifie la résolution et détecte l'upscale.

        Returns:
            (resolution_suspicious, is_upscaled)
        """
        self._initialize()

        w, h = image.size
        resolution_suspicious = w < self.MIN_RESOLUTION or h < self.MIN_RESOLUTION

        # Détection d'upscale: si l'image a été agrandie, on voit des artefacts
        # (pixels "flous" adjacents identiques)
        is_upscaled = False
        if w >= self.MIN_RESOLUTION and h >= self.MIN_RESOLUTION:
            try:
                import cv2

                img_array = np.array(image.convert("RGB"))
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

                # Compter les blocs de pixels identiques (artefact d'upscale)
                h_arr, w_arr = gray.shape
                # Comparer pixels adjacents horizontaux
                diff_h = np.abs(gray[:, :-1].astype(int) - gray[:, 1:].astype(int))
                identical_h = np.sum(diff_h == 0) / (h_arr * (w_arr - 1))

                # Comparer pixels adjacents verticaux
                diff_v = np.abs(gray[:-1, :].astype(int) - gray[1:, :].astype(int))
                identical_v = np.sum(diff_v == 0) / ((h_arr - 1) * w_arr)

                avg_identical = (identical_h + identical_v) / 2
                is_upscaled = avg_identical > self.UPSCALE_ARTIFACT_THRESHOLD
            except ImportError:
                pass  # Pas de cv2, skip

        if resolution_suspicious or is_upscaled:
            logger.info("resolution_issue", width=w, height=h, suspicious=resolution_suspicious, upscaled=is_upscaled)

        return resolution_suspicious, is_upscaled

    def check_photo(
        self,
        image: Image.Image,
        known_hashes: dict[str, str] | None = None,
        current_product_id: str | None = None,
    ) -> AuthenticityCheck:
        """Effectue tous les checks d'authenticité sur une photo produit.

        Args:
            image: Photo produit à vérifier.
            known_hashes: Hashes perceptuels des autres produits du vendeur.
            current_product_id: ID du produit en cours (exclu de la vérification de duplication).

        Returns:
            AuthenticityCheck avec le score de confiance et les flags.
        """
        self._initialize()

        flags: list[str] = []
        trust_score = 100.0

        # 1. Watermark
        has_wm = self.check_watermark(image)
        if has_wm:
            flags.append("watermark_detected")
            trust_score -= 30

        # 2. Duplication
        is_dup = False
        duplicate_of = None
        if known_hashes:
            # Exclure le produit courant
            filtered_hashes = {
                k: v for k, v in known_hashes.items() if k != current_product_id
            }
            if filtered_hashes:
                dup_result = self.check_duplicate(image, filtered_hashes)
                is_dup = dup_result.is_duplicate
                duplicate_of = dup_result.duplicate_of
                if is_dup:
                    flags.append("duplicate_photo")
                    trust_score -= 25

        # 3. Trop professionnel
        is_pro = self.check_too_professional(image)
        if is_pro:
            flags.append("too_professional")
            trust_score -= 15

        # 4. Résolution / upscale
        res_suspicious, is_upscaled = self.check_resolution(image)
        if res_suspicious:
            flags.append("low_resolution")
            trust_score -= 10
        if is_upscaled:
            flags.append("upscaled_image")
            trust_score -= 15

        trust_score = max(0.0, trust_score)

        # Recommandation
        if trust_score >= 80:
            recommendation = "Photo authentique, aucune action requise."
        elif trust_score >= 60:
            recommendation = "Photo acceptable mais quelques signaux d'alerte. Surveiller."
        elif trust_score >= 40:
            recommendation = "Photo suspecte. Demander au vendeur de remplacer par une vraie photo."
        else:
            recommendation = "Photo très probablement non authentique. Action requise: bloquer ou demander remplacement."

        result = AuthenticityCheck(
            has_watermark=has_wm,
            is_duplicate=is_dup,
            duplicate_of=duplicate_of,
            is_too_professional=is_pro,
            resolution_suspicious=res_suspicious,
            is_upscaled=is_upscaled,
            trust_score=round(trust_score, 1),
            flags=flags,
            recommendation=recommendation,
        )

        logger.info(
            "authenticity_check_complete",
            trust_score=result.trust_score,
            flags=result.flags,
            has_watermark=has_wm,
            is_duplicate=is_dup,
            is_too_professional=is_pro,
        )

        return result


# ── Singleton ─────────────────────────────────────────────────────────

_engine: AuthenticityEngine | None = None


def get_authenticity_engine() -> AuthenticityEngine:
    """Retourne l'instance unique du moteur d'authenticité."""
    global _engine
    if _engine is None:
        _engine = AuthenticityEngine()
    return _engine
