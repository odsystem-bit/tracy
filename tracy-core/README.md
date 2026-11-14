# Tracy Core

Orchestrateur IA de Tracy. Construit en FastAPI (Python 3.12+), conforme à `docs/tracy/02-ARCHITECTURE.md`.

**Source de vérité** : `docs/tracy/`. Toute décision de conception doit être cohérente avec ces documents, notamment `07-DEVELOPMENT_RULES.md`.

**Canal principal** : l'application Mantota (Flutter) et le site web. WhatsApp reste un canal de transition et d'acquisition optionnel.

Aucune ligne de code n'est reprise de `whatsapp-bot-legacy/` : ce projet démarre entièrement neuf.

## Architecture

```
Client → Gateway (auth + rate limit) → Tracy Core (orchestrateur LangGraph) → Agents → Tools → Mantota API
```

- **Gateway** : authentification par clé API, rate limiting, correlation ID middleware.
- **Tracy Core** : orchestrateur LangGraph qui classifie l'intention, sélectionne l'agent, gère la mémoire courte.
- **Agents** : unités spécialisées (CommercialAgent, NegotiationAgent, CatalogAgent) avec permissions et autonomie définies.
- **Tools** : point d'entrée unique vers Mantota, registre central avec vérification des permissions.
- **AI Gateway** : abstraction multi-fournisseurs (OpenAI, Anthropic, DeepSeek, Ollama) avec fallback automatique.
- **Mantota Client** : client HTTP async typé avec retry, backoff exponentiel, hiérarchie d'exceptions.
- **Memory** : mémoire courte (Redis en prod, RAM en dev) avec interface abstraite.

## Installation

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Éditer .env avec les vraies clés
```

## Lancer en développement

```bash
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
pytest
```

43 tests couvrent les scénarios T-001 à T-005, la classification d'intention, l'orchestrateur, les permissions des Tools, et la Gateway (auth + rate limiting).

## Structure

```
app/
├── main.py                 # point d'entrée FastAPI (DI, lifecycle, endpoints)
├── config.py               # configuration centralisée (Pydantic Settings)
├── logging_config.py       # logs structurés JSON (structlog) + correlation context
├── gateway/
│   ├── auth.py             # authentification par clé API
│   ├── rate_limit.py       # rate limiting (in-memory, V2: Redis)
│   └── middleware.py       # correlation ID middleware
├── core/
│   ├── orchestrator.py     # orchestrateur LangGraph (classify → execute)
│   ├── intent.py           # classificateur d'intention par mots-clés
│   └── schemas.py          # IncomingMessage, TracyReply, IntentClassification
├── agents/
│   ├── base.py             # BaseAgent abstrait (DI, autonomie, system prompt)
│   ├── commercial_agent.py # vendeur virtuel (recherche, présentation, envoi catalogue)
│   ├── negotiation_agent.py # négociation de prix dans la marge
│   └── catalog_agent.py    # gestion du catalogue (vendeur)
├── tools/
│   ├── base.py             # Tool abstrait, ToolResult, ToolContext
│   ├── registry.py         # registre central + vérification permissions
│   ├── search_products.py  # recherche de produits
│   ├── search_catalog.py   # exploration du catalogue
│   ├── search_store.py     # recherche de boutique
│   └── send_catalog.py     # envoi du catalogue
├── ai_gateway/
│   ├── base.py             # AIProvider abstrait, AIGateway (fallback)
│   ├── factory.py          # factory créant l'AIGateway depuis la config
│   ├── openai_provider.py  # connecteur OpenAI (GPT)
│   ├── anthropic_provider.py # connecteur Anthropic (Claude)
│   ├── deepseek_provider.py  # connecteur DeepSeek
│   └── ollama_provider.py    # connecteur Ollama (local)
├── memory/
│   └── short_term.py       # ShortTermMemory (InMemory + Redis), ConversationMessage
└── mantota_client/
    ├── client.py            # client HTTP async typé (retry, backoff, toutes les endpoints V1)
    ├── exceptions.py        # hiérarchie d'exceptions (MantotaError, NotFound, Auth, Timeout...)
    └── schemas.py           # modèles Pydantic pour toutes les réponses Mantota
```

## État actuel (V1)

- ✅ `CommercialAgent` (recherche produit, présentation, envoi catalogue)
- ✅ `NegotiationAgent` (négociation dans la marge)
- ✅ `CatalogAgent` (gestion catalogue vendeur)
- ✅ `OrderAgent` (créer, suivre, annuler des commandes)
- ✅ `PaymentAgent` (paiements, retraits, wallet, abonnement Tracy)
- ✅ `SupportAgent` (réclamations, suivi, escalade)
- ✅ `CampaignAgent` (campagnes, relances, partenaires)
- ✅ `MemoryAgent` (mémoire longue via Mantota)
- ✅ Tools (18) : search_products, search_catalog, search_store, send_catalog, create_order, cancel_order, track_order, create_payment, get_wallet, request_withdrawal, send_payment_link, get_campaign, search_partner, save_memory, search_memory, update_memory, delete_memory, activate_tracy_subscription
- ✅ Client Mantota complet (commerce, commandes, paiement, marketing, mémoire, abonnement)
- ✅ AI Gateway avec fallback (OpenAI, Anthropic, DeepSeek, Ollama)
- ✅ Mémoire courte (InMemory + Redis) avec ConversationContext enrichi
- ✅ Gateway complète (auth, rate limiting, correlation ID)
- ✅ Orchestrateur LangGraph multi-agents avec classification d'intention
- ✅ Points d'extension (Notifications, Security, Audit, Events)
- ✅ Tests : 140 tests (unitaires + intégration T-001 à T-015 contre API Mantota réelle)
- ⏳ Classification d'intention par IA (V2)
- ⏳ Live Shopping, Livraison, Notifications (V2+)

## Note sur l'API Mantota

Les endpoints de l'API Mantota "bot" (`/api/bot/...`) sont implémentés dans `od-system-staging` (Laravel). Le `mantota_client` est validé contre ces endpoints via les tests d'intégration (`tests/test_integration_mantota.py`).
