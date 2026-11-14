"""Tests de la géolocalisation client (ville déclarée, notes de proximité)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.agents.base import AgentInput
from app.agents.location import (
    extract_city,
    location_kwargs,
    location_note,
    sort_by_scope,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("je suis à Cotonou", "Cotonou"),
        ("j'habite à Porto-Novo, tu livres ?", "Porto-Novo"),
        ("je suis a abomey calavi tu livres", "Abomey Calavi"),
        ("je suis a cotonou et je veux des baskets", "Cotonou"),
        ("je suis de retour", None),
        ("je suis en colère", None),
        ("je suis à la maison", None),
        ("je veux des chaussures", None),
    ],
)
def test_extract_city(text: str, expected: str | None) -> None:
    assert extract_city(text) == expected


def _input(**kw) -> AgentInput:
    return AgentInput(message="x", store_id="public", correlation_id="c", **kw)


def _p(scope: str, city: str = "Parakou", delivers: bool | None = None):
    return SimpleNamespace(nom="Basket", prix=1000, stock=3, scope=scope,
                           shop_city=city, distance_km=None, delivers_to_you=delivers)


def test_location_kwargs_includes_city_and_gps() -> None:
    kw = location_kwargs(_input(country_code="BJ", user_city="Cotonou",
                                user_latitude=6.37, user_longitude=2.39))
    assert kw == {"country": "BJ", "city": "Cotonou", "latitude": 6.37, "longitude": 2.39}


def test_note_asks_city_when_unknown() -> None:
    assert "dans quelle ville" in location_note([_p("unknown")], _input())


def test_note_warns_when_nothing_local() -> None:
    note = location_note([_p("country", delivers=False)], _input(user_city="Cotonou"))
    assert "aucun de ces produits" in note
    assert "Parakou" in note


def test_note_prefers_local() -> None:
    note = location_note([_p("local"), _p("other")], _input(user_city="Cotonou"))
    assert "proximité" in note


def test_sort_by_scope_is_local_first() -> None:
    ordered = sort_by_scope([_p("other"), _p("local"), _p("country")])
    assert [p.scope for p in ordered] == ["local", "country", "other"]
