"""Classificateur d'intention (docs/tracy/03-AGENTS.md §Principe de sélection).

Lorsqu'un message arrive, Tracy Core :
1. Classe l'intention du message (recherche, négociation, commande, paiement...).
2. Sélectionne l'agent dont le rôle correspond à cette intention.
3. Transmet le contexte nécessaire à l'agent.

⚠️  LIMITATION V1 — Classification par mots-clés (regex) :
    La classification actuelle repose sur des patterns regex statiques. Cette
    approche est limitée :
    - ne comprend pas le contexte ni les intentions implicites,
    - ne gère pas les messages ambigus ou multi-intentions,
    - nécessite un maintien manuel des patterns.

    Migration V2 (docs/tracy/08-ROADMAP.md) :
    Remplacement par un classificateur LLM via l'AI Gateway, capable de :
    - comprendre le contexte conversationnel,
    - gérer les intentions multiples dans un seul message,
    - fournir un score de confiance calibré,
    - apprendre des corrections humaines.

    En attendant, les intentions inconnues sont routées vers CommercialAgent
    qui demande clarification au client ( comportement documenté dans
    docs/tracy/03-AGENTS.md §Principe de sélection — note V1).

ARCHITECTURE V1→V2 :
    Un IntentClassifier abstrait est défini pour permettre le swap futur.
    V1 utilise KeywordIntentClassifier (implémentation regex).
    V2 utilisera LLMIntentClassifier (implémentation via AI Gateway).
    L'orchestrateur reçoit le classificateur par injection de dépendances.
"""

from __future__ import annotations

import asyncio
import re
import time
from abc import ABC, abstractmethod

from app.core.schemas import IntentClassification
from app.logging_config import get_logger

logger = get_logger(__name__)


# ── Patterns de mots-clés par intention ─────────────────────────────
# L'ordre importe : les patterns les plus spécifiques sont testés en premier.

