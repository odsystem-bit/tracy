"""Tests du classificateur d'intention (docs/tracy/03-AGENTS.md §Principe de sélection).

Valide que le classificateur sélectionne le bon agent selon le message.
"""

from __future__ import annotations

import pytest

from app.ai_gateway.base import ChatResponse
from app.core.intent import (
    LLMIntentClassifier,
    ShadowIntentClassifier,
    classify_intent,
    classify_intent_async,
)


@pytest.mark.parametrize(
    "message,expected_intent,expected_agent",
    [
        # T-001 : recherche produit
        ("Je veux un téléphone à 100 000 FCFA", "product_search", "CommercialAgent"),
        ("Je cherche un sac", "product_search", "CommercialAgent"),
        ("Affiche-moi le catalogue", "product_search", "CommercialAgent"),
        # T-003 : négociation
        ("Je négocie, c'est possible d'avoir un meilleur prix ?", "negotiation", "NegotiationAgent"),
        ("Fais-moi 50% de réduction", "negotiation", "NegotiationAgent"),
        ("Est-ce que tu peux faire un rabais ?", "negotiation", "NegotiationAgent"),
        # T-006 : catalogue management
        ("Augmente le prix du riz à 650 FCFA", "catalog_management", "CatalogAgent"),
        ("Supprime le produit X", "catalog_management", "CatalogAgent"),
        # T-009 : commande
        ("Je confirme, je prends celui-là", "order", "OrderAgent"),
        ("Annule ma commande", "order", "OrderAgent"),
        # T-011 : paiement
        ("Je veux retirer mes gains", "payment", "PaymentAgent"),
        ("Mon wallet est à combien ?", "payment", "PaymentAgent"),
        # T-012 : support
        ("Ma commande n'est jamais arrivée", "support", "SupportAgent"),
        ("Je veux faire une réclamation", "support", "SupportAgent"),
        # T-013 : campagne
        ("Lance une campagne marketing", "campaign", "CampaignAgent"),
        ("Relance le panier abandonné", "campaign", "CampaignAgent"),
    ],
)
def test_classify_intent(
    message: str,
    expected_intent: str,
    expected_agent: str,
) -> None:
    result = classify_intent(message)
    assert result.intent == expected_intent, f"Expected {expected_intent} for '{message}', got {result.intent}"
    assert result.selected_agent == expected_agent
    assert result.confidence > 0.0




class _FakeGateway:
    """Gateway factice — répond un JSON d'intent sans appel réseau."""

    def __init__(self, content: str) -> None:
        self._content = content
        self.calls: int = 0

    async def complete(self, messages, temperature=0.0, max_tokens=None):
        self.calls += 1
        return ChatResponse(content=self._content, provider="fake", model="fake")


class TestLLMIntentClassifier:
    @pytest.mark.anyio
    async def test_llm_result_used_when_valid(self):
        gateway = _FakeGateway('{"intent": "negotiation", "confidence": 0.9}')
        clf = LLMIntentClassifier(gateway)  # type: ignore[arg-type]
        result = await clf.aclassify("je te donne 660k pour tout")
        assert result.intent == "negotiation"
        assert result.selected_agent == "NegotiationAgent"
        assert result.confidence == 0.9

    @pytest.mark.anyio
    async def test_falls_back_to_keyword_on_invalid_llm(self):
        gateway = _FakeGateway("réponse non JSON")
        clf = LLMIntentClassifier(gateway)  # type: ignore[arg-type]
        result = await clf.aclassify("je veux un téléphone")
        assert result.intent == "product_search"

    @pytest.mark.anyio
    async def test_cache_avoids_repeat_calls(self):
        gateway = _FakeGateway('{"intent": "support", "confidence": 0.9}')
        clf = LLMIntentClassifier(gateway)  # type: ignore[arg-type]
        await clf.aclassify("message inconnu xyz")
        await clf.aclassify("message inconnu xyz")
        assert gateway.calls == 1

    @pytest.mark.anyio
    async def test_sync_classify_is_keyword_fallback(self):
        gateway = _FakeGateway('{"intent": "support", "confidence": 0.9}')
        clf = LLMIntentClassifier(gateway)  # type: ignore[arg-type]
        assert clf.classify("je veux un téléphone").intent == "product_search"


class TestShadowIntentClassifier:
    @pytest.mark.anyio
    async def test_keyword_result_returned_regardless(self):
        gateway = _FakeGateway('{"intent": "support", "confidence": 0.9}')
        clf = ShadowIntentClassifier(gateway)  # type: ignore[arg-type]
        result = await clf.aclassify("je veux un téléphone")
        # Les regex décident : product_search, même si le LLM vote support
        assert result.intent == "product_search"
        assert result.selected_agent == "CommercialAgent"


@pytest.mark.anyio
async def test_classify_intent_async_matches_sync() -> None:
    """Avec le classifieur par défaut (keyword), async et sync donnent le même résultat."""
    assert (await classify_intent_async("je veux un sac")).intent == classify_intent("je veux un sac").intent
def test_classify_intent_unknown() -> None:
    """Un message sans intention claire retourne 'unknown'."""
    result = classify_intent("Bonjour, comment ça va ?")
    assert result.intent == "unknown"
    assert result.confidence == 0.0
    assert result.selected_agent == "CommercialAgent"
