# MANTOTA — Plan de Développement

> Document de suivi. Mettre à jour après chaque étape terminée.

---

## État actuel (audit 22 août 2026)

### Ce qui est prêt
- **Tracy Core** (`tracy-core/`) — V1 terminée : 8 agents, 28 tools, 314 tests, FastAPI, score maturité 99.2%. Module RAG (embeddings + retriever pgvector) + RAG Correctif (classify_relevance, knowledge_gaps) + Référentiel géographique (resolve_geo, delivery_quartiers) + Persistance règles commerciales (CatalogAgent shop_config) ajouté.
- **Laravel** (`od-system-staging/`) — Web app fonctionnelle : Auth, Vendor, Influencer, Admin, Shop, Wallet, Campaigns, KYC, Support, 114 migrations, 253 routes web, 11 contrôleurs API Bot
- **Maquette** — 34 écrans HTML, 3 rôles (Acheteur/Vendeur/Partenaire), navigation conforme
- **API Bot Laravel** — Endpoints pour Tracy Core : products, catalog, stores (search + create), orders, payments, wallet, campaigns, partners, memory, subscriptions, currencies, restaurant, vision, knowledge RAG (search + ingestion + gaps/log), geo (resolve + villes/quartiers), delivery quartiers (get + set + remove)

### Ce qui manque
- **App Mobile** — Pas de projet Flutter créé
- **Auth OTP** — L'auth actuelle est email/password, la maquette montre phone + OTP
- **Rôle Buyer** — L'enum UserRole n'a que vendor/influencer/admin
- **Modes activables** — Pas implémenté (Acheteur/Vendeur/Partenaire sur un seul compte)
- **Chat Tracy UI** — Pas d'interface de conversation dans le web ou mobile
- **Écran Découvrir** — Existe dans la maquette mais pas dans le web
- **Audio & Appels** — V2 (prévu, skip V1)
- **Notifications natives** — Pas de FCM/APNS
- **Store Score & Trust** — Non implémenté
- **Contracts** — Non implémenté

---

## Phase 0 — Tracy Country Intelligence & Continuous Learning

> **Statut :** 📋 PLANIFIÉ
>
> **Vision :** Mantota est conçu multi-pays dès l'architecture. "Benin-first knowledge depth, multi-country architecture from day one." Bénin = premier marché de référence avec la connaissance la plus profonde, mais Togo, Sénégal, Côte d'Ivoire et tout autre pays doivent pouvoir évoluer indépendamment sans modification du code.

### 0.1 Country Registry

Créer une table centralisée de gestion des pays comme **donnée/configuration**, pas comme logique codée en dur.

> **Statut :** ✅ Partiellement implémenté — Table `countries` créée (id, code, name, currency_code, is_active) avec seed de 15 pays d'Afrique. Modèle `Country` Eloquent avec relations. Endpoints admin `GET /api/admin/knowledge/countries`.
>
> **Reste à faire :** Ajouter les champs avancés (phone_country_code, default_language, supported_languages[], timezone, status, knowledge_level, readiness_score) pour le Country Intelligence Center complet.

Champs prévus :
- `country_id`, `iso_code`, `country_name`
- `phone_country_code`, `currency`, `default_language`, `supported_languages[]`
- `timezone`
- `status` : `DISCOVERING`, `COLLECTING`, `LEARNING`, `REVIEW`, `READY`, `ACTIVE`, `PAUSED`
- `knowledge_level` : `GENERAL`, `LIMITED`, `BASIC`, `INTERMEDIATE`, `ADVANCED`, `VERIFIED`
- `readiness_score`
- `created_at`, `updated_at`

> **Règle fondamentale :** ajouter un nouveau pays ne doit PAS nécessiter une modification du code source. L'Admin peut ajouter/activer/configurer un pays depuis le système d'administration.

### 0.2 Country Auto-Discovery

Si un utilisateur d'un pays inconnu s'inscrit :
1. Détecter son pays depuis les données fiables (téléphone, géolocalisation, paramètres).
2. Vérifier l'existence dans le Country Registry.
3. Si le pays n'existe pas :
   - créer automatiquement une entrée pays avec le statut `DISCOVERING` ;
   - initialiser son espace de Country Intelligence ;
   - ne pas bloquer l'inscription.
4. Collecter les signaux autorisés pour enrichir les métriques.

> Aucun développeur n'est nécessaire pour découvrir un nouveau pays.

### 0.3 Multi-pays dès le départ

Pays préparés dans l'architecture de départ :
- **Bénin** — premier marché opérationnel de référence, connaissance initiale la plus élevée.
- **Togo**, **Sénégal**, **Côte d'Ivoire** — intégration architecturale dès la conception.

Le système ne doit pas être limité à ces quatre pays. L'ajout futur se fait via l'Admin.

### 0.4 Country Knowledge Level

Le niveau de connaissance d'un pays est calculé à partir de données réelles, pas seulement du nombre d'utilisateurs.

Niveaux prévus :
- `GENERAL` — connaissances commerciales génériques, fallback.
- `LIMITED` — quelques signaux collectés.
- `BASIC` — patterns basiques détectés.
- `INTERMEDIATE` — connaissances consolidées et validées partiellement.
- `ADVANCED` — couverture large sur plusieurs domaines.
- `VERIFIED` — connaissances vérifiées par l'équipe Mantota.

### 0.5 Country Readiness Score

Score mesurant si Tracy dispose d'assez de données fiables pour progresser.

Signaux possibles :
- utilisateurs, utilisateurs actifs, vendeurs, boutiques ;
- conversations, commandes, transactions, paiements, livraisons ;
- catégories de produits, feedback, corrections, erreurs Tracy ;
- interventions humaines, stabilité des informations, diversité des sources.

> Les seuils (`COUNTRY_LEARNING_START_THRESHOLD`, `COUNTRY_READY_THRESHOLD`, `COUNTRY_ACTIVE_THRESHOLD`) doivent être configurables depuis l'Admin, jamais codés en dur.

### 0.6 Country Learning Activation

Flux de statut conseillé :

```
DISCOVERING → COLLECTING → LEARNING → REVIEW → READY → ACTIVE
```

- Le passage automatique d'un statut à l'autre est contrôlable.
- L'Admin peut :
  - voir les raisons du changement ;
  - voir le score et les données utilisées ;
  - forcer une validation ou un retour arrière ;
  - suspendre / réactiver l'apprentissage ;
  - modifier les seuils.

### 0.7 Country Learning

Tracy apprend progressivement les caractéristiques commerciales locales :

- habitudes de recherche et terminologie ;
- catégories populaires ;
- méthodes de paiement observées ;
- pratiques de livraison ;
- comportements acheteurs / vendeurs ;
- horaires d'activité, patterns de négociation ;
- vocabulaire local, contexte restaurant, commerce via WhatsApp.

> "Apprendre" = identifier et structurer des patterns. Tracy ne croit pas automatiquement toutes les affirmations des utilisateurs.

### 0.8 Shop Configuration vs Country Knowledge

Séparation obligatoire :

- **Shop Configuration** = règles officielles d'une boutique (commission, remise max, négociation, livraison, ton de Tracy). C'est la source de vérité de la boutique.
- **Country Knowledge** = connaissance générale du marché.

Si une règle de boutique diffère d'une pratique nationale, Tracy applique la règle de la boutique.

### 0.9 Seller Settings as High-Quality Data

Les paramètres vendeur peuvent alimenter la Country Intelligence **sous forme agrégée** :

- une règle boutique reste une règle boutique ;
- plusieurs observations similaires sur plusieurs boutiques produisent une **Country Knowledge Candidate** ;
- les données sensibles ou spécifiques à une boutique ne sont jamais exposées comme connaissances générales.

### 0.10 Knowledge Candidates

Lorsqu'une tendance nouvelle est détectée, créer une **Knowledge Candidate** :

- `country_id`, `category`, `claim`
- `evidence_count`, `source_types`, `confidence`
- `first_seen_at`, `last_seen_at`
- `status` : `PENDING`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `EXPIRED`, `REVOKED`
- `risk_level`, `generated_by`, `reviewed_by`, `reviewed_at`

### 0.11 Source et preuve

Chaque connaissance doit être traçable :

- `source_type`, `source_reference`, `source_count`, `evidence`
- `confidence`, `verification_date`, `expiration_date`
- `reviewer`, `version`

Sources possibles :
configuration vendeur, données transactionnelles, catalogue, conversations, feedback, intervention humaine, documentation Mantota, source externe validée.

### 0.12 Auto-learning avec niveaux de risque

Quatre niveaux de risque :

- `LOW RISK` — utilisable automatiquement dans certaines limites.
- `MEDIUM RISK` — candidate créée, validation selon règles.
- `HIGH RISK` — validation obligatoire.
- `CRITICAL` — jamais d'auto-validation.

Domaines critiques : paiements, commissions, prix, remboursements, règles contractuelles, sécurité, conformité, informations officielles Mantota.

### 0.13 Memory ≠ Knowledge

