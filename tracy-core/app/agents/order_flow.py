"""Logique partagée du flux de commande (CommercialAgent, OrderAgent, PaymentAgent, SupportAgent).

Source unique de vérité pour :
- l'extraction d'une référence de commande (CMD-XXXX ou order_XXX),
- le parsing quantité + ville dans un message client,
- la création d'une commande depuis le contexte de conversation.

Évite la duplication de logique entre agents (un seul endroit à maintenir).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.agents.base import AgentInput
from app.logging_config import get_logger
from app.memory.short_term import ConversationContext
from app.tools.base import ToolContext
from app.tools.registry import ToolRegistry

logger = get_logger(__name__)

# ── Référence de commande ───────────────────────────────────────────
# Matche : CMD-ABC123, cmd_abc, order_42, ORDER-42
_ORDER_REF_RE = re.compile(r"\b(?:(CMD)[-_]?(\w+)|order[-_](\w+))\b", re.IGNORECASE)

_NUMBER_WORDS = {
    "un": 1, "une": 1, "un seul": 1, "une seule": 1,
    "deux": 2, "trois": 3, "quatre": 4, "cinq": 5,
    "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10,
}


def extract_order_reference(text: str) -> str | None:
    """Extrait une référence de commande d'un message.

    Retourne la référence normalisée (ex: 'CMD-ABC123' ou 'order_42'),
    ou None si aucune référence n'est trouvée.
    """
    match = _ORDER_REF_RE.search(text)
    if not match:
        return None
    if match.group(1):  # forme CMD-XXXX
        return f"CMD-{match.group(2).upper()}"
    return f"order_{match.group(3)}"


@dataclass
class QuantityCity:
    """Quantité et ville extraites d'un message client."""

    quantity: int
    city: str


def parse_quantity_city(text: str) -> QuantityCity | None:
    """Détecte quantité + ville dans un message.

    Exemples reconnus : "1 cotonou", "je veux 2 a dakar", "un seul a cotonou",
    "je veux 1 je suis a cotonou", "3 sacs pour lagos".
    Retourne None si le message ne contient pas les deux informations.
    """
    qty_city_match = re.search(
        r"(?:je\s+veux\s+|je\s+veut\s+|je\s+prends\s+|je\s+souhaite\s+|donne\s+moi\s+|envoie\s+moi\s+)?"
        r"(?:(\d+)\s*(?:sacs?|pieces?|unit[ée]s?|exemplaires?|articles?)?|"
        r"(un|une|deux|trois|quatre|cinq|un\s+seul|une\s+seule))\s+"
        r"(?:s(?:ur)?\s+|a\s+|à\s+|pour\s+|livr[ée]\s+(?:a\s+|à\s+)?)?"
        r"([a-zA-Zéèêàâîïôûùç\s]{3,30})",
        text,
        re.IGNORECASE,
    )
    city_only_match = re.search(
        r"(?:je\s+suis\s+(?:a\s+|à\s+|au\s+|en\s+)?|j['\s]?habite\s+(?:a\s+|à\s+|au\s+|en\s+)?|livr[ée]e?r?\s+(?:a\s+|à\s+))"
        r"([a-zA-Zéèêàâîïôûùç\s]{3,30})",
        text,
        re.IGNORECASE,
    )
    qty_match = re.search(r"\b(\d+)\b", text)

    quantity: int | None = None
    city = ""

    if qty_city_match:
        qty_str = (qty_city_match.group(1) or qty_city_match.group(2) or "1").lower()
        quantity = _NUMBER_WORDS.get(qty_str)
        if quantity is None:
            try:
                quantity = int(qty_str)
            except ValueError:
                quantity = 1
        city = (qty_city_match.group(3) or "").strip()
    elif city_only_match and qty_match:
        quantity = int(qty_match.group(1))
        city = city_only_match.group(1).strip()

    if quantity is None or quantity > 9999:
        # quantity > 9999 = probablement un prix ("a 300000") pas une quantité
        return None

    city = _clean_city(city)
    # Extraire la vraie ville connue du fragment s'il y en a une
    _known = _CITY_RE.search(city)
    if _known:
        city = _known.group(1)
    if not city or not _is_plausible_city(city):
        return None

    return QuantityCity(quantity=quantity, city=city)


# Petits mots qui ne peuvent pas faire partie d'un nom de ville
_SMALL_WORDS = {
    "de", "le", "la", "du", "des", "les", "a", "à", "au", "aux", "en", "sur",
    "pour", "me", "moi", "te", "toi", "se", "ce", "cet", "cette", "mon", "ma",
    "mes", "ton", "ta", "tes", "son", "sa", "ses", "je", "tu", "il", "elle",
    "on", "nous", "vous", "est", "et", "ou", "ne", "pas", "que", "qui", "avec",
    "dans", "comme", "par", "sans", "sous", "chez", "vers", "entre", "un",
    "une", "y", "dont", "si", "car", "ni", "mais", "donc", "or",
}


