# TRACY — Plan d'Entraînement Complet

> Objectif : Préparer Tracy à répondre à TOUTES les éventualités possibles sur web et mobile.
> Statut : En cours
> Dernière mise à jour : 4 octobre 2026

## État d'avancement (oct. 2026)

Les priorités P1–P4 du plan initial sont couvertes à ~99% : recherche avancée,
gestion conversationnelle, restaurant/campagne/vendeur, multi-pays (28 tools,
`get_currencies`), vision (module complet, `compute-embedding` nécessite torch — V2),
audio reporté V2 (WebRTC). Mémoire web sans compte : `guest_id` localStorage.

**Reste à faire structurel** : la formation *continue* — boucle d'apprentissage
permanente détaillée en fin de document.

---

## Architecture actuelle de Tracy

### 9 Agents
| Agent | Rôle | Statut |
|---|---|---|
| **CommercialAgent** | Vente, recherche produit, conversation | ✅ En prod — le plus développé |
| **NegotiationAgent** | Négociation de prix, rabais | ✅ Implémenté |
| **CatalogAgent** | Gestion catalogue vendeur, config boutique | ✅ Implémenté |
| **OrderAgent** | Création/suivi/annulation commande | ✅ Implémenté |
| **PaymentAgent** | Paiement, wallet, retrait | ✅ Implémenté |
| **SupportAgent** | Réclamations, après-vente, disputes | ✅ Implémenté |
| **CampaignAgent** | Campagnes marketing, relances | ✅ Implémenté |
| **MemoryAgent** | Mémoire client, préférences, oubli | ✅ Implémenté |
| **RestaurantAgent** | Commande repas, menus, livraison | ✅ Implémenté |

### 27 Tools
`search_products`, `search_catalog`, `search_store`, `create_store`, `send_catalog`, `create_order`, `cancel_order`, `track_order`, `create_support_ticket`, `create_dispute`, `create_payment`, `get_wallet`, `request_withdrawal`, `send_payment_link`, `get_campaign`, `search_partner`, `save_memory`, `search_memory`, `update_memory`, `delete_memory`, `activate_tracy_subscription`, `get_shop_config`, `update_shop_config`, `search_restaurants`, `get_restaurant_menu`, `create_restaurant_order`, `track_restaurant_order`

### 12 Intents (classification)
`store_creation`, `shop_config`, `catalog_management`, `negotiation`, `support`, `campaign`, `payment`, `order`, `store_search`, `memory`, `restaurant`, `product_search`

### Modules Vision
`identify-product`, `compute-embedding`, `check-authenticity`, `check-conformity`, `shop-quality`

---

## Ce qui est déjà géré (CommercialAgent)

### Scénarios couverts
- ✅ Recherche produit par nom (téléphone, robe, canapé, lit, chemise, etc.)
- ✅ Recherche avec budget (prix max)
- ✅ Recherche avec variantes accentuées (telephone → téléphone)
- ✅ Recherche avec typos (xanape → canapé, chherche → cherche)
- ✅ "Un autre" / "autre chose" → re-recherche même catégorie
- ✅ Recherche de boutique par nom/ville/niche
- ✅ "Quelle boutique vend ce produit" → get_store_info par store_id
- ✅ Messages simples (salut, bonjour, non, hummm) → réponse courte
- ✅ Frustration (merd, tu ne comprends pas) → excuses + reformulation
- ✅ Questions hors-sujet (qui tu es, météo) → ramène à la vente
- ✅ Filtrage mémoire par pertinence (pas de fuite entre catégories)
- ✅ Demande d'accessoire ("aller avec cette robe") → ne re-propose pas le produit
- ✅ Refus de produit → ne re-propose pas
- ✅ Rappel de conversation ("au début", "rappelle-toi")
- ✅ Mots vagues filtrés (truc, chose, machin)
- ✅ Variantes pluriel (telephone → telephones)
- ✅ Déaccentuation (téléphone → telephone)

---

## Ce qui manque — Scénarios à entraîner

### Priorité 1 — Critical (Bloquant pour prod)

