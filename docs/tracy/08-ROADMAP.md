# Tracy — Roadmap

## Objectif

Ce document liste ce que Tracy fait aujourd'hui, ce qui vient ensuite, et ce qui est volontairement mis de côté pour l'instant. Aucun détail technique ici — uniquement des fonctionnalités et leur horizon.

---

## Vision du produit

Mantota n'est plus une plateforme qui utilise principalement WhatsApp. Mantota devient une plateforme de commerce conversationnel dont le canal principal est l'application Mantota et le site web. WhatsApp reste un canal de transition, d'acquisition et optionnel.

L'APK Mantota remplace progressivement WhatsApp. Chaque utilisateur possède un compte Mantota. Tous les échanges se font dans la conversation native Mantota.

Tracy est le cœur de l'expérience : le client, le vendeur, le partenaire et le livreur discutent avec Tracy. La conversation devient l'interface principale.

---

## État réel (audit)

`tracy-core` V1 est **terminée**. Les 8 agents, les 28 tools, la mémoire conversationnelle enrichie, la classification d'intention extensible et les points d'extension futurs sont implémentés. 287 tests passent, 0 régression.

### V1 — Terminée ✅

- ✅ **Gateway** — authentification par clé API, rate limiting (in-memory), middleware correlation ID.
- ✅ **Orchestrateur** — LangGraph (classify → execute), routage multi-agents, mémoire courte + contexte de conversation enrichi.
- ✅ **CommercialAgent** — recherche produit, présentation, envoi catalogue, prompt de vente enrichi (AI_BEHAVIOR.md).
- ✅ **NegotiationAgent** — négociation dans la marge, contre-offre, prompt de négociation enrichi.
- ✅ **CatalogAgent** — gestion catalogue vendeur, alertes stock, prompt catalogue enrichi.
- ✅ **OrderAgent** — créer, suivre, annuler des commandes, prompt enrichi.
- ✅ **PaymentAgent** — paiements, retraits, wallet, abonnement Tracy, prompt enrichi.
- ✅ **SupportAgent** — réclamations, suivi, escalade, prompt enrichi (empathie + escalade).
- ✅ **CampaignAgent** — campagnes, relances, partenaires, prompt enrichi (relance sans pression).
- ✅ **MemoryAgent** — mémoire longue via Mantota, prompt enrichi (confidentialité).
- ✅ **Tools (28)** — search_products, search_catalog, search_store, send_catalog, create_order, cancel_order, track_order, create_payment, get_wallet, request_withdrawal, send_payment_link, get_campaign, search_partner, save_memory, search_memory, update_memory, delete_memory, activate_tracy_subscription, get_shop_config, update_shop_config, search_restaurants, get_restaurant_menu, create_restaurant_order, track_restaurant_order, get_currencies, search_knowledge (RAG).
- ✅ **AI Gateway** — OpenAI, Anthropic, DeepSeek, Ollama avec fallback automatique.
- ✅ **Client Mantota** — tous les endpoints V1 (commerce, commandes, paiement, marketing, mémoire, abonnement).
- ✅ **Mémoire courte** — InMemory (dev) + Redis (prod), interface abstraite, `ConversationContext`.
- ✅ **Classification d'intention** — `KeywordIntentClassifier` (V1) + interface abstraite pour LLM (V2).
- ✅ **Points d'extension** — interfaces abstraites pour Notifications, Contracts, Livraison, Content, Live Shopping + `ExtensionRegistry`.
- ✅ **Tests** — 287 tests : unitaires + intégration + RAG (embeddings, retriever, tool, ingestion) + RAG Correctif (classify_relevance, gap logging, tool incorrect/ambiguous).
- ✅ **Documentation** — `05-AI_BEHAVIOR.md` (22 sections), `REPORT_V1_FINAL.md`.
- ✅ **RAG (Retrieval-Augmented Generation)** — module `app/rag/` (embeddings OpenAI text-embedding-3-small, retriever pgvector), tool `search_knowledge` (CommercialAgent + SupportAgent), tables `knowledge_documents`/`knowledge_chunks` côté Mantota, endpoints admin CRUD, script d'ingestion sémantique, corpus Bénin (5 documents draft). Règle : le LLM reformule, il ne décide jamais.
- ✅ **RAG Correctif (Corrective RAG)** — classification de pertinence numérique (`classify_relevance` : correct/ambiguous/incorrect par score cosinus, jamais par le LLM), table `knowledge_gaps` (logging des requêtes sans réponse fiable, regroupement par similarité cosinus >0.92, passage auto open→suggested au seuil), endpoints admin + bot, Admin Panel KnowledgeGaps.jsx. Repli honnête quand incorrect ("je ne suis pas sûre" / escalade).

