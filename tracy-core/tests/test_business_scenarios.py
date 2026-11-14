"""Tests métier — scénarios complets de conversation (docs/tracy/05-AI_BEHAVIOR.md).

Ces tests simulent des conversations réelles entre clients/vendeurs et Tracy.
Chaque test couvre un scénario métier documenté dans AI_BEHAVIOR.md :

- Client cherche un produit
- Client négocie
- Client change d'avis
- Client demande un catalogue
- Client abandonne la conversation
- Vendeur active une remise
- Vendeur demande à Tracy de répondre automatiquement
- Paiement accepté
- Paiement refusé
- Commande annulée
- Support / réclamation
- Relance
- Fidélisation
- Mémoire conversationnelle (contexte)
- Classification d'intention (V1 → V2 prep)
"""

from __future__ import annotations

import httpx
import pytest
import respx

from app.core.schemas import IncomingMessage
from app.memory.short_term import ConversationContext, ConversationMessage, InMemoryShortTermMemory

from tests.conftest import (
    MANTOTA_BASE_URL,
    mock_catalog_response,
    mock_product_search_response,
    mock_store_config_response,
)


# ── 1. Client cherche un produit ────────────────────────────────────


@pytest.mark.asyncio
async def test_client_searches_product(orchestrator):
    """Client cherche un téléphone — Tracy doit utiliser search_products et répondre."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response())
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Je cherche un téléphone")
    )

    assert reply.text
    assert reply.agent == "CommercialAgent"
    assert "search_products" in reply.tools_used


# ── 2. Client négocie ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_client_negotiates_price(orchestrator):
    """Client demande une réduction — Tracy doit router vers NegotiationAgent."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/stores/store_1/config").mock(
        return_value=httpx.Response(200, json={
            "store_id": "store_1",
            "min_margin_percent": 10.0,
            "first_order_discount_percent": 0.0,
            "max_discount_percent": 15.0,
            "free_shipping_threshold": None,
            "auto_accept_below": 5.0,
            "custom_rules": None,
            "currency": "XOF",
        })
    )
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(200, json=mock_catalog_response())
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Tu peux faire une remise sur le Tecno Spark 10 ?")
    )

    assert reply.agent == "NegotiationAgent"
    assert reply.text


# ── 3. Client change d'avis ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_client_changes_mind(orchestrator):
    """Client change d'avis — Tracy doit gérer la transition naturellement."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(
            200,
            json=mock_product_search_response(
                products=[
                    {"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": "store_1"},
                    {"id": "2", "nom": "Infinix Hot 30", "prix": 90000, "stock": 3, "image_url": None, "store_id": "store_1"},
                ]
            ),
        )
    )

    # Premier message : cherche un Tecno
    reply1 = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Je veux un Tecno Spark 10")
    )
    assert reply1.agent == "CommercialAgent"

    # Change d'avis : veut un Infinix
    reply2 = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Finalement je préfère l'Infinix Hot 30")
    )
    assert reply2.agent == "CommercialAgent"
    assert reply2.text


# ── 4. Client demande un catalogue ──────────────────────────────────


@pytest.mark.asyncio
async def test_client_requests_catalog(orchestrator):
    """Vendeur demande à voir son catalogue — Tracy doit utiliser search_catalog."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(200, json=mock_catalog_response())
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="seller_1", text="Montre-moi le catalogue de la boutique")
    )

    assert reply.agent == "CatalogAgent"
    assert "search_catalog" in reply.tools_used


# ── 5. Client abandonne la conversation ─────────────────────────────


@pytest.mark.asyncio
async def test_client_abandons_conversation(orchestrator):
    """Client envoie un message puis disparaît — Tracy ne doit pas crasher."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(products=[]))
    )
    reply = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Salut")
    )

    assert reply.text
    # Pas d'erreur — Tracy répond quelque chose
    assert reply.agent == "CommercialAgent"


# ── 6. Vendeur active une remise ────────────────────────────────────


@pytest.mark.asyncio
async def test_seller_activates_discount(orchestrator):
    """Vendeur modifie un prix — Tracy doit router vers CatalogAgent."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(200, json=mock_catalog_response())
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="seller_1", text="Baisse le prix du Tecno Spark 10 à 85000")
    )

    assert reply.agent == "CatalogAgent"


# ── 7. Vendeur demande à Tracy de répondre automatiquement ──────────


