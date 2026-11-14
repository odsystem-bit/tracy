"""Score de qualité boutique (Shop Quality Score).

Calcule un score [0..100] par boutique basé sur:
- Conformité des photos (authenticité)
- Feedback clients post-livraison
- Signaux positifs/négatifs accumulés

Conséquences:
- < 60: Alerte vendeur + photos marquées "non vérifiées"
- < 40: Badge "Boutique à risque" affiché aux acheteurs
- < 20: Suspension automatique + review admin
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.logging_config import get_logger

logger = get_logger(__name__)


# ── Enums ─────────────────────────────────────────────────────────────


class QualitySignalType(str, Enum):
    """Types de signaux affectant le score de qualité."""
    # Positifs
    PHOTO_CONFIRMED = "photo_confirmed"           # Client confirme: photo = produit reçu (+1)
    GOOD_RATING = "good_rating"                     # Note ≥ 4/5 (+2)
    REPEAT_CUSTOMER = "repeat_customer"             # Client revient (+3)
    FAST_DELIVERY = "fast_delivery"                 # Livraison < 2j (+2)

    # Négatifs
    PHOTO_PARTIAL = "photo_partial"                # Client: "partiellement conforme" (-2)
    PHOTO_NON_CONFORM = "photo_non_conform"        # Client: "non conforme" (-5)
    WATERMARK_DETECTED = "watermark_detected"       # Watermark sur photo (-10)
    DUPLICATE_PHOTO = "duplicate_photo"             # Même photo, produits différents (-5)
    TOO_PROFESSIONAL = "too_professional"           # Photo de catalogue volée (-5)
    LOW_RESOLUTION = "low_resolution"               # Résolution suspecte (-5)
    UPSCALED_IMAGE = "upscaled_image"               # Photo agrandie (-5)
    BAD_RATING = "bad_rating"                       # Note ≤ 2/5 (-5)
    LATE_DELIVERY = "late_delivery"                 # Livraison > 5j (-3)
    DISPUTE_OPENED = "dispute_opened"               # Litige ouvert (-5)
    DISPUTE_LOST = "dispute_lost"                   # Litige perdu par vendeur (-10)


# ── Schémas ───────────────────────────────────────────────────────────


class QualitySignal(BaseModel):
    """Un signal de qualité (positif ou négatif) enregistré pour une boutique."""
    id: str
    store_id: str
    signal_type: QualitySignalType
    weight: int = Field(description="Impact sur le score (positif ou négatif)")
    description: str = ""
    product_id: str | None = None
    order_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ShopQualityScore(BaseModel):
    """Score de qualité d'une boutique."""
    store_id: str
    score: int = Field(default=100, ge=0, le=100, description="Score [0..100]")
    level: str = Field(description="excellent, good, warning, risk, suspended")
    total_signals: int = 0
    positive_signals: int = 0
    negative_signals: int = 0
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    signals_30d: list[QualitySignal] = Field(default_factory=list)
    recommendation: str = ""
    auto_actions: list[str] = Field(default_factory=list)


# ── Configuration des poids ───────────────────────────────────────────

SIGNAL_WEIGHTS: dict[QualitySignalType, int] = {
    # Positifs
    QualitySignalType.PHOTO_CONFIRMED: 1,
    QualitySignalType.GOOD_RATING: 2,
    QualitySignalType.REPEAT_CUSTOMER: 3,
    QualitySignalType.FAST_DELIVERY: 2,
    # Négatifs
    QualitySignalType.PHOTO_PARTIAL: -2,
    QualitySignalType.PHOTO_NON_CONFORM: -5,
    QualitySignalType.WATERMARK_DETECTED: -10,
    QualitySignalType.DUPLICATE_PHOTO: -5,
    QualitySignalType.TOO_PROFESSIONAL: -5,
    QualitySignalType.LOW_RESOLUTION: -5,
    QualitySignalType.UPSCALED_IMAGE: -5,
    QualitySignalType.BAD_RATING: -5,
    QualitySignalType.LATE_DELIVERY: -3,
    QualitySignalType.DISPUTE_OPENED: -5,
    QualitySignalType.DISPUTE_LOST: -10,
}

# Seuils
LEVEL_EXCELLENT = 80
LEVEL_GOOD = 60
LEVEL_WARNING = 40
LEVEL_RISK = 20
# En dessous de 20 = suspended


# ── Engine ────────────────────────────────────────────────────────────


