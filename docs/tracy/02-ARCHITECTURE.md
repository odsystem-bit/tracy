# Tracy — Architecture

## Objectif

Ce document décrit comment Tracy est construite techniquement, et comment chaque brique communique avec les autres. C'est la source de vérité technique unique : tout autre document technique doit rester cohérent avec celui-ci.

## État actuel vs cible

Le code `tracy-core` est en développement actif. L'ancien bot conversationnel (Node.js/Express, machine à états) est archivé dans `whatsapp-bot-legacy/` — aucune ligne n'est reprise. `tracy-core` est développé entièrement neuf, à partir de ce document.

**V1 terminée** (voir `08-ROADMAP.md` pour le détail) :
- ✅ Gateway (auth, rate limiting, correlation ID)
- ✅ Orchestrateur LangGraph (classification d'intention, routage multi-agents)
- ✅ Agents : CommercialAgent, NegotiationAgent, CatalogAgent, OrderAgent, PaymentAgent, SupportAgent, CampaignAgent, MemoryAgent
- ✅ Tools (28) : search_products, search_catalog, search_store, send_catalog, create_order, cancel_order, track_order, create_payment, get_wallet, request_withdrawal, send_payment_link, get_campaign, search_partner, save_memory, search_memory, update_memory, delete_memory, activate_tracy_subscription, get_shop_config, update_shop_config, search_restaurants, get_restaurant_menu, create_restaurant_order, track_restaurant_order, get_currencies, search_knowledge (RAG)
- ✅ AI Gateway avec fallback (OpenAI, Anthropic, DeepSeek, Ollama)
- ✅ Mémoire courte (InMemory + Redis) avec ConversationContext enrichi
- ✅ Client Mantota complet (tous les endpoints V1)
- ✅ Mémoire longue via Mantota (MemoryAgent + tools save/search/update/delete)
- ✅ Classification d'intention par mots-clés (V1), interface abstraite pour LLM (V2)
- ✅ Points d'extension (Notifications, Security, Audit, Events)
- ✅ Tests : 140 tests passent (unitaires + intégration T-001 à T-015 contre API Mantota réelle)

**Critère de sortie V1** : tous les scénarios de `09-TEST_SCENARIOS.md` passent en staging connectés à l'API Mantota réelle. ✅ Validé en local.

**V2 planifiée** :
- ⏳ Classification d'intention par LLM
- ⏳ Live Shopping, Livraison, Notifications, Security, Audit, Events
- ⏳ Réseaux sociaux, Publication TikTok

**RAG (Retrieval-Augmented Generation) ajouté** :
- ✅ Module `app/rag/` : embeddings (OpenAI text-embedding-3-small), retriever (pgvector)
- ✅ Tool `search_knowledge` (28e tool) — CommercialAgent et SupportAgent uniquement
- ✅ Tables `knowledge_documents` / `knowledge_chunks` côté Mantota (PostgreSQL + pgvector)
- ✅ Endpoints admin CRUD `/api/admin/knowledge/*` (gestion des documents + gaps)
- ✅ Endpoint bot `/bot/knowledge/search` (recherche vectorielle) + `/bot/knowledge/gaps/log` (logging des lacunes)
- ✅ Script d'ingestion `scripts/ingest_knowledge.py` (découpage sémantique + embeddings + upsert)
- ✅ Corpus Bénin : 5 documents draft (quartiers, marchés, paiements, livraison, expressions)
- ✅ Règle fondamentale : le LLM reformule, il ne décide jamais — les chunks RAG sont injectés dans le prompt de reformulation, jamais utilisés pour prendre une décision métier
- ✅ **RAG Correctif** : `classify_relevance` (correct/ambiguous/incorrect par score cosinus, jamais par le LLM), table `knowledge_gaps` (regroupement par similarité cosinus >0.92, passage auto open→suggested au seuil), repli honnête quand incorrect, Admin Panel KnowledgeGaps.jsx

---

## Vue d'ensemble

```
Client
  │
APK Mantota
  │
Gateway
  │
Tracy Core
  │
Agents
  │
Tools
  │
Mantota
  │
Moneroo
  │
Base de données
```

Chaque couche ne connaît que la couche immédiatement inférieure. Aucune couche ne saute une étape.

---

## Les couches

### 1. Client
L'utilisateur final : client, vendeur, partenaire ou livreur. Interagit principalement via l'application Mantota (canal principal) ou le site web. WhatsApp reste un canal de transition et d'acquisition optionnel.

### 2. APK Mantota
L'application mobile Mantota (Flutter). Elle héberge l'interface conversationnelle avec Tracy ainsi que les écrans classiques (catalogue, commandes, portefeuille). C'est le canal principal du produit. Chaque utilisateur possède un compte Mantota. Tous les échanges se font dans la conversation native Mantota.

### 3. Gateway
Point d'entrée unique de toutes les requêtes vers Tracy Core.

Responsabilités :
- Authentification et vérification des tokens.
- Limitation de débit (rate limiting).
- Routage vers le bon service.
- Journalisation des requêtes entrantes.

Aucune requête n'atteint Tracy Core sans passer par la Gateway.

### 4. Tracy Core
Le cerveau orchestrateur. Construit en **FastAPI** (Python 3.12), il :
- reçoit le message ou l'événement,
- charge le contexte (mémoire courte, mémoire longue),
- utilise **LangGraph** pour orchestrer le raisonnement en graphe d'étapes,
- sélectionne les agents pertinents,
- collecte leurs résultats,
- produit la réponse finale.

Tracy Core ne contient aucune logique métier Mantota. Il orchestre uniquement.

### 5. Agents
Des unités spécialisées (voir `03-AGENTS.md`) qui exécutent une mission précise : négocier, gérer une commande, initier un paiement, etc. Chaque agent utilise un ou plusieurs modèles IA et des Tools.

### 6. Tools
Les seules portes d'entrée vers l'action réelle (voir `04-TOOLS.md`). Un agent ne fait jamais d'action directe : il appelle toujours un Tool, qui lui-même appelle une API Mantota.

### 7. Mantota
La plateforme e-commerce (Laravel). Elle contient **toute** la logique métier : catalogue, commandes, boutiques, wallets, campagnes. Mantota est la seule à décider et à exécuter les actions métier.

### 8. Moneroo
Le fournisseur de paiement. Mantota communique avec Moneroo pour l'encaissement, les retraits (payout) et les remboursements. Tracy ne parle jamais directement à Moneroo — toujours via Mantota.

### 9. Base de données
PostgreSQL, exploitée exclusivement par Mantota. Ni Tracy Core, ni les agents, ni les Tools n'ont d'accès direct à la base de données.

---

## Canaux de communication

### Canal principal : Application Mantota + Site web
L'application Mantota (Flutter) et le site web sont les canaux principaux. Les conversations sont natives : le client n'a plus besoin d'utiliser WhatsApp pour communiquer avec les vendeurs. Chaque utilisateur possède un compte Mantota.

### Canal secondaire : WhatsApp (transition et acquisition)
WhatsApp reste un canal de transition et d'acquisition optionnel. Il se place au niveau de la couche **Client**, sans remplacer aucune couche :

```
Client (WhatsApp)
  │
Webhook Meta Cloud API
  │
Gateway
  │
Tracy Core
  │ ...
```

Le webhook WhatsApp n'est qu'un point d'entrée supplémentaire vers la Gateway — il n'a aucune logique propre, contrairement à l'ancien `whatsapp-bot-legacy`. WhatsApp sera progressivement remplacé par les notifications natives de l'application Mantota.

---

## Exemple de bout en bout

Scénario : un client demande "Je veux un téléphone à 100 000 FCFA."

1. **Client** → message reçu via l'**application Mantota** (ou le site web, ou WhatsApp en transition).
2. **Gateway** authentifie la boutique concernée, transmet à **Tracy Core**.
3. **Tracy Core** charge la mémoire courte (Redis) et la mémoire longue pertinente (via Mantota), lance le graphe **LangGraph**.
4. Le graphe identifie une intention de recherche produit → sélectionne **CommercialAgent**.
5. `CommercialAgent` appelle le Tool `search_products` avec un budget maximum.
6. Le Tool `search_products` appelle l'API Mantota, qui interroge **PostgreSQL** et renvoie les produits correspondants.
7. `CommercialAgent` reçoit les résultats, raisonne via l'**AI Gateway** (ex: GPT) pour formuler une réponse naturelle.
8. **Tracy Core** renvoie la réponse à travers la **Gateway** jusqu'au **Client**.

Chaque étape est journalisée avec un même ID de corrélation, permettant de retracer l'intégralité du parcours en cas d'anomalie.

---

## Sécurité

- **Authentification** : chaque requête entrante (APK Mantota, site web, WhatsApp) est vérifiée par la Gateway avant d'atteindre Tracy Core.
- **Isolation multi-tenant** : chaque boutique est identifiée par un `store_id` propagé dans tout l'appel ; aucune requête ne peut accéder aux données d'une autre boutique.
- **Secrets** : les clés (AI Gateway, Mantota, WhatsApp) sont injectées par variables d'environnement, jamais commitées.
- **Validation stricte des entrées** : tout payload est validé par un modèle Pydantic avant traitement (voir `07-DEVELOPMENT_RULES.md`).
- **Aucune donnée sensible en clair dans les logs** (numéros de téléphone masqués, aucune donnée bancaire journalisée).

---

## Résilience et gestion des erreurs

- Chaque appel externe (AI Gateway, Mantota) a un timeout et une politique de retry avec backoff.
- Si un Tool échoue, l'agent reçoit une erreur typée (voir `04-TOOLS.md`) et peut informer honnêtement l'utilisateur plutôt que d'échouer silencieusement.
- Si l'AI Gateway est indisponible pour un fournisseur, il bascule automatiquement sur un fournisseur de repli déclaré.
- Si Mantota est indisponible, Tracy Core répond que le service est momentanément indisponible — elle n'invente jamais un résultat.

---

## Observabilité

- **Logs structurés (JSON)** à chaque étape : Gateway, Tracy Core, Agent, Tool.
- **ID de corrélation unique** propagé de bout en bout pour retracer une conversation complète.
- **Métriques** : temps de réponse par agent, taux d'erreur par Tool, volume de requêtes par fournisseur IA.
- **Traçabilité des décisions** : chaque appel de Tool journalise l'agent appelant, les paramètres, et le résultat (succès/erreur).

---

## Environnements

- **Développement** : Tracy Core local, connecté à un environnement Mantota de staging (`od-system-staging`), IA en mode Ollama local quand possible pour limiter les coûts.
- **Staging** : Tracy Core déployé, connecté à Mantota staging, application Mantota de test, webhook WhatsApp de test optionnel.
- **Production** : Tracy Core déployé, connecté à Mantota production, application Mantota en production, WhatsApp comme connecteur optionnel.

Le canal WhatsApp de production n'est basculé vers `tracy-core` qu'après validation complète des scénarios de `09-TEST_SCENARIOS.md` en staging. Le canal principal reste l'application Mantota.

---

## Structure de dépôt attendue (tracy-core)

```
tracy-core/
├── app/
│   ├── main.py              # point d'entrée FastAPI
│   ├── gateway/              # authentification, rate limiting
│   ├── core/                 # orchestration LangGraph
│   ├── agents/                # un module par agent (voir 03-AGENTS.md)
│   ├── tools/                  # un module par tool (voir 04-TOOLS.md)
│   ├── ai_gateway/            # connecteurs GPT, Claude, DeepSeek, Ollama
│   ├── memory/                 # accès mémoire courte (Redis) / longue (API Mantota)
│   ├── mantota_client/          # client HTTP typé vers l'API Mantota
│   ├── rag/                     # module RAG (embeddings, retriever pgvector)
│   ├── notifications/           # notifications multi-canal (préparé, V2+)
│   ├── security/                # permissions, sessions, chiffrement (préparé, V2+)
│   ├── audit/                   # journal d'audit et traçabilité (préparé, V2+)
│   └── events/                  # EventBus interne (préparé, V2+)
├── scripts/
│   └── ingest_knowledge.py      # script d'ingestion RAG (découpage + embeddings + upsert)
├── tests/
├── pyproject.toml
└── README.md
```

Cette structure respecte la séparation par domaine exigée par `07-DEVELOPMENT_RULES.md` (architecture DDD, aucune dépendance circulaire).

---

## Facturation de Tracy

Tracy n'a **pas de système de facturation propre**. L'abonnement Tracy (accès au bot, quotas, fonctionnalités) est un produit vendu par Mantota, facturé exactement comme tout autre abonnement de la plateforme (ex : badge "Meilleure Boutique").

Concrètement :
- Le solde du vendeur vit dans le **Wallet Mantota** (`get_wallet`, voir `04-TOOLS.md`).
- L'activation ou le renouvellement de l'abonnement Tracy débite ce Wallet et crée une `Transaction` de type `fee`, exactement comme les autres abonnements Mantota.
- Il n'existe qu'**une seule base de vérité pour l'argent** : le Wallet et les Transactions de Mantota. Aucune table de quotas, plans ou facturation séparée ne doit exister côté Tracy Core.
- Les règles de prix, de durée et de quotas des plans Tracy sont configurées dans Mantota (comme `mantota_setting()` pour les autres abonnements), jamais codées en dur dans Tracy Core.

Cette règle est non négociable — voir `07-DEVELOPMENT_RULES.md`.

---

## Modules transverses préparés (V2+)

Les modules suivants sont préparés sous forme d'interfaces et de schémas uniquement. Aucune implémentation n'existe en V1. Ils sont conçus pour être développés progressivement sans casser Tracy Core.

### Notifications (`app/notifications/`)

Système de notifications multi-canal (FCM, APNS, Web Push, Email, SMS, WhatsApp). Interfaces : `NotificationProvider`, `NotificationService`, `NotificationDispatcher`, `NotificationQueue`. 6 providers stub créés. Voir `app/notifications/README.md`.

### Security (`app/security/`)

Gestion des permissions, rôles, sessions, appareils, tokens, chiffrement, secrets et détection de fraude. 8 interfaces abstraites. Règle fondamentale : Tracy ne décide jamais — le `PermissionEngine` vérifie mais Mantota autorise. Voir `app/security/README.md`.

### Audit (`app/audit/`)

Journal d'audit pour traçabilité métier (distinct des logs techniques structlog). 8 types d'événements prédéfinis (connexion, commande, paiement, wallet, outil_ia, conversation, erreur, modification). Interfaces : `AuditLogger`, `AuditRepository`. Voir `app/audit/README.md`.

### Events (`app/events/`)

EventBus interne pour couplage faible entre composants. L'orchestrateur, les agents et les tools publient des événements ; les modules (audit, notifications, security) s'y abonnent. Interfaces : `BaseEvent`, `EventBus`, `EventPublisher`, `EventSubscriber`. Voir `app/events/README.md`.

---

## Composants transverses

### AI Gateway
Point d'accès unique vers les modèles de langage. Il route chaque requête IA vers le fournisseur adapté :

- **GPT** (OpenAI) — raisonnement général, rédaction.
- **Claude** (Anthropic) — analyse longue, tâches nuancées.
- **DeepSeek** — tâches économiques à fort volume.
- **Ollama** — exécution locale de modèles ouverts (Llama, Qwen, Mistral) pour la confidentialité, la latence ou le coût.

L'AI Gateway permet de changer de fournisseur sans modifier le code des agents. Le changement se fait par variable d'environnement (`DEFAULT_AI_PROVIDER`, `FALLBACK_AI_PROVIDER`).

**Fournisseurs prévus (V2)** :
- **Gemini** (Google) — non encore implémenté.
- **Qwen** (Alibaba) — exécutable via Ollama en local ou via API dédiée (V2).
- **Mistral** — exécutable via Ollama en local ou via API dédiée (V2).

Note : Llama, Qwen et Mistral sont des modèles, pas des fournisseurs. Ils s'exécutent via Ollama en local. Une intégration API dédiée (Mistral API, etc.) est envisagée en V2 si le besoin le justifie.

### Classification d'intention

V1 (actuelle) : classification par mots-clés (regex). Les patterns sont ordonnés par spécificité (négociation avant recherche produit, support avant commande, etc.). Les intentions inconnues sont routées vers CommercialAgent qui demande clarification.

⚠️ Limitations V1 :
- ne comprend pas le contexte ni les intentions implicites,
- ne gère pas les messages ambigus ou multi-intentions,
- nécessite un maintien manuel des patterns.

V2 (planifiée) : classification par LLM via l'AI Gateway, capable de comprendre le contexte conversationnel, gérer les intentions multiples, et fournir un score de confiance calibré.

Voir `app/core/intent.py` pour l'implémentation actuelle.

### Redis
Utilisé pour :
- le cache de contexte conversationnel,
- les files d'attente de tâches,
- le stockage temporaire (sessions, OTP, panier en cours).

### PostgreSQL
Base de données relationnelle principale, propriété exclusive de Mantota. Stocke les données durables : utilisateurs, produits, commandes, paiements, mémoires longues.

**Extension pgvector** : activée pour le système RAG. Les tables `knowledge_documents` et `knowledge_chunks` stockent les documents de connaissance et leurs embeddings (1536 dimensions, OpenAI text-embedding-3-small). La recherche sémantique utilise la distance cosinus via l'opérateur `<=>` de pgvector, avec un index IVFFlat pour les performances.

**Règle RAG** : les chunks récupérés sont injectés dans le prompt de reformulation du LLM. Le LLM reformule, il ne décide jamais. Aucun chunk RAG ne déclenche d'action métier (prix, commande, paiement).

**RAG Correctif** : la pertinence est classée numériquement (score cosinus) — jamais par le LLM. Quand le score est trop bas (`incorrect`), Tracy ne fabrique pas de réponse : elle logge la lacune dans `knowledge_gaps` (fire-and-forget) et produit un repli honnête. Les lacunes récurrentes (≥ 5 occurrences) passent en `suggested` pour signaler à l'admin qu'un document manque. Aucune création automatique de document — uniquement via action admin explicite.

---

## Comment tout communique

1. Le **Client** envoie un message via l'**APK Mantota** (ou WhatsApp).
2. La **Gateway** authentifie et route la requête vers **Tracy Core**.
3. **Tracy Core** charge le contexte depuis Redis/PostgreSQL et lance un graphe **LangGraph**.
4. Le graphe sélectionne un ou plusieurs **Agents**.
5. Chaque Agent raisonne via l'**AI Gateway** (GPT, Claude, DeepSeek ou Ollama).
6. Si une action est nécessaire, l'Agent appelle un **Tool**.
7. Le Tool appelle l'API de **Mantota**.
8. Mantota exécute la logique métier, éventuellement en appelant **Moneroo** pour le paiement.
9. Mantota persiste le résultat en **base de données**.
10. Le résultat remonte : Mantota → Tool → Agent → Tracy Core → Gateway → APK Mantota → Client.

Toute communication est asynchrone et journalisée à chaque étape.

---

## Règles d'architecture

- Aucune couche ne peut sauter une étape (ex : un Agent ne peut jamais appeler Moneroo directement).
- Tracy Core ne stocke aucune donnée métier durable — cette responsabilité appartient à Mantota.
- Toute communication inter-couches est asynchrone.
- Chaque appel est traçable (ID de corrélation) de bout en bout.