@pytest.mark.asyncio
async def test_seller_asks_tracy_to_respond(orchestrator):
    """Vendeur demande à Tracy de gérer les clients — Tracy doit confirmer."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(products=[]))
    )
    reply = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="seller_1", text="Tracy, réponds automatiquement aux clients")
    )

    assert reply.text
    # Tracy répond quelque chose — pas de crash


# ── 8. Paiement accepté ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_payment_accepted(orchestrator):
    """Client veut payer — Tracy doit router vers PaymentAgent."""
    respx.post(f"{MANTOTA_BASE_URL}/bot/payments").mock(
        return_value=httpx.Response(
            200,
            json={
                "payment_id": "pay_001",
                "status": "success",
                "amount": 95000,
                "currency": "XOF",
                "method": "wave",
                "reference": "REF-001",
                "checkout_url": "https://pay.moneroo.com/REF-001",
            },
        )
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Je veux payer par Wave")
    )

    assert reply.agent == "PaymentAgent"
    assert reply.text


# ── 9. Paiement refusé ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_payment_refused(orchestrator):
    """Paiement refusé par Mantota — Tracy doit informer le client."""
    respx.post(f"{MANTOTA_BASE_URL}/bot/payments").mock(
        return_value=httpx.Response(402, json={"detail": "Paiement refusé"})
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Je veux payer ma commande")
    )

    assert reply.agent == "PaymentAgent"
    assert reply.text


# ── 10. Commande annulée ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_order_cancelled(orchestrator):
    """Client veut annuler une commande — Tracy doit demander confirmation."""
    reply = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Annuler ma commande order_123")
    )

    assert reply.agent == "OrderAgent"
    assert reply.text


# ── 11. Support / réclamation ───────────────────────────────────────


@pytest.mark.asyncio
async def test_support_reclamation(orchestrator):
    """Client fait une réclamation — Tracy doit router vers SupportAgent."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/orders/order_123/track").mock(
        return_value=httpx.Response(
            200,
            json={
                "order_id": "order_123",
                "statut": "shipped",
                "historique": [{"statut": "shipped", "date": "2024-01-15"}],
                "date_estimee_livraison": "2024-01-17",
            },
        )
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Ma commande order_123 n'est jamais arrivée")
    )

    assert reply.agent == "SupportAgent"
    assert reply.text


# ── 12. Relance ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_relance(orchestrator):
    """Vendeur veut relancer un panier abandonné — Tracy doit router vers CampaignAgent."""
    reply = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="seller_1", text="Relance le panier abandonné du client c1")
    )

    assert reply.agent == "CampaignAgent"
    assert reply.text


# ── 13. Fidélisation ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_loyalty_recognition(orchestrator):
    """Client revient — Tracy doit accueillir avec reconnaissance."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response())
    )
    # Premier message
    await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Je cherche un téléphone")
    )

    # Deuxième message — client revient
    reply = await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Rebonjour, je veux voir ce que vous avez")
    )

    assert reply.text
    assert reply.agent == "CommercialAgent"


# ── 14. Mémoire conversationnelle — contexte ────────────────────────


@pytest.mark.asyncio
async def test_conversation_context_saved(orchestrator, short_term_memory: InMemoryShortTermMemory):
    """Le contexte de conversation doit être sauvegardé après chaque message."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response())
    )
    await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Je cherche un téléphone")
    )

    conv_id = "store_1:c1"
    context = await short_term_memory.get_context(conv_id)
    assert context.last_agent == "CommercialAgent"
    assert context.last_intent == "product_search"


@pytest.mark.asyncio
async def test_conversation_context_cleared(orchestrator, short_term_memory: InMemoryShortTermMemory):
    """La mémoire courte doit être effaçable."""
    conv_id = "store_1:c1"
    await short_term_memory.append(
        conv_id, ConversationMessage(role="user", content="test")
    )
    await short_term_memory.update_context(
        conv_id, ConversationContext(last_agent="CommercialAgent")
    )

    await short_term_memory.clear(conv_id)

    history = await short_term_memory.get_history(conv_id)
    context = await short_term_memory.get_context(conv_id)
    assert history == []
    assert context.last_agent is None


