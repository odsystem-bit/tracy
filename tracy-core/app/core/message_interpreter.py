"""Pré-processeur de message — extraction d'entités à chaque tour (multi-pays).

Problème résolu : l'extraction quantité/ville/produit existait mais ne tournait
que dans une branche du CommercialAgent. Si le routing envoyait ailleurs ou que
la branche était sautée, les entités se perdaient → Tracy redemandait la ville,
la quantité, promettait le lien sans jamais créer la commande.

Ce module tourne dans l'orchestrateur AVANT le routing, pour tous les messages :
- ville (déclaration "je suis à X" → user_city ; "livrer à X" → pending_city)
- quantité ("un seul", "2 paires", "je veux 3") → pending_quantity
- moyen de paiement (momo/MTN/Moov/Orange/Wave/carte/cash) → pending_payment_method
- produit cité nommément parmi les dernières cards → product_id/name/price
- confirmation courte (oui/non) → last_user_confirmation

Les slots remplis sont persistés dans ConversationContext (mémoire courte),
et un résumé canonique `[État]` est injecté dans l'historique passé aux agents
pour que le LLM voie l'état structuré au lieu de reparser le brut.

Aucune logique métier : on remplit des slots, la décision reste aux agents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.agents.location import extract_city
from app.agents.order_flow import parse_partial_order_details
from app.memory.short_term import ConversationContext

# Moyens de paiement par zone — Afrique de l'Ouest/Centrale + international.
_PAYMENT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(?:momo|mtn\s*(?:money|momo)?|mtn\b)\b", re.IGNORECASE), "MTN MoMo"),
    (re.compile(r"\bmoov\b", re.IGNORECASE), "Moov Money"),
    (re.compile(r"\borange\s*(?:money)?\b|\bom\b", re.IGNORECASE), "Orange Money"),
    (re.compile(r"\bwave\b", re.IGNORECASE), "Wave"),
    (re.compile(r"\bflooz\b", re.IGNORECASE), "Flooz"),
    (re.compile(r"\b(?:carte|visa|master\s*card|mastercard|cb)\b", re.IGNORECASE), "carte bancaire"),
    (re.compile(r"\b(?:cash|esp[èe]ces?|liquide|main\s+en\s+main)\b", re.IGNORECASE), "cash"),
)

_CONFIRM_YES = {"oui", "ok", "ouais", "ouep", "d'accord", "daccord", "go",
                "vas-y", "vas y", "parfait", "super", "volontiers", "c'est bon",
                "c est bon", "je confirme", "confirmé", "yes"}
_CONFIRM_NO = {"non", "no", "nan", "annule", "annuler", "laisse",
               "laisse tomber", "oublie", "pas maintenant", "non merci"}

_ORDER_STATES = ("awaiting_qty_city", "awaiting_confirmation", "awaiting_multi_confirm")

# Numéro de téléphone : 8 à 15 chiffres, séparateurs . - ( ) espace tolérés.
_PHONE_RE = re.compile(r"\+?(?:\d[\s\-.()]*){8,15}")

# Marqueurs rendant la présence d'un numéro évidente dans un texte plus long.
_PHONE_MARKER_RE = re.compile(
    r"num[eé]ro|\bnum\b|t[ée]l(?:[ée]phone)?|whatsapp|\bphone\b|"
    r"appel(?:er|e)?|joindre|rappel|contact",
    re.IGNORECASE,
)


@dataclass
class InterpretedMessage:
    """Entités extraites d'un message client (toutes optionnelles)."""

    declared_city: str | None = None
    """Ville où le client se trouve (« je suis à Calavi »)."""

    delivery_city: str | None = None
    """Ville de livraison pour la commande en cours."""

    quantity: int | None = None
    """Quantité détectée (« un seul », « 2 paires », « je veux 3 »)."""

    payment_method: str | None = None
    """Moyen de paiement cité (« momo », « carte », « wave »…)."""

    confirmation: str | None = None
    """« yes » / « no » pour les réponses courtes."""

    named_product_ids: list[str] = field(default_factory=list)
    """IDs des produits des dernières cards nommés dans le message."""

    phone: str | None = None
    """Numéro de téléphone détecté dans le message (« 0195900616 », « +229 01 95 90 06 16 »)."""


def _extract_payment_method(text: str) -> str | None:
    for pattern, label in _PAYMENT_PATTERNS:
        if pattern.search(text):
            return label
    return None


# Suffixes de gamme souvent omis par le client : « iPhone 12 » = « iPhone 12 Pro ».
_RANGE_SUFFIXES = {"pro", "plus", "max", "ultra", "mini", "lite", "go", "se"}


def _match_named_products(text: str, ctx: ConversationContext) -> list[str]:
    """IDs des cards récentes dont le nom apparaît dans le message.

    « super les mocassins homme » → sélectionne la card « Mocassins homme »
    sans attendre que l'agent reproduise la recherche.
    « iPhone 12 » matche « iPhone 12 Pro » (suffixe de gamme omis).
    """
    if not ctx.last_cards:
        return []
    low = text.lower()
    matched: list[str] = []
    for card in ctx.last_cards:
        name = card.name.lower()
        if name in low:
            matched.append(str(card.id))
            continue
        words = [w for w in name.split() if len(w) > 2]
        if not words:
            continue
        if all(w in low for w in words):
            matched.append(str(card.id))
            continue
        # Suffixes de gamme optionnels : tous les mots non-suffixe suffisent
        core = [w for w in words if w not in _RANGE_SUFFIXES]
        if core and len(core) < len(words) and all(w in low for w in core):
            matched.append(str(card.id))
            continue
        # Correspondance partielle : ≥50% des mots significatifs présents,
        # dont au moins un mot distinctif (≥5 lettres) — « ordinateur »
        # matche « Ordinateur portable HP », « mocassins » matche « Mocassins homme ».
        hits = [w for w in words if w in low]
        if hits and len(hits) * 2 >= len(words) and any(len(h) >= 5 for h in hits):
            matched.append(str(card.id))
    return matched


