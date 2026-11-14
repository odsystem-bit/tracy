"""Batterie de régression : routage d'intent (101+ scénarios).

Valide que chaque phrase client/vendeur est routée vers le bon agent.
Lancée automatiquement via pytest, elle garantit que toute modification
des patterns d'intent ne casse pas le routage existant.

Usage :
    .venv/bin/pytest tests/test_intent_scenarios.py -v
"""

from __future__ import annotations

import pytest

from app.core.intent import classify_intent

# (phrase, intent_attendu_ou_liste, agent_attendu)
# None pour agent = "peu importe"
SCENARIOS: list[tuple[str, list[str], str | None]] = [
    # ══════════ CLIENT : Recherche produit ══════════
    ("Je cherche un téléphone pas cher", ["product_search", "negotiation"], None),
    ("Tu as des robes de soirée ?", ["product_search", "unknown"], None),
    ("Montre-moi des chaussures taille 42", ["product_search"], "CommercialAgent"),
    ("Je veux acheter un frigo", ["product_search"], "CommercialAgent"),
    ("Vous vendez des matelas ?", ["product_search", "unknown"], None),
    ("Y a quoi comme nouveautés ?", ["product_search", "unknown"], None),
    ("Je cherche un cadeau pour ma femme", ["product_search"], "CommercialAgent"),
    ("Avez-vous des groupes électrogènes ?", ["product_search", "unknown"], None),
    ("Il me faut un ventilateur", ["product_search", "unknown"], None),
    ("Je veux une perruque", ["product_search"], "CommercialAgent"),
    ("Tu as du tissu wax ?", ["product_search", "unknown"], None),
    ("C'est combien le sac noir ?", ["product_search"], "CommercialAgent"),
    ("Prix du iPhone 13 ?", ["product_search"], "CommercialAgent"),
    ("est ce que tu as des pagnes", ["product_search", "unknown"], None),

    # ══════════ CLIENT : Négociation ══════════
    ("C'est trop cher, baisse un peu", ["negotiation"], "NegotiationAgent"),
    ("Tu peux me faire un prix ?", ["negotiation"], "NegotiationAgent"),
    ("Dernier prix c'est combien ?", ["negotiation"], "NegotiationAgent"),
    ("Fais-moi une remise", ["negotiation"], "NegotiationAgent"),
    ("10000 c'est ma dernière offre", ["negotiation", "unknown"], None),
    ("Je te donne 5000, ça passe ?", ["negotiation", "unknown"], None),
    ("Diminue le prix s'il te plaît", ["negotiation"], "NegotiationAgent"),

    # ══════════ CLIENT : Commande ══════════
    ("Je le prends", ["order"], "OrderAgent"),
    ("Je confirme ma commande", ["order"], "OrderAgent"),
    ("Où est ma commande ?", ["order"], "OrderAgent"),
    ("Annule ma commande", ["order"], "OrderAgent"),
    ("Statut de ma commande CMD-123", ["order"], "OrderAgent"),
    ("Je veux commander 2 pièces", ["order"], "OrderAgent"),
    ("ok c'est bon je prends", ["order"], "OrderAgent"),

    # ══════════ CLIENT : Paiement ══════════
    ("Comment je paie ?", ["payment"], "PaymentAgent"),
    ("Je peux payer par MoMo ?", ["payment"], "PaymentAgent"),
    ("Envoie-moi le lien de paiement", ["payment"], "PaymentAgent"),
    ("Vous acceptez les cartes bancaires ?", ["payment"], "PaymentAgent"),
    ("Je paie à la livraison ?", ["payment"], "PaymentAgent"),
    ("mon paiement a échoué", ["payment", "support"], None),

    # ══════════ CLIENT : Livraison (questions) ══════════
    ("Vous livrez à Porto-Novo ?", ["delivery"], "LogisticsAgent"),
    ("C'est combien la livraison ?", ["product_search", "unknown"], None),
    ("Combien de temps pour livrer ?", ["product_search", "unknown"], None),
    ("Vous livrez le dimanche ?", ["delivery", "unknown"], None),
    ("livraison gratuite ?", ["delivery", "shop_config", "unknown"], None),

    # ══════════ CLIENT : Support / Litige ══════════
    ("Mon colis n'est jamais arrivé", ["support"], "SupportAgent"),
    ("Le produit est cassé", ["support"], "SupportAgent"),
    ("Je veux un remboursement", ["support"], "SupportAgent"),
    ("C'est une arnaque !", ["support"], "SupportAgent"),
    ("Je veux parler à un humain", ["support"], "SupportAgent"),
    ("le produit ne marche pas", ["support"], "SupportAgent"),
    ("J'ai reçu le mauvais article", ["support"], "SupportAgent"),
    ("signaler un problème", ["support"], "SupportAgent"),
    ("J'ai payé mais rien reçu", ["support"], "SupportAgent"),

    # ══════════ CLIENT : Restaurant ══════════
    ("J'ai faim", ["restaurant"], "RestaurantAgent"),
    ("Je cherche un restaurant", ["restaurant"], "RestaurantAgent"),
    ("Montre le menu", ["restaurant"], "RestaurantAgent"),
    ("Je veux du poulet braisé", ["restaurant"], "RestaurantAgent"),
    ("Vous avez des pizzas ?", ["restaurant"], "RestaurantAgent"),
    ("C'est quoi le plat du jour ?", ["restaurant"], "RestaurantAgent"),
    ("Le restau est ouvert ?", ["restaurant"], "RestaurantAgent"),

    # ══════════ CLIENT : Mémoire ══════════
    ("Je m'appelle Koffi", ["memory"], "MemoryAgent"),
    ("Tu te souviens de moi ?", ["memory"], "MemoryAgent"),
    ("Oublie ce que je t'ai dit", ["memory"], "MemoryAgent"),
    ("Qu'est-ce que je t'ai dit hier ?", ["memory"], "MemoryAgent"),
    ("Rappelle-moi ce que j'ai commandé", ["memory", "order"], None),

    # ══════════ CLIENT : App download ══════════
    ("Où télécharger l'app ?", ["app_download"], "CommercialAgent"),
    ("Donne-moi le lien Play Store", ["app_download"], "CommercialAgent"),
    ("Comment installer Mantota ?", ["app_download"], "CommercialAgent"),

    # ══════════ CLIENT : Salutations / small talk ══════════
    ("Bonjour", ["unknown"], "CommercialAgent"),
    ("Salut ça va ?", ["unknown"], "CommercialAgent"),
    ("Merci beaucoup", ["unknown"], "CommercialAgent"),
    ("Au revoir", ["unknown"], "CommercialAgent"),
    ("Tu es qui ?", ["unknown"], "CommercialAgent"),
    ("C'est quoi Mantota ?", ["unknown"], "CommercialAgent"),

    # ══════════ VENDEUR : Onboarding ══════════
    ("Je veux vendre sur Mantota", ["vendor_onboarding"], "CatalogAgent"),
    ("Comment devenir vendeur ?", ["vendor_onboarding"], "CatalogAgent"),

    # ══════════ VENDEUR : Création boutique ══════════
    ("Je veux créer ma boutique", ["store_creation", "catalog_management"], "CatalogAgent"),
    ("Comment ouvrir une boutique ?", ["store_creation", "catalog_management"], "CatalogAgent"),

    # ══════════ VENDEUR : Gestion catalogue ══════════
    ("Ajoute un produit", ["catalog_management"], "CatalogAgent"),
    ("Supprime le sac rouge", ["catalog_management"], "CatalogAgent"),
    ("Change le prix du téléphone à 90000", ["catalog_management"], "CatalogAgent"),
    ("Le produit X est en rupture de stock", ["catalog_management"], "CatalogAgent"),
    ("Modifie le stock à 50", ["catalog_management"], "CatalogAgent"),
    ("Montre mon catalogue", ["catalog_management"], "CatalogAgent"),

    # ══════════ VENDEUR : Config Tracy / règles ══════════
    ("Configure mes règles de négociation", ["shop_config", "catalog_management"], "CatalogAgent"),
    ("Marge minimum 10%", ["shop_config"], "CatalogAgent"),
    ("Active la livraison gratuite", ["shop_config"], "CatalogAgent"),
    ("Réduction max 15%", ["shop_config"], "CatalogAgent"),

    # ══════════ VENDEUR : Ventes / stats ══════════
    ("Combien j'ai vendu ce mois ?", ["vendor_stats"], "VendorCopilot"),
    ("Mes statistiques de vente", ["vendor_stats"], "VendorCopilot"),
    ("Quel est mon chiffre d'affaires ?", ["vendor_stats"], "VendorCopilot"),
    ("Combien de commandes aujourd'hui ?", ["vendor_stats"], "VendorCopilot"),
    ("Fais-moi le point du jour", ["vendor_stats"], "VendorCopilot"),
    ("Fais-moi un résumé des discussions avec les clients", ["vendor_stats"], "VendorCopilot"),
    ("Quels produits sont en rupture ?", ["vendor_stats"], "VendorCopilot"),

    # ══════════ VENDEUR : Wallet / retrait ══════════
    ("Je veux retirer mon argent", ["payment"], "PaymentAgent"),
    ("Solde de mon wallet", ["payment"], "PaymentAgent"),
    ("Quand je reçois mon argent ?", ["payment", "unknown"], None),

    # ══════════ VENDEUR : Campagnes ══════════
    ("Lance une campagne de promo", ["campaign"], "CampaignAgent"),
    ("Relance les paniers abandonnés", ["campaign"], "CampaignAgent"),
    ("Statistiques de ma campagne", ["campaign"], "CampaignAgent"),

    # ══════════ CAS AMBIGUS / PIÈGES ══════════
    ("Je veux payer moins cher", ["negotiation", "payment"], None),
    ("Le moins cher c'est lequel ?", ["product_search"], "CommercialAgent"),
    ("Ma commande de poulet n'est pas arrivée", ["support"], "SupportAgent"),
    ("Annule tout", ["order", "unknown"], None),
    ("C'est disponible ?", ["product_search"], "CommercialAgent"),
    ("Tu livres où ?", ["delivery", "unknown"], None),
    ("Mon paiement est passé ?", ["payment"], "PaymentAgent"),
    ("Je veux du pays", ["payment", "unknown", "product_search"], None),  # piège \bpay\b
]