Séparation stricte :

- **User Memory** — préférences personnelles.
- **Conversation Memory** — contexte immédiat.
- **Shop Configuration** — règles boutique.
- **Country Knowledge** — connaissance générale marché.
- **Mantota Official Knowledge** — règles officielles de la plateforme.
- **Transactional Data** — états réels (commandes, paiements).

Ces informations ne doivent jamais être mélangées.

### 0.14 Tracy Response Pipeline

Le pipeline conceptuel mis à jour :

```
USER
 ↓ Country Detection
 ↓ User Context
 ↓ Shop Context
 ↓ Memory Retrieval
 ↓ Country Knowledge Retrieval
 ↓ Mantota Official Knowledge
 ↓ Intent / Agent
 ↓ Reasoning
 ↓ Tool Selection
 ↓ Tool Execution
 ↓ Result Validation
 ↓ Response Generation
 ↓ Language Selection
 ↓ Learning Signal
 ↓ Memory / Knowledge Candidate
```

> Priorité : données transactionnelles et configurations officielles > connaissance générale ou supposition du modèle.

### 0.15 Country Fallback

Si Tracy connaît peu un pays, elle reste utile :

- aider avec les fonctionnalités disponibles ;
- utiliser les données de Mantota et de la boutique ;
- poser des questions si nécessaire ;
- reconnaître ses limites ;
- éviter d'inventer une pratique locale ;
- collecter des signaux pour améliorer progressivement le support.

### 0.16 Country Intelligence Admin

Transformer la page **Countries** en véritable **Country Intelligence Center**.

Vue Admin :
- liste des pays avec statut, score, niveau de connaissance ;
- métriques : utilisateurs, vendeurs, boutiques, conversations, commandes, transactions, langues, monnaies ;
- connaissances actives, candidates, rejetées, expirées ;
- erreurs Tracy, feedback, tendances, dernières mises à jour.

Actions :
- ajouter / modifier / activer / désactiver / mettre en pause un pays ;
- modifier les seuils ;
- consulter, approuver, rejeter, modifier, révoquer, expirer, vérifier une connaissance ;
- consulter l'historique.

### 0.17 Country Knowledge Dashboard

Dashboard pour comprendre ce que Tracy connaît réellement par pays :

- métriques : users, vendors, shops, orders ;
- **Knowledge Coverage** : Commerce, Payments, Delivery, Products, Restaurants, Terminology, Languages ;
- Readiness Score, statut du pays, candidates en attente, corrections humaines, erreurs Tracy.

### 0.18 Continuous Learning Loop

Boucle d'amélioration continue :

```
REAL USER ACTIVITY
 ↓ DATA COLLECTION
 ↓ SIGNAL DETECTION
 ↓ PATTERN ANALYSIS
 ↓ KNOWLEDGE CANDIDATE
 ↓ RISK CLASSIFICATION
 ↓ AUTO-APPROVAL (si autorisé)  OU  ADMIN REVIEW
 ↓ KNOWLEDGE VERSION
 ↓ TRACY RETRIEVAL
 ↓ EVALUATION
 ↓ NEW FEEDBACK
 ↓ LOOP
```

Cette boucle doit fonctionner sans modification du code pour chaque nouveau pays.

### 0.19 Country-Specific Language

Pays et langue sont deux concepts distincts.

- Tracy détecte la langue de l'utilisateur.
- Un pays ne force pas une langue unique.
- Exemple : Sénégal → français ou anglais ; Bénin → français, anglais, fon, yoruba, mina (progressivement).
- Tracy répond dans la langue appropriée à la conversation.

### 0.20 Country Expansion Strategy

Pas de stratégie rigide Bénin → Togo → Sénégal → Côte d'Ivoire.

Chaque pays progresse indépendamment selon ses données réelles :

```
Bénin     → READY
Togo      → LEARNING
Sénégal   → COLLECTING
Côte d'Ivoire → DISCOVERING
```

Cela doit être possible simultanément.

### 0.21 No Code Change for Normal Country Expansion

> **Règle architecturale fondamentale :** ajouter un pays, modifier ses paramètres, changer ses seuils, compléter ses connaissances ou faire évoluer son statut ne doit normalement PAS nécessiter de modifier le code de Tracy.

Le code fournit : mécanismes, règles de sécurité, pipelines, outils, structures de données, moteurs d'analyse, validation.
Les données et connaissances pays sont administrables dynamiquement.

### 0.22 Country Knowledge Versioning

Les connaissances importantes sont versionnées :

- historique des versions (auteur, date, raison du changement) ;
- comparaison, rollback, historique consultable.

### 0.23 Knowledge Expiration

Certaines connaissances peuvent devenir obsolètes. Champs prévus :
- `verified_at`, `expires_at`, `last_seen_at`, `status`

Cycle possible :
```
ACTIVE → EXPIRED → REVIEW → UPDATED
```

Tracy ne conserve pas indéfiniment une information potentiellement périmée.

### 0.24 Country Evaluation

Créer des tests spécifiques par pays :

- recherche produit, négociation, paiement, livraison, restaurant, support ;
- langue, terminologie, règles vendeur, situations ambiguës, informations inconnues.

Un pays ne doit pas être déclaré `READY` uniquement à cause du volume de données — il doit réussir un minimum d'évaluations.

### 0.25 Observability

Métriques par pays dans l'Admin :

- answer accuracy, tool success, hallucination rate ;
- user correction rate, human escalation rate ;
- language accuracy, country knowledge coverage ;
- response usefulness, unresolved intents.

### 0.26 Privacy & Data Separation

L'apprentissage pays privilégie les **données agrégées**.

- "Je préfère acheter le soir" = préférence utilisateur.
- Cela ne devient pas automatiquement "Les Sénégalais préfèrent acheter le soir".
- Une tendance nationale nécessite suffisamment de données agrégées et une interprétation correcte.

### 0.27 Country Discovery Without Developer — Scénario

Jour 1 : un utilisateur du Sénégal s'inscrit. Le Sénégal n'existe pas encore.

Le système :
1. Détecte le Sénégal.
2. Crée le pays, statut `DISCOVERING`.
3. Initialise configuration + espace de Country Intelligence.
4. Laisse l'utilisateur utiliser Mantota.
5. Collecte les signaux autorisés.
6. Augmente les métriques, passe à `COLLECTING`, puis `LEARNING`.
7. Crée des Knowledge Candidates.
8. Permet leur validation.
9. Augmente le Knowledge Level.
10. Passe à `READY` puis `ACTIVE`.

Aucune modification du code de Tracy n'est nécessaire pour cette progression.

### 0.28 Bénin-First mais Multi-Pays

- Bénin = premier marché de référence, connaissances les plus détaillées, plus de données validées, plus de tests, meilleure couverture locale.
- Togo, Sénégal, Côte d'Ivoire et autres pays progressent indépendamment dès qu'ils génèrent suffisamment de données fiables.

### 0.29 Ordre de priorité de l'architecture pays

Cette architecture doit être abordée avant d'accumuler de nouvelles fonctionnalités IA. Ordre conseillé :

1. Country Registry
2. Country Context
3. Shop Configuration separation
4. User/Conversation Memory separation
5. Country Knowledge structure
6. Country Readiness Score
7. Country Learning Pipeline
8. Knowledge Candidates
9. Risk Classification
10. Admin Country Intelligence Center
11. Knowledge Validation
12. Knowledge Versioning
13. Evaluation system
14. Continuous Learning Loop
15. Multilingual intelligence
16. Expansion progressive des pays

### 0.30 Intégration avec le plan existant

La nouvelle architecture s'intègre aux fonctionnalités existantes sans les supprimer :

- Tracy Core, agents, tools, Laravel, Flutter, WhatsApp, reconnaissance cross-canal, restaurant, vision, Shop Quality, Admin Panel, configuration Tracy par boutique, règles de négociation, support, paiement, découverte, multi-langue.
- Elle fournit le cadre multi-pays et d'apprentissage continu dans lequel ces fonctionnalités évolueront.

---

## Phase 0b — Tracy Memory System (Mémoire long terme)

> **Statut :** 📋 PLANIFIÉ
>
> **Vision :** La mémoire de Tracy est une couche centrale entre l'utilisateur, le contexte, les connaissances et le raisonnement. Elle ne se réduit pas à une liste de préférences. Elle permet à Tracy de ne pas repartir de zéro à chaque conversation, tout en évitant l'invention de souvenirs.

### 0b.1 Objectif de la mémoire

Tracy doit pouvoir conserver, retrouver, mettre à jour, oublier et utiliser les informations pertinentes dans le temps. Elle doit donner l'impression d'une continuité relationnelle sans inventer de souvenirs.

Exemple : aujourd'hui "Je cherche une robe pour un mariage", dans quelques jours "Tu peux me montrer quelque chose dans le même style que la robe dont on parlait ?" → Tracy retrouve le contexte si disponible et autorisé.

### 0b.2 Types de mémoire

Plusieurs niveaux de mémoire clairement séparés :

