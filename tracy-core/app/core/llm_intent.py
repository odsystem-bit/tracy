"""Classifieur d'intention par LLM — repli pour les messages que les regex n'ont pas compris.

Principe (sans surcoût pour les cas courants) :
- Les regex restent le chemin rapide (0 ms, 0 appel LLM).
- Le LLM n'est sollicité que si le résultat est "unknown", et seulement si
  le réglage `llm_intent_fallback` est activé.
- Toute erreur ou réponse invalide => None : l'orchestrateur garde son routage actuel.
"""

from __future__ import annotations

import json
import re

from app.ai_gateway.base import AIGateway, ChatMessage
from app.core.schemas import IntentClassification
from app.logging_config import get_logger

logger = get_logger(__name__)

INTENT_TO_AGENT: dict[str, str] = {
    "product_search": "CommercialAgent",
    "store_search": "CommercialAgent",
    "negotiation": "NegotiationAgent",
    "catalog_management": "CatalogAgent",
    "store_creation": "CatalogAgent",
    "shop_config": "CatalogAgent",
    "order": "OrderAgent",
    "payment": "PaymentAgent",
    "support": "SupportAgent",
    "campaign": "CampaignAgent",
    "memory": "MemoryAgent",
    "restaurant": "RestaurantAgent",
    "delivery": "LogisticsAgent",
    "app_download": "CommercialAgent",
    "vendor_onboarding": "CommercialAgent",
    "vendor_stats": "VendorCopilot",
}

MIN_CONFIDENCE = 0.6

_PROMPT = (
    "Tu classes le message d'un client ou vendeur d'une marketplace africaine (Mantota) "
    "dans UNE intention. Intentions possibles : "
    + ", ".join(INTENT_TO_AGENT)
    + ", unknown.\n"
    "- delivery : question de couverture/zone/frais de livraison\n"
    "- order : commander, suivre ou annuler une commande\n"
    "- support : problème, plainte, litige, parler à un humain\n"
    "- unknown : salutation, hors sujet, ou tu n'es pas sûr\n"
    'Réponds UNIQUEMENT par un JSON : {"intent": "...", "confidence": 0.0-1.0}. '
    "Le message peut contenir des fautes ou du français familier."
)

_JSON_RE = re.compile(r"\{.*?\}", re.DOTALL)


async def classify_with_llm(
    gateway: AIGateway,
    message: str,
    last_intent: str | None = None,
) -> IntentClassification | None:
    """Retourne une classification fiable, ou None (=> garder le routage par défaut)."""
    context_hint = f"\nIntention précédente de la conversation : {last_intent}" if last_intent else ""
    try:
        response = await gateway.complete(
            [
                ChatMessage(role="system", content=_PROMPT),
                ChatMessage(role="user", content=f"Message : {message[:300]}{context_hint}"),
            ],
            temperature=0.0,
            max_tokens=40,
        )
        match = _JSON_RE.search(response.content)
        if not match:
            return None
        data = json.loads(match.group(0))
        intent = str(data.get("intent", "")).strip()
        confidence = float(data.get("confidence", 0.0))
    except Exception as exc:  # noqa: BLE001 — le repli LLM ne doit jamais casser le routage
        logger.warning("llm_intent_failed", error=str(exc)[:120])
        return None

    if intent not in INTENT_TO_AGENT or not 0.0 <= confidence <= 1.0 or confidence < MIN_CONFIDENCE:
        return None

    return IntentClassification(
        intent=intent,  # type: ignore[arg-type]
        confidence=confidence,
        selected_agent=INTENT_TO_AGENT[intent],
        reason="LLM fallback (regex = unknown)",
    )