#### 1.1 Recherche produit avancée
- [ ] Recherche par catégorie ("tu as quoi en téléphones ?")
- [ ] Recherche par marque ("tu as du Samsung ?")
- [ ] Recherche par gamme de prix ("entre 50000 et 100000")
- [ ] Recherche combinée ("téléphone Samsung moins de 100000")
- [ ] Recherche par couleur ("robe rouge", "chaussure noire")
- [ ] Recherche par taille ("chemise taille M")
- [ ] Filtre par disponibilité ("tu as quoi en stock ?")
- [ ] Tri par prix ("le moins cher", "le plus cher")
- [ ] Produit similaire ("tu as quelque chose comme ça mais moins cher ?")
- [ ] Comparaison ("c'est quoi la différence entre A et B ?")

#### 1.2 Négociation de prix
- [ ] "C'est trop cher" → contre-offre dans la marge
- [ ] "Tu peux faire un prix ?" → vérifie config boutique
- [ ] "Je prends 2, tu peux faire un rabais ?" → remise quantité
- [ ] "L'autre boutique le fait à X" → argumentaire valeur
- [ ] "Je paie cash" → remise possible
- [ ] "Je reviendrai" → relance douce
- [ ] Refus de contre-offre → alternative (produit moins cher, paiement échelonné)

#### 1.3 Commande et paiement
- [ ] "Je veux commander" → crée commande via OrderAgent
- [ ] "Comment je paie ?" → MoMo, carte, cash à la livraison
- [ ] "Je paie par MoMo" → lien de paiement
- [ ] "Je paie par carte" → lien de paiement
- [ ] "Je paie à la livraison" → confirmation
- [ ] "Annule ma commande" → annulation via OrderAgent
- [ ] "Où en est ma commande ?" → suivi via track_order
- [ ] "Quand est-ce livré ?" → délai estimé
- [ ] "Je veux un reçu" → confirmation de commande
- [ ] Paiement échoué → retry + alternative

#### 1.4 Support après-vente
- [ ] "Mon colis n'est pas arrivé" → vérification + ticket
- [ ] "Le produit est défectueux" → dispute + remboursement
- [ ] "Ce n'est pas ce que j'ai commandé" → dispute
- [ ] "Je veux être remboursé" → escalade vers humain
- [ ] "La livraison est en retard" → vérification + suivi
- [ ] "Le vendeur ne répond pas" → escalade
- [ ] "Je veux parler à un humain" → escalade
- [ ] "C'est une arnaque" → dispute + escalade

### Priorité 2 — High (Important pour UX pro)

#### 2.1 Gestion conversationnelle
- [ ] Client change d'avis en cours ("non finalement je veux un téléphone")
- [ ] Client demande conseil ("qu'est-ce qui est le mieux pour moi ?")
- [ ] Client indécis ("je ne sais pas quoi choisir")
- [ ] Client pressé ("vite, je veux un téléphone")
- [ ] Client qui compare ("et le Samsung A15 il est comment ?")
- [ ] Client qui hésite sur le budget ("je ne sais pas trop, maybe 50000")
- [ ] Client qui revient après absence ("je reviens, tu as du nouveau ?")
- [ ] Client qui parle à plusieurs sujets ("je veux un téléphone et aussi une robe")
- [ ] Client qui donne une image/photo → vision identify-product
- [ ] Client qui envoie un audio → transcription + réponse
- [ ] Messages très longs (paragraphe entier)
- [ ] Messages en majuscules (COLÈRE)
- [ ] Messages avec emojis (🔥👍❤️)
- [ ] Langues mixtes (français + anglais + langues locales)
- [ ] Argot africain ("wai", "cho", "fafa", "bic")

#### 2.2 Contexte boutique
- [ ] "Tu vends quoi ici ?" → catalogue de la boutique
- [ ] "Tu as quelles catégories ?" → catégories disponibles
- [ ] "C'est quoi les nouveautés ?" → produits récents
- [ ] "Tu as des promotions ?" → promotions actives
- [ ] "Tu livres où ?" → zones de livraison
- [ ] "C'est quoi les frais de livraison ?" → frais
- [ ] "Tu es ouverte quand ?" → horaires
- [ ] "Comment on vous contacte ?" → contact boutique

#### 2.3 Mémoire et personnalisation
- [ ] "Souviens-toi que je fais du 42" → save_memory
- [ ] "Tu te souviens de moi ?" → search_memory
- [ ] "J'avais vu un téléphone la dernière fois" → recall
- [ ] "Oublie ce que je t'ai dit" → delete_memory
- [ ] "Mes préférences c'est..." → save_memory
- [ ] "Tu me connais non ?" → search_memory
- [ ] "La dernière fois j'ai pris un Samsung" → recall + suggestion