_INTENT_PATTERNS: list[tuple[str, list[str], str]] = [
    # Onboarding vendeur — avant app_download et product_search
    (
        "vendor_onboarding",
        [
            r"(?:vendre.*sur.*mantota|devenir.*vendeur|devenir.*vendeuse|"
            r"commencer.*[àa].*vendre|je.*veux.*vendre|comment.*vendre|"
            r"inscrire.*vendeur|inscription.*vendeur)",
        ],
        "CatalogAgent",
    ),
    # Stats vendeur — avant order et product_search (« combien de commandes »)
    (
        "vendor_stats",
        [
            r"(?:combien.*(?:j'ai|jai).*vendu|combien.*de.*commandes|"
            r"mes.*statistiques|statistiques.*de.*vente|mes.*ventes|"
            r"chiffre.*d.affaires|mes.*performances|rapport.*de.*vente)",
            r"(?:point.*du.*jour|briefing|quoi.*de.*neuf|r[ée]sum[ée].*(?:des|de).*(?:discussions?|conversations?|clients?)|"
            r"compte.?rendu|que.*disent.*(?:les.*)?clients?|clients?.*(?:ont|a).*n[ée]goci|"
            r"mes.*(?:ruptures?|stocks?)|stock.*(?:faible|bas)|quels?.*produits?.*(?:rupture|stock)|"
            r"qui.*veut.*me.*parler|demandes?.*de.*contact)",
        ],
        "VendorCopilot",
    ),
    # Création de boutique — le plus spécifique, testé en premier
    (
        "store_creation",
        [
            r"(?:cr[ée]er.*boutique|ouvrir.*boutique|nouvelle.*boutique|"
            r"lancer.*boutique|ma boutique|monter.*boutique|installer.*boutique|boutique.*physique|boutique.*en ligne)",
        ],
        "CatalogAgent",
    ),
    # Configuration boutique — vendeur veut configurer ses règles (avant negotiation)
    (
        "shop_config",
        [
            r"(?:configur.*r[èe]gle|configur.*boutique|r[èe]gle.*n[ée]goci|"
            r"marge.*minim|marge.*\d+|change.*marge|param[èe]tre.*boutique|"
            r"r[ée]glage|auto.?accept|livraison.*gratuit|r[ée]duction.*max|"
            r"r[ée]duction.*premier|mes r[èe]gles)",
        ],
        "CatalogAgent",
    ),
    # Catalogue — instructions vendeur spécifiques (avant negotiation car "fais 5% de remise" = gestion permanente)
    # ATTENTION: "baisse le prix" seul = négociation client, pas catalog
    # Catalog = changement permanent de prix avec valeur ou contexte vendeur
    (
        "catalog_management",
        [
            r"(?:à partir de maintenant|fais.*remise.*sur|fais.*\d+.*remise|"
            r"remise.*permanent|augmente.*prix.*\d|baisse.*prix.*\d|change.*prix.*\d|"
            r"modif.*prix|supprim|ajoute.*produit|rupture.*stock|"
            r"catalogue.*boutique|inventaire|mon.*catalogue|"
            r"cr[ée]er.*boutique|ouvrir.*boutique|nouvelle.*boutique|"
            r"configurer|r[èe]glage|r[èe]gles|n[ée]gociation.*config|marge.*min|"
            r"modifie.*prix|modifie.*stock|ajoute.*stock)",
        ],
        "CatalogAgent",
    ),
    # Négociation — avant product_search car "je veux un téléphone moins cher" = nego
    # Mais "montre-moi le moins cher" = product_search (tri), pas nego
    (
        "negotiation",
        [
            r"(?:n[ée]goci|rabais|remise|r[ée]duction|baiser.*prix|"
            r"meilleur prix|prix.*bas|discount|d[ée]stockage|"
            r"trop cher|faire.*prix|faire.*un.*prix|tu.*peux.*prix|"
            r"baisser.*prix|diminue.*prix|n[ée]gocier.*prix|"
            r"(?<!le )moins cher|c'est.*cher|trop.*cher|"
            r"tu.*peux.*baisser|tu.*peux.*faire.*meilleur|"
            r"tu.*peux.*faire.*effort|fais.*effort|"
            r"dernier prix|meilleur.*prix.*tu.*peux|"
            # Offres de prix : "prendre a 300000", "cest possible a 20000", "tu me le fais a 5000"
            r"c['e]st\s+possible|possible.*(?:a|à)\s*\d|"
            r"(?:prendre|prends|prend|avoir|donne).*(?:a|à)\s*\d{3,}|"
            r"tu.*(?:peux|fais|faire|me\s+donne).*(?:a|à)\s*\d{3,}|"
            r"(?:a|à)\s*\d{4,}\s*(?:fcfa|cfa|francs?|f\b)|"
            # Offre directe du client : « je te donne 660k », « je donne 5000 »,
            # « 660k », « je peux mettre 300k »
            r"je\s+(?:te|vous|t['\u2019])\s*donne\b|je\s+peux\s+(?:mettre|donner|faire)\s+\d|"
            r"\bje\s+donne\s+\d{3,}|\b\d{2,}\s*k\s*(?:fcfa|cfa|f)?\b|"
            # « réduis-moi », « fais-moi une réduction », « dernier prix »
            r"r[ée]dui|derni[eè]re\s+offre|ton\s+dernier|prix\s+final)",
        ],
        "NegotiationAgent",
    ),
    # Support — avant order car "ma commande n'est jamais arrivée" = support
    (
        "support",
        [
            r"(?:r[ée]clamation|probl[èe]me|pas.*livr|jamais.*arriv|"
            r"pay[ée].*(?:mais|et).*(?:rien|pas).*re[çc]u|(?:rien|pas).*re[çc]u.*pay[ée]|"
            r"pas.*arriv|colis|mauvais|d[ée]f[ée]ctueux|rembours|insatisf|plainte|"
            r"signaler|signalement|support|contacter|contact|aide|bug|bugue|arnaque|escroquerie|"
            r"humain|vrai.*personne|parler.*[àa].*humain|quelqu['']un|support.*humain|"
            r"livraison.*retard|retard.*livraison|non.*livr|commande.*non.*re[çc]u|"
            r"cass|ab[îi]m|ne.*marche.*pas|ne.*fonctionne.*pas|"
            r"produit.*d[ée]faut|d[ée]faut.*produit|produit.*probl[èe]me|"
            # Non-conformité / litige : "pas conforme", "pas ce que j'ai demandé", "faux produit"
            r"pas.*conforme|non.*conforme|conformit|"
            r"pas.*ce.*que.*(?:command|demand|attend|voulu|reçu|recu|pay)|"
            r"faux.*produit|contrefa|mauvais.*(?:produit|article|commande)|"
            r"erreur.*(?:de|dans|sur).*(?:commande|produit)|"
            r"[ée]chang|retour.*produit|renvoy.*produit)",
        ],
        "SupportAgent",
    ),
    # Campagne / relance — avant order car "relance le panier abandonné" = campagne
    (
        "campaign",
        [
            r"(?:campagne|relance|marketing|promotionnel|panier.*abandonn|"
            r"fidelis|partenaire|parrain|commission|affili|performance.*campagne|"
            r"statistique.*campagne|lancer.*campagne|cr[ée]er.*campagne|"
            r"lancer.*campagne|commission.*campagne|affili.*campagne)",
        ],
        "CampaignAgent",
    ),
    # Paiement
    (
        "payment",
        [
            r"(?:\bpay\b|\bpaie\b|payer|paiement|wallet|portefeuille|retrait|retirer|d[ée]p[ôo]t|"
            r"moneroo|lien.*paiement|comment.*paie|comment.*payer|m[ée]thode.*paiement|"
            r"mobile.*money|momo|carte.*bancaire|esp[èe]ce|cash)",
        ],
        "PaymentAgent",
    ),
    # Restaurant — AVANT order car "commander un plat" = restaurant, pas order
    (
        "restaurant",
        [
            r"(?:restaurant|restau\b|resto\b|manger|repas|plat|menu|nourriture|faim|d[ée]jeuner|d[îi]ner|petit.?d[ée]j|"
            r"pizza|burger|riz|atti[ée]k[ée]|poulet|poisson|brais[ée]|grill|"
            r"commander.*plat|commander.*repas|commander.*manger|livrer.*repas|livraison.*repas|"
            r"boisson|dessert|entr[ée]e|plat.*du.*jour|sp[ée]cialit[ée]|"
            r"horaire.*restaurant|restaurant.*horaire|ouvert.*ferm[ée]|"
            r"menu.*restaurant|restaurant.*menu|carte.*restaurant|"
            r"c'est quoi.*horaire|quel.*horaire|les horaires|tu.*es.*ouvert|tu.*es.*ferm)",
        ],
        "RestaurantAgent",
    ),
    # Livraison (couverture / zone / frais) — hors suivi de commande (référence CMD-)
    (
        "delivery",
        [
            r"^(?!.*\bcmd-)(?=.*(?:\btu\s+livres?\b|\bvous\s+livrez\b|\blivrez[- ]vous\b|\blivres[- ]tu\b|"
            r"frais\s+de\s+livraison|d[ée]lai\s+de\s+livraison|zone\s+de\s+livraison|"
            r"livraison\s+(?:à|a|vers|possible|gratuite|disponible)|"
            r"(?:peut|puis|peux).*(?:me\s+)?faire\s+livrer|livr[ée]\s+(?:à|a|chez)|"
            r"retrait\s+sur\s+place|r[ée]cup[ée]rer\s+sur\s+place)).*$",
        ],
        "LogisticsAgent",
    ),
    # Commande — plus spécifique pour éviter de capturer "commande" dans support/campaign/restaurant
    (
        "order",
        [
            r"(?:commander|je.*prends|je.*le.*prends|je.*la.*prends|je.*veux.*celui.l[àa]|"
            r"je confirme|annul.*command|"
            r"panier|je.*veux.*commander|passer.*commande|"
            r"annul.*ma.*command|suivi.*command|o[ùu].*ma.*command|"
            r"suiv\w*\s+(?:cette|ma|la|ta)\s+command|notifi\w*|tiens.*moi.*(?:inform|au courant)|"
            r"livreur|ma.*livraison|statut.*livraison|où.*en.*est.*command|"
            r"statut.*command|livr[ée].*command|"
            r"je.*l'ach[èe]te|"
            r"c'est.*bon.*je.*prends|ok.*je.*prends|"
            r"je.*veux.*celui|je.*prends.*celui)",
        ],
        "OrderAgent",
    ),
    # Recherche de boutique — avant mémoire car "liste moi des boutiques" est du commerce
    (
        "store_search",
        [
            r"(?:liste.*boutique|donne.*boutique|montre.*boutique|"
            r"boutique.*disponible|boutique.*fiable|"
            r"\d+\s*boutique|des boutiques|un magasin|"
            r"parle.*boutique|adresse.*boutique|situ[ée].*boutique|"
            r"coordonn?[eé]+s?|cordonn[eé]+s?|coordonn[eé]es|"
            r"(?:boutique|boutiq|boutis|magasin|vendeur).*(?:adresse|coordon|contact|num[ée]ro|o[ùu])|"
            r"(?:adresse|contact|num[ée]ro|localis|o[ùu]).*(?:boutique|magasin))",
        ],
        "CommercialAgent",
    ),
    # Mémoire (préférences / oubli / rappels)
    (
        "memory",
        [
            r"(?:m[ée]moris|souviens?|pr[ée]f[ée]rence|oublie|efface.*donn[ée]e|"
            r"souviens.*toi|rappel|tu.*te.*souviens|tu.*me.*rappel|"
            r"qu['']est.*que.*j.*ai.*dit|ce.*que.*j.*ai.*dit|"
            r"tu.*sais.*qui.*je.*suis|tu.*connais.*mon.*nom|"
            r"mon.*nom.*c'est|je.*m'appelle|appelle.*moi)",
        ],
        "MemoryAgent",
    ),
    # Téléchargement app — après mémoire, avant product_search
    (
        "app_download",
        [
            r"(?:t[ée]l[ée]charger.*app|t[ée]lecharger.*app|t[ée]l[ée]charger.*mantota|t[ée]lecharger.*mantota|"
            r"download.*app|download.*mantota|installer.*app|installer.*mantota|"
            r"o[ùu].*t[ée]l[ée]charger|o[ùu].*t[ée]lecharger|o[ùu].*app|"
            r"lien.*app|app.*lien|donne.*lien|lien.*t[ée]l[ée]charger|lien.*t[ée]lecharger|"
            r"play.*store|app.*store|apk|l.app|l.application|"
            r"comment.*installer|je.*veux.*(?:l.)?app\b)",
        ],
        "CommercialAgent",
    ),
    # Recherche produit — intention la plus courante, testée en dernier
    (
        "product_search",
        [
            r"(?:je veux|je cherche|recherche|trouve|disponib|combien|prix|"
            r"t[ée]l[ée]phone|montre|sac|chaussure|v[êe]tement|produit|"
            r"envoie.*catalogue|affiche|montre.*moi|"
            r"le moins cher|le plus cher|"
            r"parfum|cosm[ée]tique|maquillage|ordinateur|laptop|tablette|"
            r"jupe|pantalon|short|manteau|veste|pull|tshirt|t-shirt|"
            r"lunette|sacoche|jouet|enfant|b[ée]b[ée]|"
            r"[ée]couteur|chargeur|coque|c[âa]ble|batterie|"
            r"casque|enceinte|clavier|souris|imprimante|"
            r"montre.*connect[ée]|smartwatch|tablette.*graphique)"
        ],
        "CommercialAgent",
    ),
]


