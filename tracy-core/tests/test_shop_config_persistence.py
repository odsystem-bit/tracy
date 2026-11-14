"""Tests CatalogAgent — persistance des règles commerciales (shop_config).

Couvre :
  1. CatalogAgent appelle update_shop_config quand le vendeur donne une règle claire.
  2. CatalogAgent NE l'appelle PAS quand l'information est incomplète (clarification).
  3. Message de confirmation seulement après succès réel du tool.
  4. Message d'échec clair si update_shop_config échoue.
  5. Valeurs incohérentes → avertissement, pas d'appel à update_shop_config.
  6. Plusieurs règles dans un seul message → un seul appel avec toutes les valeurs.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from app.agents.base import AgentInput
from app.agents.catalog_agent import CatalogAgent
from app.ai_gateway.base import AIGateway, ChatMessage, ChatResponse
from app.mantota_client.client import MantotaClient
from app.mantota_client.schemas import ShopConfig
from app.tools.base import ToolContext
from app.tools.registry import ToolRegistry
from app.tools.get_shop_config import GetShopConfigTool
from app.tools.update_shop_config import UpdateShopConfigTool

from tests.conftest import MANTOTA_BASE_URL, mock_store_config_response


class ScriptedAIGateway(AIGateway):
    """AI Gateway de test qui retourne des réponses scriptées.

    - Si le system prompt contient "extracteur", retourne la réponse d'extraction.
    - Sinon, retourne une réponse conversationnelle générique.
    """

    def __init__(self, extraction_response: str = '{"extracted": false}',
                 conversational_response: str = "OK, c'est enregistré.") -> None:
        self._extraction_response = extraction_response
        self._conversational_response = conversational_response
        self._call_count = 0
        self._last_messages: list[ChatMessage] = []

    async def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        self._call_count += 1
        self._last_messages = messages

        system_msg = next((m for m in messages if m.role == "system"), None)
        if system_msg and "extracteur" in system_msg.content.lower():
            return ChatResponse(
                content=self._extraction_response,
                provider="fake",
                model="test-model",
            )

        return ChatResponse(
            content=self._conversational_response,
            provider="fake",
            model="test-model",
        )

    @property
    def call_count(self) -> int:
        return self._call_count


def _make_shop_config(store_id: str = "store_1") -> ShopConfig:
    return ShopConfig(
        store_id=store_id,
        min_margin_percent=10.0,
        first_order_discount_percent=0.0,
        max_discount_percent=15.0,
        free_shipping_threshold=None,
        auto_accept_below=5.0,
        custom_rules=None,
        currency="XOF",
    )


@pytest.fixture
def scripted_catalog_agent(request) -> CatalogAgent:
    """CatalogAgent avec une AI Gateway scriptée.

    Usage : marker param "extraction" pour la réponse d'extraction LLM,
    "conversational" pour la réponse conversationnelle.
    """
    extraction = getattr(request, "param", {}).get("extraction", '{"extracted": false}')
    conversational = getattr(request, "param", {}).get(
        "conversational", "OK, c'est enregistré."
    )

    gateway = ScriptedAIGateway(
        extraction_response=extraction,
        conversational_response=conversational,
    )

    mantota = MantotaClient(
        base_url=MANTOTA_BASE_URL,
        api_key="test-bot-key",
        retry_max=1,
        retry_backoff=0.01,
    )

    registry = ToolRegistry()
    registry.register(GetShopConfigTool(mantota))
    registry.register(UpdateShopConfigTool(mantota))

    return CatalogAgent(ai_gateway=gateway, tool_registry=registry)


# ── Test 1 : règle claire → update_shop_config appelé ────────────


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("scripted_catalog_agent", [
    {"extraction": '{"max_discount_percent": 5.0}', "conversational": "C'est enregistré !"},
], indirect=True)
async def test_shop_config_clear_rule_calls_update(scripted_catalog_agent: CatalogAgent):
    """Le vendeur donne 'ne négocie jamais plus de 5%' → update_shop_config appelé."""
    # get_shop_config mock
    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    # update_shop_config mock
    update_route = respx.post(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "store_id": "store_1",
            "message": "Configuration mise à jour",
        })
    )

    result = await scripted_catalog_agent.handle(
        AgentInput(
            message="Ne négocie jamais plus de 5%",
            store_id="store_1",
            correlation_id="test-clear-rule",
        ),
    )

    assert result.handled is True
    assert "update_shop_config" in result.tools_used
    assert update_route.called


# ── Test 2 : information incomplète → pas d'update, clarification ─


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("scripted_catalog_agent", [
    {"extraction": '{"extracted": false}', "conversational": "Combien de réduction tu veux ?"},
], indirect=True)
async def test_shop_config_incomplete_no_update(scripted_catalog_agent: CatalogAgent):
    """Le vendeur dit 'fais une remise' sans préciser → pas d'update, clarification."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    update_route = respx.post(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json={"success": True, "store_id": "store_1"})
    )

    result = await scripted_catalog_agent.handle(
        AgentInput(
            message="Fais une remise pour les nouveaux clients",
            store_id="store_1",
            correlation_id="test-incomplete",
        ),
    )

    assert result.handled is True
    assert "update_shop_config" not in result.tools_used
    assert not update_route.called


