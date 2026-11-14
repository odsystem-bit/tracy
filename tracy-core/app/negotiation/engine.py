"""Moteur de négociation déterministe.

Les PRIX sont décidés ici (jamais par le LLM). Le LLM ne fait que formuler la
décision. Principes d'un vrai vendeur :
- le prix plancher (prix catalogue - max_discount_percent du vendeur) n'est jamais révélé ni franchi ;
- on ne cède pas au premier « dernier prix ? » : on valorise le produit d'abord ;
- les concessions sont progressives, de plus en plus petites, et ne remontent jamais ;
- le « dernier prix » n'est annoncé qu'à la dernière étape, après plusieurs échanges.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

# Part de la remise maximale concédée à chaque relance du client.
# Relance 1 : on tient le prix catalogue (sauf remise auto-acceptée par le vendeur).
CONCESSION_SCHEDULE: tuple[float, ...] = (0.0, 0.40, 0.70, 0.90, 1.0)

Action = Literal["disabled", "hold", "counter", "accept", "final", "too_low"]

_NUMBER_RE = re.compile(r"(\d[\d\s.,]*)\s*(k|mille|000)?\b", re.IGNORECASE)
_LAST_PRICE_RE = re.compile(
    r"dernier\s+prix|prix\s+final|dernier\s+mot|derni[eè]re\s+offre|meilleur\s+prix|"
    r"le\s+moins\s+cher|prix\s+le\s+plus\s+bas|tout\s+dernier|last\s+price",
    re.IGNORECASE,
)

# Part maximale de remise accessible tant que le client n'a pas insisté sur le
# « dernier prix » (le plancher n'est jamais atteint avant).
SOFT_CAP = 0.5
# Nombre de demandes explicites de « dernier prix » avant de l'annoncer.
INSIST_THRESHOLD = 2

_PERCENT_RE = re.compile(r"(\d{1,2}(?:[.,]\d+)?)\s*(?:%|pour\s*cent|pourcent)", re.IGNORECASE)


@dataclass(frozen=True)
class Rules:
    """Règles du vendeur (issues de shop_negotiation_configs)."""

    max_discount_percent: float
    auto_accept_below: float = 0.0
    custom_rules: str | None = None
    free_shipping_threshold: float | None = None


@dataclass(frozen=True)
class Decision:
    action: Action
    price: float
    rounds: int
    is_final: bool = False
    accepted: bool = False


def floor_price(list_price: float, rules: Rules) -> float:
    pct = min(max(rules.max_discount_percent, 0.0), 100.0)
    return round(list_price * (1 - pct / 100), 0)


def asks_last_price(message: str) -> bool:
    """Le client demande explicitement le dernier prix."""
    return bool(_LAST_PRICE_RE.search(message))


def round_price(value: float) -> float:
    """Prix « parlant » : arrondi à 100 FCFA vers le haut (jamais sous le plancher)."""
    return float(-(-value // 100) * 100)


def parse_offer(message: str, list_price: float) -> float | None:
    """Extrait le prix proposé par le client (montant ou pourcentage de remise)."""
    pct = _PERCENT_RE.search(message)
    if pct:
        discount = float(pct.group(1).replace(",", "."))
        if 0 < discount < 100:
            return round(list_price * (1 - discount / 100), 0)

    best: float | None = None
    for m in _NUMBER_RE.finditer(message):
        raw = re.sub(r"[\s.,]", "", m.group(1))
        if not raw.isdigit():
            continue
        value = float(raw)
        suffix = (m.group(2) or "").lower()
        if suffix in ("k", "mille"):
            value *= 1000
        elif suffix == "000" and value < 1000:
            value *= 1000
        # Un montant plausible : au moins 10 % du prix catalogue, pas une quantité
        if value >= list_price * 0.1:
            best = value if best is None else max(best, value)
    return best


def decide(
    list_price: float,
    rules: Rules,
    rounds_so_far: int,
    last_ask: float | None,
    offer: float | None,
    last_price_asks: int = 0,
) -> Decision:
    """Calcule la réponse de Tracy à une relance de prix du client."""
    if list_price <= 0 or rules.max_discount_percent <= 0:
        return Decision("disabled", list_price, rounds_so_far)

    floor = floor_price(list_price, rules)
    rounds = rounds_so_far + 1

    # Remise demandée dans la zone « auto-acceptée » par le vendeur
    if offer is not None and offer >= list_price * (1 - rules.auto_accept_below / 100):
        price = min(offer, list_price)
        return Decision("accept", max(price, floor), rounds, accepted=True)

    insisted = last_price_asks >= INSIST_THRESHOLD
    step = CONCESSION_SCHEDULE[min(rounds - 1, len(CONCESSION_SCHEDULE) - 1)]
    step = 1.0 if insisted else min(step, SOFT_CAP)
    scheduled = round_price(list_price - (list_price - floor) * step)
    ask = max(min(scheduled, last_ask if last_ask is not None else list_price), floor)
    is_final = insisted and ask <= floor

    if offer is not None:
        if offer >= ask:
            return Decision("accept", min(offer, list_price), rounds, accepted=True)
        if offer < floor:
            return Decision("too_low", ask, rounds, is_final=is_final)

    if rounds == 1 and (last_ask is None or ask >= list_price):
        return Decision("hold", ask, rounds)
    if last_ask is not None and ask >= last_ask and not is_final:
        return Decision("hold", ask, rounds)
    if is_final:
        return Decision("final", ask, rounds, is_final=True)
    return Decision("counter", ask, rounds)
