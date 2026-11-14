# MANTOTA - Plateforme de E-commerce Intelligente propulsée par Tracy IA

**Version:** 1.0.0
**Statut:** En développement
**Lancement prévu:** WhatsApp MVP (2 semaines)

---

## 🎯 Vision

Mantota est une plateforme de e-commerce africaine révolutionnaire propulsée par Tracy, une IA de conversation avancée. Notre mission est de moderniser le commerce en Afrique de l'Ouest en rendant l'achat, la vente et la livraison aussi simples qu'une conversation sur WhatsApp.

---

## 🏗️ Architecture du Projet

```
TRACY IA/
├── tracy-core/              # Orchestrateur IA (Python/FastAPI)
├── od-system-staging/       # Backend Laravel (Web app + API)
├── mantota_app/             # Mobile app Flutter
├── admin-panel/             # Admin panel React
├── docs/                    # Documentation
└── whatsapp-bot-legacy/     # Legacy (non utilisé)
```

---

## 📊 Composants Principaux

### 1. Tracy Core (Orchestrateur IA)
- **Stack:** Python 3.12+, FastAPI, LangGraph
- **Agents:** 9 agents spécialisés (Commercial, Negotiation, Catalog, Order, Payment, Support, Campaign, Memory, Restaurant)
- **Tools:** 28 tools intégrés
- **Tests:** 140+ tests
- **Maturité:** 96%

**Fonctionnalités:**
- Recherche produit intelligente
- Négociation automatique
- Gestion catalogue vendeur
- Création/suivi commandes
- Paiements et wallet
- Support après-vente
- Campagnes marketing
- Mémoire conversationnelle
- Commande restaurant

### 2. Backend Laravel (od-system-staging)
- **Stack:** Laravel 12, PHP 8.2+, PostgreSQL
- **Migrations:** 114 migrations
- **Routes:** 253 routes web
- **API Bot:** 11 contrôleurs
- **Maturité:** 85%

