# MANTOTA — Spécification Admin Panel

> Document de conception — Admin Panel sur sous-domaine séparé (`admin.mantota.com`)
> Caché du public, accessible uniquement aux administrateurs authentifiés.
> Stack : React 18 (Vite) + TailwindCSS + React-Leaflet | API Laravel (Sanctum token auth)

---

## Architecture

### Sécurité & Accès
- **Sous-domaine dédié** : `admin.mantota.com` (non indexé, pas de liens publics)
- **Auth** : email + mot de passe (admin uniquement, pas d'OTP)
- **Token API** : Laravel Sanctum (bearer token, expiration 8h)
- **Headers de sécurité** : `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, CSP strict
- **Rate limiting** : 5 tentatives de login / 15 min, lock IP après 10 échecs
- **Audit log** : toutes les actions admin sont tracées (qui, quoi, quand, IP)
- **Mode Fantôme** : impersonation d'un utilisateur (super_admin uniquement)

### Stack Frontend
- **React 18** + Vite (build rapide, HMR)
- **TailwindCSS** (design system Mantota : teal #0BBFA0, dark sidebar)
- **React-Leaflet** (carte interactive, OpenStreetMap tiles)
- **React Router v6** (navigation SPA)
- **Axios** (HTTP client avec intercepteur de token)
- **Recharts** (graphiques)
- **Lucide React** (icônes)

### Stack Backend (API)
- **Laravel 12** — nouveaux endpoints `/api/admin/*` (JSON, pas Inertia)
- **Sanctum** — authentification par token
- **Middleware** : `auth:sanctum` + `role:admin` + `admin.ip` (IP allowlist)
- **Cache** : Redis pour les KPIs (10 min TTL)

---

## Pages — Conception complète

### 1. Auth

#### 1.1 Login
- Formulaire email + mot de passe
- Rate limiting visible (compteur de tentatives restantes)
- Pas de lien "créer un compte" (accès admin sur invitation uniquement)
- Récupération IP (si IP changée, formulaire de récupération par email)

#### 1.2 Récupération IP
- Saisie email + nouvelle IP → envoi email de confirmation
- Permet à l'admin de mettre à jour son IP si elle a changé

---

### 2. Pilotage temps réel

#### 2.1 Live Dashboard
**Données temps réel :**
- Compteurs live : utilisateurs en ligne, commandes en cours, paiements du jour
- **Carte interactive** : tous les marqueurs de boutiques (shop_latitude/longitude) avec clusters
  - Filtres : par pays, par plan (free/starter/standard/pro), par statut KYC
  - Popup marqueur : nom boutique, vendeur, plan, nombre de produits, statut
  - Heat map optionnelle : densité de boutiques par zone
- Graphiques :
  - Revenus MANTOTA (markups + commissions + fees) par mois (6 derniers)
  - Nouveaux utilisateurs par jour (buyers, vendors, créateurs)
  - Volume escrow actif
- Alertes critiques : KYC en attente, retraits en attente, litiges non résolus, messages suspects
- Sparklines : dépôts, nouveaux vendeurs, nouveaux créateurs (7 derniers jours)

**Modèles :** User, Order, Transaction, Wallet, Product

#### 2.2 Centre d'opérations
- **Flux d'activité live** : derniers événements plateforme (inscriptions, commandes, paiements, litiges, KYC soumis)
- **Interventions rapides** : actions en 1 clic depuis le flux (valider KYC, approuver retrait, bloquer user)
- **File d'alertes** : alertes triées par priorité (critique → info)
- **Statut Tracy Core** : santé du bot, nombre de conversations actives, taux de conversion des négociations

**Modèles :** User, Order, Transaction, SecurityEvent, WhatsappConnection

#### 2.3 Carte géographique
- **Vue carte plein écran** avec tous les marqueurs
- Filtres avancés :
  - Par type (boutiques, utilisateurs, commandes en cours)
  - Par pays / région
  - Par période (aujourd'hui, 7j, 30j, tout)
- **Heat map** : densité d'activité par zone
- **Zones d'opportunité** : zones avec beaucoup d'acheteurs mais peu de vendeurs
- **Export données** : CSV des boutiques visibles sur la carte

**Modèles :** User (shop_latitude/longitude), Order (country/city), PageVisit (country)

---

### 3. Business Intelligence

#### 3.1 Croissance & Rétention
- **Funnel d'onboarding vendeur** : inscrit → KYC soumis → KYC validé → 1er produit → 1ère vente
  - Voir à quelle étape les vendeurs bloquent
  - Taux de conversion par étape
- **Cohortes** : rétention par mois d'inscription (quand reviennent-ils ?)
- **Churn** : vendeurs inactifs (pas de commande depuis 30j/60j/90j)
- **MRR** : revenus récurrents mensuels (abonnements Tracy)

**Modèles :** User, KycLog, Product, Order, Transaction (type=deposit pour abonnement)

#### 3.2 Revenus & Commissions
- **Breakdown par source** : abonnements, commissions transaction, frais de retrait, markups passerelle
- **Évolution mensuelle** : graphique stacked par source de revenu
- **Simulateur de frais** : sliders pour commission (%) et frais de retrait (%) → projection de revenu
- **Top contributeurs** : vendeurs qui génèrent le plus de commissions plateforme

**Modèles :** Transaction (mantota_markup, gateway_fee, type), Order (commission_amount)

#### 3.3 Performance par pays
- **Tableau** : par pays → utilisateurs, boutiques, commandes, revenus, GMV
- **Carte choroplèthe** : intensité de couleur selon le revenu généré
- **Opportunités d'expansion** : pays avec demande (visiteurs) mais peu de vendeurs
- **Devises utilisées** : quelles devises par pays, volumes convertis

**Modèles :** User (country), Order (country), Transaction, PageVisit (country_code), Currency

---

### 4. Gestion Communauté

#### 4.1 Utilisateurs unifiés
- **Tableau unique** : tous les users avec filtres par rôle, mode, pays, statut KYC, statut bannissement
- **Vue 360°** (clic sur un user) :
  - Profil : nom, email, téléphone, pays, photo, date inscription
  - Modes actifs : buyer / vendor / partner (toggle on/off)
  - Wallet : balance, escrow, pending, referral, statut lock
  - Commandes : en tant que vendeur (vendues) + en tant qu'acheteur (achetées)
  - Boutique : nom, logo, adresse, GPS, plan, nombre produits
  - Réseaux sociaux : TikTok, Instagram, Facebook, YouTube, Snapchat + followers
  - Transactions : historique complet
  - KYC : statut, documents, historique
  - Parrainage : qui a parrainé, combien de filleuls, gains referral
- **Actions** : bannir/débloquer, locker wallet, créditer wallet, envoyer email, activer/désactiver mode, promouvoir admin (super_admin)

**Modèles :** User, UserMode, Wallet, Order, Product, Transaction, KycLog

#### 4.2 Onboarding vendeurs
- **Funnel visuel** : inscrit → KYC → 1er produit → 1ère vente
- **Liste des vendeurs bloqués** : à quelle étape, depuis combien de temps
- **Actions de relance** : envoyer un email/sms de relance personnalisé
- **Statistiques** : temps moyen entre chaque étape, taux de drop-off

**Modèles :** User (role=vendor), KycLog, Product, Order

#### 4.3 Créateurs de contenu
- **Classement par engagement** : pas juste followers — score = (vues converties en ventes / vues totales)
- **Réseaux sociaux** : total followers par plateforme, évolution
- **Services UGC** : services proposés (ugc_humain, video_pub_ia), prix, nombre de commandes
- **Demandes VIP** : file d'approbation (vip_requested_at non null)
- **Actions** : approuver/rejeter VIP, toggle ambassadeur

**Modèles :** User (role=influencer), InfluencerService, ServiceOrder, Campaign, SmartLink, ClickLog

#### 4.4 Ambassadeurs
- **Liste des ambassadeurs** : avec tier, source, date inscription, expiration
- **Performance par ambassadeur** : nombre de filleuls, revenus générés par les filleuls
- **Gestion abonnements** : étendre, révoquer, changer tier
- **Code de parrainage** : générer et suivre les codes

**Modèles :** User (is_ambassador, ambassador_tier, referral_code), User (referred_by)

---

### 5. Boutiques & Catalogue

#### 5.1 Carte des boutiques
- **Carte interactive plein écran** avec marqueurs pour chaque boutique (shop_latitude/longitude)
- **Clusters** : regroupement automatique par zone (zoom-dependent)
- **Filtres** :
  - Par plan : free / starter / standard / pro
  - Par statut KYC : validé / en attente / rejeté
  - Par pays
  - Par nombre de produits (min/max)
  - Par date d'inscription
- **Popup marqueur** :
  - Nom boutique + logo
  - Nom du vendeur + téléphone
  - Plan actuel
  - Nombre de produits
  - Statut KYC
  - Lien vers la fiche détaillée
- **Vue liste** basculable (tableau avec tri)
- **Export CSV** des boutiques filtrées

**Modèles :** User (shop_name, shop_latitude, shop_longitude, shop_logo_path, bot_plan), Product (count par vendor)

#### 5.2 Qualité des boutiques
- **Scoring automatique** : note calculée sur critères :
  - Photos produits (présence + qualité)
  - Description produits (longueur + clarté)
  - Temps de réponse moyen (via Tracy)
  - Notes clients (si avis implémentés)
  - Taux de litige
  - Taux de livraison à temps
- **Classement** : top boutiques / boutiques à risque
- **Actions** : contacter le vendeur, proposer améliorations, flag pour révision

**Modèles :** Product, ProductImage, Order (delivery_deadline, status=disputed), OrderDisputeMessage

#### 5.3 Modération produits
- **File de validation** : produits signalés ou auto-flaggés
- **Critères de signalement** : prix anormal, description suspecte, image manquante, stock = 0
- **Actions** : approuver, suspendre, supprimer, contacter vendeur
- **Vue produit** : images, description, prix, stock, type (physique/digital), commission %

**Modèles :** Product, ProductImage

#### 5.4 Gestion des plans
- **Configuration plans freemium** :
  - Free : 1 boutique, 10 produits, Tracy app + WhatsApp essai (50 conv/mois, hybride 60s, 0 relance)
  - Starter : 2 500 FCFA/mois — 1 boutique, 50 produits, Tracy active + WhatsApp illimité (hybride 30s, 10 relances/jour)
  - Standard : 12 000 FCFA/mois — 3 boutiques, 200 produits, Tracy + WhatsApp auto 24/7 + relances illimitées + catalogue sync
  - Pro : 25 000 FCFA/mois — boutiques illimitées, Tracy + WhatsApp auto + analytics + campagnes + priorité
- **Liste abonnés** : qui est sur quel plan, date d'expiration, revenus par plan
- **Actions** : changer plan, étendre, révoquer
- **Évolution** : upgrades/downgrades par mois

**Modèles :** User (bot_plan), Transaction (type=deposit, abonnement), WhatsappConnection (monthly_conversation_limit)

---

### 6. Finance & Escrow

#### 6.1 Cockpit financier
- **Cashflow temps réel** :
  - Entrées : dépôts, abonnements, commissions
  - Sorties : retraits, remboursements
  - Escrow actif : total fonds bloqués
  - Liquidité plateforme : balance MANTOTA (non-escrow)
- **Projections** : sorties prévues (retraits en attente, escrow à libérer)
- **Graphique** : cashflow sur 30j / 90j / 12 mois
- **Alertes** : liquidité faible, escrow anormal, pic de retraits

**Modèles :** Transaction, Wallet (escrow_balance, balance), Order (amount_paid, vendor_earnings)

#### 6.2 Payouts (Retraits)
- **File de validation** : retraits en attente avec détails user, montant, méthode (mobile money)
- **Validation en lot** : sélectionner plusieurs → approuver/rejeter
- **Détection d'anomalies** :
  - Montant inhabituel (> 3x la moyenne)
  - Compte récent (< 7 jours)
  - KYC non validé
  - Wallet bloqué
- **Historique** : tous les retraits avec statut
- **Export** : CSV pour comptabilité

**Modèles :** Transaction (type=withdrawal, status=pending), User, Wallet, KycLog

#### 6.3 Fraude & Anomalies
- **Détection automatique** :
  - Transactions suspectes (montant, fréquence, pattern)
  - Multi-comptes (même téléphone, même IP, même appareil)
  - Comportements anormaux (tentatives de contournement escrow)
  - Retraits immédiats après dépôt (potentiel blanchiment)
- **File de investigation** : cas suspects à examiner
- **Actions** : bloquer wallet, bannir user, bloquer IP, créer ticket
- **Règles configurables** : seuils de détection ajustables

**Modèles :** Transaction, User, Wallet, SecurityEvent, BlockedIp, PageVisit (IP)

#### 6.4 Passerelles & Devises
- **Passerelles de paiement** : config FedaPay / Moneroo
  - Statut (actif/inactif)
  - Pays couverts
  - Frais de passerelle
  - Test de connexion
- **Devises** : CRUD complet
  - Code, nom, symbole, taux de change vers FCFA
  - Pays associés
  - Activer/désactiver
- **Historique des taux** : évolution des taux de change

**Modèles :** Gateway, Currency

---

### 7. Commandes & Livraison

#### 7.1 Suivi commandes live
- **Toutes les commandes** avec filtres : statut, pays, vendeur, période, montant
- **Vue carte** : commandes en cours sur la carte (country/city)
- **Timeline** : création → paiement → expédition → livraison → escrow libéré
- **Détail commande** :
  - Référence, statut, montant (amount_paid, commission, vendor_earnings, delivery_fee)
  - Client (nom, téléphone, whatsapp, email, adresse, ville, pays)
  - Livraison (company, livreur, deadline, tracking_token, PIN)
  - Escrow : statut du séquestre
  - Litige : raison, défense vendeur, messages
- **Actions** : rembourser client, favor vendeur, forcer libération escrow
- **Export** : CSV

**Modèles :** Order, User (vendor), Product, OrderDisputeMessage, Transaction

#### 7.2 Performance livraison
- **Stats par service** : Gozem, Yango, Rema, Kaba, autre
  - Temps moyen de livraison
  - Taux de livraison à temps vs retard
  - Taux d'échec / annulation
  - Volume par service
- **Retards actifs** : commandes en retard (isOverdue)
- **Classement des livreurs** : par nombre de livraisons, taux de succès
- **Graphique** : évolution des temps de livraison par service

**Modèles :** Order (delivery_company, delivery_deadline, status, isOverdue)

#### 7.3 Litiges & Résolution
- **Liste litiges** : actifs / résolus, avec filtres
- **Centre de résolution** :
  - Chat complet (client ↔ vendeur ↔ admin)
  - Preuves (photos, messages)
  - Historique de la commande
  - Décision assistée : recommandation basée sur les preuves
- **Actions** : rembourser client, favor vendeur, split (partiel)
- **Stats** : taux de litige par vendeur, temps moyen de résolution

**Modèles :** Order (status=disputed), OrderDisputeMessage, User, Product

#### 7.4 Commandes UGC / Services
- **Liste des commandes de services créateurs** (ServiceOrder)
- **Statuts** : pending → shooting → delivered → revision → completed / disputed
- **Détail** : brief, vidéo livrée, révisions (utilisées / autorisées), sample shipping
- **Chat** : messages entre vendeur et créateur
- **Litiges UGC** : remboursement vendeur ou favor créateur

**Modèles :** ServiceOrder, InfluencerService, User (vendor + influencer), ServiceOrderMessage

---

### 8. Tracy Core / IA

#### 8.1 Pilotage Tracy
- **Statut bot** : santé Tracy Core (API reachable, latency, uptime)
- **Connexions WhatsApp** : toutes les connexions actives avec statut
  - Vendeur, numéro, statut (connected/disconnected)
  - Tracy active (on/off), mode hybride (délai)
  - Conversations du mois (count / limit)
- **Conversations actives** : nombre, canaux (app / WhatsApp)
- **Performance** :
  - Taux de conversion des négociations (message → commande)
  - Temps moyen de réponse
  - Nombre de relances envoyées
  - Taux de satisfaction (si feedback implémenté)
- **Graphique** : activité Tracy par heure / jour

**Modèles :** WhatsappConnection, Conversation, ConversationMessage, Order (via Tracy)

#### 8.2 Configuration IA
- **Paramètres globaux Tracy** :
  - Délai mode hybride par défaut (secondes avant que Tracy réponde)
  - Limites de conversations par plan
  - Personnalité (ton, style de négociation)
  - Règles de négociation par défaut (ShopNegotiationConfig)
    - min_margin_percent, max_discount_percent
    - first_order_discount_percent
    - free_shipping_threshold
    - auto_accept_below
- **Config par boutique** : override des règles globales
- **Templates de relance** : messages de suivi configurables
- **Test Tracy** : interface de chat de test pour valider la config

**Modèles :** ShopNegotiationConfig, WhatsappConnection, Setting

#### 8.3 Logs & Analytics IA
- **Conversations marquantes** : meilleures négociations, échecs, conversations flaggées
- **Erreurs Tracy** : logs d'erreurs, timeouts, fallbacks
- **Outils utilisés** : fréquence d'utilisation de chaque tool Tracy (search_product, create_order, etc.)
- **Apprentissage** : mémoires clients (MemoryEntry), patterns détectés
- **Filtres** : par vendeur, par période, par tool, par résultat

**Modèles :** Conversation, ConversationMessage, MemoryEntry, Setting

---

### 9. Trust & Safety

#### 9.1 KYC Pipeline
- **File de validation visuelle** :
  - Photo pièce d'identité (recto/verso)
  - Selfie
  - Date d'expiration de la pièce
  - Score de risque (pays, âge compte, activité)
- **Actions** : approuver, rejeter (avec raison), demander plus de documents
- **Historique KYC** : tous les KYC avec statut et décision
- **Stats** : temps moyen de validation, taux d'approbation

**Modèles :** User (kyc_status, kyc_document_front/back/selfie, id_card_expiry), KycLog

#### 9.2 Modération communautaire
- **Messages suspects** : flaggés par l'IA (contenu inapproprié, spam, arnaque)
- **Signalements users** : reports faits par d'autres utilisateurs
- **Actions en masse** : supprimer messages, bannir users, bloquer IPs
- **Règles de modération** : mots-clés, patterns, seuils configurables

**Modèles :** ConversationMessage (flagged), SecurityEvent, User, BlockedIp

#### 9.3 Sécurité plateforme
- **Événements sécurité** : intrusions, logins échoués, accès non autorisés
  - Filtres : par type, par IP, par user, par période
- **IPs bloquées** : gestion de la blocklist
  - Ajouter / supprimer / bloquer permanent
  - Raison du blocage
- **Appareils de confiance admin** : liste des devices enregistrés
  - Ajouter / supprimer
- **Graphique** : événements de sécurité par jour, par type

**Modèles :** SecurityEvent, BlockedIp, AdminTrustedDevice

---

### 10. Growth & Marketing

#### 10.1 Campagnes
- **Liste campagnes** : toutes les campagnes (système + vendor)
  - Filtres : statut (draft/active/paused/completed), vendeur, tier, période
- **Créer / éditer campagne** :
  - Titre, description, URL cible, média
  - Budget total, CPC, commission %
  - Tier (Open Sea / Cercle Restreint)
  - Pays cibles, plateformes, niche
  - Mode de participation (ouvert / sur invitation)
  - Max participants
- **Détail campagne** :
  - Smart links générés, clicks, conversions
  - Budget consommé vs restant
  - Créateurs participants
  - Commandes générées
  - ROI (dépenses vs ventes)
- **Actions** : pause / reprise, suppression

**Modèles :** Campaign, SmartLink, ClickLog, Order, User (vendor)

#### 10.2 Notifications push
- **Envoi ciblé** : par segment (pays, rôle, mode, comportement)
- **Templates** : titre + corps + action (ouvrir app, ouvrir produit, ouvrir boutique)
- **Historique** : notifications envoyées, taux d'ouverture
- **Programmation** : envoi immédiat ou différé

**Modèles :** User (segmentation), Notification (à créer), FCM

#### 10.3 Emails
- **Templates** : éditeur visuel (HTML)
- **Envoi groupé** : à tous les users, par segment, ou users sélectionnés
- **Historique** : emails envoyés, open rate, click rate
- **Test** : envoi de test avant diffusion

**Modèles :** AdminEmail, User

#### 10.4 Annonces plateforme
- **Bannières in-app** : texte, type (info/warning/success), période d'affichage
- **Ciblage** : tous les users, par rôle, par mode
- **CRUD** : créer, éditer, supprimer, activer/désactiver
- **Programmation** : date de début / fin

**Modèles :** Announcement

#### 10.5 Témoignages
- **CRUD témoignages** : nom, photo, texte, note (1-5), ordre d'affichage
- **Activer / désactiver** : contrôle de la visibilité
- **Témoignages vedettes** : sélection pour la landing page

**Modèles :** Testimonial

#### 10.6 Partenaires
- **CRUD partenaires** : nom, logo, URL, description
- **Activer / désactiver**
- **Ordre d'affichage**

**Modèles :** Partner

---

### 11. Analytics

#### 11.1 Top créateurs
- **Classement** : par earnings, par vues converties, par score d'engagement
- **Période** : 7j / 30j / 90j / tout
- **Détail** : clics générés, ventes converties, revenus, campagnes participées
- **Évolution** : graphique de performance dans le temps

**Modèles :** User (role=influencer), SmartLink, ClickLog, Transaction (type=earning), Order (influencer_id)

#### 11.2 Top vendeurs
- **Classement** : par volume de ventes, par nombre de commandes, par revenus générés
- **Période** : 7j / 30j / 90j / tout
- **Détail** : produits vendus, panier moyen, taux de litige, note clients
- **Évolution** : graphique de croissance

**Modèles :** User (role=vendor), Order, Product, Transaction

#### 11.3 Visiteurs
- **Analytics trafic** :
  - Visiteurs uniques, sessions, pages vues par jour
  - Device type (mobile / desktop / tablet)
  - Pays, ville
  - Page d'entrée, referrer
  - Temps moyen sur site
- **Graphique** : trafic sur 7j / 30j / 90j
- **Top pages** : pages les plus visitées
- **Heat map géographique** : visiteurs par pays

**Modèles :** PageVisit

---

### 12. Système

#### 12.1 Réglages globaux
- **Config plateforme** :
  - Nom, logo, email contact
  - Frais de retrait (%)
  - Commission transaction (%)
  - Markup passerelle par défaut (%)
  - Délai mode hybride Tracy par défaut
  - Limites conversations par plan
- **Modes activables** : buyer (toujours on), vendor, partner, livreur (grisé)
- **Sauvegarde** : toutes les modifications sont audit-tracked

**Modèles :** Setting, AuditLog

#### 12.2 Audit & Traçabilité
- **Toutes les actions admin** : qui, quoi, quand, IP, user agent
- **Filtres** : par admin, par action, par cible, par période
- **Recherche** : par user ID, par type d'action
- **Export** : CSV pour conformité

**Modèles :** AuditLog

#### 12.3 Santé système
- **Serveur** : CPU, RAM, disk, uptime
- **Base de données** : connexions, taille, lenteur queries
- **Queue** : jobs en attente, jobs échoués
- **API** : latency, taux d'erreur
- **Tracy Core** : statut, latency, conversations actives
- **Redis** : connexions, mémoire utilisée
- **Alertes** : config alertes email pour seuils critiques
- **Actions** : run check manuel, clear log

**Modèles :** Setting, SecurityEvent, AuditLog

#### 12.4 Sauvegarde & Restauration
- **Download backup BDD** : dump PostgreSQL
- **Historique des backups** : date, taille, téléchargement
- **Restauration** : upload d'un dump + restauration (super_admin uniquement)

**Modèles :** N/A (filesystem + pg_dump)

---

## Navigation (Sidebar)

```
┌─────────────────────────┐
│  MANTOTA Admin          │
│  admin.mantota.com      │
├─────────────────────────┤
│ PILOTAGE                │
│  ├ Dashboard            │
│  ├ Centre d'opérations  │
│  └ Carte géographique   │
├─────────────────────────┤
│ BUSINESS                │
│  ├ Croissance           │
│  ├ Revenus              │
│  └ Performance pays     │
├─────────────────────────┤
│ COMMUNAUTÉ              │
│  ├ Utilisateurs         │
│  ├ Onboarding vendeurs  │
│  ├ Créateurs            │
│  └ Ambassadeurs         │
├─────────────────────────┤
│ BOUTIQUES               │
│  ├ Carte des boutiques  │
│  ├ Qualité              │
│  ├ Modération produits  │
│  └ Plans vendeurs       │
├─────────────────────────┤
│ FINANCE                 │
│  ├ Cockpit financier    │
│  ├ Payouts              │
│  ├ Fraude & anomalies   │
│  └ Passerelles & devises│
├─────────────────────────┤
│ COMMANDES               │
│  ├ Commandes live       │
│  ├ Performance livraison│
│  ├ Litiges              │
│  └ Commandes UGC        │
├─────────────────────────┤
│ TRACY CORE              │
│  ├ Pilotage Tracy       │
│  ├ Configuration IA     │
│  └ Logs & analytics     │
├─────────────────────────┤
│ TRUST & SAFETY          │
│  ├ KYC Pipeline         │
│  ├ Modération           │
│  └ Sécurité             │
├─────────────────────────┤
│ GROWTH                  │
│  ├ Campagnes            │
│  ├ Notifications push   │
│  ├ Emails               │
│  ├ Annonces             │
│  ├ Témoignages          │
│  └ Partenaires          │
├─────────────────────────┤
│ ANALYTICS               │
│  ├ Top créateurs        │
│  ├ Top vendeurs         │
│  └ Visiteurs            │
├─────────────────────────┤
│ SYSTÈME                 │
│  ├ Réglages globaux     │
│  ├ Audit log            │
│  ├ Santé système        │
│  └ Sauvegarde           │
├─────────────────────────┤
│  [Avatar] Admin Name    │
│  Mode Fantôme: [OFF]    │
│  Déconnexion            │
└─────────────────────────┘
```

---

## API Endpoints (à créer côté Laravel)

### Auth
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/admin/login` | Login admin → retourne token Sanctum |
| POST | `/api/admin/logout` | Logout + revoke token |
| GET | `/api/admin/me` | Profil admin connecté |
| POST | `/api/admin/recover-ip` | Récupération IP |

### Dashboard & Ops
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/admin/dashboard` | KPIs globaux + sparklines + alertes |
| GET | `/api/admin/live-feed` | Flux d'activité temps réel |
| GET | `/api/admin/map/shops` | Toutes les boutiques avec lat/lng |
| GET | `/api/admin/map/users` | Users par pays |
| GET | `/api/admin/map/orders` | Commandes en cours par pays |

### Business Intelligence
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/admin/growth/funnel` | Funnel onboarding vendeur |
| GET | `/api/admin/growth/retention` | Cohortes de rétention |
| GET | `/api/admin/revenue/breakdown` | Revenus par source |
| GET | `/api/admin/revenue/simulate` | Simulateur de frais |
| GET | `/api/admin/countries/performance` | Performance par pays |

### Utilisateurs
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/admin/users` | Liste paginée avec filtres |
| GET | `/api/admin/users/{id}` | Vue 360° d'un user |
| PATCH | `/api/admin/users/{id}/ban` | Bannir/débloquer |
| PATCH | `/api/admin/users/{id}/wallet-lock` | Locker/délocker wallet |
| POST | `/api/admin/users/{id}/credit-wallet` | Créditer wallet |
| PATCH | `/api/admin/users/{id}/modes` | Activer/désactiver mode |
| POST | `/api/admin/users/{id}/send-email` | Envoyer email |
| POST | `/api/admin/admins` | Créer admin (super_admin) |
| DELETE | `/api/admin/admins/{id}` | Supprimer admin (super_admin) |
| POST | `/api/admin/impersonate/{id}` | Mode fantôme |

### Boutiques
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/admin/shops` | Liste boutiques avec filtres |
| GET | `/api/admin/shops/{id}` | Détail boutique + produits + stats |
| GET | `/api/admin/shops/map` | Boutiques avec lat/lng pour carte |
| GET | `/api/admin/shops/quality-scores` | Scores qualité boutiques |
| GET | `/api/admin/products` | Tous les produits (modération) |
| PATCH | `/api/admin/products/{id}/status` | Suspendre/approuver produit |

### Finance
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/admin/finance/cashflow` | Cashflow temps réel |
| GET | `/api/admin/finance/escrow` | Escrow actif |
| GET | `/api/admin/withdrawals` | Retraits en attente |
| PATCH | `/api/admin/withdrawals/{id}/approve` | Approuver retrait |
| PATCH | `/api/admin/withdrawals/{id}/reject` | Rejeter retrait |
| GET | `/api/admin/fraud/alerts` | Alertes fraude |
| GET | `/api/admin/gateways` | Passerelles paiement |
| PUT | `/api/admin/gateways/{id}` | Modifier passerelle |
| GET | `/api/admin/currencies` | Devises |
| POST | `/api/admin/currencies` | Créer devise |
| PUT | `/api/admin/currencies/{id}` | Modifier devise |

### Commandes
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/admin/orders` | Toutes les commandes |
| GET | `/api/admin/orders/{id}` | Détail commande |
| GET | `/api/admin/orders/delivery-stats` | Stats livraison par service |
| GET | `/api/admin/disputes` | Litiges |
| GET | `/api/admin/disputes/{id}` | Détail litige + chat |
| PATCH | `/api/admin/disputes/{id}/refund` | Rembourser client |
| PATCH | `/api/admin/disputes/{id}/favor-vendor` | Favor vendeur |
| GET | `/api/admin/service-orders` | Commandes UGC |
| GET | `/api/admin/service-orders/{id}` | Détail UGC + chat |

### Tracy Core
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/admin/tracy/status` | Statut Tracy Core |
| GET | `/api/admin/tracy/whatsapp-connections` | Connexions WhatsApp |
| GET | `/api/admin/tracy/conversations` | Conversations actives |
| GET | `/api/admin/tracy/performance` | Métriques performance |
| GET | `/api/admin/tracy/config` | Config globale Tracy |
| PUT | `/api/admin/tracy/config` | Modifier config globale |
| GET | `/api/admin/tracy/logs` | Logs Tracy |

### Trust & Safety
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/admin/kyc` | KYC en attente |
| PATCH | `/api/admin/kyc/{id}/approve` | Approuver KYC |
| PATCH | `/api/admin/kyc/{id}/reject` | Rejeter KYC |
| GET | `/api/admin/flagged-messages` | Messages suspects |
| GET | `/api/admin/security/events` | Événements sécurité |
| GET | `/api/admin/security/blocked-ips` | IPs bloquées |
| POST | `/api/admin/security/block-ip` | Bloquer IP |
| DELETE | `/api/admin/security/blocked-ips/{id}` | Débloquer IP |
| GET | `/api/admin/security/trusted-devices` | Appareils de confiance |
| DELETE | `/api/admin/security/trusted-devices/{id}` | Supprimer device |

### Growth
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/admin/campaigns` | Liste campagnes |
| POST | `/api/admin/campaigns` | Créer campagne |
| GET | `/api/admin/campaigns/{id}` | Détail campagne |
| PUT | `/api/admin/campaigns/{id}` | Modifier campagne |
| POST | `/api/admin/campaigns/{id}/toggle-pause` | Pause/reprise |
| DELETE | `/api/admin/campaigns/{id}` | Supprimer campagne |
| POST | `/api/admin/notifications/send` | Envoyer notification push |
| GET | `/api/admin/notifications/history` | Historique notifications |
| POST | `/api/admin/emails/send` | Envoyer email groupé |
| GET | `/api/admin/emails` | Historique emails |
| GET | `/api/admin/announcements` | Liste annonces |
| POST | `/api/admin/announcements` | Créer annonce |
| PUT | `/api/admin/announcements/{id}` | Modifier annonce |
| DELETE | `/api/admin/announcements/{id}` | Supprimer annonce |
| GET | `/api/admin/testimonials` | Liste témoignages |
| POST | `/api/admin/testimonials` | Créer témoignage |
| PUT | `/api/admin/testimonials/{id}` | Modifier témoignage |
| DELETE | `/api/admin/testimonials/{id}` | Supprimer témoignage |
| GET | `/api/admin/partners` | Liste partenaires |
| POST | `/api/admin/partners` | Créer partenaire |
| POST | `/api/admin/partners/{id}` | Modifier partenaire |
| DELETE | `/api/admin/partners/{id}` | Supprimer partenaire |

### Analytics
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/admin/rankings/creators` | Top créateurs |
| GET | `/api/admin/rankings/vendors` | Top vendeurs |
| GET | `/api/admin/visitors` | Analytics visiteurs |

### Système
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/admin/settings` | Réglages globaux |
| PUT | `/api/admin/settings` | Modifier réglages |
| POST | `/api/admin/settings/logo` | Upload logo |
| GET | `/api/admin/audit-logs` | Audit log |
| GET | `/api/admin/health` | Santé système |
| POST | `/api/admin/health/toggle-alerts` | Toggle alertes |
| POST | `/api/admin/health/run-check` | Run check manuel |
| GET | `/api/admin/backup/download` | Download backup BDD |

---

## Structure du projet React

```
admin-panel/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── .env
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── api/
│   │   ├── client.js          # Axios + intercepteur token
│   │   ├── auth.js            # Endpoints auth
│   │   ├── dashboard.js       # Endpoints dashboard
│   │   ├── users.js           # Endpoints users
│   │   ├── shops.js           # Endpoints boutiques
│   │   ├── finance.js         # Endpoints finance
│   │   ├── orders.js          # Endpoints commandes
│   │   ├── tracy.js           # Endpoints Tracy
│   │   ├── security.js        # Endpoints sécurité
│   │   ├── growth.js          # Endpoints growth
│   │   └── system.js          # Endpoints système
│   ├── contexts/
│   │   ├── AuthContext.jsx    # État auth + token
│   │   └── ThemeContext.jsx   # Dark/light mode
│   ├── components/
│   │   ├── Layout.jsx         # Layout principal (sidebar + topbar)
│   │   ├── Sidebar.jsx        # Navigation sidebar
│   │   ├── Topbar.jsx         # Barre supérieure (recherche, notifs, avatar)
│   │   ├── ProtectedRoute.jsx # Route guard (auth requise)
│   │   ├── Card.jsx           # Carte KPI réutilisable
│   │   ├── DataTable.jsx      # Tableau avec tri/pagination/filtres
│   │   ├── Modal.jsx          # Modal réutilisable
│   │   ├── Badge.jsx          # Badge statut
│   │   ├── Sparkline.jsx      # Mini graphique
│   │   ├── ChartLine.jsx      # Graphique ligne (Recharts)
│   │   ├── ChartBar.jsx       # Graphique barres
│   │   ├── ChartArea.jsx      # Graphique aire
│   │   ├── ShopMap.jsx        # Carte Leaflet boutiques
│   │   ├── HeatMap.jsx        # Heat map géographique
│   │   └── ImpersonationBanner.jsx # Banner mode fantôme
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── IpRecovery.jsx
│   │   ├── dashboard/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Operations.jsx
│   │   │   └── GeoMap.jsx
│   │   ├── business/
│   │   │   ├── Growth.jsx
│   │   │   ├── Revenue.jsx
│   │   │   └── CountryPerformance.jsx
│   │   ├── users/
│   │   │   ├── UsersList.jsx
│   │   │   ├── UserDetail.jsx
│   │   │   ├── VendorOnboarding.jsx
│   │   │   ├── Creators.jsx
│   │   │   └── Ambassadors.jsx
│   │   ├── shops/
│   │   │   ├── ShopsMap.jsx
│   │   │   ├── ShopQuality.jsx
│   │   │   ├── ProductModeration.jsx
│   │   │   └── VendorPlans.jsx
│   │   ├── finance/
│   │   │   ├── Cashflow.jsx
│   │   │   ├── Payouts.jsx
│   │   │   ├── Fraud.jsx
│   │   │   └── Gateways.jsx
│   │   ├── orders/
│   │   │   ├── OrdersLive.jsx
│   │   │   ├── DeliveryPerformance.jsx
│   │   │   ├── Disputes.jsx
│   │   │   └── ServiceOrders.jsx
│   │   ├── tracy/
│   │   │   ├── TracyStatus.jsx
│   │   │   ├── TracyConfig.jsx
│   │   │   └── TracyLogs.jsx
│   │   ├── safety/
│   │   │   ├── KycPipeline.jsx
│   │   │   ├── Moderation.jsx
│   │   │   └── Security.jsx
│   │   ├── growth/
│   │   │   ├── Campaigns.jsx
│   │   │   ├── CampaignDetail.jsx
│   │   │   ├── PushNotifications.jsx
│   │   │   ├── Emails.jsx
│   │   │   ├── Announcements.jsx
│   │   │   ├── Testimonials.jsx
│   │   │   └── Partners.jsx
│   │   ├── analytics/
│   │   │   ├── TopCreators.jsx
│   │   │   ├── TopVendors.jsx
│   │   │   └── Visitors.jsx
│   │   └── system/
│   │       ├── Settings.jsx
│   │       ├── AuditLog.jsx
│   │       ├── SystemHealth.jsx
│   │       └── Backup.jsx
│   └── styles/
│       └── index.css          # Tailwind + variables Mantota
└── public/
    └── favicon.ico
```

---

## Design System

### Couleurs
- **Primary** : Teal #0BBFA0 (Mantota)
- **Accent** : Coral #FF6B35
- **Dark** : #0F172A (sidebar, fond)
- **Light** : #F8FAFC (fond pages)
- **Success** : #22C55E
- **Warning** : #F59E0B
- **Danger** : #EF4444
- **Info** : #3B82F6

### Typographie
- **Font** : Inter (Google Fonts)
- **Titres** : 600/700 weight
- **Corps** : 400 weight, 14px base

### Composants
- **Cards** : fond blanc, border-radius 12px, shadow-sm, border gray-100
- **Sidebar** : fond dark (#0F172A), texte gray-300, icônes Lucide
- **Badges** : rounded-full, px-2.5, py-0.5, text-xs, couleur selon statut
- **Tableaux** : hover gray-50, header gray-100, pagination en bas
- **Boutons** : rounded-lg, primary teal, secondary gray, danger red

---

## Sécurité sous-domaine

### Configuration Nginx (admin.mantota.com)
```
server {
    listen 443 ssl http2;
    server_name admin.mantota.com;

    # SSL cert (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/admin.mantota.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.mantota.com/privkey.pem;

    # Headers de sécurité
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api.mantota.com;" always;

    # Pas de robots
    location = /robots.txt {
        return 200 "User-agent: *\nDisallow: /\n";
    }

    # Frontend React (build statique)
    root /var/www/admin-panel/dist;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy vers Laravel
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name admin.mantota.com;
    return 301 https://$host$request_uri;
}
```

### Protection anti-hacker
- **IP allowlist** : middleware `admin.ip` côté Laravel (seules IPs enregistrées peuvent accéder)
- **Rate limiting** : 5 req/min sur login, 100 req/min sur API générale
- **Audit log** : toutes les actions sont tracées avec IP + user agent
- **Session courte** : token Sanctum expire après 8h
- **2FA optionnel** : OTP via email pour connexions depuis nouvelle IP
- **Pas de CORS ouvert** : uniquement `admin.mantota.com` autorisé
- **Pas de directory listing** : Nginx désactive l'autoindex
- **HTTPS obligatoire** : redirect 301 HTTP → HTTPS

---

## Ordre de développement

1. **Setup projet React** (Vite + Tailwind + Leaflet + Router)
2. **API Laravel** : Sanctum + endpoints auth + dashboard
3. **Login + Layout + Sidebar**
4. **Dashboard + Carte des boutiques** (priorité utilisateur)
5. **Utilisateurs** (liste + détail 360°)
6. **Finance** (cashflow + payouts)
7. **Commandes + Litiges**
8. **Tracy Core** (pilotage + config)
9. **Trust & Safety** (KYC + sécurité)
10. **Growth** (campagnes + notifications)
11. **Analytics** (top créateurs + visiteurs)
12. **Système** (settings + audit + santé)
