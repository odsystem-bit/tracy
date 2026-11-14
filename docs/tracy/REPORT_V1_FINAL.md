# Tracy Core V1 — Rapport Final

## 1. Documents mis à jour

| Document | Description |
|---|---|
| `docs/tracy/05-AI_BEHAVIOR.md` | Document de référence principal. Passé de 15 à 22 sections détaillées : personnalité, ton, vocabulaire interdit/privilégié, accueil, découverte du besoin, conseils, vente, persuasion, négociation, objections, refus, relances, fidélisation, recommandations, promotions, suivi client, support, émotions, comportements interdits, passage au vendeur humain, limites de Tracy, comportement selon profil, prompts de référence. |
| `docs/mantota/09-CONTRACTS.md` | Spécification fonctionnelle du futur module Contracts (créé lors de la session précédente). |

## 2. Agents améliorés

Les 8 agents ont vu leur system prompt enrichi avec les règles du `05-AI_BEHAVIOR.md` :

| Agent | Améliorations |
|---|---|
| **CommercialAgent** | Vocabulaire interdit/privilégié, logique de vente (comprendre→proposer→rassurer→conclure), max 3 produits, urgence fondée, tutoiement, phrases courtes. |
| **NegotiationAgent** | Règles de négociation (valoriser, contre-offre, alternatives), vocabulaire interdit, refus de double négociation, acceptation du refus final. |
| **CatalogAgent** | Ton collègue de confiance, alertes proactives, confirmation pour actions destructives, vocabulaire interdit. |
| **OrderAgent** | Vocabulaire privilégié (« Je te le mets de côté ? »), confirmation systématique, interdiction de promettre un délai, vocabulaire interdit. |
| **PaymentAgent** | Sécurité avant vitesse, rassurance Moneroo, interdiction stockage données bancaires, vocabulaire interdit. |
| **SupportAgent** | Règles d'empathie (une seule expression suffit), reformulation, escalade transparente, interdiction excuses excessives, face à client agressif. |
| **CampaignAgent** | Règles de relance (aide potentielle, max 2 relances, pas de pression), règles partenaire, vocabulaire interdit (ton agressif proscrit). |
| **MemoryAgent** | Règles de mémorisation (utile, durable, fiable, confirmée), confidentialité, droit à l'oubli, isolation par boutique, vocabulaire interdit. |

## 3. Tests ajoutés

Fichier : `tests/test_business_scenarios.py` — **29 nouveaux tests**.

### Scénarios métier (17 tests)
- Client cherche un produit
- Client négocie un prix
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

### Tests de mémoire conversationnelle (3 tests)
- Contexte sauvegardé après chaque message (last_agent, last_intent)
- Contexte effaçable
- Historique préservé entre les messages

### Tests de classification d'intention (5 tests)
- Reconnaissance produit/négociation/support/inconnu
- Swap de classificateur via `set_intent_classifier`

### Tests des points d'extension (3 tests)
- Registre vide en V1
- Enregistrement d'une extension
- Refus de doublon

### Tests des system prompts enrichis (5 tests)
- CommercialAgent : vocabulaire interdit présent
- NegotiationAgent : règles de négociation présentes
- SupportAgent : règles d'empathie présentes
- CampaignAgent : règles de relance présentes
- Tous les agents : section VOCABULAIRE INTERDIT + référence "chatbot"

**Résultat : 118 tests passent (89 existants + 29 nouveaux), 0 régression.**

## 4. Comportements ajoutés à Tracy

### Vocabulaire & ton
- Vocabulaire interdit formalisé dans tous les agents (« En tant que IA », « Comment puis-je vous aider », listes à puces, etc.)
- Vocabulaire privilégié (tutoiement, phrases courtes, transitions naturelles)
- Max 3-4 phrases par réponse (sauf explication nécessaire)