- **Working Memory** — mémoire de travail de la conversation en cours (intention, produits présentés, choix, étape commande, contexte immédiat). Durée courte.
- **Episodic Memory** — événements / conversations importants (achat, problème, demande clé, interaction avec vendeur/restaurant, décision prise avec Tracy). Chaque souvenir conserve son contexte et sa date.
- **Semantic User Memory** — informations stables sur l'utilisateur (langue, pointure, taille, préférences de catégorie, mode de communication). Chaque champ avec `confidence`, `source`, `first_seen_at`, `last_confirmed_at`, `frequency`, `status`.
- **Preference Memory** — préférences explicites ou déduites avec prudence. Distinguer : explicite / temporaire / déduite / confirmée.
- **Relationship Memory** — historique relationnel utile (première interaction, sujets fréquents, commandes, problèmes résolus, familiarité conversationnelle). Tracy reste une IA : pas de relation inventée.
- **Shop Memory** — contexte et historique d'une boutique. Ne remplace **pas** la Shop Configuration (règles officielles).
- **Country Memory** — observations et apprentissages liés à un pays. Relié au **Country Intelligence**.
- **Tracy Self-Memory / System Memory** — configurations validées, décisions système, connaissances validées, résultats d'évaluation. Ne permet **pas** au modèle de modifier ses règles fondamentales.

### 0b.3 Memory Record

Chaque souvenir structuré :
- `memory_id`, `memory_type`, `owner_type`, `owner_id`
- `content`, `structured_data`
- `source_type`, `source_reference`
- `confidence`, `importance`
- `created_at`, `updated_at`, `last_used_at`, `last_confirmed_at`, `expires_at`
- `status` : `ACTIVE`, `TEMPORARY`, `EXPIRED`, `ARCHIVED`, `DELETED`, `REJECTED`
- `version`

### 0b.4 Memory Source

Tracy sait d'où vient chaque souvenir.

Sources possibles : `user_statement`, `conversation`, `transaction`, `shop_configuration`, `admin`, `system`, `validated_knowledge`, `tool_result`.

Une mémoire issue d'une conversation n'a pas le même niveau de confiance qu'une donnée Laravel ou une configuration officielle.

### 0b.5 Memory Confidence

Chaque mémoire importante a un niveau de confiance :
- `HIGH` : langue préférée confirmée, pointure donnée explicitement.
- `LOW` : utilisateur semble aimer les produits premium (déduction).

Tracy utilise la confiance pour décider si elle peut s'appuyer sur un souvenir.

### 0b.6 Memory Importance

Niveaux : `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`. Les informations importantes sont conservées plus longtemps ; les temporaires expirent.

### 0b.7 Memory Retrieval

Tracy ne charge pas toute la mémoire à chaque conversation.

Pipeline :
```
Nouvelle question
 ↓ Analyse du contexte
 ↓ Recherche des souvenirs pertinents
 ↓ Classement par pertinence
 ↓ Vérification de confiance
 ↓ Sélection des souvenirs utiles
 ↓ Injection dans le contexte Tracy
```

La mémoire doit être pertinente, limitée, contextualisée, fiable.

### 0b.8 Memory Update

Tracy sait mettre à jour une mémoire existante.

Exemple : ancienne pointure 41, nouvelle information "Je prends du 42 maintenant" → mise à jour de la mémoire, pas création infinie de souvenirs contradictoires. Conserver l'historique utile.

### 0b.9 Memory Conflict Resolution

Gestion des contradictions. Exemple : pointure 41 puis 42. La nouvelle information explicitement confirmée a priorité. Conserver : ancienne valeur, nouvelle valeur, date, source, confiance.

### 0b.10 Memory Decay / Expiration

Toutes les mémoires ne sont pas éternelles. Exemple : "Je cherche une voiture cette semaine" → temporaire. "Je préfère recevoir les réponses en anglais" → durable.

Prévoir : expiration automatique, renouvellement, confirmation, archivage.

### 0b.11 Memory Confirmation

Pour certaines informations importantes, Tracy demande confirmation : "Tu préfères toujours les chaussures en taille 42 ?"
- confirmation → augmente la confiance ;
- correction → met à jour la mémoire.

### 0b.12 User Control

L'utilisateur contrôle sa mémoire :
- voir ce que Tracy se rappelle ;
- modifier / supprimer une mémoire ;
- demander à Tracy d'oublier ;
- désactiver certaines catégories si le système le permet.

Exemples : "Tracy, oublie que je cherche une voiture.", "Qu'est-ce que tu sais sur mes préférences ?", "Supprime cette préférence."

### 0b.13 Memory Privacy

Respecter la confidentialité. Une information personnelle ne devient pas automatiquement une connaissance générale du pays.

Exemple : "Je préfère acheter le soir" reste une préférence utilisateur, pas "Les Sénégalais préfèrent acheter le soir".

### 0b.14 Memory vs Knowledge

Séparation stricte :
- **Memory** — ce que Tracy sait/retient d'un utilisateur, conversation, boutique, contexte.
- **Knowledge** — connaissance générale validée.
- **Shop Configuration** — règles officielles d'une boutique.
- **Transactional Data** — données actuelles de Laravel.

### 0b.15 Memory vs Country Learning

Les conversations produisent :
- **User Memory** : "Je préfère le rouge."
- **Learning Signal** : "Beaucoup de clients demandent ce type de produit."
- **Country Knowledge Candidate** : tendance commerciale validée après analyse pays.

### 0b.16 Memory Learning

Tracy apprend automatiquement certaines informations personnelles à faible risque. Limites strictes :
- jamais apprendre automatiquement comme vérité officielle : commissions, prix, règles Mantota, paiement, conditions contractuelles, remboursement, sécurité, réglementation.
- Ces données doivent provenir de leur source officielle.

### 0b.17 Memory From Tools

Les résultats des tools peuvent alimenter la mémoire. Exemple : une commande livrée est conservée comme événement. La donnée transactionnelle officielle reste dans Laravel.

### 0b.18 Memory-Aware Tracy

Le raisonnement intègre la mémoire :
```
USER
 ↓ Identify user
 ↓ Identify country
 ↓ Identify shop
 ↓ Retrieve relevant memory
 ↓ Retrieve relevant knowledge
 ↓ Retrieve official data
 ↓ Reason
 ↓ Use tools
 ↓ Validate result
 ↓ Respond
 ↓ Determine new memory / update
 ↓ Determine learning signal
```

### 0b.19 Memory Quality

Métriques : `memory retrieval accuracy`, `memory relevance`, `false memory rate`, `outdated memory rate`, `contradiction rate`, `user correction rate`, `forgotten-information compliance`, `memory usefulness`.

### 0b.20 Memory Admin

Ajouter au Tracy Knowledge / Intelligence Center une vue santé du système mémoire pour les administrateurs autorisés.

L'Admin voit : volumes, catégories, erreurs, conflits, corrections, expiration, qualité, métriques.

L'accès au contenu personnel est strictement contrôlé selon les permissions.

### 0b.21 Existing Memory API

Le DEV_PLAN indique déjà que l'API Bot Laravel possède des endpoints pour Tracy Memory.

- **Ne pas créer un second système parallèle.**
- Auditer l'existant (`memory` endpoint dans l'API Bot Laravel).
- Faire évoluer l'architecture actuelle pour supporter : types, confiance, importance, source, expiration, versioning, retrieval, update, conflict resolution, user deletion, learning signals.
- Réutiliser l'existant lorsque possible.

### 0b.22 Final Principle

Tracy ne dit "Je me souviens que..." que si elle possède réellement ce souvenir. Si elle ne trouve rien, elle fonctionne normalement sans prétendre se souvenir. La mémoire améliore Tracy ; elle ne devient jamais une source d'hallucination.

---

## Phase 1 — Fondations API & Auth (Semaines 1-2)

### 1.1 Rôles & Modes
- [ ] Ajouter rôle `buyer` dans `UserRole` enum
- [ ] Créer migration `user_modes` (table pivot : user_id, mode, is_active)
- [ ] Un utilisateur peut activer/désactiver les modes : buyer (toujours actif), vendor, partner
- [ ] API : `POST /api/user/modes` — activer/désactiver un mode
- [ ] API : `GET /api/user/modes` — lister les modes actifs
- [ ] Le mode `livreur` est grisé (bientôt) — non activable en V1

### 1.2 Auth OTP (Téléphone)
- [ ] Créer migration `otp_codes` (phone, code, expires_at, used)
- [ ] API : `POST /api/auth/otp/request` — envoyer un code OTP par SMS
- [ ] API : `POST /api/auth/otp/verify` — vérifier le code, créer/session utilisateur
- [ ] Un utilisateur = un numéro de téléphone (unique)
- [ ] Si nouveau numéro → création automatique de compte avec mode buyer par défaut
- [ ] Si numéro existant → connexion directe
- [ ] Garder l'auth email/password pour l'admin uniquement