@pytest.mark.asyncio
async def test_conversation_history_preserved(orchestrator, short_term_memory: InMemoryShortTermMemory):
    """L'historique de conversation doit être préservé entre les messages."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(products=[]))
    )
    await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Premier message")
    )
    await orchestrator.handle_message(
        IncomingMessage(store_id="store_1", customer_id="c1", text="Deuxième message")
    )

    conv_id = "store_1:c1"
    history = await short_term_memory.get_history(conv_id)
    # 2 messages user + 2 messages assistant = 4
    assert len(history) == 4
    assert history[0].role == "user"
    assert history[0].content == "Premier message"
    assert history[1].role == "assistant"
    assert history[2].role == "user"
    assert history[2].content == "Deuxième message"


# ── 15. Classification d'intention — V1 → V2 prep ───────────────────


def test_intent_classifier_keyword_product_search():
    """Le classificateur V1 doit reconnaître une recherche produit."""
    from app.core.intent import KeywordIntentClassifier

    classifier = KeywordIntentClassifier()
    result = classifier.classify("Je cherche un téléphone")
    assert result.intent == "product_search"
    assert result.selected_agent == "CommercialAgent"
    assert result.confidence > 0


def test_intent_classifier_keyword_negotiation():
    """Le classificateur V1 doit reconnaître une négociation."""
    from app.core.intent import KeywordIntentClassifier

    classifier = KeywordIntentClassifier()
    result = classifier.classify("Tu peux faire une remise ?")
    assert result.intent == "negotiation"
    assert result.selected_agent == "NegotiationAgent"


def test_intent_classifier_keyword_support():
    """Le classificateur V1 doit reconnaître une réclamation."""
    from app.core.intent import KeywordIntentClassifier

    classifier = KeywordIntentClassifier()
    result = classifier.classify("Ma commande n'est jamais arrivée")
    assert result.intent == "support"
    assert result.selected_agent == "SupportAgent"


def test_intent_classifier_unknown():
    """Le classificateur V1 doit router vers CommercialAgent si inconnu."""
    from app.core.intent import KeywordIntentClassifier

    classifier = KeywordIntentClassifier()
    result = classifier.classify("xyz abc def")
    assert result.intent == "unknown"
    assert result.selected_agent == "CommercialAgent"
    assert result.confidence == 0.0


def test_intent_classifier_swap():
    """Le classificateur doit pouvoir être swappé via set_intent_classifier."""
    from app.core.intent import (
        IntentClassifier,
        get_intent_classifier,
        set_intent_classifier,
    )
    from app.core.schemas import IntentClassification

    class CustomClassifier(IntentClassifier):
        def classify(self, message: str) -> IntentClassification:
            return IntentClassification(
                intent="memory",
                confidence=1.0,
                selected_agent="MemoryAgent",
                reason="custom",
            )

    original = get_intent_classifier()
    custom = CustomClassifier()
    set_intent_classifier(custom)

    try:
        assert get_intent_classifier() is custom
        result = get_intent_classifier().classify("test")
        assert result.selected_agent == "MemoryAgent"
    finally:
        set_intent_classifier(original)


# ── 16. Points d'extension ──────────────────────────────────────────


def test_extension_registry_empty():
    """Le registre d'extensions doit être vide en V1."""
    from app.core.extensions import ExtensionRegistry

    registry = ExtensionRegistry()
    assert not registry.has("notifications")
    assert registry.get("notifications") is None


def test_extension_registry_register():
    """Le registre d'extensions doit accepter une nouvelle extension."""
    from app.core.extensions import ExtensionRegistry

    registry = ExtensionRegistry()
    registry.register("test_ext", object())
    assert registry.has("test_ext")
    assert registry.get("test_ext") is not None


def test_extension_registry_duplicate():
    """Le registre d'extensions doit refuser un doublon."""
    from app.core.extensions import ExtensionRegistry

    registry = ExtensionRegistry()
    registry.register("test_ext", object())
    with pytest.raises(ValueError, match="déjà enregistrée"):
        registry.register("test_ext", object())


# ── 17. Tests des system prompts enrichis ───────────────────────────


def test_commercial_agent_prompt_has_vocabulaire_interdit():
    """Le prompt du CommercialAgent doit contenir les règles de vocabulaire interdit."""
    from app.agents.commercial_agent import SYSTEM_PROMPT

    assert "VOCABULAIRE INTERDIT" in SYSTEM_PROMPT
    assert "IA" in SYSTEM_PROMPT
    assert "listes" in SYSTEM_PROMPT.lower()


def test_negotiation_agent_prompt_has_negotiation_rules():
    """Le prompt du NegotiationAgent doit contenir les règles de négociation."""
    from app.agents.negotiation_agent import SYSTEM_PROMPT

    assert "RÈGLES DE NÉGOCIATION" in SYSTEM_PROMPT
    assert "marge" in SYSTEM_PROMPT.lower()
    assert "contre-offre" in SYSTEM_PROMPT.lower()


