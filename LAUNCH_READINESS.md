# MANTOTA - Plan de Lancement & Points Critiques

**Date:** 30 octobre 2026
**Repository:** https://github.com/odsystem-bit/tracy.git
**Objectif:** Lancement MVP via WhatsApp en priorité

---

## 🚨 POINTS CRITIQUES BLOQUANTS POUR LE LANCEMENT

### 1. CONFIGURATION WHATSAPP (HAUTE PRIORITÉ)

#### 1.1 Configuration Meta WhatsApp Business API
**Statut:** ⚠️ Code prêt, configuration manquante

**Ce qui existe:**
- ✅ `WhatsAppWebhookController` - Webhook réception messages
- ✅ `WhatsAppCloudService` - Envoi messages (texte, cartes, listes)
- ✅ `WhatsappConnection` - Model connexion vendeur
- ✅ Migration table `whatsapp_connections`
- ✅ Routes webhook configurées (`/api/whatsapp/webhook`)

**Ce qui manque:**
- ❌ Compte Meta Business créé
- ❌ WhatsApp Business App créée
- ❌ Phone Number ID obtenu
- ❌ Access Token généré
- ❌ Webhook configuré dans Meta Dashboard
- ❌ Variables .env configurées:
  ```env
  WHATSAPP_ACCESS_TOKEN=
  WHATSAPP_PHONE_NUMBER_ID=
  WHATSAPP_WABA_ID=
  WHATSAPP_API_VERSION=v21.0
  WHATSAPP_WEBHOOK_VERIFY_TOKEN=mantota_verify_2026
  ```

**Actions requises:**
1. Créer compte Meta Business (si pas déjà)
2. Créer WhatsApp Business App dans Meta for Developers
3. Obtenir Phone Number ID (acheter ou utiliser numéro existant)
4. Générer Access Token avec permissions:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
5. Configurer webhook dans Meta Dashboard:
   - URL: `https://votre-domaine.com/api/whatsapp/webhook`
   - Verify Token: `mantota_verify_2026`
   - Subscriptions: `messages`
6. Configurer variables .env
7. Tester webhook avec Meta Webhook Tester

**Estimation temps:** 2-4 heures

---

#### 1.2 Interface Admin pour Connexion WhatsApp Vendeurs
**Statut:** ❌ Non implémenté

**Ce qui est nécessaire:**
- Page admin "Connexions WhatsApp" pour les vendeurs
- Formulaire pour connecter numéro WhatsApp vendeur
- Stockage `phone_number_id`, `waba_id`, `access_token` par vendeur
- Toggle pour activer/désactiver Tracy sur WhatsApp
- Configuration mode hybride (délai avant réponse Tracy)
- Configuration limites mensuelles (free=50, paid=illimité)

**Actions requises:**
1. Créer controller `Admin/WhatsAppConnectionController`
2. Créer page React dans admin-panel
3. API endpoints:
   - `GET /api/admin/whatsapp/connections` - liste connexions
   - `POST /api/admin/whatsapp/connections` - créer connexion
   - `PUT /api/admin/whatsapp/connections/{id}` - modifier
   - `DELETE /api/admin/whatsapp/connections/{id}` - supprimer
4. Frontend React avec formulaire
5. Test complet du flux

**Estimation temps:** 1-2 jours

---

#### 1.3 Tests Intégration WhatsApp
**Statut:** ❌ Aucun test

**Tests nécessaires:**
1. Test webhook verify (GET)
2. Test webhook handle (POST) avec payload réel
3. Test forwardToTracyCore
4. Test sendText
5. Test sendProductCard
6. Test sendInteractiveList
7. Test limits conversationnelles
8. Test message d'image/audio (TODO actuel)

**Actions requises:**
1. Créer `tests/Feature/WhatsAppWebhookTest.php`
2. Mock Tracy Core response
3. Mock WhatsApp Cloud API
4. Tester tous les scénarios

**Estimation temps:** 4-6 heures

---

### 2. AUTHENTIFICATION OTP (BLOQUANT)

**Statut:** ❌ Non implémenté

**Actuel:** Email + password seulement
**Requis:** Phone + OTP (selon maquette)