class IntentClassifier(ABC):
    """Interface abstraite du classificateur d'intention.

    V1 : KeywordIntentClassifier (regex).
    V2 : LLMIntentClassifier (via AI Gateway).
    L'orchestrateur reçoit le classificateur par injection de dépendances,
    permettant le swap sans modification du code de l'orchestrateur.
    """

    @abstractmethod
    def classify(self, message: str) -> IntentClassification:
        """Classifie l'intention d'un message.

        Args:
            message: Texte du message du client/vendeur/partenaire.

        Returns:
            IntentClassification avec l'intention détectée, le niveau de confiance
            et l'agent sélectionné.
        """

    async def aclassify(
        self, message: str, last_intent: str | None = None
    ) -> IntentClassification:
        """Version asynchrone de classify — délègue à classify() par défaut.

        Les classifieurs basés sur l'AI Gateway (LLM, shadow) surchargent cette
        méthode ; le classifieur regex reste synchrone.
        """
        return self.classify(message)


class KeywordIntentClassifier(IntentClassifier):
    """Classificateur V1 par mots-clés (regex).

    Implémentation par défaut. Teste les patterns dans l'ordre et retourne
    la première correspondance. Si aucune correspondance, route vers
    CommercialAgent pour clarification.
    """

    def classify(self, message: str) -> IntentClassification:
        message_lower = message.lower()

        for intent, patterns, agent in _INTENT_PATTERNS:
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    logger.info(
                        "intent_classified",
                        intent=intent,
                        agent=agent,
                        confidence=0.8,
                    )
                    return IntentClassification(
                        intent=intent,  # type: ignore[arg-type]
                        confidence=0.8,
                        selected_agent=agent,
                        reason=f"Pattern matched: {pattern}",
                    )

        # Aucune intention détectée — clarification requise
        logger.info("intent_unknown", message_preview=message[:100])
        return IntentClassification(
            intent="unknown",
            confidence=0.0,
            selected_agent="CommercialAgent",
            reason="Aucun pattern correspondant — CommercialAgent demandera clarification",
        )