### Mémoire conversationnelle enrichie
- `ConversationContext` : produit évoqué, préférences détectées, résumé, dernier agent, dernière intention
- Sauvegarde automatique du contexte après chaque message dans l'orchestrateur
- Effaçable via `clear()` (historique + contexte)

### Classification d'intention préparable pour V2
- `IntentClassifier` (interface abstraite) + `KeywordIntentClassifier` (V1)
- `get_intent_classifier()` / `set_intent_classifier()` pour swap V2 sans modification de l'orchestrateur
- `classify_intent()` délègue au classificateur injecté (compatibilité V1)

### Points d'extension futurs
- `ExtensionRegistry` : registre vide en V1, prêt pour V2+
- Interfaces abstraites : `NotificationSender`, `ContractNotifier`, `DeliveryTracker`, `ContentGenerator`, `LiveShoppingHandler`
- Aucune implémentation — uniquement les contrats d'extension

## 5. Optimisations réalisées

- **Orchestrateur** : charge et sauvegarde le contexte de conversation à chaque message
- **Mémoire courte** : `InMemoryShortTermMemory` et `RedisShortTermMemory` supportent tous deux `get_context` / `update_context`
- **Intent** : refactoring sans casser l'API existante (`classify_intent` reste compatible)

## 6. Éléments reportés à la V2

| Élément | Raison |
|---|---|
| Classification LLM des intentions | Nécessite calibration et tests approfondis — V1 utilise regex |
| Implémentation des points d'extension (Notifications, Contracts, Livraison, etc.) | Interfaces définies, implémentation reportée |
| Mémoire longue (PostgreSQL via Mantota) | Endpoints Mantota définis, MemoryAgent implémenté, mais données côté Mantota |
| Résumé automatique des conversations longues | Mécanisme préparé dans `ConversationContext.conversation_summary`, implémentation reportée |
| Mémoire d'apprentissage (habitudes de langage) | Documenté dans `06-MEMORY.md`, implémentation reportée |
| Live Shopping | Interface définie, implémentation V3+ |

## 7. Vérification finale (ÉTAPE 7)

- **Rôles** : chaque agent respecte son rôle documenté (CommercialAgent = vente, NegotiationAgent = négociation, etc.)
- **Permissions Tools** : vérifié — 18 tools, permissions correctes pour chaque agent
- **Logique métier** : aucun agent ne contient de calcul de prix, remise, marge ou décision métier — tout passe par Mantota via les Tools
- **Indépendance AI provider** : aucun agent n'importe un provider spécifique — tous utilisent `AIGateway` abstraite
- **Architecture** : aucune modification de l'architecture, aucun nouveau dossier, aucune nouvelle dépendance

---

**Tracy Core V1 est stable, cohérente et prête pour l'intégration avec Mantota.**

---

## 8. Vision produit (mise à jour)

Mantota n'est plus une plateforme qui utilise principalement WhatsApp. Mantota devient une plateforme de commerce conversationnel dont le canal principal est l'application Mantota et le site web. WhatsApp reste un canal de transition, d'acquisition et optionnel.

L'APK Mantota remplace progressivement WhatsApp. Chaque utilisateur possède un compte Mantota. Tous les échanges se font dans la conversation native Mantota.

Tracy est le cœur de l'expérience : le client, le vendeur, le partenaire et le livreur discutent avec Tracy. La conversation devient l'interface principale.

### Nouvelle priorité (voir `08-ROADMAP.md`)

1. Mantota API — ✅ opérationnelle en local (PostgreSQL)
2. Tracy Core — ✅ V1 terminée (140 tests)
3. Application Mantota (Flutter) — ⏳ canal principal à développer
4. Connexion Tracy + APK — ⏳ intégration Tracy dans l'APK
5. Notifications natives — ⏳ notifications de l'application Mantota
6. Contracts — ⏳ paiements échelonnés et contrats
7. Store Location & Trust — ⏳ géolocalisation, Store Score, badges de confiance
8. WhatsApp — connecteur optionnel (transition et acquisition)