**Ce qui manque:**
- ❌ Table `otp_codes` ou similaire
- ❌ Service envoi SMS OTP
- ❌ Vérification OTP
- ❌ Routes API OTP
- ❌ Integration SMS provider (Twilio, Africa's Talking, etc.)
- ❌ Frontend Flutter OTP screen (existe déjà)
- ❌ Frontend Web OTP screen

**Actions requises:**
1. Choisir provider SMS (Twilio, Africa's Talking, Termii)
2. Créer migration table `otp_codes`:
   ```php
   - phone
   - code
   - expires_at
   - verified_at
   - purpose (register, login, reset)
   ```
3. Créer `OtpService`:
   - Générer code 6 digits
   - Envoyer SMS
   - Vérifier code
   - Expiration (5 min)
4. Créer controller `Api/OtpAuthController`:
   - `POST /api/otp/send` - envoyer code
   - `POST /api/otp/verify` - vérifier code
5. Mettre à jour `User` model pour auth par phone
6. Mettre à jour Flutter (screen existe déjà)
7. Créer screen OTP web Laravel
8. Tests

**Estimation temps:** 2-3 jours

---

### 3. RÔLE BUYER (BLOQUANT)

**Statut:** ❌ Enum UserRole incomplet

**Actuel:** vendor, influencer, admin
**Requis:** buyer

**Actions requises:**
1. Modifier `app/Enums/UserRole.php`:
   ```php
   enum UserRole: string
   {
       case BUYER = 'buyer';
       case VENDOR = 'vendor';
       case INFLUENCER = 'influencer';
       case ADMIN = 'admin';
   }
   ```
2. Migration pour mettre à jour données existantes
3. Mise à jour permissions/middleware
4. Tests

**Estimation temps:** 2-3 heures

---

### 4. MODES ACTIVABLES (BLOQUANT)

**Statut:** ❌ Non implémenté

**Requis:** Un utilisateur peut activer/désactiver Buyer, Vendor, Partner sur le même compte

**Ce qui manque:**
- ❌ Table `user_modes` ou pivot table
- ❌ API endpoints pour activer/désactiver modes
- ❌ Frontend Flutter pour sélectionner modes
- ❌ Frontend Web pour sélectionner modes
- ❌ Logique validation (ex: pas de vendor sans KYC)

**Actions requises:**
1. Créer migration table `user_modes`:
   ```php
   - user_id
   - mode (buyer, vendor, partner)
   - is_active
   - activated_at
   ```
2. Créer model `UserMode`
3. Créer controller `Api/UserModeController`:
   - `GET /api/user/modes` - modes actifs
   - `POST /api/user/modes/{mode}/activate` - activer
   - `POST /api/user/modes/{mode}/deactivate` - désactiver
4. Update Flutter (screen mode_selection existe déjà)
5. Créer screen web mode selection
6. Logique validation:
   - Vendor: KYC requis
   - Partner: ambassadeur requis
7. Tests

**Estimation temps:** 1-2 jours

---

### 5. LIVRAISON (PRIORITÉ ÉLEVÉE)

**Statut:** ⚠️ Partiellement implémenté

**Ce qui existe:**
- ✅ Table `orders` avec champs livraison:
  - `delivery_company`
  - `delivery_fee`
  - `delivery_deadline`
  - `delivery_address`
  - `delivery_city`
  - `delivery_country`
  - `is_overdue`
- ✅ Endpoints geo:
  - `GET /api/bot/geo/resolve` - résolution ville/quartier
  - `GET /api/bot/geo/cities` - villes par pays
  - `GET /api/bot/geo/quartiers` - quartiers par ville
- ✅ Endpoints delivery:
  - `GET /api/bot/delivery/quartiers` - quartiers livrables
  - `POST /api/bot/delivery/quartiers` - ajouter quartier
  - `DELETE /api/bot/delivery/quartiers` - supprimer quartier
- ✅ Tracy peut calculer frais livraison

**Ce qui manque:**
- ❌ Intégration API services livraison (Gozem, Yango, Rema, Kaba)
- ❌ Interface admin pour configurer services
- ❌ Calcul automatique frais livraison par distance
- ❌ Tracking en temps réel
- ❌ Notifications statut livraison
- ❌ Interface client pour suivre livraison

**Actions requises:**

#### 5.1 Intégration Services Livraison
1. Choisir services à intégrer (priorité: Gozem, Yango)
2. Créer `DeliveryService` abstrait
3. Implémenter `GozemDeliveryService`:
   - API Gozem pour estimate price
   - API Gozem pour créer ride
   - API Gozem pour tracking
4. Implémenter `YangoDeliveryService` (similaire)
5. Configurer dans `config/services.php`

#### 5.2 Interface Admin
1. Page "Services de livraison"
2. CRUD services actifs
3. Configuration par service:
   - API key
   - Zones couvertes
   - Frais de base
   - Frais par km

#### 5.3 Frontend Client
1. Screen sélection service livraison
2. Screen suivi livraison (map)
3. Notifications statut

**Estimation temps:** 3-5 jours

---

### 6. CHAT TRACY UI (MOBILE)

**Statut:** ⚠️ Screen existe, non connecté

**Ce qui existe:**
- ✅ `tracy_channel_screen.dart` - Screen créé
- ✅ `tracy_chat_service.dart` - Service défini

**Ce qui manque:**
- ❌ Intégration réelle avec Tracy Core API
- ❌ WebSocket pour messages temps réel
- ❌ Gestion conversation_id
- ❌ Affichage Product Cards
- ❌ Tests

**Actions requises:**
1. Connecter `TracyChatService` à Tracy Core
2. Implémenter WebSocket (`web_socket_channel` déjà dans pubspec)
3. Gérer conversation_id persistant
4. Afficher Product Cards comme dans spec
5. Tests

**Estimation temps:** 1-2 jours

---

### 7. ÉCRAN DÉCOUVRIR (MOBILE + WEB)

**Statut:** ❌ Non implémenté

**Ce qui existe:**
- ✅ `discover_screen.dart` - Screen créé (vide)

**Ce qui manque:**
- ❌ API endpoint `/api/discover` ou similaire
- ❌ Contenu: produits tendances, boutiques recommandées, promos
- ❌ Implémentation Flutter
- ❌ Implémentation Web Laravel
- ❌ Tests

**Actions requises:**
1. Créer controller `DiscoverController` (Laravel)
2. Implémenter logique recommandation:
   - Produits populaires
   - Boutiques nearby
   - Promos actives
3. API endpoint
4. Implémenter Flutter screen
5. Implémenter Web page
6. Tests

**Estimation temps:** 2-3 jours

---

### 8. NOTIFICATIONS NATIVES (FCM/APNS)

**Statut:** ❌ Non implémenté

**Ce qui manque:**
- ❌ Configuration Firebase Cloud Messaging
- ❌ Configuration Apple Push Notification Service
- ❌ Service envoi notifications Laravel
- ❌ Intégration Flutter (firebase_messaging)
- ❌ Gestion tokens par device
- ❌ Templates notifications

**Actions requises:**
1. Créer projet Firebase
2. Configurer FCM
3. Ajouter `firebase_messaging` dans Flutter
4. Créer `NotificationService` Laravel
5. Stocker device tokens par user
6. Envoyer notifications sur événements:
   - Nouvelle commande
   - Statut commande
   - Message Tracy
   - Promotion
7. Tests

**Estimation temps:** 2-3 jours

---

### 9. STORE SCORE & TRUST

**Statut:** ❌ Non implémenté

**Ce qui manque:**
- ❌ Algorithme scoring boutique
- ❌ Metrics: qualité photos, réponse temps, notes, litiges
- ❌ Calcul automatique score
- ❌ Affichage score boutique
- ❌ Classement boutiques
- ❌ Badge "Trusted"

**Actions requises:**
1. Créer `ShopQualityService`
2. Implémenter algorithme scoring:
   - Photos produits (présence + qualité)
   - Temps de réponse moyen
   - Notes clients
   - Taux litige
   - Taux livraison à temps
3. Job calcul score quotidien
4. Affichage score sur fiche boutique
5. Admin page gestion scores
6. Tests

**Estimation temps:** 2-3 jours

---

### 10. CONTRACTS

**Statut:** ❌ Non implémenté

**Ce qui manque:**
- ❌ Model `Contract`
- ❌ Génération PDF
- ❌ Signature électronique
- ❌ Stockage documents
- ❌ Workflow contrat vendeur

**Actions requises:**
1. Créer model `Contract`
2. Implémenter génération PDF (dompdf/snappy)
3. Intégration signature (DocuSign ou similaire)
4. Workflow: création → signature → stockage
5. Admin page gestion contrats
6. Tests

**Estimation temps:** 3-4 jours

---

## 📋 PLAN D'ACTION PRIORITAIRE (LAUNCH WHATSAPP)

### PHASE 1: FONDATION WHATSAPP (1 semaine)

**Objectif:** Tracy fonctionnelle sur WhatsApp

#### Jour 1-2: Configuration Meta WhatsApp
- [ ] Créer compte Meta Business
- [ ] Créer WhatsApp Business App
- [ ] Obtenir Phone Number ID et Access Token
- [ ] Configurer webhook Meta Dashboard
- [ ] Configurer variables .env
- [ ] Tester webhook verify

#### Jour 3: Tests WhatsApp
- [ ] Créer tests webhook
- [ ] Tester réception message
- [ ] Test envoi réponse Tracy
- [ ] Test envoi Product Cards
- [ ] Test envoi listes interactives
- [ ] Debug et fix

#### Jour 4-5: Interface Admin WhatsApp
- [ ] Créer controller Admin WhatsApp
- [ ] Créer API endpoints
- [ ] Créer page React admin
- [ ] Formulaire connexion vendeur
- [ ] Test flux admin → vendeur

#### Jour 6-7: End-to-End Test
- [ ] Test complet: client WhatsApp → Tracy → réponse
- [ ] Test avec plusieurs vendeurs
- [ ] Test limites conversationnelles
- [ ] Documentation setup vendeur
- [ ] Debug final

---

### PHASE 2: LIVRAISON MINIMUM (3-5 jours)

**Objectif:** Livraison fonctionnelle basique

#### Option 1: Livraison manuelle ( rapide)
- [ ] Interface admin pour marquer "livré"
- [ ] Client peut voir statut
- [ ] Pas d'intégration API externe
- [ ] Temps: 1-2 jours

#### Option 2: Intégration Gozem (complet)
- [ ] Intégration API Gozem
- [ ] Estimate price
- [ ] Create ride
- [ ] Tracking
- [ ] Temps: 3-5 jours

**Recommandation:** Commencer avec livraison manuelle pour MVP, intégrer Gozem après lancement.

---

### PHASE 3: AUTH OTP (2-3 jours)

**Objectif:** Auth par téléphone pour lancement mobile

- [ ] Choisir provider SMS
- [ ] Créer table otp_codes
- [ ] Créer OtpService
- [ ] Créer API endpoints
- [ ] Update UserRole enum
- [ ] Tests

---

### PHASE 4: MODES ACTIVABLES (1-2 jours)

**Objectif:** Permettre multi-rôles sur un compte

- [ ] Créer table user_modes
- [ ] Créer API endpoints
- [ ] Update Flutter (screen existe)
- [ ] Créer screen web
- [ ] Tests

---

### PHASE 5: CHAT TRACY UI MOBILE (1-2 jours)

**Objectif:** Chat fonctionnel dans l'app

- [ ] Connecter TracyChatService à API
- [ ] Implémenter WebSocket
- [ ] Afficher Product Cards
- [ ] Tests

---

## 🎯 SCÉNARIO DE LANCEMENT MINIMUM

### MVP WHATSAPP (2 semaines)

**Fonctionnalités incluses:**
1. ✅ Tracy répond sur WhatsApp
2. ✅ Recherche produit via WhatsApp
3. ✅ Négociation via WhatsApp
4. ✅ Envoi catalogue via WhatsApp
5. ✅ Livraison manuelle (marqué livré par admin)
6. ✅ Paiement via lien (Moneroo/FedaPay)
7. ✅ Auth email/password (temporaire, OTP après)
8. ✅ Rôle vendor uniquement (buyer plus tard)

**Fonctionnalités exclues (V2):**
- ❌ Auth OTP
- ❌ Mode buyer
- ❌ Modes activables
- ❌ Livraison API (Gozem/Yango)
- ❌ Chat Tracy UI mobile
- ❌ Écran Découvrir
- ❌ Notifications natives
- ❌ Store Score & Trust
- ❌ Contracts

**Pourquoi ce MVP:**
- WhatsApp = canal d'acquisition puissant
- Pas besoin de télécharger l'app
- Teste la valeur de Tracy
- Feedback rapide
- Time-to-market minimal

---

## 📊 RÉSUMÉ ESTIMATIONS

| Tâche | Estimation | Priorité |
|-------|-----------|----------|
| Configuration Meta WhatsApp | 2-4h | 🔴 Critique |
| Tests WhatsApp | 4-6h | 🔴 Critique |
| Interface Admin WhatsApp | 1-2j | 🔴 Critique |
| Livraison manuelle | 1-2j | 🟠 Haute |
| Auth OTP | 2-3j | 🟠 Haute |
| Rôle Buyer | 2-3h | 🟠 Haute |
| Modes activables | 1-2j | 🟡 Moyenne |
| Chat Tracy UI mobile | 1-2j | 🟡 Moyenne |
| Livraison API (Gozem) | 3-5j | 🟡 Moyenne |
| Écran Découvrir | 2-3j | 🟢 Basse |
| Notifications FCM | 2-3j | 🟢 Basse |
| Store Score & Trust | 2-3j | 🟢 Basse |
| Contracts | 3-4j | 🟢 Basse |

**Total MVP WhatsApp:** ~2 semaines

---

## 🚀 PROCHAINES ÉTAPES IMMÉDIATES

1. **Configuration Meta WhatsApp** - Démarrer aujourd'hui
2. **Tests WhatsApp** - Une fois config prête
3. **Décision livraison** - Manuelle ou API ?
4. **Setup GitHub** - Pousser le code
5. **Documentation vendeur** - Comment connecter WhatsApp

---

## 💭 RÉFLEXION LIVRAISON

### Option A: Livraison Manuelle (Rapide)
**Avantages:**
- Implémentation rapide (1-2 jours)
- Pas de dépendance API externe
- Flexibilité totale
- Coût zéro

**Inconvénients:**
- Pas de tracking temps réel
- Dépendance admin pour marquer livré
- Expérience client moins bonne
- Scalabilité limitée

**Recommandé pour:** MVP initial

### Option B: Intégration Gozem (Complet)
**Avantages:**
- Tracking temps réel
- Calcul automatique prix
- Expérience client premium
- Scalable

**Inconvénients:**
- Implémentation complexe (3-5 jours)
- Dépendance API externe
- Coût par API call
- Maintenance continue

**Recommandé pour:** V2 post-lancement

### Option C: Hybride
- Commencer avec livraison manuelle
- Intégrer Gozem progressivement
- Permettre au vendeur de choisir

**Recommandation:** Option C - Hybride

---

## 📝 IDÉE TUTORIEL

À capturer: L'utilisateur a mentionné une idée de tutoriel à proposer.
**Question:** Quelle est cette idée de tutoriel ?

---

## ✅ CHECKLIST PRÉ-LANCEMENT

### Technique
- [ ] Git installé et configuré
- [ ] Code poussé sur GitHub
- [ ] .env.example créé
- [ ] Secrets non commités
- [ ] Base de données production configurée
- [ ] Tracy Core déployé
- [ ] Laravel déployé
- [ ] Webhook WhatsApp accessible publiquement
- [ ] SSL certificate (Let's Encrypt)

### Métier
- [ ] Meta WhatsApp configuré
- [ ] Numéro WhatsApp testé
- [ ] 5-10 vendeurs beta testeurs
- [ ] Produits catalogue chargés
- [ ] Passerelle paiement testée
- [ ] Processus support défini
- [ ] Documentation vendeur créée

### Légal
- [ ] Conditions d'utilisation
- [ ] Politique de confidentialité
- [ ] Terms of service vendeurs
- [ ] CGV (si applicable)

---

## 🎯 CONCLUSION

**Pourcentage actuel:** ~65%
**Pourcentage après MVP WhatsApp:** ~75%
**Pourcentage lancement complet:** ~85%

**Recommandation:** Prioriser WhatsApp MVP pour lancement en 2 semaines, puis itérer sur les fonctionnalités manquantes.
