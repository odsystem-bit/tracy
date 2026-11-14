"""Comptes-rendus de Tracy au vendeur (résumés factuels, sans LLM).

Chaque événement n'est envoyé qu'une fois par produit et par conversation.
"""

from __future__ import annotations

import re

from app.logging_config import get_logger
from app.memory.short_term import ConversationContext
from app.negotiation.engine import Decision
from app.tools.base import ToolContext

logger = get_logger(__name__)

CONTACT_VENDOR_RE = re.compile(
    r"(?:parler|discuter|joindre|contacter|appeler|[ée]change\w*)\s+(?:\w+\s+){0,3}?"
    r"(?:au|avec\s+le|le|du|[àa]\s+la|avec\s+la|la)\s+(?:vendeu\w+|propri[ée]taire|g[ée]rant\w*|boutiqu\w+)|"
    r"(?:num[ée]ro|contact|whatsapp)\s+(?:du|de\s+la|de)\s+(?:vendeu\w+|propri[ée]taire|boutiqu\w+)|"
    r"(?:passe|passez)(?:\s+|-)(?:moi\s+)?(?:le|la)\s+(?:vendeu\w+|patron\w*)",
    re.IGNORECASE,
)


def wants_vendor_contact(message: str) -> bool:
    return bool(CONTACT_VENDOR_RE.search(message))


def resolve_vendor_id(store_id: str, conv: ConversationContext | None) -> str | None:
    """Le vendeur est identifié par le store_id (ou le store du produit en chat public)."""
    if store_id and store_id != "public" and store_id.isdigit():
        return store_id
    if conv and conv.product_store_id and str(conv.product_store_id).isdigit():
        return str(conv.product_store_id)
    return None


def negotiation_summary(conv: ConversationContext, decision: Decision) -> tuple[str, str]:
    """Retourne (kind, résumé factuel) pour un événement de négociation."""
    name = conv.product_name or "un produit"
    listed = f"{conv.product_price:.0f} FCFA" if conv.product_price else "prix inconnu"
    if decision.accepted:
        return (
            "sale",
            f"Accord de prix sur {name} : {decision.price:.0f} FCFA (prix affiché {listed}) "
            f"après {decision.rounds} échange(s) de négociation.",
        )
    return (
        "negotiation",
        f"Le client insiste sur le dernier prix de {name} (prix affiché {listed}, "
        f"{conv.negotiation_last_price_asks} demande(s) explicite(s)). "
        f"Tracy a proposé {decision.price:.0f} FCFA, dans vos limites de remise. En attente de sa réponse.",
    )


async def send_vendor_report(
    tool_registry,
    ctx: ToolContext,
    conv: ConversationContext | None,
    store_id: str,
    kind: str,
    summary: str,
    customer_name: str | None = None,
    customer_phone: str | None = None,
    conversation_id: str | None = None,
) -> bool:
    """Envoie un compte-rendu au vendeur (une seule fois par événement). Jamais bloquant."""
    vendor_id = resolve_vendor_id(store_id, conv)
    if vendor_id is None:
        return False
    key = f"{kind}:{conv.product_id if conv else ''}"
    if conv is not None:
        if key in conv.vendor_reports_sent:
            return False
    try:
        result = await tool_registry.execute(
            "send_vendor_report",
            ctx,
            vendor_id=vendor_id,
            kind=kind,
            summary=summary,
            customer_name=customer_name,
            customer_phone=customer_phone,
            product_name=conv.product_name if conv else None,
            conversation_id=conversation_id,
        )
    except Exception as exc:  # noqa: BLE001 — un compte-rendu raté ne doit jamais casser le chat
        logger.warning("vendor_report_failed", error=str(exc))
        return False
    if result.success and conv is not None:
        conv.vendor_reports_sent.append(key)
    return bool(result.success)