def _is_plausible_city(city: str) -> bool:
    """Vérifie qu'un fragment ressemble à une ville.

    Règle : ville connue, ou 1-2 mots dont aucun n'est un mot parasite
    (stopword, préposition, pronom). Rejette "possible de le prendre a",
    "seul", "pro" tout en acceptant "cotonou", "grand-popo", "allada".
    """
    low = (city or "").strip().lower()
    if not low:
        return False
    if _CITY_RE.search(low):
        return True
    words = [w for w in re.split(r"[\s'\-]+", low) if w]
    if not words or len(words) > 2:
        return False
    if any(w in _CITY_STOPWORDS or w in _SMALL_WORDS for w in words):
        return False
    return True


# Mots qui ressemblent à une ville capturée mais n'en sont pas :
# quantité ("un seul"), fragments de nom de produit ("pro", "max", "iphone"),
# restes de locutions ("c'est possible" → "possible"), adverbes et fillers.
_CITY_STOPWORDS = {
    "seul", "seule", "seulement", "exemplaire", "exemplaires",
    "piece", "pieces", "pièce", "pièces", "unite", "unites", "unité", "unités",
    "article", "articles", "sac", "sacs", "pro", "max", "plus", "mini",
    "modele", "modèle", "version", "generation", "génération",
    "iphone", "samsung", "tecno", "infinix", "xiaomi", "redmi", "huawei",
    "nokia", "oppo", "vivo", "realme", "honor", "ipad",
    "telephone", "téléphone", "portable", "ordinateur", "laptop", "tablette",
    "produit", "produits", "commande", "livraison", "ville", "merci", "stp", "svp",
    "basket", "baskets", "chaussure", "chaussures", "sandale", "sandales",
    "chemise", "chemises", "robe", "robes", "montre", "montres", "canape", "canapé",
    # Locutions / adverbes / fillers français fréquemment capturés
    "possible", "vrai", "vraie", "vraiment", "bien", "juste", "maintenant",
    "alors", "aussi", "tres", "très", "trop", "meme", "même", "encore",
    "beaucoup", "certain", "certaine", "autre", "autres", "toujours",
    "jamais", "parfois", "souvent", "assez", "plutot", "plutôt",
    "ensemble", "rapidement", "vite", "demain", "ici", "la", "là",
    "premier", "premiere", "première", "dernier", "derniere", "dernière",
    "meme chose", "total", "totale", "complet", "complete", "complète",
    "gratuit", "gratuite", "disponible", "urgent", "urgente", "direct",
    "directe", "directement", "exactement", "vrais", "bon", "bonne",
    "meilleur", "meilleure", "pire", "grand", "grande", "petit", "petite",
    "necessaire", "nécessaire", "obligatoire", "important", "importante",
    "simple", "facile", "difficile", "normal", "normale", "special", "speciale",
    "spécial", "spéciale", "pareil", "pareille", "tout", "toute", "tous",
    "rien", "personne", "quelque", "chose", "truc", "affaire", "faire",
    "prendre", "avoir", "donner", "voir", "venir", "aller", "payer",
    "livrer", "commander", "acheter", "vendre", "envoyer", "recevoir",
    # "je suis prêt" / "je suis chez moi" ≠ ville
    "pres", "prêt", "pret", "prete", "prête", "prets", "prêts", "maison",
    "chez", "moi", "boulot", "taf", "travail", "bureau", "marché", "marche",
    "moto", "voiture", "taxi", "zem", "zémidjan", "zemidjan", "keke", "kéké",
    # Unités de quantité : "je veux une paire" → paire ≠ ville
    "paire", "paires", "exemplaire", "exemplaires", "unité", "unite", "unites",
    "unités", "pièce", "piece", "pièces", "pieces", "modèle", "modele", "modeles",
    "modèles", "article", "articles", "carton", "cartons", "lot", "lots",
    "boîte", "boite", "boîtes", "boites", "sac", "sacs", "colis",
    "kilo", "kilos", "litre", "litres", "mètre", "metre", "mètres", "douzaine",
    # Questions de prix & verbes fréquemment capturés en fin de message :
    # « les deux feront combien » → « feront combien » ≠ ville
    "combien", "fera", "ferait", "feront", "font", "fait", "fais",
    "coûte", "coute", "coûtera", "coutera", "coûtent", "coutent", "vaut",
    "valoir", "total", "pourquoi", "comment", "quand", "quel", "quelle",
    "quels", "quelles", "prend", "prends", "donne", "donne moi", "ca", "ça",
    "sera", "seront", "reste", "reste il", "tout", "deux", "trois",
}