# ── Test 3 : confirmation seulement après succès réel ─────────────


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("scripted_catalog_agent", [
    {"extraction": '{"max_discount_percent": 5.0}', "conversational": "C'est enregistré ! La réduction max est maintenant 5%."},
], indirect=True)
async def test_shop_config_confirmation_after_success(scripted_catalog_agent: CatalogAgent):
    """Le message de confirmation ne contient 'enregistré' que si l'API a réussi."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "store_id": "store_1",
            "message": "Configuration mise à jour",
        })
    )

    result = await scripted_catalog_agent.handle(
        AgentInput(
            message="Ne négocie jamais plus de 5%",
            store_id="store_1",
            correlation_id="test-confirm-success",
        ),
    )

    assert result.handled is True
    assert "enregistré" in result.reply.lower() or "enregistr" in result.reply.lower()


# ── Test 4 : échec API → message d'échec clair ───────────────────


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("scripted_catalog_agent", [
    {"extraction": '{"max_discount_percent": 5.0}', "conversational": "Je n'ai pas pu enregistrer, réessaie."},
], indirect=True)
async def test_shop_config_failure_message(scripted_catalog_agent: CatalogAgent):
    """Si update_shop_config échoue, Tracy dit que ça n'a pas marché."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    respx.post(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(500, json={"error": "Internal Server Error"})
    )

    result = await scripted_catalog_agent.handle(
        AgentInput(
            message="Ne négocie jamais plus de 5%",
            store_id="store_1",
            correlation_id="test-failure",
        ),
    )

    assert result.handled is True
    assert "update_shop_config" in result.tools_used
    # Le message ne doit pas confirmer un succès
    assert "enregistré" not in result.reply.lower() or "n'ai pas pu enregistrer" in result.reply.lower()


# ── Test 5 : valeurs incohérentes → avertissement, pas d'update ──


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("scripted_catalog_agent", [
    {
        "extraction": '{"min_margin_percent": 60.0, "max_discount_percent": 50.0}',
        "conversational": "Attention, marge 60% + réduction 50% = 110%, tu vendrais à perte.",
    },
], indirect=True)
async def test_shop_config_incoherent_values_no_update(scripted_catalog_agent: CatalogAgent):
    """min_margin=60% + max_discount=50% > 100% → avertissement, pas d'update."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    update_route = respx.post(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json={"success": True, "store_id": "store_1"})
    )

    result = await scripted_catalog_agent.handle(
        AgentInput(
            message="Marge minimum 60% et réduction max 50%",
            store_id="store_1",
            correlation_id="test-incoherent",
        ),
    )

    assert result.handled is True
    assert "update_shop_config" not in result.tools_used
    assert not update_route.called


# ── Test 6 : plusieurs règles en un message → un seul appel ───────


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("scripted_catalog_agent", [
    {
        "extraction": '{"min_margin_percent": 10.0, "max_discount_percent": 15.0, "free_shipping_threshold": 20000.0}',
        "conversational": "Tout est enregistré !",
    },
], indirect=True)
async def test_shop_config_multiple_rules_single_call(scripted_catalog_agent: CatalogAgent):
    """Le vendeur donne 3 règles → un seul appel à update_shop_config avec toutes."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response())
    )
    update_route = respx.post(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "store_id": "store_1",
            "message": "Configuration mise à jour",
        })
    )

    result = await scripted_catalog_agent.handle(
        AgentInput(
            message="Marge min 10%, remise max 15%, livraison gratuite au-dessus de 20000 FCFA",
            store_id="store_1",
            correlation_id="test-multi-rules",
        ),
    )

    assert result.handled is True
    assert "update_shop_config" in result.tools_used
    assert update_route.called
    assert update_route.call_count == 1

    # Vérifie que toutes les valeurs sont dans le payload envoyé
    sent_json = json.loads(update_route.calls[0].request.content)
    assert sent_json["min_margin_percent"] == 10.0
    assert sent_json["max_discount_percent"] == 15.0
    assert sent_json["free_shipping_threshold"] == 20000.0