async def connect_client_vendor(
    tool_registry,
    ctx: ToolContext,
    conv: ConversationContext | None,
    store_id: str,
    customer_id: str | None,
    conversation_id: str | None,
    summary: str,
) -> str | None:
    """Tente une vraie mise en relation in-app (APK uniquement).

    Sur l'APK, `customer_id` est l'id utilisateur connecté et `conversation_id`
    a la forme "app:{user_id}:{salon}" (préfixe posé par MobileTracyController) —
    Laravel crée alors une Conversation client↔vendeur + un message d'intro de
    Tracy. Sur le web public et WhatsApp (IP ou téléphone), on renvoie None :
    le compte-rendu de notification reste le bon canal. Jamais bloquant.

    Returns:
        L'id de la conversation créée (deep-link APK) ou None.
    """
    vendor_id = resolve_vendor_id(store_id, conv)
    if vendor_id is None:
        return None
    if not (customer_id or "").isdigit():
        return None
    # Le préfixe "app:" distingue un id utilisateur APK d'un numéro WhatsApp.
    if not (conversation_id or "").startswith("app:"):
        return None
    key = f"connect:{conv.product_id if conv else ''}"
    if conv is not None and key in conv.vendor_reports_sent:
        return "connected"  # déjà mis en relation dans cette conversation
    try:
        result = await tool_registry.execute(
            "connect_client_vendor",
            ctx,
            vendor_id=vendor_id,
            client_user_id=str(customer_id),
            summary=summary,
            product_name=conv.product_name if conv else None,
        )
    except Exception as exc:  # noqa: BLE001 — jamais bloquant
        logger.warning("vendor_connect_failed", error=str(exc))
        return None
    if not result.success:
        return None
    if conv is not None:
        conv.vendor_reports_sent.append(key)
    data = result.data if isinstance(result.data, dict) else {}
    return str(data.get("conversation_id") or "connected")


async def schedule_client_followup(
    tool_registry,
    ctx: ToolContext,
    conv: ConversationContext | None,
    store_id: str,
    customer_id: str | None,
    conversation_id: str | None,
    delay_minutes: int | None = None,
) -> bool:
    """Planifie une relance proactive au client après une négociation sans achat.

    Canal déduit du conversation_id : "app:{user}:{salon}" → notification in-app
    (customer_id = id utilisateur), "wa_*" ou numéro → WhatsApp (customer_id = phone).
    Le web public (IP) n'est pas joignable → on ignore. Dédup par produit : une seule
    relance par produit négocié et par conversation. Jamais bloquant.
    """
    vendor_id = resolve_vendor_id(store_id, conv)
    if vendor_id is None or not (customer_id or "").strip():
        return False
    conv_id = conversation_id or ""
    if conv_id.startswith("app:"):
        channel = "app"
        if not str(customer_id).isdigit():
            return False
    elif conv_id.startswith("wa_") or (customer_id or "").lstrip("+").isdigit():
        channel = "whatsapp"
    else:
        return False
    # Délai par canal : in-app 3h ; WhatsApp 6h (la fenêtre de messages libres Meta
    # se ferme à 24h — une relance ~24h exigerait un template approuvé).
    delay_minutes = delay_minutes or (360 if channel == "whatsapp" else 180)
    key = f"followup:{conv.product_id if conv else ''}"
    if conv is not None and key in conv.vendor_reports_sent:
        return True  # relance déjà planifiée dans cette conversation
    name = conv.product_name if conv and conv.product_name else "le produit"
    price = (
        f"{conv.negotiated_price or conv.negotiation_last_ask or conv.product_price:.0f} FCFA"
        if conv and (conv.negotiated_price or conv.negotiation_last_ask or conv.product_price)
        else None
    )
    price_note = f" à {price}" if price else ""
    if channel == "whatsapp":
        message = (
            f"Salut ! C'est encore moi — tu hésitais sur {name}{price_note}. "
            f"Le vendeur peut encore discuter, dis-moi si tu veux qu'on reprenne. "
            f"Au passage, tu peux aussi télécharger l'app Mantota pour discuter "
            f"directement avec lui : https://mantota.com/app"
        )
    else:
        message = (
            f"Toujours intéressé(e) par {name}{price_note} ? "
            f"Le vendeur peut encore discuter le prix — rouvre ta conversation Tracy "
            f"ou contacte-le directement."
        )
    try:
        result = await tool_registry.execute(
            "schedule_follow_up",
            ctx,
            vendor_id=vendor_id,
            customer_id=str(customer_id),
            channel=channel,
            message=message,
            context_key=key,
            send_at_minutes=delay_minutes,
        )
    except Exception as exc:  # noqa: BLE001 — jamais bloquant
        logger.warning("follow_up_schedule_failed", error=str(exc))
        return False
    if result.success and conv is not None:
        conv.vendor_reports_sent.append(key)
    return bool(result.success)