class LLMIntentClassifier(IntentClassifier):
    """Classifieur V2 : le LLM décide en premier, les regex servent de repli.

    Activé via INTENT_CLASSIFIER=llm. Garanties de robustesse :
    - timeout configurable (défaut 1.5 s) → repli regex au-delà ;
    - réponse LLM invalide ou confiance < 0.6 → repli regex ;
    - cache mémoire sur message normalisé (TTL 24 h) pour éviter de re-payer
      des classifications identiques.
    """

    _CACHE_TTL_S = 86400.0

    def __init__(
        self,
        gateway: "AIGateway",
        fallback: IntentClassifier | None = None,
        timeout_s: float = 1.5,
    ) -> None:
        from app.ai_gateway.base import AIGateway  # noqa: F401 — type hint runtime

        self._gateway = gateway
        self._fallback = fallback or KeywordIntentClassifier()
        self._timeout_s = timeout_s
        self._cache: dict[str, tuple[float, IntentClassification]] = {}

    def classify(self, message: str) -> IntentClassification:
        """Chemin synchrone — utilisé si l'appelant ne peut pas await : repli regex."""
        return self._fallback.classify(message)

    async def aclassify(
        self, message: str, last_intent: str | None = None
    ) -> IntentClassification:
        from app.core.llm_intent import classify_with_llm

        key = " ".join(message.lower().split())[:200]
        cached = self._cache.get(key)
        if cached and (time.monotonic() - cached[0]) < self._CACHE_TTL_S:
            return cached[1]

        try:
            llm_result = await asyncio.wait_for(
                classify_with_llm(self._gateway, message, last_intent),
                timeout=self._timeout_s,
            )
        except Exception as exc:  # noqa: BLE001 — timeout compris, repli regex
            logger.warning("llm_intent_classifier_failed", error=str(exc)[:120])
            llm_result = None

        if llm_result is not None:
            self._cache[key] = (time.monotonic(), llm_result)
            return llm_result
        return self._fallback.classify(message)