### Priorité 3 — Medium (Enrichissement)

#### 3.1 Restaurant
- [ ] "Je veux manger" → search_restaurants
- [ ] "Tu as des restaurants ?" → liste restaurants
- [ ] "Montre-moi le menu" → get_restaurant_menu
- [ ] "Je veux un riz au poulet" → create_restaurant_order
- [ ] "Où en est ma commande de repas ?" → track_restaurant_order
- [ ] "Tu livres à domicile ?" → info livraison restaurant
- [ ] "Je veux payer en cash à la livraison" → confirmation

#### 3.2 Campagne et fidélité
- [ ] "Tu as des promos ?" → get_campaign
- [ ] "Je veux parrainer un ami" → parrainage
- [ ] "C'est quoi mon statut ?" → statut fidélité
- [ ] "Je veux une réduction fidèle" → remise fidélité

#### 3.3 Vendeur (CatalogAgent)
- [ ] "Ajoute un produit" → création produit
- [ ] "Change le prix du téléphone" → update prix
- [ ] "Supprime ce produit" → suppression
- [ ] "Combien j'ai de stock ?" → inventaire
- [ ] "Configure mes règles de négociation" → shop_config
- [ ] "Active une remise de 10%" → config remise
- [ ] "Active Tracy pour ma boutique" → activate_subscription

### Priorité 4 — Low (V2 et au-delà)

#### 4.1 Multi-pays
- [ ] Détection automatique du pays (numéro de téléphone)
- [ ] Devise locale (FCFA, Naira, Cedi)
- [ ] Langues locales (Fon, Yoruba, Wolof)
- [ ] Produits spécifiques par région

#### 4.2 Vision
- [ ] Client envoie photo → identify-product
- [ ] Vendeur envoie photo produit → compute-embedding
- [ ] Vérification authenticité photo
- [ ] Vérification conformité post-livraison

#### 4.3 Audio
- [ ] Message vocal → transcription
- [ ] Réponse vocale (TTS)
- [ ] Appel audio (WebRTC)

---

## Plan d'action — Étapes

### Étape 1 : Tests de couverture (immédiat)
Créer une suite de tests automatisés qui couvre tous les scénarios ci-dessus.

### Étape 2 : Amélioration du CommercialAgent
- Enrichir les `search_phrases` avec tous les mots produits possibles
- Ajouter détection de catégorie ("en téléphones", "en robes")
- Ajouter détection de marque (Samsung, iPhone, Tecno, Infinix, etc.)
- Ajouter détection de couleur (rouge, noir, blanc, bleu, etc.)
- Ajouter détection de taille (S, M, L, XL, 42, 43, etc.)
- Améliorer la gestion des messages multi-sujets

### Étape 3 : Amélioration des autres agents
- NegotiationAgent : tester avec vrais scénarios de négociation
- OrderAgent : tester le flux complet commande → paiement
- SupportAgent : tester les réclamations et disputes
- RestaurantAgent : tester le flux commande repas

### Étape 4 : Tests end-to-end
- Simuler des conversations complètes de A à Z
- Tester sur web (chat interface)
- Tester sur mobile (APK Flutter)
- Tester avec différents profils clients

### Étape 5 : Entraînement continu
Voir la section dédiée ci-dessous — architecture complète de la boucle
« collecte → enrichissement → évaluation → entraînement ».

---

# ARCHITECTURE DE FORMATION CONTINUE (V2)

Objectif : Tracy s'améliore à chaque conversation réelle, sans intervention
manuelle systématique. Quatre couches indépendantes, activables séparément.

## Couche 1 — Boucle de données (fondation)

### 1.1 Capture des transcripts
- Chaque tour de conversation est journalisé (déjà : logs structurés JSON
  `orchestrator_received_message`, `tool_execution_*`, `orchestrator_reply_sent`).
- Nouveau : table `training_transcripts` (PostgreSQL staging) stockant par tour :
  `conversation_id`, `turn`, `user_message`, `intent_classifié`, `agent`,
  `tools_called`, `reply`, `slots_contexte`, `latence_ms`.