def test_support_agent_prompt_has_empathy_rules():
    """Le prompt du SupportAgent doit contenir les règles d'empathie."""
    from app.agents.support_agent import SYSTEM_PROMPT

    assert "RÈGLES DE SUPPORT" in SYSTEM_PROMPT
    assert "empath" in SYSTEM_PROMPT.lower()
    assert "escalade" in SYSTEM_PROMPT.lower()


def test_campaign_agent_prompt_has_relance_rules():
    """Le prompt du CampaignAgent doit contenir les règles de relance."""
    from app.agents.campaign_agent import SYSTEM_PROMPT

    assert "RÈGLES DE RELANCE" in SYSTEM_PROMPT
    assert "pression" in SYSTEM_PROMPT.lower()
    assert "deux fois" in SYSTEM_PROMPT.lower()


def test_all_agent_prompts_have_vocabulaire_interdit():
    """Tous les agents doivent avoir une section VOCABULAIRE INTERDIT."""
    from app.agents.campaign_agent import SYSTEM_PROMPT as campaign_prompt
    from app.agents.catalog_agent import SYSTEM_PROMPT as catalog_prompt
    from app.agents.commercial_agent import SYSTEM_PROMPT as commercial_prompt
    from app.agents.memory_agent import SYSTEM_PROMPT as memory_prompt
    from app.agents.negotiation_agent import SYSTEM_PROMPT as negotiation_prompt
    from app.agents.order_agent import SYSTEM_PROMPT as order_prompt
    from app.agents.payment_agent import SYSTEM_PROMPT as payment_prompt
    from app.agents.support_agent import SYSTEM_PROMPT as support_prompt

    for name, prompt in [
        ("CampaignAgent", campaign_prompt),
        ("CatalogAgent", catalog_prompt),
        ("CommercialAgent", commercial_prompt),
        ("MemoryAgent", memory_prompt),
        ("NegotiationAgent", negotiation_prompt),
        ("OrderAgent", order_prompt),
        ("PaymentAgent", payment_prompt),
        ("SupportAgent", support_prompt),
    ]:
        assert "VOCABULAIRE INTERDIT" in prompt, f"{name} missing VOCABULAIRE INTERDIT"


# ── 18. Scénarios T-006 à T-015 (09-TEST_SCENARIOS.md) ─────────────


# T-006 : Remise permanente sur une catégorie
@pytest.mark.asyncio
async def test_t006_permanent_discount_category(orchestrator):
    """T-006 : Le vendeur demande une remise permanente sur une catégorie."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(200, json=mock_catalog_response())
    )
    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="seller_1",
            text="À partir de maintenant, fais 5% de remise sur les sacs.",
        )
    )
    assert reply.agent == "CatalogAgent"
    assert reply.text


# T-007 : Modification de prix
@pytest.mark.asyncio
async def test_t007_price_modification(orchestrator):
    """T-007 : Le vendeur modifie le prix d'un produit."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(200, json=mock_catalog_response())
    )
    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="seller_1",
            text="Augmente le prix du riz à 650 FCFA.",
        )
    )
    assert reply.agent == "CatalogAgent"
    assert reply.text


# T-008 : Suppression de produit — confirmation requise
@pytest.mark.asyncio
async def test_t008_product_deletion_confirmation(orchestrator):
    """T-008 : Tracy doit demander confirmation avant une suppression (action destructive)."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/catalog/search").mock(
        return_value=httpx.Response(200, json=mock_catalog_response())
    )
    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="seller_1",
            text="Supprime le produit X.",
        )
    )
    assert reply.agent == "CatalogAgent"
    assert reply.text
    # Tracy doit demander confirmation — la réponse doit contenir une question
    # ou un terme lié à la confirmation
    assert any(
        word in reply.text.lower()
        for word in ("confirm", "sûr", "certain", "supprim", "vraiment")
    ), "Tracy doit demander confirmation pour une action destructive"


# T-009 : Commande simple
@pytest.mark.asyncio
async def test_t009_simple_order(orchestrator):
    """T-009 : Le client confirme une commande — Tracy doit router vers OrderAgent."""
    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="c1",
            text="Je confirme, je prends celui-là.",
        )
    )
    assert reply.agent == "OrderAgent"
    assert reply.text


# T-010 : Annulation de commande
@pytest.mark.asyncio
async def test_t010_order_cancellation(orchestrator):
    """T-010 : Le client annule sa commande — Tracy doit router vers OrderAgent."""
    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="c1",
            text="Annule ma commande, j'ai changé d'avis.",
        )
    )
    assert reply.agent == "OrderAgent"
    assert reply.text


# T-011 : Demande de retrait vendeur
@pytest.mark.asyncio
async def test_t011_withdrawal_request(orchestrator):
    """T-011 : Le vendeur demande un retrait — Tracy doit router vers PaymentAgent."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/wallet/seller_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "user_id": "seller_1",
                "solde_disponible": 150000,
                "solde_en_attente": 25000,
                "devise": "XOF",
                "dernieres_transactions": [],
            },
        )
    )
    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="seller_1",
            text="Je veux retirer mes gains.",
        )
    )
    assert reply.agent == "PaymentAgent"
    assert reply.text