class ShadowIntentClassifier(IntentClassifier):
    """Mode shadow : les regex décident, le LLM vote en arrière-plan.

    Chaque divergence regex/LLM est loguée (intent_shadow_divergence) —
    constitue gratuitement un dataset d'entraînement supervisé avant
    d'activer INTENT_CLASSIFIER=llm en production.
    """

    def __init__(
        self,
        gateway: "AIGateway",
        primary: IntentClassifier | None = None,
    ) -> None:
        from app.ai_gateway.base import AIGateway  # noqa: F401

        self._gateway = gateway
        self._primary = primary or KeywordIntentClassifier()

    def classify(self, message: str) -> IntentClassification:
        return self._primary.classify(message)

    async def aclassify(
        self, message: str, last_intent: str | None = None
    ) -> IntentClassification:
        result = self._primary.classify(message)
        asyncio.ensure_future(self._shadow_vote(message, last_intent, result))
        return result

    async def _shadow_vote(
        self, message: str, last_intent: str | None, keyword_result: IntentClassification
    ) -> None:
        from app.core.llm_intent import classify_with_llm

        try:
            llm_result = await classify_with_llm(self._gateway, message, last_intent)
        except Exception:  # noqa: BLE001 — le shadow ne doit jamais impacter
            return
        if llm_result is None:
            return
        if llm_result.intent != keyword_result.intent:
            logger.info(
                "intent_shadow_divergence",
                keyword_intent=keyword_result.intent,
                keyword_agent=keyword_result.selected_agent,
                llm_intent=llm_result.intent,
                llm_agent=llm_result.selected_agent,
                llm_confidence=llm_result.confidence,
                message_preview=message[:80],
            )