### 1.3 Profil utilisateur étendu
- [ ] Ajouter champs : `phone` (déjà présent), `phone_verified_at`, `display_name`, `avatar_url`
- [ ] API : `GET /api/user/profile` — profil complet avec modes actifs
- [ ] API : `PATCH /api/user/profile` — mettre à jour le profil

### 1.4 WhatsApp Cloud API (V1 — canal d'acquisition)
**Objectif** : Tracy répond sur WhatsApp du vendeur ET sur l'app. Même cerveau, deux canaux.

- [ ] Créer une Meta Business App (WhatsApp Business Cloud API)
- [ ] Migration `whatsapp_connections` (vendor_id, phone_number_id, waba_id, status, connected_at)
- [ ] Service `WhatsAppCloudService` — envoie/reçoit via API Meta
- [ ] `POST /api/whatsapp/webhook` — reçoit les webhooks Meta (messages entrants)
- [ ] `GET /api/whatsapp/webhook` — vérification du webhook (challenge Meta)
- [ ] Table `messages` étendue avec `channel` (app / whatsapp)
- [ ] Channel Router : identifie le canal d'entrée, normalise en `IncomingMessage` pour Tracy Core
- [ ] Channel Dispatcher : route la `TracyReply` vers le bon canal (app WebSocket ou WhatsApp API)
- [ ] **WhatsApp Commerce** : synchroniser le catalogue Mantota vers le catalogue WhatsApp Business
  - Product cards dans WhatsApp (image + nom + prix + bouton) — pas de lien externe
  - Product lists (jusqu'à 10 produits en carousel)
  - Single product detail avec description
- [ ] Settings vendeur (app) : toggle "Tracy sur WhatsApp" on/off
- [ ] Mode hybride : Tracy répond sur WhatsApp si le vendeur ne répond pas dans X secondes (configurable)
- [ ] Templates Meta : approuver les templates pour messages proactifs (relances, confirmations)
- [ ] Remplace le vieux bot Node.js (`whatsapp-bot-legacy/`)

### 1.5 Reconnaissance cross-canal (WhatsApp → App)
**Objectif** : Le client qui passe de WhatsApp à l'app garde son historique.

- [ ] `customer_id` = numéro de téléphone normalisé (format international sans +, ex: `2290197123456`)
- [ ] Quand un client écrit sur WhatsApp → customer_id créé automatiquement
- [ ] Quand le client installe l'app et s'inscrit avec le même numéro → OTP vérifie
- [ ] Mantota reconnaît le numéro → fusion automatique du compte
- [ ] Le client retrouve son historique de conversation WhatsApp dans l'app
- [ ] Tracy dit : "Content de te revoir !" avec contexte de la conversation précédente
- [ ] Migration : `customers` table (customer_id, phone, display_name, store_id, channel_origin, created_at)

---

## Phase 1b — Mantota Web V1 (Semaines 1-4)

> **Le web est un canal principal en V1**, au même titre que l'APK Flutter.
> Source : `docs/tracy/08-ROADMAP.md` ligne 11 et `docs/tracy/02-ARCHITECTURE.md` ligne 108.
>
> **Règle fondamentale** : Le web est un canal d'acquisition + découverte + démo Tracy.
> - **Pas de compte utilisateur sur le web** — pour avoir un compte (buyer, vendor, partner) → télécharger l'APK.
> - **Chat Tracy éphémère** — on peut discuter avec Tracy sans compte, mais les conversations ne sont pas sauvegardées.
> - **Pas de dashboard vendeur sur le web** — tout passe par l'APK.
> - **Admin sur un domaine séparé** (ex: `admin.mantota.com`) — auth email/password, pas sur `mantota.com`.

### 1b.1 Landing Page (Welcome)
- [ ] Refondre `Welcome.vue` — commerce conversationnel, Tracy au centre
- [ ] Hero : "Discutez avec Tracy, votre vendeuse IA" (pas e-commerce classique)
- [ ] Sections : comment ça marche (conversation), boutiques de confiance, Store Score
- [ ] CTA principal : "Télécharger l'app Mantota" (lien Play Store / APK direct)
- [ ] CTA secondaire : "Essayer le chat" (ouvre le chat éphémère, sans compte)
- [ ] Supprimer : anciens sections influenceurs, campagnes CPC, vidéos génériques
- [ ] Branding Mantota : teal #0BBFA0, coral #FF6B35, design system existant

### 1b.2 Chat Tracy Éphémère (Web — sans compte)
- [ ] Page conversation avec Tracy — interface chat temps réel
- [ ] **Aucun compte requis** — le visiteur discute directement avec Tracy
- [ ] **Conversations éphémères** — Tracy ne garde pas les conversations (pas de sauvegarde)
- [ ] **Bandeau d'avertissement** : "Tu discutes sans compte. Tracy ne garde pas tes conversations. Télécharge l'app pour sauvegarder ton historique."
- [ ] Input texte + bouton envoi
- [ ] Cartes produit cliquables dans le chat (quand Tracy propose un produit)
- [ ] Bouton "Payer" dans le chat (quand Tracy envoie un lien de paiement Moneroo)
- [ ] Récap commande dans le chat (quand Tracy crée une commande)
- [ ] **Lien de suivi de commande** — Tracy génère un lien magique (`/track/{order}?token=...`) que le client peut copier
- [ ] Indicateur "Tracy écrit..." (typing indicator)
- [ ] **CTA APK discret** après chaque interaction positive : "Installer l'app Mantota"
- [ ] Connexion à Tracy Core (`POST /chat`) — session éphémère (pas de user_id)
- [ ] **Support via Tracy** — le visiteur peut demander "je veux signaler" ou "je veux contacter le support"
  - Tracy essaie de résoudre d'abord (statut commande, question simple)
  - Si Tracy ne peut pas → crée un ticket support (mode guest) via `create_support_ticket`
  - Si c'est un litige → crée un dispute via `create_dispute` + alerte l'équipe Mantota
  - Le code de référence du ticket est donné dans le chat
  - L'utilisateur peut suivre sur `/support/track` (page existante)

### 1b.3 Découvrir (Web — sans compte)
- [ ] Page Découvrir — catégories, boutiques populaires, produits tendance
- [ ] Recherche produit par catégorie/boutique
- [ ] Carte des boutiques à proximité (géolocalisation — Store Location & Trust)
- [ ] Badges de confiance (GPS vérifié, photo de façade, boutique vérifiée)
- [ ] CTA sur chaque produit/boutique : "Discuter avec Tracy" ou "Télécharger l'app"

### 1b.4 Page Suivi de Commande (Web — sans compte)
- [ ] **Existe déjà** — `OrderTrackingController::show()` + `Track.vue`
- [ ] Réutiliser la page existante `/track/{order}?token=...`
- [ ] Accessible sans compte (magic link via tracking_token)
- [ ] Affiche le statut de commande, infos vendeur, produit
- [ ] Confirmation de réception avec code PIN (libération escrow)
- [ ] Bouton "Signaler un problème" → ouvre un litige (dispute) via `OrderTrackingController::dispute()`
- [ ] Chat de litige public existant (`PublicDisputeController` + `DisputeChat.vue`)
- [ ] Recherche de commande existante : `/order/lookup` (email/téléphone + référence)

### 1b.5 Support (Web — sans compte)
- [ ] **Existe déjà** — `Public\SupportController`
- [ ] Page création de ticket : `/support` (guest_name + guest_email + sujet + catégorie + message)
- [ ] Page suivi de ticket : `/support/track` (par code de référence TKT-XXXX)
- [ ] Page détail ticket : `/support/{reference}` (messages + réponse)
- [ ] **Amélioration** : connecter à Tracy via le chat éphémère (le support se déclenche depuis la conversation, pas depuis un formulaire)
- [ ] **Amélioration** : étendre les catégories de `bug, paiement, question` à `bug, paiement, question, litige, signalement, autre`

### 1b.6 Admin (Domaine séparé)
- [ ] **Domaine séparé** : `admin.mantota.com` (ou similaire) — pas sur `mantota.com`
- [ ] Auth email/password (admin uniquement)
- [ ] Tableau de bord admin — utilisateurs, boutiques, transactions
- [ ] Gestion des boutiques — validation, Store Score
- [ ] Gestion des utilisateurs — rôles, modes
- [ ] Modération — signalements, litiges (existant : `DisputeController`, `FlaggedMessageController`)
- [ ] Support — gestion des tickets (existant : `Admin\SupportController`)
- [ ] **Existant** : la plupart des contrôleurs admin existent déjà dans `od-system-staging/app/Http/Controllers/Admin/`

---

## Phase 2 — App Mobile Flutter (Semaines 2-5)

### 2.1 Setup projet
- [ ] Créer projet Flutter `mantota_app/`
- [ ] Architecture : Riverpod (state) + Dio (HTTP) + go_router (navigation)
- [ ] Design system : couleurs Mantota (teal #0BBFA0, dark), typographie, composants
- [ ] Config : API base URL, Tracy Core URL, environnement dev/staging/prod

### 2.2 Onboarding (écrans 01, 02a, 02b, 15e)
- [ ] Splash screen (écran 01) — logo Mantota + Tracy
- [ ] Saisie numéro + sélecteur de pays (écran 02a)
- [ ] Vérification OTP — 6 cases (écran 02b)
- [ ] Choix des modes (écran 15e) — Acheteur (défault), Vendeur, Partenaire (Livreur grisé)

### 2.3 Navigation par rôle
- [ ] Bottom navigation dynamique selon modes actifs :
  - **Acheteur** : Chats · Découvrir · Wallet · Profil
  - **Vendeur** : Chats · Boutique · Wallet · Profil
  - **Partenaire** : Chats · Missions · Wallet · Profil
- [ ] Si plusieurs modes actifs → onglet central changeable (toggle)

### 2.4 Messagerie (écrans 03, 04, 05)
- [ ] Liste des conversations (écran 03) — badge canal (app / WhatsApp)
- [ ] Conversation active avec Tracy (écran 04) — badge canal visible
- [ ] Canal privé @Tracy (écran 05)
- [ ] Intégration WebSocket (Laravel Reverb) pour temps réel
- [ ] Input texte + bouton envoi
- [ ] **Messages audio** : enregistrement, envoi, lecture (voir §5.1)
- [ ] **Appels audio** : bouton appel dans la conversation (voir §5.2)
- [ ] **Cross-canal** : si un client vient de WhatsApp, badge "WhatsApp" sur sa conversation
- [ ] **Reconnaissance** : si le client s'inscrit sur l'app, Tracy le reconnaît (même numéro)

### 2.5 Acheteur (écrans 06, 07, 07b-g)
- [ ] Découvrir — catégories, boutiques populaires, produits tendance (écran 07g)
- [ ] Recherche produit (écran 07b)
- [ ] Négociation avec Tracy (écran 07c)
- [ ] Paiement (écran 06)
- [ ] Suivi livraison (écran 07)
- [ ] Récap commande (écran 07d)
- [ ] Confirmation paiement (écran 07e)
- [ ] Historique commandes (écran 07f)

### 2.6 Vendeur (écrans 08-10f)
- [ ] Dashboard Vendeur (écran 08)
- [ ] Ma boutique — catalogue grille (écran 09)
- [ ] Config Tracy — autonomie, personnalité, règles (écran 10)
- [ ] Création boutique guidée par Tracy (écran 10b)
- [ ] Ajout produit via Tracy — photo + description (écran 10c)
- [ ] Commandes entrantes (écran 10d)
- [ ] Détail commande vendeur (écran 10e)
- [ ] Notifications vendeur (écran 10f)
- [ ] **Connecter WhatsApp** (écran 10g) — configurer Tracy sur son WhatsApp Business
  - Saisie du numéro WhatsApp Business
  - Vérification via Meta
  - Toggle on/off Tracy sur WhatsApp
  - Mode hybride : délai avant que Tracy réponde (ex: 30s, 1min, immédiat)
  - Statut de connexion en temps réel

### 2.7 Partenaire (écrans 11-14d) — *En attente*
- [ ] Dashboard Partenaire (écran 11)
- [ ] Opportunités (écran 12)
- [ ] Mes liens (écran 13)
- [ ] Studio Mantota (écran 14)
- [ ] Détail mission (écran 14b)
- [ ] Suivi commissions (écran 14c)
- [ ] Retrait fonds (écran 14d)
- *Note : Le mode Partenaire sera développé après la validation des modes Acheteur et Vendeur.*

### 2.8 Profil & Settings (écrans 15, 15b-e)
- [ ] Profil & Modes — activation/désactivation (écran 15)
- [ ] Wallet détaillé (écran 15b)
- [ ] Centre notifications (écran 15c)
- [ ] Paramètres — langue, notif, sécurité (écran 15d)

---

## Phase 3 — Intégration Tracy Core (Semaines 4-5)

### 3.1 Connexion App ↔ Tracy Core
- [ ] Service Flutter : `TracyChatService` — appelle `POST /chat` de Tracy Core
- [ ] Gestion des réponses asynchrones (streaming si possible)
- [ ] Affichage des réponses de Tracy dans la conversation
- [ ] Indicateur "Tracy écrit..." (typing indicator)

### 3.2 Contexte conversationnel
- [ ] Envoi du `store_id` et `customer_id` avec chaque message
- [ ] Gestion du `conversation_id` côté app
- [ ] Historique de conversation persistant (local + API)

### 3.3 Actions Tracy dans l'app
- [ ] Quand Tracy propose un produit → carte produit cliquable dans le chat
- [ ] Quand Tracy envoie un lien de paiement → bouton "Payer" dans le chat
- [ ] Quand Tracy crée une commande → récap dans le chat
- [ ] Quand Tracy suit une livraison → statut live dans le chat

---

## Phase 4 — Laravel : Endpoints manquants (Semaines 3-4)

### 4.1 Conversations
- [ ] Migration `conversations` (id, user_id, store_id, type, created_at)
- [ ] Migration `messages` (id, conversation_id, sender_type, content, type, created_at)
- [ ] API : `GET /api/conversations` — liste des conversations
- [ ] API : `GET /api/conversations/{id}/messages` — messages d'une conversation
- [ ] API : `POST /api/conversations/{id}/messages` — envoyer un message
- [ ] WebSocket : broadcast nouveaux messages via Reverb

### 4.2 Découvrir
- [ ] API : `GET /api/discover/categories` — catégories avec compte de boutiques
- [ ] API : `GET /api/discover/stores/popular` — boutiques populaires (par note/ventes)
- [ ] API : `GET /api/discover/products/trending` — produits tendance (par vues/ventes récentes)

### 4.3 Notifications
- [ ] Migration `notifications` (id, user_id, type, title, body, data, read_at)
- [ ] API : `GET /api/notifications` — liste
- [ ] API : `PATCH /api/notifications/{id}/read` — marquer comme lu
- [ ] Push FCM pour mobile (Firebase Cloud Messaging)

### 4.4 Tools Tracy — Support & Litiges (APK + Web)
> **Existant** : `BotOrderTrackingController` (track + cancel), `Public\SupportController`, `PublicDisputeController`, `Admin\DisputeController`, `Admin\FlaggedMessageController`
> **Manquant** : Tools Tracy pour créer tickets et litiges depuis une conversation

- [ ] **Tool `create_support_ticket`** — Tracy crée un ticket support via l'API Mantota
  - Endpoint : `POST /bot/support/tickets` (à créer)
  - Params : `subject`, `category` (bug/paiement/question/litige/signalement/autre), `message`, `guest_name?`, `guest_email?`, `user_id?`
  - Response : `reference_code` (TKT-XXXX)
  - **À documenter** dans `docs/tracy/04-TOOLS.md`
- [ ] **Tool `create_dispute`** — Tracy crée un litige sur une commande
  - Endpoint : `POST /bot/orders/{id}/dispute` (à créer)
  - Params : `order_id`, `reason`
  - Response : `dispute_id`, `status: disputed`
  - **À documenter** dans `docs/tracy/04-TOOLS.md`
- [ ] **Tool `track_order`** — déjà existant (`BotOrderTrackingController::track`)
  - Confirmer dans `docs/tracy/04-TOOLS.md`
- [ ] **Étendre catégories support** : migration pour ajouter `litige`, `signalement`, `autre` dans l'enum `category`
- [ ] **SupportAgent** : mettre à jour le system prompt pour gérer les 3 niveaux (Tracy → humain → litige)
  - Niveau 1 : Tracy résout directement (statut commande, question simple)
  - Niveau 2 : Tracy crée un ticket + informe l'utilisateur
  - Niveau 3 : Tracy crée un litige + alerte l'équipe Mantota
- [ ] **Flux support sur APK** (avec compte) : ticket lié au user_id, notifications push
- [ ] **Flux support sur Web** (sans compte) : ticket en mode guest, code de référence donné dans le chat, suivi via `/support/track`

---

## Phase 5 — Fonctionnalités avancées

### 5.1 Messages audio
- [ ] Côté app : enregistrement audio (flutter_sound ou record)
- [ ] Upload du fichier audio vers Laravel (`POST /api/conversations/{id}/messages` avec type=audio)
- [ ] Stockage S3/local, URL retournée
- [ ] Lecture audio dans le chat (waveform + bouton play)
- [ ] Transcription automatique envoyée à Tracy Core (pour que Tracy comprenne le vocal)
- [ ] Tracy peut répondre en texte (V1) ou en audio (V2 — TTS)

### 5.2 Appels audio dans les conversations
- [ ] **V1 (simple)** : bouton "Appeler" → ouvre un appel VoIP in-app
  - Utiliser WebRTC via flutter_webrtc
  - Signalisation via WebSocket (Laravel Reverb)
  - L'appel est entre l'utilisateur et Tracy (réponse automatique)
  - Tracy répond en voix (TTS) et comprend la voix (STT)
- [ ] **V2 (avancé)** : appels entre utilisateurs (client → vendeur)
  - WebRTC peer-to-peer
  - Signalisation via Laravel
  - Enregistrement optionnel pour qualité

### 5.3 Géolocalisation boutiques
- [ ] API : `GET /api/stores/nearby?lat=...&lng=...&radius=...` — boutiques à proximité
- [ ] Carte interactive dans l'app (Google Maps / Mapbox)
- [ ] Store Score interne (non visible) — voir `docs/mantota/10-STORE_LOCATION_AND_TRUST.md`
- [ ] Badges de confiance (GPS vérifié, photo de façade, boutique vérifiée)

---

## Phase 6 — Modèle économique

### Modèle actuel (hérité)
| Source | Montant | Concerne |
|---|---|---|
| Abonnement Tracy Starter | 2 500 FCFA / mois | Vendeurs |
| Abonnement Tracy Standard | 12 000 FCFA / mois | Vendeurs |
| Abonnement Tracy Pro | 25 000 FCFA / mois | Vendeurs |
| Abonnement Tracy TPF | 50 000 FCFA / an | Vendeurs |
| CPC minimum | 25 FCFA / clic | Vendeurs (campagnes) |
| Frais de retrait | 20% | Créateurs de contenu |
| Commission Studio UGC | 15% | Créateurs de contenu |

### Modèle proposé V2 (à valider)
| Source | Montant | Concerne | Statut |
|---|---|---|---|
| **Acheteur** — Gratuit | 0 FCFA | Tous les acheteurs | Toujours gratuit |
| **Vendeur** — Freemium | | | |
| └ Plan Free | 0 FCFA / mois | 1 boutique, 10 produits, Tracy sur app + WhatsApp essai (50 conv/mois, hybride 60s, 0 relance) | Acquisition |
| └ Plan Starter | 2 500 FCFA / mois | 1 boutique, 50 produits, Tracy active + WhatsApp illimité (hybride 30s, 10 relances/jour) | Existing |
| └ Plan Standard | 12 000 FCFA / mois | 3 boutiques, 200 produits, Tracy + WhatsApp auto 24/7 + relances illimitées + catalogue sync | Existing |
| └ Plan Pro | 25 000 FCFA / mois | Boutiques illimitées, Tracy + WhatsApp auto + analytics + campagnes + priorité | Existing |
| **Partenaire** — Gratuit + commission | 0 FCFA / mois | Commission sur clics et ventes | Existing |
| **Commission transaction** | 2-5% par vente | Plateforme sur chaque transaction | **NOUVEAU** |
| **Frais de retrait** | 5-10% (à revoir) | Tous | À optimiser |
| **Studio UGC** | 15% | Créateurs | Existing |
| **Live Shopping** | Commission sur ventes live | Vendeurs + créateurs | **FUTURE** |
| **Contrats échelonnés** | Frais de gestion 1-2% | Vendeurs + acheteurs | **FUTURE** |

### Questions à trancher
1. **Commission sur transaction** : Mantota prend quel % sur chaque vente ?
2. **Frais de retrait** : 20% c'est élevé — réduire à 5-10% ?
3. **Plan Free vendeur** : existe-t-il déjà ou faut-il le créer ?
4. **Monétisation acheteur** : reste 100% gratuit ?
5. **Abonnement vs transaction** : privilégier les abonnements ou les commissions ?

---

## Phase 7 — Fonctionnalités futures (propositions)

### Court terme (V2)
1. **Stories commerce** — boutiques postent des stories produits (24h), Tracy recommande
2. **Panier intelligent** — Tracy propose un panier basé sur l'historique d'achat
3. **Parrainage** — inviter des amis, gagner du crédit wallet
4. **Avis & notes** — après livraison, Tracy demande un avis naturellement
5. **Catalogue intelligent** — Tracy suggère d'ajouter des produits basés sur les demandes clients
6. **Multi-langue** — français, fon, yoruba, mina (langues locales Bénin/Togo)
7. **Mode hors-ligne** — consulter l'historique des conversations sans connexion
8. **Recherche vocale** — parler au lieu d'écrire pour chercher un produit

### Moyen terme (V2-V3)
9. **Live Shopping** — vente en direct avec Tracy qui anime et prend les commandes
10. **Contrats échelonnés** — paiement en 2-3 fois, Tracy explique et gère
11. **Delivery Agent** — rôle livreur avec Tracy pour mise à jour de tournée
12. **IA visuelle** — photo d'un produit → Tracy trouve une correspondance dans le catalogue
13. **Stories analytics** — qui a vu, cliqué, acheté depuis les stories
14. **Programme de fidélité** — points, badges, réductions automatiques gérés par Tracy
15. **Marketplace cross-boutiques** — recherche un produit across all boutiques Mantota

### Long terme (V3)
16. **Assistant vocal complet** — Tracy parle et comprend la voix en temps réel
17. **Publication auto TikTok/Instagram** — Tracy génère et poste du contenu produit
18. **Détection de fraude** — IA qui détecte les comportements suspects
19. **Prédiction de stock** — Tracy anticipe les ruptures et suggère des réapprovisionnements
20. **Négociation automatique B2B** — Tracy négocie avec les fournisseurs pour le vendeur

---

## Ordre de développement prioritaire

```
Phase 1 (Fondations API + Auth OTP + WhatsApp) ──→ Phase 2 (App Flutter) ──→ Phase 3 (Intégration Tracy)
         ↕                                                ↕
  Phase 1b (Mantota Web V1)                       Phase 4 (Endpoints Laravel)
  Landing + Chat éphémère + Découvre                      ↓
  + Suivi commande + Support                      Phase 5 (Audio & Appels)
  + Admin (domaine séparé)                               ↓
         ↕                                        Phase 6 (Modèle économique — valider)
  Phase 4 (Endpoints Laravel)                            ↓
         ↓                                        Phase 7 (Fonctionnalités futures)
  Phase 3 (Intégration Tracy)
```

> **Note** : Le web pousse l'installation de l'APK. Pas de compte utilisateur sur `mantota.com`.
> L'admin est sur `admin.mantota.com` (domaine séparé, auth email/password).

### Canaux en V1
- ✅ **App Mantota** — canal principal (Flutter)
- ✅ **Web Mantota** (`mantota.com`) — canal d'acquisition + découverte + démo Tracy (Laravel Inertia + Vue 3) — landing page, chat Tracy éphémère, découvre, suivi commande, support
- ✅ **Web Admin** (`admin.mantota.com`) — domaine séparé, auth email/password (admin uniquement)
- ✅ **WhatsApp** — canal d'acquisition (Meta Cloud API + Commerce)

### Rôles en production V1
- ✅ **Acheteur** — prêt en premier
- ✅ **Vendeur** — prêt en deuxième
- ⏳ **Partenaire** — en attente (développé mais pas en prod immédiatement)
- ⏳ **Livreur** — en attente (grisé dans l'app)

---

## Infrastructure & Déploiement

### Environnements
- **Dev** : Local (Laravel + Tracy Core + PostgreSQL + Redis)
- **Staging** : VPS (PostgreSQL + Redis + Nginx + Supervisor)
- **Prod** : VPS (même stack, domaine mantota.com)

### Stack
- **Backend** : Laravel 12 (PHP 8.2+) + PostgreSQL + Redis
- **IA** : Tracy Core (FastAPI + LangGraph) — Python 3.12+
- **Mobile** : Flutter (Android + iOS)
- **Web** : Laravel + Inertia.js + Vue 3 (landing + chat Tracy éphémère + découvre + suivi commande + support — **pas de compte utilisateur**, admin sur domaine séparé)
- **Realtime** : Laravel Reverb (WebSocket)
- **Paiement** : Moneroo
- **Push** : Firebase Cloud Messaging (FCM)
- **Stockage** : Local → S3 (futures audios/images)

---

## Suivi des modifications

| Date | Étape | Statut | Notes |
|---|---|---|---|
| 22/08/2026 | Audit complet | ✅ Terminé | Scan Tracy Core + Laravel + Maquette |
| 22/08/2026 | CreateStoreTool enregistré | ✅ | main.py corrigé |
| 22/08/2026 | Route POST /bot/stores Laravel | ✅ | BotStoreController + api.php |
| 22/08/2026 | Maquette conforme | ✅ | 35 écrans, 3 rôles, menus corrects, écran WhatsApp ajouté |
| 22/08/2026 | WhatsApp Cloud API en V1 | 📋 | Plan mis à jour — canal d'acquisition |
| 22/08/2026 | Reconnaissance cross-canal | 📋 | customer_id = phone normalisé |
| — | Phase 1 : Rôles & Auth OTP + WhatsApp | ✅ | Code créé — migrations + modèles + contrôleurs |
| 24/08/2026 | Web = canal d'acquisition (pas de compte) | 📋 | Pas d'auth sur web, chat éphémère, admin sur domaine séparé |
| 24/08/2026 | Support via Tracy (3 niveaux) | 📋 | Tracy → humain → litige. Tools `create_support_ticket` + `create_dispute` à ajouter |
| 24/08/2026 | Code existant réutilisé | 📋 | OrderTracking, DisputeChat, SupportController, FlaggedMessage — déjà dans od-system-staging |
| — | Phase 1b : Mantota Web V1 | ⏳ | À commencer — landing, chat éphémère, découvre, suivi commande, support, admin (domaine séparé) |
| — | Phase 2 : App Flutter | ⏳ | À commencer |
| — | Phase 3 : Intégration Tracy | ⏳ | À commencer |
| 26/08/2026 | Admin Panel React (Vite + Tailwind) | ✅ | 21 pages pro: Dashboard, Users, ShopsMap, Finance, Orders, KYC, TracyCore, Operations, Growth, Revenue, Countries, Creators, Campaigns, Security, Notifications, System, ShopQuality |
| 26/08/2026 | Product Vision (CLIP + YOLOv8) | ✅ | Tracy Core: app/vision/product_vision.py — identification produit par photo client |
| 26/08/2026 | Product Authenticity Checker | ✅ | Tracy Core: app/vision/authenticity.py — watermark, duplication, upscale, photo pro |
| 26/08/2026 | Conformité post-livraison | ✅ | Tracy Core: app/vision/conformity.py — feedback client + comparaison CLIP |
| 26/08/2026 | Shop Quality Score | ✅ | Tracy Core: app/vision/shop_quality.py — score 0-100, seuils auto (60/40/20) |
| 26/08/2026 | Vision API endpoints | ✅ | Tracy Core: app/vision/endpoints.py — 7 endpoints FastAPI |
| 26/08/2026 | Admin Shop Quality page | ✅ | admin-panel: ShopQuality.jsx — monitoring scores, flags, signaux |
| — | Laravel: product_image_embedding migration | ✅ | Migration + Model ProductImageEmbedding + 7 endpoints bot |
| — | Laravel: shop_quality_signals table | ✅ | Migration + Models ShopQualitySignal + ProductAuthenticityCheck |
| — | Laravel: BotVisionController | ✅ | 7 endpoints: embeddings, authenticity, quality signals/score |
| — | Laravel: MobileTracyController vision | ✅ | 3 endpoints mobile: identify-product, check-conformity, shop-quality |
| — | Flutter: capture photo + envoi à Tracy | ✅ | tracy_channel_screen.dart: bouton caméra, image_picker, product match cards |
| — | Flutter: feedback conformité post-livraison | ✅ | conformity_screen.dart: 3 verdicts + photo + comparaison CLIP |
| — | Flutter: tracy_chat_service vision methods | ✅ | identifyProduct, checkConformity, getShopQuality + models |
| 26/08/2026 | Restaurant module — Laravel | ✅ | 2 migrations (7 tables), 7 models, BotRestaurantController (10 endpoints), MobileRestaurantController (5 endpoints) |
| 26/08/2026 | Restaurant module — Flutter | ✅ | restaurant_service.dart, restaurants_screen.dart, restaurant_menu_screen.dart (panier multi-plats, checkout) |
| 26/08/2026 | Restaurant module — Admin | ✅ | Restaurants.jsx: monitoring, stats, filtres, détails |
| 26/08/2026 | Photos obligatoires catalogues | ✅ | ProductController: image_url required, MenuItem: image_path NOT NULL |
| 26/08/2026 | Tracy Core: RestaurantAgent + 4 tools | ✅ | search_restaurants, get_restaurant_menu, create_restaurant_order, track_restaurant_order |
| 26/08/2026 | Tracy Core: restaurant endpoints | ✅ | /restaurant/list, /restaurant/menu/{id}, /restaurant/order, /restaurant/order/{id} |
| 26/08/2026 | Tracy Core: intent restaurant | ✅ | Pattern regex restaurant → RestaurantAgent (manger, repas, pizza, etc.) |
| 26/08/2026 | Tracy Core: AI Gateway OpenAI | ✅ | .env: DEFAULT_AI_PROVIDER=openai, model gpt-4o-mini, Ollama gardé pour V2 (VPS Contabo) |
| 26/08/2026 | Laravel: bot restaurant routes for Tracy | ✅ | /bot/restaurant/search, /bot/restaurant/menu/{id}, /bot/restaurant/orders/{id}/status |
| 26/08/2026 | Tracy Core: test chat restaurant | ✅ | "jai faim" → RestaurantAgent → search_restaurants → OpenAI → réponse naturelle |
| 26/08/2026 | Tracy Core: address_form par boutique | ✅ | ShopConfig.address_form, BaseAgent.set_address_form(), orchestrator fetch config per store |
| 26/08/2026 | Laravel: address_form migration | ✅ | shop_negotiation_configs + address_form enum(tu/vous), BotStoreController + MobileTracyController |
| 26/08/2026 | Laravel: proxy restaurant MobileTracyController | ✅ | 4 endpoints: /tracy/restaurants, /tracy/restaurants/{id}/menu, /tracy/restaurants/order, /tracy/restaurants/order/{id} |
| 26/08/2026 | Laravel: proxy shop-config MobileTracyController | ✅ | GET/POST /tracy/shop-config (address_form + negotiation rules) |
| 28/08/2026 | Tracy Country Intelligence & Continuous Learning Architecture | 📋 PLANIFIÉ | Ajout au DEV_PLAN — Country Registry, auto-discovery, readiness score, learning pipeline, knowledge candidates, risk, versioning, admin dashboard |
| 28/08/2026 | Tracy Memory System — Long-Term Memory | 📋 PLANIFIÉ | Ajout au DEV_PLAN — Working, Episodic, Semantic, Preference, Relationship, Shop, Country, Self-Memory ; record, source, confidence, importance, retrieval, update, conflict, decay, privacy |
| 28/08/2026 | Tracy Training P1 — Recherche avancée | ✅ Terminé | Gamme prix, couleur+marque, couleur+taille, tri ascendant/descendant, multi-requête, typo, slang |
| 28/08/2026 | Tracy Training P2 — Conversation naturelle | ✅ Terminé | Change d'avis, conseil, indécision, contexte boutique, mémoire, messages courts, remerciement |
| 28/08/2026 | Tracy Training P3.1 — Restaurant | ✅ Terminé | RestaurantAgent: menu, plats, spécialités, horaires, routing corrigé (restaurant avant order) |
| 28/08/2026 | Tracy Training P3.2 — Campagne | ✅ Terminé | CampaignAgent: relance panier abandonné, promotions boutique, handler public (partenaire ok, campagnes redirigent vers app) |
| 28/08/2026 | Tracy Training P3.3 — Vendeur | ✅ Terminé | CatalogAgent: gestion catalogue, prix, stock depuis le chat, handler public (création boutique, config, catalogue redirigent vers app) |
| 28/08/2026 | Tracy Training P3.4 — Tests boutiques réelles | ✅ Terminé | Tests sur store_id 6 et 7: recherche, devises, catalog, promos |
| 28/08/2026 | Tracy Training P4.1 — Multi-pays | ✅ Terminé | Tool get_currencies, détection monnaie/pays dans CommercialAgent, pré-check non-produit, public_context contextuel |
| 28/08/2026 | Tracy Training P4.2 — Vision | ✅ Terminé | Module CLIP+YOLOv8: product_vision, authenticity, conformity, shop_quality, 7 endpoints API. V1 utilise OpenAI Vision API |
| 28/08/2026 | Tracy Training P4.3 — Audio | ✅ Skip V1 | Prévu V2 (WebRTC), skip V1 |
| 28/08/2026 | Intent routing — 12 intents corrigés | ✅ Terminé | \bpay\b (évite pays), restaurant avant order, (?<!le )moins cher (distingue tri vs nego), défectueux regex, je le prends, memory patterns (rappel/souviens/nom) |
| 28/08/2026 | MemoryAgent — auto-save + search optimisé | ✅ Terminé | Auto-save (je m'appelle X, j'aime Y), search avec fallback sans query, extraction mots-clés, source=observed |
| 28/08/2026 | Mantota — BotMemoryController source user_provided | ✅ Terminé | Ajout de user_provided dans les sources acceptées |
| 28/08/2026 | Welcome.vue — guest_id localStorage | ✅ Terminé | Mémoire web sans compte: guest_id persistant envoyé comme customer_id à Tracy |
| 28/08/2026 | Scan de maturité Tracy | ✅ Terminé | Score: 99.2% — 12 catégories testées, 53 tests, 52 passés. Tracy prête pour utilisateurs réels |
| 05/09/2026 | RAG — Migration countries table | ✅ Terminé | Table countries (id, code, name, currency_code, is_active) + seed 15 pays Afrique. Modèle Country Eloquent |
| 05/09/2026 | RAG — Migration knowledge_documents | ✅ Terminé | Table knowledge_documents (title, content, country_id FK, category, status enum, version, created_by FK) + extension pgvector activée |
| 05/09/2026 | RAG — Migration knowledge_chunks | ✅ Terminé | Table knowledge_chunks (document_id FK, chunk_index, content, embedding vector(1536), metadata jsonb) + index IVFFlat cosinus |
| 05/09/2026 | RAG — Modèles Laravel | ✅ Terminé | Country, KnowledgeDocument, KnowledgeChunk avec relations Eloquent |
| 05/09/2026 | RAG — KnowledgeAdminController | ✅ Terminé | CRUD admin complet: index, show, store, update, changeStatus, destroy, countries, upsertChunks. Routes /api/admin/knowledge/* |
| 05/09/2026 | RAG — BotKnowledgeController | ✅ Terminé | Endpoints bot: search (pgvector), documents (liste approved), showDocument, upsertChunks (ingestion). Routes /bot/knowledge/* |
| 05/09/2026 | RAG — Corpus Bénin (5 documents) | ✅ Terminé | Migration seed: quartiers/villes, marchés (Dantokpa, Ganhi, Arzèkè, Ouando), moyens de paiement (MTN MoMo, Moov Money), livraison (Zem, coursiers), expressions commerciales. Statut draft |
| 05/09/2026 | RAG — Tracy Core: embeddings.py | ✅ Terminé | EmbeddingService OpenAI text-embedding-3-small (1536 dim), retry backoff exponentiel, support batch |
| 05/09/2026 | RAG — Tracy Core: retriever.py | ✅ Terminé | KnowledgeRetriever: search_knowledge (embedding + Mantota API), fallback global, format_chunks_for_prompt |
| 05/09/2026 | RAG — Tracy Core: SearchKnowledgeTool | ✅ Terminé | 28e tool. Permissions: CommercialAgent + SupportAgent uniquement. OrderAgent/PaymentAgent exclus |
| 05/09/2026 | RAG — Tracy Core: MantotaClient.search_knowledge | ✅ Terminé | Méthode async ajoutée au MantotaClient (POST /bot/knowledge/search) |
| 05/09/2026 | RAG — Tracy Core: main.py registration | ✅ Terminé | Tool enregistré conditionnellement si openai_api_key présente. EmbeddingService + KnowledgeRetriever initialisés |
| 05/09/2026 | RAG — Script ingest_knowledge.py | ✅ Terminé | Découpage sémantique (sections, markdown, paragraphes, phrases), embeddings batch, upsert via API bot. Idempotent |
| 05/09/2026 | RAG — Tests (29 tests) | ✅ Terminé | test_rag.py (21: embeddings, retriever, tool + permissions), test_ingest_knowledge.py (8: découpage sémantique). 276 tests total, 0 régression |
| 05/09/2026 | RAG — Documentation mise à jour | ✅ Terminé | 02-ARCHITECTURE.md, 03-AGENTS.md, 04-TOOLS.md, 08-ROADMAP.md mis à jour avec section RAG |
| 05/09/2026 | RAG Correctif — Migration knowledge_gaps | ✅ Terminé | Table knowledge_gaps (query_text, query_embedding vector(1536), country_id FK, category_guess, occurrence_count, status enum, resolved_document_id FK) + index IVFFlat |
| 05/09/2026 | RAG Correctif — Modèle KnowledgeGap | ✅ Terminé | Modèle Eloquent avec relations country + resolvedDocument |
| 05/09/2026 | RAG Correctif — Endpoints admin gaps | ✅ Terminé | GET /api/admin/knowledge/gaps (liste filtrable triée par occurrence_count desc), PATCH /api/admin/knowledge/gaps/{id} (change statut) |
| 05/09/2026 | RAG Correctif — Endpoint bot gaps/log | ✅ Terminé | POST /bot/knowledge/gaps/log : similarité cosinus >0.92 pour regrouper, incrémente ou crée, passage auto open→suggested au seuil (défaut 5) |
| 05/09/2026 | RAG Correctif — classify_relevance (Tracy Core) | ✅ Terminé | Fonction numérique (score cosinus) : correct ≥0.85, ambiguous ≥0.6, incorrect <0.6. Jamais par le LLM |
| 05/09/2026 | RAG Correctif — MantotaClient.log_knowledge_gap | ✅ Terminé | Méthode async ajoutée au MantotaClient (POST /bot/knowledge/gaps/log) |
| 05/09/2026 | RAG Correctif — SearchKnowledgeTool mis à jour | ✅ Terminé | Retour inclut relevance. incorrect → fire-and-forget gap logging + contexte de repli honnête. ambiguous → note de prudence. correct → chunks normaux |
| 05/09/2026 | RAG Correctif — Tests (11 nouveaux) | ✅ Terminé | classify_relevance (8: correct/ambiguous/incorrect + seuils + liste vide + custom), tool incorrect (2: gap logging + échec silencieux), tool ambiguous (1: warning). 287 tests total, 0 régression |
| 05/09/2026 | RAG Correctif — Admin Panel KnowledgeGaps.jsx | ✅ Terminé | Page admin : KPIs, filtres par statut, table des lacunes, actions (ignorer/suggérer/résoudre), info banner. Route /knowledge-gaps + sidebar Tracy Core |
| 05/09/2026 | Store Location — Doc mise à jour | ✅ Terminé | 10-STORE_LOCATION_AND_TRUST.md : section 6 Référentiel géographique (Département→Commune→Arrondissement→Quartier), section 7 Rayon livraison (district→quartiers, city=raccourci), section 8 Recherche géo (résolution référentiel + delivery_quartiers) |
| 05/09/2026 | Store Location — Migration villes | ✅ Terminé | Table villes (id, country_id FK, name, department_name nullable) + seed 77 communes du Bénin (12 départements) |
| 05/09/2026 | Store Location — Migration quartiers | ✅ Terminé | Table quartiers (id, ville_id FK, name, arrondissement_name nullable) + seed quartiers principaux (Cotonou, Porto-Novo, Parakou, Abomey-Calavi, etc.) |
| 05/09/2026 | Store Location — Migration shop_delivery_quartiers | ✅ Terminé | Table pivot shop_delivery_quartiers (shop_id FK users, quartier_id FK quartiers, unique constraint) |
| 05/09/2026 | Store Location — Migration delivery columns | ✅ Terminé | Ajout colonnes users : delivery_mode enum (pickup_only/quartiers/multi_city/national/international), pickup_available bool, delivery_cities json, delivery_countries json |
| 05/09/2026 | Store Location — Modèles Eloquent | ✅ Terminé | Ville, Quartier, ShopDeliveryQuartier + relation deliveryQuartiers() sur User |
| 05/09/2026 | Store Location — Endpoint GET /api/geo/resolve | ✅ Terminé | Recherche quartiers (priorité) puis villes (fallback), insensible casse/accents via transliterator. Retourne type+id+name+ville_id+department |
| 05/09/2026 | Store Location — Endpoint GET /api/villes/{id}/quartiers | ✅ Terminé | Liste tous les quartiers d'une ville, triés par arrondissement puis nom |
| 05/09/2026 | Store Location — Bot endpoints delivery quartiers | ✅ Terminé | GET/POST/DELETE /bot/stores/{id}/delivery-quartiers : ajout par IDs ou par ville (toute la ville), exclusion (sauf quartier), retrait individuel, auto delivery_mode pickup_only→quartiers |
| 05/09/2026 | Store Location — MantotaClient (Tracy Core) | ✅ Terminé | Méthodes resolve_geo, get_ville_quartiers, get/set/remove_delivery_quartiers ajoutées au client Python |
| 05/09/2026 | Store Location — Tests Python (10 nouveaux) | ✅ Terminé | test_geo_client.py : resolve_geo (3: quartier/ville/not found), get_ville_quartiers (1), get/set delivery_quartiers (4: by IDs/whole city/exclusion), remove (2: success/not found). 297 tests total, 0 régression |
| 05/09/2026 | Store Location — Tests Laravel (14 nouveaux) | ✅ Terminé | GeoReferentialTest.php : seed Bénin (3), resolve (3: quartier/case-insensitive/ville/404), ville quartiers (2), delivery quartiers CRUD (6: create/whole city/exclusion/remove/revert/get). phpunit.xml + TestCase + CreatesApplication créés |
| 05/09/2026 | Shop Config Bug — CatalogAgent persistance règles | ✅ Terminé | Bug corrigé : CatalogAgent détectait shop_config mais n'appelait jamais update_shop_config. Nouveau flow : LLM extrait params structurés → validation cohérence (marge+remise≤100%, auto_accept≤max_discount, shipping>0) → appel réel update_shop_config → confirmation uniquement après succès. Mots-clés étendus (négocie, remise, livraison gratuite, auto-accept) |
| 05/09/2026 | Shop Config Bug — Tests (17 nouveaux) | ✅ Terminé | test_shop_config_persistence.py : règle claire→update appelé (1), incomplète→clarification (1), confirmation après succès (1), échec API→message d'erreur (1), incohérent→avertissement (2: marge+remise>100%, auto_accept>max_discount), multi-règles→un appel (1), _parse_extraction_response (5), _validate_config_coherence (5). 314 tests total, 0 régression |