# ── Test 7 : auto_accept_below > max_discount → incohérent ────────


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("scripted_catalog_agent", [
    {
        "extraction": '{"auto_accept_below": 20.0}',
        "conversational": "L'auto-acceptation ne peut pas dépasser la réduction max.",
    },
], indirect=True)
async def test_shop_config_auto_accept_above_max_discount(scripted_catalog_agent: CatalogAgent):
    """auto_accept_below=20% mais max_discount actuel=15% → incohérent, pas d'update."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json=mock_store_config_response(
            max_discount_percent=15.0,
        ))
    )
    update_route = respx.post(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json={"success": True, "store_id": "store_1"})
    )

    result = await scripted_catalog_agent.handle(
        AgentInput(
            message="Auto-accepte jusqu'à 20%",
            store_id="store_1",
            correlation_id="test-auto-accept",
        ),
    )

    assert result.handled is True
    assert "update_shop_config" not in result.tools_used
    assert not update_route.called


# ── Test 8 : _parse_extraction_response unit tests ────────────────


def test_parse_extraction_response_valid():
    """Parse un JSON valide avec des paramètres."""
    result = CatalogAgent._parse_extraction_response(
        '{"max_discount_percent": 5.0, "min_margin_percent": 10.0}'
    )
    assert result is not None
    assert result["max_discount_percent"] == 5.0
    assert result["min_margin_percent"] == 10.0


def test_parse_extraction_response_extracted_false():
    """Retourne None si le LLM dit extracted: false."""
    result = CatalogAgent._parse_extraction_response('{"extracted": false}')
    assert result is None


def test_parse_extraction_response_no_json():
    """Retourne None si pas de JSON dans la réponse."""
    result = CatalogAgent._parse_extraction_response("Je ne peux pas extraire de paramètres.")
    assert result is None


def test_parse_extraction_response_with_surrounding_text():
    """Extrait le JSON même s'il est entouré de texte."""
    result = CatalogAgent._parse_extraction_response(
        'Voici le résultat : {"max_discount_percent": 5.0} voilà.'
    )
    assert result is not None
    assert result["max_discount_percent"] == 5.0


def test_parse_extraction_response_filters_invalid_keys():
    """Filtre les clés qui ne sont pas des paramètres valides."""
    result = CatalogAgent._parse_extraction_response(
        '{"max_discount_percent": 5.0, "unknown_param": "test"}'
    )
    assert result is not None
    assert "max_discount_percent" in result
    assert "unknown_param" not in result


# ── Test 9 : _validate_config_coherence unit tests ───────────────


def test_validate_coherence_ok():
    """Combinaison cohérente → ok=True."""
    result = CatalogAgent._validate_config_coherence({
        "min_margin_percent": 10.0,
        "max_discount_percent": 15.0,
    })
    assert result["ok"] is True


def test_validate_coherence_margin_plus_discount_over_100():
    """min_margin + max_discount > 100 → incohérent."""
    result = CatalogAgent._validate_config_coherence({
        "min_margin_percent": 60.0,
        "max_discount_percent": 50.0,
    })
    assert result["ok"] is False
    assert "100%" in result["reason"]


def test_validate_coherence_auto_accept_above_max():
    """auto_accept_below > max_discount → incohérent."""
    result = CatalogAgent._validate_config_coherence({
        "auto_accept_below": 20.0,
        "max_discount_percent": 15.0,
    })
    assert result["ok"] is False
    assert "auto-accept" in result["reason"].lower() or "auto_accept" in result["reason"].lower()


def test_validate_coherence_negative_shipping():
    """free_shipping_threshold <= 0 → incohérent."""
    result = CatalogAgent._validate_config_coherence({
        "free_shipping_threshold": 0,
    })
    assert result["ok"] is False
    assert "positif" in result["reason"].lower() or "positive" in result["reason"].lower()


def test_validate_coherence_with_current_config():
    """Valide avec la config actuelle pour les valeurs manquantes."""
    current = _make_shop_config()  # max_discount=15, min_margin=10
    # Le vendeur donne min_margin=90, max_discount reste 15 → 90+15=105 > 100
    result = CatalogAgent._validate_config_coherence(
        {"min_margin_percent": 90.0}, current_config=current
    )
    assert result["ok"] is False