# ── Instance par défaut (V1) ────────────────────────────────────────

_default_classifier: IntentClassifier = KeywordIntentClassifier()


def get_intent_classifier() -> IntentClassifier:
    """Retourne le classificateur d'intention actif.

    V1 : retourne toujours KeywordIntentClassifier.
    V2 : pourra retourner LLMIntentClassifier selon la configuration.
    """
    return _default_classifier


def set_intent_classifier(classifier: IntentClassifier) -> None:
    """Définit le classificateur d'intention actif.

    Permet à V2 de remplacer le classificateur sans modifier l'orchestrateur.
    """
    global _default_classifier
    _default_classifier = classifier
    logger.info("intent_classifier_set", classifier=type(classifier).__name__)


def classify_intent(message: str) -> IntentClassification:
    """Classifie l'intention d'un message via le classificateur actif.

    Fonction de compatibilité V1 — délègue au classificateur injecté.
    Permet à l'orchestrateur existant de fonctionner sans modification
    tout en supportant le swap de classificateur pour V2.

    Args:
        message: Texte du message du client/vendeur/partenaire.

    Returns:
        IntentClassification avec l'intention détectée, le niveau de confiance
        et l'agent sélectionné. Si aucune intention n'est détectée, retourne
        "unknown" avec CommercialAgent par défaut (qui demandera clarification).
    """
    return get_intent_classifier().classify(message)


async def classify_intent_async(
    message: str, last_intent: str | None = None
) -> IntentClassification:
    """Version asynchrone de classify_intent — à utiliser dans du code async.

    Permet aux classifieurs V2 (LLM, shadow) de fonctionner sans bloquer
    la boucle d'événements ; avec KeywordIntentClassifier, équivalent à
    classify_intent().
    """
    return await get_intent_classifier().aclassify(message, last_intent)