# T-012 : Réclamation client
@pytest.mark.asyncio
async def test_t012_customer_complaint(orchestrator):
    """T-012 : Le client fait une réclamation — Tracy doit router vers SupportAgent."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/orders/order_123/track").mock(
        return_value=httpx.Response(
            200,
            json={
                "order_id": "order_123",
                "statut": "shipped",
                "historique": [{"statut": "shipped", "date": "2024-01-15"}],
                "date_estimee_livraison": "2024-01-17",
            },
        )
    )

    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="c1",
            text="Ma commande n'est jamais arrivée.",
        )
    )
    assert reply.agent == "SupportAgent"
    assert reply.text


# T-013 : Panier abandonné — relance
@pytest.mark.asyncio
async def test_t013_abandoned_cart_relance(orchestrator):
    """T-013 : Relance de panier abandonné — Tracy doit router vers CampaignAgent."""
    reply = await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="seller_1",
            text="Relance le panier abandonné du client c1.",
        )
    )
    assert reply.agent == "CampaignAgent"
    assert reply.text


# T-014 : Isolation des boutiques
@pytest.mark.asyncio
async def test_t014_store_isolation(orchestrator, short_term_memory: InMemoryShortTermMemory):
    """T-014 : Une information de la boutique A ne doit pas être accessible à la boutique B."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(products=[]))
    )
    # Boutique A envoie un message
    await orchestrator.handle_message(
        IncomingMessage(store_id="store_A", customer_id="c1", text="Je cherche un téléphone")
    )

    # Boutique B envoie un message
    await orchestrator.handle_message(
        IncomingMessage(store_id="store_B", customer_id="c2", text="Je cherche des chaussures")
    )

    # L'historique de la boutique A ne doit pas contenir le message de la boutique B
    history_A = await short_term_memory.get_history("store_A:c1")
    history_B = await short_term_memory.get_history("store_B:c2")

    # Vérifier que les historiques sont isolés
    contents_A = [msg.content for msg in history_A]
    contents_B = [msg.content for msg in history_B]

    assert any("téléphone" in c for c in contents_A), "Boutique A doit contenir 'téléphone'"
    assert not any("chaussures" in c for c in contents_A), "Boutique A ne doit pas contenir 'chaussures'"
    assert any("chaussures" in c for c in contents_B), "Boutique B doit contenir 'chaussures'"
    assert not any("téléphone" in c for c in contents_B), "Boutique B ne doit pas contenir 'téléphone'"


# T-015 : Donnée non mémorisable (numéro de carte bancaire)
@pytest.mark.asyncio
async def test_t015_non_memorable_data(orchestrator, short_term_memory: InMemoryShortTermMemory):
    """T-015 : Tracy ne doit pas stocker de données bancaires dans la mémoire courte."""
    respx.get(f"{MANTOTA_BASE_URL}/bot/products/search").mock(
        return_value=httpx.Response(200, json=mock_product_search_response(products=[]))
    )
    # Le client envoie un numéro de carte dans le chat
    await orchestrator.handle_message(
        IncomingMessage(
            store_id="store_1",
            customer_id="c1",
            text="Mon numéro de carte est 4242 4242 4242 4242",
        )
    )

    conv_id = "store_1:c1"
    history = await short_term_memory.get_history(conv_id)

    # Le message du client est dans l'historique (Tracy le traite)
    # mais le contexte de conversation ne doit pas contenir le numéro de carte
    context = await short_term_memory.get_context(conv_id)

    # Vérifier que les préférences ne contiennent pas le numéro de carte
    for pref in context.preferences_detected:
        assert "4242" not in pref, "Le numéro de carte ne doit pas être dans les préférences"

    # Le résumé de conversation ne doit pas contenir le numéro de carte
    if context.conversation_summary:
        assert "4242" not in context.conversation_summary, "Le numéro de carte ne doit pas être dans le résumé"