def _clean_city(frag: str) -> str:
    """Nettoie un fragment de ville : retire pronoms, prépositions et ponctuation.

    'a cotonou' → 'cotonou', 'je suis a cotonou' → 'cotonou'.
    """
    frag = frag.strip().rstrip(".,;!?")
    frag = re.sub(
        r"^(?:je\s+suis|j['\s]?habite|je\s+me\s+trouve|je\s+vis|c['e]st|cest)\s+",
        "", frag, flags=re.IGNORECASE,
    )
    frag = re.sub(r"^(?:a|à|au|aux|en|dans|de|sur)\s+", "", frag, flags=re.IGNORECASE)
    return frag.strip()


# ── Extraction partielle (quantité OU ville dans un message seul) ──
_QTY_PATTERNS = (
    # "2 exemplaires", "3 sacs", "1 piece"
    re.compile(r"\b(\d{1,2})\s*(?:exemplaires?|pièces?|pieces?|unit[ée]s?|sacs?|articles?)\b", re.IGNORECASE),
    # "un seul", "une seule", "juste un", "seulement une", "qu'un seul"
    re.compile(r"\b(?:un|une)\s+seule?\b|\bjuste\s+(?:un|une)\b|\bseulement\s+(?:un|une)\b|\bqu['\s]+une?\s+seule?\b", re.IGNORECASE),
    # "je veux deux", "j'en veux 3", "je prends un"
    re.compile(
        r"\b(?:je\s+(?:veux|veut|prends|commande|souhaite)|j['\s]+en\s+veux)\s+"
        r"(un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|\d{1,2})\b",
        re.IGNORECASE,
    ),
    # Réponse courte : "deux", "3"
    re.compile(r"^\s*(un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|\d{1,2})\s*$", re.IGNORECASE),
)

# Villes connues d'Afrique de l'Ouest/Centrale — permet de capter "cotonou" seul
_KNOWN_CITIES = {
    "cotonou", "porto-novo", "porto novo", "parakou", "abomey", "abomey-calavi",
    "calavi", "abomey calavi", "djougou", "natitingou", "bohicon", "ouidah", "lokossa", "kandi",
    "malanville", "godomey", "allada", "savalou", "savè", "save",
    "dakar", "thiès", "thies", "saint-louis", "kaolack", "ziguinchor", "touba",
    "rufisque", "mbour", "tambacounda",
    "abidjan", "yamoussoukro", "bouaké", "bouake", "san-pedro", "san pedro",
    "korhogo", "daloa", "man", "gagnoa", "divo",
    "lomé", "lome", "kara", "sokodé", "sokode", "kpalimé", "kpalime",
    "atakpamé", "atakpame", "dapaong",
    "ouagadougou", "ouaga", "bobo-dioulasso", "bobo", "koudougou", "banfora",
    "niamey", "zinder", "maradi", "agadez", "tahoua", "dosso",
    "bamako", "sikasso", "kayes", "mopti", "ségou", "segou", "gao", "tombouctou",
    "accra", "kumasi", "tamale", "takoradi",
    "lagos", "abuja", "kano", "ibadan",
    "douala", "yaoundé", "yaounde", "bafoussam", "garoua", "bamenda",
    "conakry", "kankan", "bissau", "monrovia", "freetown", "nouakchott",
    "libreville", "brazzaville", "pointe-noire", "kinshasa", "lubumbashi",
    "bangui", "ndjamena", "n'djamena", "kigali", "nairobi", "mombasa", "kampala",
}

