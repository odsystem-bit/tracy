# Tracy — Tools

## Objectif

Ce document liste tous les outils (Tools) disponibles pour les agents de Tracy. Un Tool est la seule façon pour un agent d'agir sur le monde réel — toujours via l'API Mantota, jamais directement sur une base de données ou un service externe.

Ce document est celui qui grandira le plus au fil du temps : chaque nouvelle capacité de Tracy doit d'abord être déclarée ici.

Pour chaque outil : **description**, **paramètres**, **réponse**, **erreurs**, **permissions**.

---

## Contrat standard d'un Tool

Tout Tool respecte la même enveloppe de réponse, quel que soit le résultat :

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "correlation_id": "..."
}
```

En cas d'échec :

```json
{
  "success": false,
  "data": null,
  "error": { "code": "OUT_OF_STOCK", "message": "..." },
  "correlation_id": "..."
}
```

Chaque Tool est un appel HTTP typé (Pydantic) vers un endpoint de l'API Mantota. Aucun Tool ne contient de logique métier : il valide les paramètres, appelle Mantota, retransmet le résultat.

---

## Commerce

### search_products
**Description** : Recherche des produits selon des critères (nom, catégorie, prix, disponibilité).
**Paramètres** : `query` (str), `store_id` (str, optionnel), `min_price` (float, optionnel), `max_price` (float, optionnel), `limit` (int, optionnel).
**Réponse** : liste de produits (id, nom, prix, stock, image).
**Erreurs** : `NO_RESULTS`, `INVALID_QUERY`.
**Permissions** : CommercialAgent, CatalogAgent, NegotiationAgent.

### search_catalog
**Description** : Explore le catalogue complet d'une boutique (catégories, collections).
**Paramètres** : `store_id` (str), `category` (str, optionnel).
**Réponse** : arborescence du catalogue.
**Erreurs** : `STORE_NOT_FOUND`.
**Permissions** : CommercialAgent, CatalogAgent, NegotiationAgent, CampaignAgent.

### search_store
**Description** : Recherche une boutique par nom, secteur ou localisation.
**Paramètres** : `query` (str), `city` (str, optionnel).
**Réponse** : liste de boutiques (id, nom, note, ville).
**Erreurs** : `NO_RESULTS`.
**Permissions** : CommercialAgent, CatalogAgent.

---

## Commandes

### create_order
**Description** : Crée une commande à partir d'un produit confirmé.
**Paramètres** : `vendor_id` (str), `product_id` (str), `customer_name` (str), `customer_phone` (str), `customer_whatsapp` (str), `country` (str), `city` (str), `customer_email` (str, optionnel), `landmark_indication` (str, optionnel).
**Réponse** : commande créée (order_id, reference, payment_url, tracking_url, tracking_token, delivery_pin, amount).
**Erreurs** : `OUT_OF_STOCK`, `INVALID_PRODUCT`, `INVALID_CUSTOMER`, `STORE_UNAVAILABLE`.
**Permissions** : OrderAgent.

### cancel_order
**Description** : Annule une commande existante si elle n'est pas encore expédiée.
**Paramètres** : `order_id` (str), `reason` (str).
**Réponse** : confirmation d'annulation, statut du remboursement éventuel.
**Erreurs** : `ORDER_NOT_CANCELLABLE`, `ORDER_NOT_FOUND`.
**Permissions** : OrderAgent, SupportAgent.

### track_order
**Description** : Retourne le statut actuel d'une commande.
**Paramètres** : `order_id` (str).
**Réponse** : statut, historique des étapes, date estimée de livraison.
**Erreurs** : `ORDER_NOT_FOUND`.
**Permissions** : OrderAgent, SupportAgent, DeliveryAgent.

---

## Paiement

### create_payment
**Description** : Initie un paiement pour une commande via Moneroo (par Mantota).
**Paramètres** : `order_id` (str), `amount` (float), `currency` (str), `method` (str).
**Réponse** : lien de paiement ou statut, référence de transaction.
**Erreurs** : `PAYMENT_METHOD_UNAVAILABLE`, `AMOUNT_MISMATCH`, `GATEWAY_ERROR`.
**Permissions** : PaymentAgent.

### get_wallet
**Description** : Retourne le solde et l'historique récent du portefeuille d'un vendeur ou partenaire.
**Paramètres** : `user_id` (str).
**Réponse** : solde disponible, solde en attente, dernières transactions.
**Erreurs** : `WALLET_NOT_FOUND`.
**Permissions** : PaymentAgent, SupportAgent.

### request_withdrawal
**Description** : Soumet une demande de retrait de fonds depuis le wallet.
**Paramètres** : `user_id` (str), `amount` (float), `payout_method` (str), `phone` (str), `country` (str).
**Réponse** : statut de la demande, référence de retrait.
**Erreurs** : `INSUFFICIENT_BALANCE`, `PAYOUT_METHOD_UNSUPPORTED`, `INVALID_PHONE`.
**Permissions** : PaymentAgent.

### send_payment_link
**Description** : Envoie un lien de paiement au client via le canal de conversation.
**Paramètres** : `order_id` (str), `channel` (str).
**Réponse** : confirmation d'envoi.
**Erreurs** : `LINK_GENERATION_FAILED`.
**Permissions** : PaymentAgent, CommercialAgent.

---

## Marketing & Partenaires

### get_campaign
**Description** : Retourne les détails ou performances d'une campagne.
**Paramètres** : `campaign_id` (str).
**Réponse** : statut, audience, performance (vues, clics, conversions).
**Erreurs** : `CAMPAIGN_NOT_FOUND`.
**Permissions** : CampaignAgent, NegotiationAgent.

### search_partner
**Description** : Recherche un partenaire par nom ou identifiant de code de parrainage.
**Paramètres** : `query` (str).
**Réponse** : profil du partenaire, commissions cumulées.
**Erreurs** : `PARTNER_NOT_FOUND`.
**Permissions** : CampaignAgent.

### send_catalog
**Description** : Envoie le catalogue (ou une sélection) au client ou à un partenaire.
**Paramètres** : `store_id` (str), `product_ids` (list, optionnel), `channel` (str).
**Réponse** : confirmation d'envoi.
**Erreurs** : `CATALOG_EMPTY`.
**Permissions** : CommercialAgent, CampaignAgent.

---

## Création de boutique (V2)

### create_store
**Description** : Crée une boutique guidée par Tracy (Store Creation Flow).
**Paramètres** : `vendor_id` (str), `shop_type` (str : `physical` | `online` | `both`), `name` (str), `description` (str, optionnel), `gps_lat` (float, optionnel — automatique), `gps_lng` (float, optionnel — automatique), `facade_photo` (str, optionnel — URL), `address` (str, optionnel), `hours` (dict, optionnel), `delivery_zones` (list, optionnel).
**Réponse** : boutique créée (id, type, statut, store_score initial).
**Erreurs** : `INVALID_SHOP_TYPE`, `GPS_REQUIRED`, `STORE_ALREADY_EXISTS`.
**Permissions** : CatalogAgent.

> Le vendeur ne saisit jamais latitude ni longitude. Le GPS est lancé automatiquement par l'application Mantota et transmis au Tool.

---

## Store Location & Trust (V2)

### search_nearby_stores
**Description** : Recherche des boutiques proches par GPS ou adresse.
**Paramètres** : `lat` (float, optionnel), `lng` (float, optionnel), `radius_km` (float, optionnel), `query` (str, optionnel).
**Réponse** : liste de boutiques avec distance, badges de confiance, Store Score.
**Erreurs** : `NO_RESULTS`, `GPS_REQUIRED`.
**Permissions** : CommercialAgent, CatalogAgent.

### get_store_trust
**Description** : Retourne les badges de confiance et le statut de vérification d'une boutique.
**Paramètres** : `store_id` (str).
**Réponse** : badges (GPS vérifié, photo de façade, boutique vérifiée), statut de vérification.
**Erreurs** : `STORE_NOT_FOUND`.
**Permissions** : CommercialAgent, CatalogAgent, SupportAgent.

> Le Store Score est interne. Le client ne voit jamais une note. Il voit uniquement des badges. Le critère "temps moyen de réponse" est supprimé car Tracy répond 24h/24.

---

## Livraison (Bientôt)

### assign_delivery
**Description** : Assigne une commande confirmée à un livreur disponible.
**Paramètres** : `order_id` (str), `zone` (str).
**Réponse** : livreur assigné, délai estimé.
**Erreurs** : `NO_DELIVERY_AVAILABLE`.
**Permissions** : DeliveryAgent.

---

## Mémoire

### save_memory
**Description** : Enregistre durablement une information validée (voir critères dans `06-MEMORY.md`).
**Paramètres** : `scope` (str : `client`|`store`|`conversation`), `entity_id` (str), `key` (str), `value` (str).
**Réponse** : confirmation d'enregistrement, identifiant de la mémoire.
**Erreurs** : `INVALID_SCOPE`, `NOT_CONFIRMED`.
**Permissions** : MemoryAgent.

### search_memory
**Description** : Recherche une information mémorisée pertinente pour le contexte courant.
**Paramètres** : `scope` (str), `entity_id` (str), `query` (str, optionnel).
**Réponse** : liste des entrées de mémoire correspondantes.
**Erreurs** : `NOT_FOUND`.
**Permissions** : MemoryAgent (consulté pour tous les autres agents via Tracy Core).

### update_memory
**Description** : Met à jour une information mémorisée existante.
**Paramètres** : `memory_id` (str), `value` (str).
**Réponse** : confirmation de mise à jour.
**Erreurs** : `MEMORY_NOT_FOUND`.
**Permissions** : MemoryAgent.

### delete_memory
**Description** : Supprime une information mémorisée (droit à l'oubli, expiration).
**Paramètres** : `memory_id` (str), `reason` (str).
**Réponse** : confirmation de suppression.
**Erreurs** : `MEMORY_NOT_FOUND`.
**Permissions** : MemoryAgent.

---

## Abonnement Tracy (facturation unifiée)

### activate_tracy_subscription
**Description** : Active ou renouvelle l'abonnement Tracy pour un vendeur, en débitant son Wallet Mantota (même mécanisme que les autres abonnements Mantota, voir `02-ARCHITECTURE.md`).
**Paramètres** : `vendor_id` (str), `plan` (str).
**Réponse** : statut de l'abonnement, date d'expiration, référence de transaction.
**Erreurs** : `INSUFFICIENT_BALANCE`, `PLAN_NOT_AVAILABLE`.
**Permissions** : PaymentAgent.

Aucun autre mécanisme de facturation Tracy n'existe. Ce Tool appelle le même endpoint Mantota que les abonnements Ambassadeur/Meilleure Boutique.

---

## RAG (Retrieval-Augmented Generation)

### search_knowledge
**Description** : Recherche sémantique dans la base de connaissances RAG (quartiers, marchés, moyens de paiement, procédures, FAQ). Utilise pgvector sur PostgreSQL avec embeddings OpenAI text-embedding-3-small (1536 dimensions). Le résultat est injecté dans le prompt de reformulation du LLM pour enrichir la réponse avec du contexte local.

**RAG Correctif** : la pertinence est classée numériquement (score cosinus), jamais par le LLM :
- `correct` (score ≥ 0.85) : chunks utilisés normalement.
- `ambiguous` (score ≥ 0.6) : chunks utilisés avec une note de prudence en amont du contexte.
- `incorrect` (score < 0.6 ou liste vide) : aucun chunk retourné, un contexte de repli honnête est injecté ("AUCUNE INFORMATION FIABLE TROUVÉE"), et la lacune est loggée en arrière-plan (fire-and-forget) via `POST /bot/knowledge/gaps/log`.

**Paramètres** : `query` (str), `country_id` (int, optionnel — filtrage par pays, fallback sur documents globaux si null), `category` (str, optionnel — ex: "benin_marches", "procedures", "support_faq"), `top_k` (int, optionnel — défaut 5).
**Réponse** : `relevance` ("correct"/"ambiguous"/"incorrect") + liste de chunks (id, content, score, title, category) + `formatted_context` (texte prêt à injecter dans le prompt).
**Erreurs** : `INVALID_QUERY`.
**Permissions** : CommercialAgent, SupportAgent.

> **Règle fondamentale** : le LLM reformule, il ne décide jamais. Les chunks récupérés par ce tool sont injectés dans le prompt de reformulation finale. Ils ne déclenchent jamais d'action métier (prix, commande, paiement). OrderAgent et PaymentAgent n'ont pas accès à ce tool — ils exécutent des actions transactionnelles, ils ne cherchent pas de contexte.

### Gestion des connaissances (côté Mantota)

Les documents de connaissance sont gérés via les endpoints admin :
- `GET /api/admin/knowledge/documents` — liste paginée (filtres : status, category, country_id)
- `POST /api/admin/knowledge/documents` — crée un document (statut `draft` par défaut)
- `PUT /api/admin/knowledge/documents/{id}` — modifie (repasse en `draft` si contenu modifié sur un `approved`)
- `PATCH /api/admin/knowledge/documents/{id}/status` — change le statut (`draft` → `pending` → `approved` → `archived`)
- `DELETE /api/admin/knowledge/documents/{id}` — supprime (cascade sur les chunks)
- `POST /api/admin/knowledge/documents/{id}/chunks` — upsert des chunks avec embeddings (utilisé par le script d'ingestion)
- `GET /api/admin/knowledge/gaps` — liste des lacunes de connaissance (triée par occurrence_count desc, filtrable par status/country_id/category_guess)
- `PATCH /api/admin/knowledge/gaps/{id}` — change le statut d'une lacune (open/suggested/resolved/ignored) + resolved_document_id optionnel

L'indexation (calcul des embeddings) se fait uniquement lors du passage à `approved`, via le script `scripts/ingest_knowledge.py` côté Tracy Core.

### Script d'ingestion (`scripts/ingest_knowledge.py`)

Le script :
1. Récupère le document `approved` via l'API bot Mantota.
2. Découpe le contenu en chunks sémantiques (par sections `---`, titres `#`, paragraphes, phrases — pas de découpage à taille fixe arbitraire).
3. Génère les embeddings via OpenAI `text-embedding-3-small` (batch).
4. Upsert les chunks dans `knowledge_chunks` via `POST /bot/knowledge/documents/{id}/chunks`.