### Critère de sortie V1
La V1 code est terminée. Le critère de sortie restant est : tous les scénarios de `09-TEST_SCENARIOS.md` passent en environnement de staging, connectés à l'API Mantota réelle, sans aucune donnée dupliquée hors Mantota. ✅ Validé en local.

---

## Nouvelle priorité produit

La priorité n'est plus le canal WhatsApp. La priorité devient :

1. **Mantota API** — maintenir et enrichir l'API backend (Laravel + PostgreSQL)
2. **Tracy Core** — ✅ terminée, prête pour l'intégration
3. **Application Mantota** (Flutter) — le canal principal du produit
4. **Connexion Tracy + APK** — intégration de Tracy dans l'application Mantota
5. **Notifications natives** — notifications de l'application Mantota (paiement, commandes, contrats, rappels, relances)
6. **Contracts** — module de paiements échelonnés et contrats
7. **Store Location & Trust** — géolocalisation, Store Score, badges de confiance
8. **WhatsApp** — connecteur supplémentaire optionnel (transition et acquisition)

---

## Version 2 (V2)

⏳ **Application Mantota (Flutter)** — le canal principal. Remplace progressivement WhatsApp. Conversations natives, compte Mantota pour chaque utilisateur.
⏳ **Connexion Tracy + APK** — intégration de Tracy Core dans l'application Mantota. Le client, le vendeur, le partenaire discutent avec Tracy via l'APK.
⏳ **Notifications natives** — notifications de l'application Mantota remplaçant progressivement les notifications WhatsApp (paiement, commandes, contrats, rappels, relances).
⏳ **Store Creation Flow** — parcours conversationnel de création de boutique guidé par Tracy (voir `docs/mantota/11-STORE_CREATION_FLOW.md`). Boutiques physiques, en ligne, ou hybrides. GPS automatique, photo de façade, horaires, zones de livraison.
⏳ **Store Location & Trust** — module Mantota de géolocalisation et confiance (voir `docs/mantota/10-STORE_LOCATION_AND_TRUST.md`). Recherche de boutiques proches, carte, Store Score interne, badges de confiance, vérification GPS.
⏳ **Store Score** — score interne (non visible par le client). Badges visibles uniquement. Critères : GPS vérifié, photo de façade, boutique vérifiée, informations complètes, catalogue à jour, respect des engagements, satisfaction client, ancienneté, disponibilité des produits, participation à l'écosystème. Le critère "temps moyen de réponse" est supprimé car Tracy répond 24h/24.
⏳ **Contracts** — module Mantota de paiements échelonnés et contrats (voir `docs/mantota/09-CONTRACTS.md`). Paiement comptant, réservation, paiement échelonné. Tracy explique les contrats, Mantota les génère.
⏳ **Classification d'intention par LLM** — Remplacement du classificateur par mots-clés (interface `IntentClassifier` déjà prête).
⏳ **Live Shopping** — Vente en direct assistée par Tracy pendant une diffusion live.
⏳ **Réseaux sociaux** — Présence et réponse automatisée sur d'autres canaux (Instagram, Facebook).
⏳ **Publication TikTok** — Génération et publication automatisée de contenu produit.
⏳ **Livraison** — Activation complète du rôle Livreur et de `DeliveryAgent`.
⏳ **Notifications providers** — Implémentation des providers FCM, APNS, Web Push, Email, SMS.
⏳ **Security** — Implémentation de PermissionEngine, SessionManager, TokenManager, EncryptionService.
⏳ **Audit** — Implémentation de AuditLogger et AuditRepository (via Mantota).
⏳ **Events** — Implémentation de InMemoryEventBus puis RedisEventBus.

---

## Version 3 (V3)

⏳ Agents vocaux — Interaction par la voix, appels entrants et sortants.
⏳ IA locale — Exécution de modèles en local (Ollama) pour davantage de confidentialité et de rapidité.
⏳ Assistant vidéo — Génération et présentation de contenu vidéo produit.
⏳ FraudDetector — Détection de fraude par règles + ML.
⏳ WhatsApp Notifications — Provider WhatsApp Business Cloud API (connecteur optionnel).
⏳ RabbitMQ EventBus — File persistante avec retry et dead-letter queue.

---

## Ce qui est volontairement reporté

- Marketplace IA multi-fournisseurs avancée.
- Analyse concurrentielle automatisée.
- Vision avancée (reconnaissance d'image produit complexe).
- Automatisation complète des publicités sans validation humaine.

Ces fonctionnalités ne sont pas abandonnées — elles sont simplement hors périmètre tant que les fondations (V1 + APK Mantota) ne sont pas stables et éprouvées en production.