_CITY_RE = re.compile(
    r"\b(" + "|".join(sorted((re.escape(c) for c in _KNOWN_CITIES), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

_CITY_PATTERNS = (
    # "je suis a cotonou", "j'habite à dakar", "je me trouve a abidjan"
    re.compile(
        r"\b(?:je\s+suis|j['\s]?habite|je\s+me\s+trouve|je\s+vis)\s+(?:a|à|au|aux|en|dans)?\s*"
        r"([a-zA-Zéèêàâîïôûùç'\- ]{2,30})",
        re.IGNORECASE,
    ),
    # "livrer a cotonou", "livré à parakou"
    re.compile(
        r"\blivr[ée]e?r?\s+(?:a|à|au|aux|en)\s+([a-zA-Zéèêàâîïôûùç'\- ]{2,30})",
        re.IGNORECASE,
    ),
    # Message entier = "a cotonou" / "à dakar"
    re.compile(r"^\s*(?:a|à)\s+([a-zA-Zéèêàâîïôûùç'\- ]{2,30})\s*$", re.IGNORECASE),
)


def parse_partial_order_details(text: str) -> QuantityCity | None:
    """Extrait la quantité ET/OU la ville d'un message (chacun optionnel).

    Complète parse_quantity_city qui exige les deux dans le même message.
    Retourne QuantityCity avec quantity=0 et/ou city="" quand un seul des
    deux est présent ; None si rien n'est détecté.
    """
    quantity: int | None = None
    city = ""

    # Quantité seule
    for rx in _QTY_PATTERNS:
        m = rx.search(text)
        if not m:
            continue
        if m.lastindex and m.group(1) and m.group(1).isdigit():
            quantity = int(m.group(1))
        elif m.lastindex and m.group(1):
            quantity = _NUMBER_WORDS.get(m.group(1).lower())
        else:
            # motif sans groupe capturant ("un seul", "juste un"…)
            quantity = 1
        if quantity:
            break

    # Ville : motif prépositionnel puis ville connue isolée
    for rx in _CITY_PATTERNS:
        m = rx.search(text)
        if m:
            frag = _clean_city(m.group(1))
            known = _CITY_RE.search(frag)
            if known:
                city = known.group(1).strip()
            elif _is_plausible_city(frag):
                city = frag.strip()
            if city:
                break
    if not city:
        known = _CITY_RE.search(text)
        if known:
            city = known.group(1).strip()

    if quantity and quantity > 9999:
        # Prix capturé par erreur ("j'ai 300 000") — pas une quantité
        quantity = None

    if not quantity and not city:
        return None
    return QuantityCity(quantity=quantity or 0, city=city)


@dataclass
class OrderCreationResult:
    """Résultat de la création d'une commande depuis le contexte."""

    order_id: str | None
    reference: str | None
    payment_url: str | None
    tracking_url: str | None
    amount: float | None
    quantity: int
    city: str


async def create_order_from_context(
    tool_registry: ToolRegistry,
    ctx: ToolContext,
    conv_ctx: ConversationContext,
    input_data: AgentInput,
    quantity: int,
    city: str,
) -> OrderCreationResult | None:
    """Crée une commande via le tool create_order depuis le contexte de conversation.

    Retourne un OrderCreationResult si la création réussit, None sinon.
    L'appelant est responsable de formuler la réponse au client.
    """
    if not conv_ctx.product_id:
        return None
    price_kwargs: dict[str, float] = {}
    if (
        conv_ctx.negotiated_price is not None
        and conv_ctx.negotiation_product_id == conv_ctx.product_id
    ):
        price_kwargs["agreed_price"] = conv_ctx.negotiated_price
    try:
        order_result = await tool_registry.execute(
            "create_order",
            ctx,
            vendor_id=conv_ctx.product_store_id or input_data.store_id,
            product_id=conv_ctx.product_id,
            customer_name=input_data.customer_id or "Client Web",
            customer_phone=conv_ctx.user_phone or "N/A",
            customer_whatsapp=conv_ctx.user_phone or "N/A",
            country=input_data.country_code or "BJ",
            city=city,
            **price_kwargs,
        )
    except Exception as exc:  # noqa: BLE001 — la création ne doit jamais faire crasher l'agent
        logger.warning(
            "order_creation_failed",
            error=str(exc),
            correlation_id=input_data.correlation_id,
        )
        return None

    if not (order_result.success and order_result.data):
        logger.warning(
            "order_creation_failed",
            error=order_result.error.message if order_result.error else "unknown",
            correlation_id=input_data.correlation_id,
        )
        return None

    order = order_result.data
    amount = getattr(order, "amount", None)
    if amount is None and conv_ctx.product_price:
        amount = conv_ctx.product_price * quantity

    return OrderCreationResult(
        order_id=str(getattr(order, "order_id", None) or getattr(order, "id", "") or "") or None,
        reference=getattr(order, "reference", None),
        payment_url=getattr(order, "payment_url", None),
        tracking_url=getattr(order, "tracking_url", None),
        amount=amount,
        quantity=quantity,
        city=city,
    )


def apply_order_to_context(conv_ctx: ConversationContext, result: OrderCreationResult) -> None:
    """Enregistre la commande créée dans le contexte de conversation."""
    conv_ctx.order_id = result.order_id
    conv_ctx.order_reference = result.reference
    conv_ctx.order_payment_url = result.payment_url
    conv_ctx.order_tracking_url = result.tracking_url
    conv_ctx.pending_quantity = None
    conv_ctx.pending_city = None
    conv_ctx.pending_payment_method = None
    conv_ctx.current_task = "order"
    conv_ctx.task_state = "order_created"
    conv_ctx.last_tool_result = f"create_order: {result.reference or result.order_id}"