Idempotent : relancer sur le même document ne duplique pas les chunks (delete + insert par `document_id`).

Usage :
```bash
python scripts/ingest_knowledge.py --document-id 1
python scripts/ingest_knowledge.py --all-approved
```

### RAG Correctif — Knowledge Gaps

Quand Tracy ne trouve pas d'information fiable (relevance = "incorrect"), la requête est automatiquement enregistrée dans la table `knowledge_gaps` :
- `POST /bot/knowledge/gaps/log` — reçoit query_text, query_embedding, country_id, category_guess. Cherche un gap existant par similarité cosinus (seuil > 0.92 = même lacune) : si trouvé, incrémente occurrence_count ; sinon crée un nouveau gap.
- Quand `occurrence_count` atteint `KNOWLEDGE_GAP_THRESHOLD` (configurable, défaut 5), le gap passe automatiquement de `open` à `suggested`.
- **Jamais de passage automatique à `resolved` ou `approved`** — uniquement via action admin explicite.
- L'admin peut consulter, filtrer, et changer le statut des gaps depuis l'Admin Panel (page Knowledge Gaps).

---

## Règles générales des Tools

- Chaque Tool possède un nom unique, une description, des permissions déclarées et un résultat toujours structuré (succès ou erreur typée).
- Aucun Tool n'accède directement à la base de données : chaque Tool appelle l'API Mantota.
- Chaque exécution de Tool est journalisée (agent appelant, paramètres, résultat, durée).
- Un Tool ne modifie jamais de règle métier : il exécute ce que Mantota autorise.