- Label qualité déduit automatiquement :
  `order_created` | `payment_link_sent` | `contact_vendor` (succès),
  `clarification_loop` (3+ clarifs d'affilée), `abandoned` (client part sans succès),
  `correction` (client dit « non j'ai dit… », « tu ne comprends pas »).

### 1.2 knowledge_gaps (déjà migré)
- `knowledge_gaps` capture les questions sans réponse (table créée oct. 2026,
  colonne `query_embedding` en `text` en local, `vector(1536)` sur VPS avec pgvector).
- Cron quotidien : agrège `occurrence_count`, génère une liste admin
  « top 20 questions sans réponse » → enrichissement `knowledge_documents`.

### 1.3 Replayer de transcripts (harnais de régression IA)
- `tests/replay/` : rejoue N conversations réelles capturées contre Tracy Core
  en local, compare les sorties attendues (agent, tools, slots) vs obtenues.
- Intégré en CI : chaque PR de prompt/code rejoue le set ; écart > seuil = blocage.
- Dataset versionné : `tests/fixtures/transcripts/*.jsonl` (réels, anonymisés).

## Couche 2 — RAG pgvector (connaissances métier)

- Sur le VPS Contabo : `CREATE EXTENSION vector` → les migrations
  `knowledge_chunks` / `knowledge_gaps` créent automatiquement `vector(1536)`
  + index IVFFlat (le code migre proprement dans les deux modes).
- Ingestion : catalogues produits, politiques de livraison par pays
  (BJ/SN/CI/TG — villes, quartiers, délais, frais), FAQ vendeurs,
  conditions Moneroo, guides tailles/marques.
- Tool `search_knowledge` (existe) : avant chaque réponse, top-k chunks
  injectés dans le prompt → réponses factuelles au lieu d'hallucinations.
- Le fallback `text` en local garde tout le code fonctionnel sans pgvector.

## Couche 3 — Intelligence de classification

### Phase A : LLMIntentClassifier (feature flag)
- L'ABC `IntentClassifier` existe → swap sans toucher l'orchestrateur.
- `LLMIntentClassifier` (gpt-4o-mini, temperature 0, JSON strict : intent,
  confidence, entities{product,city,qty,price}) avec :
  - timeout 800 ms + fallback automatique sur `KeywordIntentClassifier`,
  - cache Redis sur message normalisé (TTL 24 h),
  - shadow mode : classifie en parallèle des regex, log les divergences
    → dataset d'entraînement supervisé gratuit.
- Flag : `INTENT_CLASSIFIER=keyword|llm|shadow` (default keyword).

### Phase B : entités LLM
- Le message interpreter actuel (regex) reste le fast-path ; en shadow mode
  les entités LLM corrigent/completent : produits ambigus, villes inconnues,
  multi-intentions (« je veux 2 chaussures à Calavi et le moins cher »).

### Phase C : fine-tune (les « millions de paramètres »)
- Quand ≥500 transcripts labellisés `success`/`correction` :
  - Option A : fine-tune OpenAI `gpt-4o-mini` (API, ~5–20 $/run) sur
    (system_prompt, message+contexte → réponse+tools attendus).
  - Option B (cible VPS) : Llama-3.1-8B / Mistral-7B + LoRA (QLoRA, GPU
    Contabo ou RunPod à la demande) — modèle possédé, entraînement illimité.
- Critère de swap : le candidat doit battre la version prod sur le replayer
  (taux succès + taux de bon agent +0% régression tools) avant mise en prod.

## Couche 4 — Feedback opérationnel

- Bouton « réponse utile ? » côté web/app → `feedback` sur les transcripts.
- Vendeur peut corriger une réponse Tracy → correction enregistrée comme
  exemple d'entraînement (`source: vendor_correction`).
- Rapport hebdo automatique : top gaps, divergences classifieur, taux de
  complétion des commandes par agent.

## Ordre d'exécution recommandé

1. `training_transcripts` + labellisation auto (2 j)
2. Replayer + fixtures transcripts (2 j)
3. LLMIntentClassifier en `shadow` (2 j) → activer `llm` après 1 semaine de logs
4. pgvector VPS + ingestion corpus Afrique Ouest (3 j)
5. Fine-tune quand dataset ≥500 (continu)

---

## Métriques de succès

| Métrique | Objectif | Actuel |
|---|---|---|
| Taux de bonne classification d'intent | > 95% | ~80% |
| Taux de recherche produit réussie | > 90% | ~85% |
| Réponses hors-sujet correctement gérées | > 95% | ~90% |
| Satisfaction client (feedback) | > 4/5 | Non mesuré |
| Temps de réponse moyen | < 3s | ~2s |
| Typos corrigées | > 80% | ~60% |
| Mémoire correctement filtrée | 100% | ~95% |