**Fonctionnalités:**
- Authentification (Sanctum)
- Gestion utilisateurs (Vendor, Influencer, Admin)
- Produits et catalogue
- Commandes et transactions
- Wallet et escrow
- Campagnes et partenaires
- Connexions WhatsApp
- Knowledge base (RAG)
- Multi-pays (15 pays d'Afrique)
- API complète pour Tracy Core

### 3. Mobile App (mantota_app)
- **Stack:** Flutter 3.12+, Riverpod, go_router
- **Screens:** 30+ screens
- **Services:** 12 services API
- **Maturité:** 30%

**Fonctionnalités:**
- Onboarding (OTP, mode selection)
- Chat Tracy
- Catalogue et recherche
- Commandes et paiement
- Livraison et tracking
- Restaurant
- Wallet
- Vendor dashboard
- Abonnements Tracy

### 4. Admin Panel (admin-panel)
- **Stack:** React 19, Vite, TailwindCSS, React-Leaflet
- **Pages:** 20+ pages
- **Maturité:** 40%

**Fonctionnalités:**
- Dashboard temps réel
- Gestion utilisateurs
- Boutiques et catalogue
- Commandes et livraison
- Finance et escrow
- Campagnes et créateurs
- Tracy Core pilotage
- Knowledge management
- Sécurité et modération

---

## 🚀 Système de Livraison Révolutionnaire

### Concept: "Click & Track" 100% WhatsApp

Nous avons conçu un système de livraison **jamais vu en Afrique** qui combine:
- **WhatsApp** pour la communication
- **PWA (Progressive Web App)** pour le tracking GPS
- **Carte interactive** pour le suivi temps réel

### Pour les LIVREURS (Ultra simple)

#### Flow d'inscription
```
1. Livreur: "je veux devenir livreur" sur WhatsApp
2. Tracy: Demande nom, véhicule, zone, photo pièce d'identité
3. Livreur: Envoie infos + photo
4. Admin: Approuve l'inscription
5. Tracy: "Compte activé ! Dis 'je suis disponible' pour commencer"
```

#### Activation du tracking
```
Livreur: "je suis disponible"
Tracy: "✅ Tu es maintenant DISPONIBLE

📱 Clique sur ce lien pour activer le tracking GPS:
🔗 https://mantota.com/track/abc123

Une fois activé, ferme la page et reviens sur WhatsApp.
Ton téléphone continuera à envoyer ta position automatiquement."
```

#### La PWA de Tracking
- S'installe en 2 secondes (< 50 KB)
- Demande la permission GPS
- Commence à envoyer la position toutes les 30 secondes
- Affiche: "🟢 Tracking actif - Tu es visible pour les clients"
- Le livreur ferme l'onglet, revient sur WhatsApp
- **Le tracking continue en arrière-plan automatiquement**

#### Acceptation de commande
```
Tracy: "📦 COMMANDE PRÈS DE TOI

📍 Distance: 1.2 km
⏱️ Temps estimé: 3 min
🛍️ Commande: Sac à main
💰 Livraison: 1 500 FCFA
💸 Tes gains: 1 200 FCFA

Tu es dans la zone et disponible. Acceptes-tu ?
Réponds: 'oui' ou 'non' (5 min)"
```

### Pour les CLIENTS (Visuel et moderne)

#### Recherche de livreur
```
Client: "je veux être livré"
Tracy: "Ok ! Pour te trouver le meilleur livreur, j'ai besoin de ta position.

📍 Envoie ta position GPS via WhatsApp
   Menu > Envoyer ma position actuelle

Ou donne-moi ton adresse précise."
```

#### Choix du livreur
```
Client: [envoie position GPS]
Tracy: "✅ Position reçue ! Tu es à: Haie Vive, Cotonou

🚚 LIVREURS DISPONIBLES DANS TA ZONE

1. Jean K. 🏍️ Moto
   ⏱️ 3 min de toi
   ⭐ 4.8/5 (127 livraisons)
   💰 Livraison: 1 500 FCFA

2. Marc A. 🚗 Voiture
   ⏱️ 5 min de toi
   ⭐ 4.6/5 (89 livraisons)
   💰 Livraison: 2 000 FCFA

Quel livreur choisis-tu ? (1, 2, 3)"
```

#### Suivi temps réel
```
Client: "1"
Tracy: "✅ Choix enregistré

🚚 Livreur: Jean K. (Moto)
⏱️ Arrivée estimée: 3 min
💰 Livraison: 1 500 FCFA

Voir en temps réel:
🔗 https://mantota.com/live/xyz789

Prépare ton colis !"
```

#### La PWA de Visualisation
- Carte interactive Leaflet (OpenStreetMap)
- Point vert = livreur (bouge en temps réel)
- Point rouge = client
- Ligne verte = itinéraire
- Mise à jour toutes les 3 secondes
- ETA en temps réel

### Technologie du Tracking

#### PWA Tracking (Livreur)
```javascript
// Position toutes les 30 secondes
setInterval(async () => {
    const position = await navigator.geolocation.getCurrentPosition();
    await fetch('/api/driver/location', {
        method: 'POST',
        body: JSON.stringify({
            token: DRIVER_TOKEN,
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
        })
    });
}, 30000);
```

#### PWA Live View (Client)
```javascript
// Mise à jour toutes les 3 secondes
setInterval(async () => {
    const data = await fetch('/api/order/token/live');
    driverMarker.setLatLng([data.driver_lat, data.driver_lon]);
    map.fitBounds([driver, client]);
}, 3000);
```

### Avantages de cette Approche

1. **Ultra simple pour le livreur**
   - "je suis disponible" → Clique lien → C'est tout
   - Pas d'app à installer
   - Tracking automatique

2. **100% WhatsApp**
   - Communication = WhatsApp
   - Tracking = PWA (lien depuis WhatsApp)
   - Les deux travaillent ensemble

3. **Moderne et légère**
   - PWA < 50 KB vs App > 50 MB
   - Installation en 2 secondes
   - Compatible tous les téléphones

4. **Jamais vu en Afrique**
   - Personne n'a fait WhatsApp + PWA pour livraison
   - Expérience Uber/Gozem mais accessible à tous
   - Innovation africaine

5. **Visuel pour le client**
   - Carte interactive temps réel
   - Voir le livreur arriver
   - Lien direct depuis WhatsApp

---

## 🌐 Multi-Pays Architecture

Mantota est conçu pour être multi-pays dès le jour 1:

### Pays préparés
- **Bénin** - Premier marché de référence
- **Togo** - Intégration architecturale
- **Sénégal** - Intégration architecturale
- **Côte d'Ivoire** - Intégration architecturale

### Country Intelligence
- Country Registry (données configurables, pas codées en dur)
- Auto-discovery de nouveaux pays
- Country Learning (apprentissage automatique des pratiques locales)
- Knowledge Candidates (tendances détectées)
- Risk Classification (LOW/MEDIUM/HIGH/CRITICAL)

### Multi-devises
- FCFA (XOF, XAF)
- Naira (NGN)
- Cedi (GHS)
- Et plus...

---

## 📚 Documentation

- [DEV_PLAN.md](./DEV_PLAN.md) - Plan de développement complet
- [ADMIN_SPEC.md](./ADMIN_SPEC.md) - Spécification Admin Panel
- [TRACY_TRAINING_PLAN.md](./TRACY_TRAINING_PLAN.md) - Plan d'entraînement Tracy
- [LAUNCH_READINESS.md](./LAUNCH_READINESS.md) - Points critiques pour le lancement
- [DELIVERY_REVOLUTIONARY.md](./DELIVERY_REVOLUTIONARY.md) - Système de livraison détaillé
- [AUDIT_REPORT.md](./AUDIT_REPORT.md) - Audit complet du projet
- [META_WHATSAPP_TROUBLESHOOTING.md](./META_WHATSAPP_TROUBLESHOOTING.md) - Guide résolution WhatsApp

---

## 🚀 Installation

### Prérequis
- Python 3.12+
- PHP 8.2+
- Composer
- Node.js 18+
- Flutter 3.12+
- PostgreSQL 14+
- Redis

### Tracy Core
```bash
cd tracy-core
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Éditer .env avec les vraies clés
uvicorn app.main:app --reload --port 8000
```

### Backend Laravel
```bash
cd od-system-staging
composer install
npm install
cp .env.example .env
php artisan key:generate
php artisan migrate
php artisan serve
```

### Mobile App Flutter
```bash
cd mantota_app
flutter pub get
flutter run
```

### Admin Panel React
```bash
cd admin-panel
npm install
npm run dev
```

---

## 🧪 Tests

### Tracy Core
```bash
cd tracy-core
pytest
```

### Laravel
```bash
cd od-system-staging
php artisan test
```

### Flutter
```bash
cd mantota_app
flutter test
```

---

## 📊 Statut Actuel

| Composant | Maturité | Tests |
|-----------|----------|-------|
| Tracy Core | 96% | 140+ ✅ |
| Backend Laravel | 85% | Présents |
| Mobile Flutter | 30% | À faire |
| Admin Panel | 40% | À faire |
| **Global** | **~65%** | - |

---

## 🎯 Roadmap

### Phase 1: WhatsApp MVP (2 semaines)
- [x] Tracy Core prêt
- [x] Backend Laravel prêt
- [ ] Configuration Meta WhatsApp
- [ ] Interface Admin WhatsApp
- [ ] Tests WhatsApp
- [ ] Livraison manuelle
- [ ] Lancement beta

### Phase 2: Système Livraison GPS (2-3 semaines)
- [ ] PWA Tracking
- [ ] PWA Live View
- [ ] Integration Tracy Core
- [ ] Backend endpoints
- [ ] Tests

### Phase 3: Mobile App Complète (3-4 semaines)
- [ ] Chat Tracy UI
- [ ] Écran Découvrir
- [ ] Notifications FCM
- [ ] Tests

### Phase 4: Lancement Production (1 semaine)
- [ ] Configuration production
- [ ] Monitoring
- [ ] Backup
- [ ] Documentation utilisateur

---

## 🤝 Contribution

Pour contribuer:
1. Fork le repository
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📄 Licence

Propriétaire - Mantota © 2026

---

## 👥 Équipe

- **Fondateur:** Yanou
- **Architecture:** Stan
- **Développement:** En cours

---

## 📞 Contact

- **Email:** contact@mantota.com
- **WhatsApp:** +229 XX XX XX XX
- **Web:** https://mantota.com

---

## 🙏 Remerciements

- OpenAI pour GPT
- Laravel pour le framework
- Flutter pour le mobile
- La communauté open-source

---

**Mantota - Le commerce africain, réinventé.** 🚀