def _extract_phone(text: str) -> str | None:
    """Extrait un numéro de téléphone du message (8 à 15 chiffres).

    « mon numéro c'est 0195900616 », « +229 01 95 90 06 16 » ou numéro nu.
    Un numéro nu n'est accepté que s'il constitue la majeure partie du message
    — évite de prendre un prix (« je paie 50000000 ») pour un téléphone.
    """
    m = _PHONE_RE.search(text)
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(0))
    if not (8 <= len(digits) <= 15):
        return None
    if _PHONE_MARKER_RE.search(text):
        return digits
    # Numéro nu : les chiffres doivent représenter ≥60% du contenu non-espace
    content_len = len(re.sub(r"\s", "", text))
    if content_len and len(digits) / content_len >= 0.6:
        return digits
    return None


def interpret_message(text: str, ctx: ConversationContext) -> InterpretedMessage:
    """Extrait toutes les entités exploitables d'un message client."""
    result = InterpretedMessage()

    # ── Ville déclarée (« je suis à X ») : localisation réelle du client ──
    result.declared_city = extract_city(text)

    # ── Quantité / ville de livraison : seulement si contexte commande actif ──
    # Évite les faux positifs (« j'ai 2 enfants » en pleine recherche produit).
    order_context = bool(
        ctx.product_id
        or ctx.task_state in _ORDER_STATES
        or ctx.pending_quantity is not None
        or ctx.pending_city is not None
    )
    if order_context:
        partial = parse_partial_order_details(text)
        if partial is not None:
            if partial.quantity:
                result.quantity = partial.quantity
            if partial.city:
                result.delivery_city = partial.city.title()
        # « je suis à Calavi » pendant la collecte = ville de livraison aussi
        if not result.delivery_city and result.declared_city:
            result.delivery_city = result.declared_city

    # ── Moyen de paiement ──
    result.payment_method = _extract_payment_method(text)

    # ── Produit nommé parmi les cards récentes ──
    result.named_product_ids = _match_named_products(text, ctx)

    # ── Confirmation courte ──
    normalized = text.lower().strip().strip(" !.")
    if normalized in _CONFIRM_YES:
        result.confirmation = "yes"
    elif normalized in _CONFIRM_NO:
        result.confirmation = "no"

    # ── Numéro de téléphone ──
    result.phone = _extract_phone(text)

    return result


def apply_to_context(ctx: ConversationContext, extracted: InterpretedMessage) -> None:
    """Remplit les slots du contexte de conversation avec les entités extraites.

    N'écrase jamais une info déjà collectée par None, et ne réinitialise pas
    le flux : le client peut corriger une valeur en la répétant.
    """
    if extracted.declared_city:
        ctx.user_city = extracted.declared_city
    if extracted.delivery_city:
        ctx.pending_city = extracted.delivery_city
    if extracted.quantity:
        ctx.pending_quantity = extracted.quantity
    if extracted.payment_method:
        ctx.pending_payment_method = extracted.payment_method
    # Confirmation = valeur du tour courant uniquement : un vieux « oui »
    # ne doit jamais confirmer une action future par effet de bord.
    ctx.last_user_confirmation = extracted.confirmation

    if extracted.phone:
        ctx.user_phone = extracted.phone
    ctx.last_named_ids = list(extracted.named_product_ids)

    # Produit nommé parmi les cards récentes → devient le produit courant
    if len(extracted.named_product_ids) == 1 and ctx.last_cards:
        wanted = extracted.named_product_ids[0]
        for card in ctx.last_cards:
            if str(card.id) == wanted:
                if ctx.product_id and ctx.product_id != wanted:
                    # Changement de produit pendant la collecte : repartir à zéro
                    ctx.pending_quantity = extracted.quantity
                    ctx.pending_city = extracted.delivery_city
                ctx.product_id = wanted
                ctx.product_name = card.name
                ctx.product_mentioned = card.name
                ctx.product_price = card.raw_price
                ctx.product_store_id = card.store_id
                break


def state_summary(ctx: ConversationContext) -> str:
    """Résumé canonique de l'état de la demande, injecté dans les prompts.

    Une ligne compacte lue par tous les agents — remplace le re-parsing du
    message brut par le LLM (« je suis a calavi jai dit » → ville=Calavi).
    """
    parts: list[str] = []
    if ctx.product_name:
        price = f" ({ctx.product_price:,.0f} FCFA)" if ctx.product_price else ""
        parts.append(f"produit={ctx.product_name}{price}")
    if ctx.pending_quantity:
        parts.append(f"quantité={ctx.pending_quantity}")
    if ctx.pending_city:
        parts.append(f"ville_livraison={ctx.pending_city}")
    elif ctx.user_city:
        parts.append(f"ville_client={ctx.user_city}")
    if ctx.pending_payment_method:
        parts.append(f"paiement={ctx.pending_payment_method}")
    if ctx.order_reference or ctx.order_id:
        parts.append(f"commande={ctx.order_reference or ctx.order_id}")

    if not parts:
        return ""
    return "[État collecté] " + " | ".join(parts)