class ShopQualityEngine:
    """Calcule et gère les scores de qualité des boutiques.

    Le score démarre à 100 et est ajusté par les signaux accumulés.
    Les signaux sont conservés 30 jours (fenêtre glissante).
    """

    def compute_score(
        self,
        store_id: str,
        signals: list[QualitySignal],
    ) -> ShopQualityScore:
        """Calcule le score de qualité d'une boutique à partir de ses signaux.

        Args:
            store_id: ID de la boutique.
            signals: Tous les signaux enregistrés (au moins 30 derniers jours).

        Returns:
            ShopQualityScore avec le score, le niveau et les actions automatiques.
        """
        # Filtrer les signaux des 30 derniers jours
        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() - (30 * 24 * 3600)
        recent_signals = [
            s for s in signals
            if s.created_at.timestamp() > cutoff
        ]

        # Calculer le score
        base_score = 100
        positive_count = 0
        negative_count = 0

        for signal in recent_signals:
            weight = SIGNAL_WEIGHTS.get(signal.signal_type, 0)
            base_score += weight
            if weight > 0:
                positive_count += 1
            elif weight < 0:
                negative_count += 1

        score = max(0, min(100, base_score))

        # Déterminer le niveau
        if score >= LEVEL_EXCELLENT:
            level = "excellent"
        elif score >= LEVEL_GOOD:
            level = "good"
        elif score >= LEVEL_WARNING:
            level = "warning"
        elif score >= LEVEL_RISK:
            level = "risk"
        else:
            level = "suspended"

        # Actions automatiques selon le niveau
        auto_actions: list[str] = []
        recommendation = ""

        if level == "warning":
            auto_actions.append("notify_vendor")
            auto_actions.append("mark_photos_unverified")
            recommendation = (
                "Boutique en alerte. Photos marquées 'non vérifiées' dans l'app. "
                "Le vendeur a été notifié pour améliorer la qualité de ses photos."
            )
        elif level == "risk":
            auto_actions.append("notify_vendor")
            auto_actions.append("display_risk_badge")
            auto_actions.append("limit_visibility")
            recommendation = (
                "Boutique à risque. Badge '⚠ Boutique à risque' affiché aux acheteurs. "
                "Visibilité réduite dans les recherches et catalogues."
            )
        elif level == "suspended":
            auto_actions.append("notify_vendor")
            auto_actions.append("suspend_store")
            auto_actions.append("admin_review_required")
            recommendation = (
                "Boutique suspendue automatiquement. Review admin requise. "
                "Le vendeur doit soumettre de nouvelles photos conformes pour réactivation."
            )
        elif level == "good":
            recommendation = "Boutique de bonne qualité. Quelques signaux d'alerte mineurs."
        else:
            recommendation = "Boutique excellente. Aucune action requise."

        result = ShopQualityScore(
            store_id=store_id,
            score=score,
            level=level,
            total_signals=len(recent_signals),
            positive_signals=positive_count,
            negative_signals=negative_count,
            last_updated=now,
            signals_30d=recent_signals[-20:],  # Garder les 20 derniers pour l'affichage
            recommendation=recommendation,
            auto_actions=auto_actions,
        )

        logger.info(
            "shop_quality_scored",
            store_id=store_id,
            score=score,
            level=level,
            positive=positive_count,
            negative=negative_count,
            actions=auto_actions,
        )

        return result

    def create_signal(
        self,
        store_id: str,
        signal_type: QualitySignalType,
        product_id: str | None = None,
        order_id: str | None = None,
        description: str = "",
    ) -> QualitySignal:
        """Crée un signal de qualité pour une boutique.

        Args:
            store_id: ID de la boutique.
            signal_type: Type de signal (voir QualitySignalType).
            product_id: ID du produit concerné (optionnel).
            order_id: ID de la commande concernée (optionnel).
            description: Description libre du signal.

        Returns:
            QualitySignal créé.
        """
        import uuid

        weight = SIGNAL_WEIGHTS.get(signal_type, 0)

        signal = QualitySignal(
            id=str(uuid.uuid4()),
            store_id=store_id,
            signal_type=signal_type,
            weight=weight,
            description=description,
            product_id=product_id,
            order_id=order_id,
        )

        logger.info(
            "quality_signal_created",
            store_id=store_id,
            signal_type=signal_type.value,
            weight=weight,
            product_id=product_id,
            order_id=order_id,
        )

        return signal


# ── Singleton ─────────────────────────────────────────────────────────

_engine: ShopQualityEngine | None = None


def get_shop_quality_engine() -> ShopQualityEngine:
    """Retourne l'instance unique du moteur de score qualité."""
    global _engine
    if _engine is None:
        _engine = ShopQualityEngine()
    return _engine
