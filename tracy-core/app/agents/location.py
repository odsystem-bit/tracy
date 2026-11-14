"""Aide de géolocalisation pour les agents (proximité client / vendeur).

Aucune logique d'accès réseau : Mantota classe déjà les produits
(`scope` = local | country | other | unknown). Ce module ne fait que
transformer ce classement en consignes honnêtes pour le LLM.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from app.agents.base import AgentInput
from app.agents.order_flow import _CITY_RE, _is_plausible_city

_CITY_DECLARATION_RE = re.compile(
    r"(?:je\s+suis|j[' ]?habite|je\s+vis|je\s+r[ée]side|je\s+me\s+trouve|on\s+est|nous\s+sommes)"
    r"\s+(?:actuellement\s+)?(?:[àa]|au|dans|sur)\s+"
    r"([a-zà-ÿ][a-zà-ÿ'-]*(?:[ ][a-zà-ÿ][a-zà-ÿ'-]*){0,2})",
    re.IGNORECASE,
)

_SPAN_BREAKERS = frozenset({
    "et", "ou", "pour", "avec", "mais", "si", "tu", "je", "vous", "il", "on",
    "donc", "car", "que", "qui", "alors", "svp", "stp", "merci", "depuis",
})

_SCOPE_RANK = {"local": 0, "country": 1, "other": 2, "unknown": 3, None: 3}


def extract_city(message: str) -> str | None:
    """Ville déclarée par le client (« je suis à Cotonou »), validée comme plausible."""
    m = _CITY_DECLARATION_RE.search(message.strip())
    if not m:
        return None
    words: list[str] = []
    for w in m.group(1).strip(" -'").split():
        if w.lower() in _SPAN_BREAKERS:
            break
        words.append(w)
    for n in range(min(len(words), 2), 0, -1):
        candidate = " ".join(words[:n])
        if _is_plausible_city(candidate.lower()):
            # Ville connue dans le fragment ? (« calavi jai » → « calavi »)
            known = _CITY_RE.search(candidate.lower())
            return (known.group(0) if known else candidate).title()
    return None


_CITY_AFTER_PREP_RE = re.compile(
    r"(?:\b[àa]|\bau|\bvers|\bdans)\s+"
    r"([a-zà-ÿ][a-zà-ÿ'-]*(?:[ ][a-zà-ÿ][a-zà-ÿ'-]*){0,2})",
    re.IGNORECASE,
)


def extract_city_after_preposition(message: str) -> str | None:
    """Ville après une préposition (« tu livres à Parakou ? »), validée comme plausible."""
    for m in _CITY_AFTER_PREP_RE.finditer(message.strip()):
        words: list[str] = []
        for w in m.group(1).strip(" -'").split():
            if w.lower() in _SPAN_BREAKERS:
                break
            words.append(w)
        for n in range(min(len(words), 2), 0, -1):
            candidate = " ".join(words[:n])
            if _is_plausible_city(candidate.lower()):
                return candidate.title()
    return None


def sort_by_scope(products: list[Any]) -> list[Any]:
    """Tri stable : proximité d'abord (local > pays > ailleurs),
    puis produits en rupture de stock relégués en fin de liste."""
    def _key(p: Any) -> tuple[int, int]:
        out_of_stock = 1 if getattr(p, "stock", 1) <= 0 else 0
        return (_SCOPE_RANK.get(getattr(p, "scope", None), 3), out_of_stock)

    return sorted(products, key=_key)


def location_kwargs(input_data: AgentInput) -> dict[str, Any]:
    """Paramètres de localisation à passer à l'outil `search_products`."""
    kwargs: dict[str, Any] = {}
    if input_data.country_code:
        kwargs["country"] = input_data.country_code
    if input_data.user_city:
        kwargs["city"] = input_data.user_city
    if input_data.user_latitude is not None and input_data.user_longitude is not None:
        kwargs["latitude"] = input_data.user_latitude
        kwargs["longitude"] = input_data.user_longitude
    return kwargs


def product_line(p: Any) -> str:
    """Ligne produit pour le prompt, avec la zone du vendeur si connue."""
    stock_txt = "RUPTURE DE STOCK, ne pas proposer à l'achat" if p.stock <= 0 else f"stock: {p.stock}"
    line = f"- {p.nom} : {p.prix:.0f} FCFA ({stock_txt})"
    extras: list[str] = []
    shop_city = getattr(p, "shop_city", None)
    if shop_city:
        extras.append(f"boutique : {str(shop_city)[:40]}")
    distance = getattr(p, "distance_km", None)
    if distance is not None:
        extras.append(f"{distance:g} km")
    delivers = getattr(p, "delivers_to_you", None)
    if delivers is True:
        extras.append("livre chez le client")
    elif delivers is False:
        extras.append("ne livre PAS chez le client (retrait sur place)")
    elif getattr(p, "scope", None) in ("country", "other"):
        extras.append("livraison non confirmée, à vérifier avec le vendeur")
    return f"{line} [{' ; '.join(extras)}]" if extras else line


def location_note(products: Sequence[Any], input_data: AgentInput) -> str:
    """Consigne de localisation à injecter dans le prompt de présentation."""
    city = input_data.user_city
    has_gps = input_data.user_latitude is not None and input_data.user_longitude is not None

    if not city and not has_gps:
        return (
            "Localisation du client inconnue : après avoir présenté les produits, "
            "demande-lui dans quelle ville il se trouve pour vérifier la livraison. "
        )

    where = city or "chez le client"
    local = [p for p in products if getattr(p, "scope", None) == "local"]
    others = [p for p in products if getattr(p, "scope", None) in ("country", "other")]

    if products and not local and others:
        zones = sorted({str(p.shop_city)[:30] for p in others if getattr(p, "shop_city", None)})
        zone_txt = f" (boutiques : {', '.join(zones[:3])})" if zones else ""
        return (
            f"IMPORTANT : aucun de ces produits n'est disponible près de {where}. "
            f"Ils viennent d'une autre zone{zone_txt}. Dis-le clairement dès le début, "
            "indique pour chacun s'il livre chez le client (voir crochets), "
            "puis propose-les comme alternative. N'affirme jamais qu'ils sont proches. "
            "N'invente jamais de modalité (retrait sur place, livraison) absente des crochets. "
        )
    if local and others:
        return (
            f"Certains produits sont près de {where}, d'autres dans une autre zone. "
            "Présente d'abord ceux de proximité et précise que les autres viennent d'ailleurs. "
        )
    if local:
        return f"Ces produits sont disponibles près de {where} : tu peux le mentionner. "
    return ""
