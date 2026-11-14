"""Vérification de conformité post-livraison.

Après la livraison d'une commande, Tracy demande au client si le produit
correspond à la photo. Si non, Tracy demande une photo du produit reçu
et compare avec la photo du catalogue (CLIP).

Flow:
    1. Commande livrée → Tracy envoie: "Le produit correspond à la photo ?"
    2. Client répond: Oui / Partiellement / Non
    3. Si Non/Partiellement → Tracy demande une photo du produit reçu
    4. Comparaison CLIP: photo catalogue vs photo reçue
    5. Génération de signaux de qualité (ShopQualityEngine)
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from PIL import Image
from pydantic import BaseModel, Field

from app.logging_config import get_logger
from app.vision.product_vision import get_product_vision_engine
from app.vision.shop_quality import (
    QualitySignalType,
    get_shop_quality_engine,
)

logger = get_logger(__name__)


# ── Enums ─────────────────────────────────────────────────────────────


class ConformityVerdict(str, Enum):
    """Verdict de conformité donné par le client."""
    CONFORM = "conform"            # Le produit correspond à la photo
    PARTIAL = "partial"            # Partiellement conforme
    NON_CONFORM = "non_conform"    # Non conforme


# ── Schémas ───────────────────────────────────────────────────────────


class ConformityCheck(BaseModel):
    """Résultat de la vérification de conformité post-livraison."""
    order_id: str
    product_id: str
    store_id: str
    client_verdict: ConformityVerdict
    photo_similarity: float | None = Field(default=None, description="Similarité CLIP [0..1] si photo reçue")
    photo_checked: bool = False
    signal_generated: bool = False
    signal_type: QualitySignalType | None = None
    message_to_client: str = ""
    message_to_vendor: str = ""
    admin_notification: str | None = None


# ── Seuils de similarité ──────────────────────────────────────────────

CONFORMITY_HIGH = 0.70    # Photo reçue très similaire au catalogue
CONFORMITY_MEDIUM = 0.50  # Similarité moyenne
# En dessous = non conforme


# ── Engine de conformité ──────────────────────────────────────────────


class ConformityEngine:
    """Vérifie la conformité des produits livrés vs photos catalogue."""

    def process_client_verdict(
        self,
        order_id: str,
        product_id: str,
        store_id: str,
        verdict: ConformityVerdict,
        received_photo: Image.Image | None = None,
        catalog_photo: Image.Image | None = None,
    ) -> ConformityCheck:
        """Traite le verdict du client et génère les signaux appropriés.

        Args:
            order_id: ID de la commande.
            product_id: ID du produit.
            store_id: ID de la boutique.
            verdict: Verdict du client (conform / partial / non_conform).
            received_photo: Photo du produit reçu (si client en a envoyé une).
            catalog_photo: Photo du catalogue (pour comparaison).

        Returns:
            ConformityCheck avec les messages et signaux générés.
        """
        quality_engine = get_shop_quality_engine()
        photo_similarity = None
        photo_checked = False
        signal_type: QualitySignalType | None = None
        message_to_client = ""
        message_to_vendor = ""
        admin_notification = None

        if verdict == ConformityVerdict.CONFORM:
            # Client confirme: produit conforme
            signal_type = QualitySignalType.PHOTO_CONFIRMED
            message_to_client = "Merci pour votre confirmation ! Nous espérons vous revoir bientôt sur MANTOTA."
            message_to_vendor = f"Bonne nouvelle : votre client a confirmé que le produit de la commande {order_id} correspond à la photo. +1 point qualité boutique."

        elif verdict == ConformityVerdict.PARTIAL:
            signal_type = QualitySignalType.PHOTO_PARTIAL

            # Si photo reçue, comparer avec le catalogue
            if received_photo and catalog_photo:
                photo_similarity = self._compare_photos(received_photo, catalog_photo)
                photo_checked = True

                if photo_similarity < CONFORMITY_MEDIUM:
                    # La photo reçue est très différente du catalogue
                    message_to_client = "Merci pour la photo. Nous constatons une différence avec la photo du catalogue. Nous avons informé le vendeur et notre équipe qualité."
                    message_to_vendor = f"Attention : le client de la commande {order_id} a signalé que le produit reçu ne correspond pas à la photo du catalogue (similarité: {photo_similarity:.0%}). Veuillez vérifier et mettre à jour vos photos. -2 points qualité boutique."
                    admin_notification = f"Conformité partielle: commande {order_id}, boutique {store_id}, similarité {photo_similarity:.0%}"
                else:
                    message_to_client = "Merci pour la photo. Le produit semble globalement conforme avec quelques différences mineures. Nous avons noté votre retour."
                    message_to_vendor = f"Le client de la commande {order_id} a noté une conformité partielle ({photo_similarity:.0%} de similarité avec la photo catalogue). Pensez à mettre à jour vos photos pour plus de précision."
            else:
                message_to_client = "Merci pour votre retour. Pourriez-vous envoyer une photo du produit reçu pour que nous puissions vérifier ?"
                message_to_vendor = f"Le client de la commande {order_id} a signalé une conformité partielle. -2 points qualité boutique."

        elif verdict == ConformityVerdict.NON_CONFORM:
            signal_type = QualitySignalType.PHOTO_NON_CONFORM

            if received_photo and catalog_photo:
                photo_similarity = self._compare_photos(received_photo, catalog_photo)
                photo_checked = True

                message_to_client = "Merci pour la photo. Nous confirmons que le produit reçu ne correspond pas à la photo du catalogue. Nous avons ouvert une investigation et notifié le vendeur."
                message_to_vendor = f"ALERTE : le client de la commande {order_id} a signalé que le produit reçu ne correspond PAS à la photo du catalogue (similarité: {photo_similarity:.0%}). -5 points qualité boutique. Veuillez corriger vos photos immédiatement."
                admin_notification = f"NON CONFORMITÉ: commande {order_id}, boutique {store_id}, similarité {photo_similarity:.0%}. Action requise."
            else:
                message_to_client = "Nous sommes désolés pour ce problème. Pourriez-vous envoyer une photo du produit reçu ? Cela nous aidera à traiter votre réclamation rapidement."
                message_to_vendor = f"ALERTE : le client de la commande {order_id} a signalé que le produit ne correspond pas à la photo. -5 points qualité boutique. En attente de photo du client pour investigation."

        # Générer le signal de qualité
        signal = quality_engine.create_signal(
            store_id=store_id,
            signal_type=signal_type,
            product_id=product_id,
            order_id=order_id,
            description=f"Verdict client: {verdict.value}, similarity: {photo_similarity}",
        )

        result = ConformityCheck(
            order_id=order_id,
            product_id=product_id,
            store_id=store_id,
            client_verdict=verdict,
            photo_similarity=round(photo_similarity, 4) if photo_similarity else None,
            photo_checked=photo_checked,
            signal_generated=True,
            signal_type=signal_type,
            message_to_client=message_to_client,
            message_to_vendor=message_to_vendor,
            admin_notification=admin_notification,
        )

        logger.info(
            "conformity_checked",
            order_id=order_id,
            verdict=verdict.value,
            similarity=photo_similarity,
            signal=signal_type.value if signal_type else None,
            admin_notified=admin_notification is not None,
        )

        return result

    def _compare_photos(self, photo1: Image.Image, photo2: Image.Image) -> float:
        """Compare deux photos avec CLIP et retourne la similarité cosinus [0..1].

        Args:
            photo1: Première photo (ex: photo catalogue).
            photo2: Deuxième photo (ex: photo reçue par le client).

        Returns:
            Score de similarité [0..1].
        """
        import numpy as np

        vision_engine = get_product_vision_engine()
        emb1 = np.array(vision_engine.compute_embedding(photo1))
        emb2 = np.array(vision_engine.compute_embedding(photo2))

        similarity = float(np.dot(emb1, emb2))
        return max(0.0, min(1.0, similarity))


# ── Singleton ─────────────────────────────────────────────────────────

_engine: ConformityEngine | None = None


def get_conformity_engine() -> ConformityEngine:
    """Retourne l'instance unique du moteur de conformité."""
    global _engine
    if _engine is None:
        _engine = ConformityEngine()
    return _engine