def _make_test_id(scenario: tuple[str, list[str], str | None]) -> str:
    """Génère un ID lisible pour pytest."""
    phrase = scenario[0]
    # Garder seulement les 30 premiers caractères, remplacer les espaces
    safe = phrase[:30].replace(" ", "_").replace("'", "").replace("?", "").replace("!", "")
    return safe


@pytest.mark.parametrize(
    "phrase,expected_intents,expected_agent",
    SCENARIOS,
    ids=[_make_test_id(s) for s in SCENARIOS],
)
def test_intent_routing(
    phrase: str,
    expected_intents: list[str],
    expected_agent: str | None,
) -> None:
    """Vérifie que la phrase est routée vers le bon intent et agent."""
    result = classify_intent(phrase)
    intent_ok = result.intent in expected_intents
    agent_ok = expected_agent is None or result.selected_agent == expected_agent
    assert intent_ok, (
        f"Intent incorrect pour {phrase!r}:\n"
        f"  obtenu : intent={result.intent}, agent={result.selected_agent}\n"
        f"  attendu : intent∈{expected_intents}, agent={expected_agent or 'peu importe'}"
    )
    assert agent_ok, (
        f"Agent incorrect pour {phrase!r}:\n"
        f"  obtenu : intent={result.intent}, agent={result.selected_agent}\n"
        f"  attendu : intent∈{expected_intents}, agent={expected_agent or 'peu importe'}"
    )


def test_scenario_count() -> None:
    """Vérifie qu'on a bien au moins 100 scénarios (anti-régression de la batterie)."""
    assert len(SCENARIOS) >= 100, f"La batterie doit contenir au moins 100 scénarios, actuel : {len(SCENARIOS)}"
