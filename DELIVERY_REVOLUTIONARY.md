# Système de Livraison Révolutionnaire - "Click & Track"

**Date:** 30 octobre 2026
**Vision:** Expérience Uber/Gozem mais 100% WhatsApp
**Innovation:** Tracking GPS automatique via Progressive Web App (PWA)

---

## 🚀 LE CONCEPT RÉVOLUTIONNAIRE

### L'Expérience

#### Pour le LIVREUR (Ultra simple)
```
Livreur: "je suis disponible"
Tracy: "✅ Tu es maintenant DISPONIBLE

📱 Clique sur ce lien pour activer le tracking GPS:
🔗 https://mantota.com/track/abc123

Une fois activé, ferme la page et reviens sur WhatsApp.
Ton téléphone continuera à envoyer ta position automatiquement.

💡 Astuce: Garde l'onglet ouvert en arrière-plan pour un tracking optimal."
```

#### Le lien ouvre une **PWA ultra-légère**
- S'installe en 2 secondes
- Demande la permission GPS
- Commence à envoyer la position toutes les 30 secondes
- Affiche: "🟢 Tracking actif - Tu es visible pour les clients"
- Le livreur ferme l'onglet, revient sur WhatsApp
- Le tracking continue en arrière-plan

#### Pour le CLIENT (Visuel et moderne)
```
Client: "je veux être livré"
Tracy: "📍 Envoie ta position"
Client: [envoie position]
Tracy: "🚚 LIVREURS DISPONIBLES

Jean K. est à 1.2 km
⏱️ Arrivée: 3 min
🟢 Actif maintenant

Voir en temps réel:
🔗 https://mantota.com/live/xyz789

[Carte interactive avec position livreur en temps réel]"
```

#### Le client voit:
- Carte interactive
- Point vert = livreur
- Point rouge = client
- Ligne = itinéraire
- Temps réel qui se met à jour

---

## 🏗️ ARCHITECTURE TECHNIQUE

### 1. Progressive Web App (PWA) de Tracking

#### `track-pwa/` - Application web ultra-légère

**Fichier: `index.html`**
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mantota Tracking</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0BBFA0 0%, #089174 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
            padding: 20px;
        }
        .status {
            background: rgba(255,255,255,0.2);
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        .pulse {
            width: 20px;
            height: 20px;
            background: #00ff00;
            border-radius: 50%;
            animation: pulse 2s infinite;
            margin: 20px auto;
        }
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.5); opacity: 0.5; }
            100% { transform: scale(1); opacity: 1; }
        }
        .info {
            font-size: 14px;
            opacity: 0.9;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="status">
        <div class="pulse"></div>
        <h1 id="status-text">Activation...</h1>
        <p class="info" id="info-text">Demande de la permission GPS...</p>
    </div>

    <script>
        const DRIVER_TOKEN = new URLSearchParams(window.location.search).get('token');
        const API_URL = 'https://mantota.com/api/driver/location';

        async function startTracking() {
            if (!navigator.geolocation) {
                document.getElementById('status-text').textContent = '❌ GPS non supporté';
                return;
            }

            try {
                // Demander la permission
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 0
                    });
                });

                document.getElementById('status-text').textContent = '🟢 Tracking actif';
                document.getElementById('info-text').textContent = 'Ta position est envoyée automatiquement';

                // Envoyer la position immédiatement
                await sendLocation(position.coords);

                // Puis toutes les 30 secondes
                setInterval(async () => {
                    try {
                        const pos = await new Promise((resolve, reject) => {
                            navigator.geolocation.getCurrentPosition(resolve, reject, {
                                enableHighAccuracy: true,
                                timeout: 10000,
                                maximumAge: 60000 // Accepte position jusqu'à 1 min
                            });
                        });
                        await sendLocation(pos.coords);
                    } catch (e) {
                        console.error('Erreur GPS:', e);
                    }
                }, 30000);

                // Éviter que l'écran s'éteigne (Screen Wake Lock API)
                if ('wakeLock' in navigator) {
                    try {
                        await navigator.wakeLock.request('screen');
                    } catch (e) {
                        console.log('Wake Lock non supporté');
                    }
                }

            } catch (error) {
                document.getElementById('status-text').textContent = '❌ Erreur GPS';
                document.getElementById('info-text').textContent = error.message;
            }
        }

        async function sendLocation(coords) {
            try {
                await fetch(API_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        token: DRIVER_TOKEN,
                        latitude: coords.latitude,
                        longitude: coords.longitude,
                        accuracy: coords.accuracy,
                        speed: coords.speed,
                        heading: coords.heading,
                    })
                });
            } catch (e) {
                console.error('Erreur envoi position:', e);
            }
        }

        // Démarrer
        startTracking();
    </script>
</body>
</html>
```

**Fichier: `manifest.json`**
```json
{
    "name": "Mantota Tracking",
    "short_name": "Mantota",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0BBFA0",
    "theme_color": "#0BBFA0",
    "icons": [
        {
            "src": "/icon-192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/icon-512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}
```

**Caractéristiques:**
- ⚡ Ultra-léger (< 50 KB)
- 📱 Compatible tous les navigateurs modernes
- 🚀 Installation en 2 secondes
- 🔋 Optimisé batterie (position toutes les 30s)
- 🎨 Design moderne et intuitif
- 🌐 Fonctionne hors-ligne (service worker)

---

### 2. PWA de Visualisation Client

#### `live-view-pwa/` - Carte interactive temps réel

**Fichier: `index.html`**
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mantota Live</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; padding: 0; }
        #map { height: 100vh; width: 100%; }
        .info-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            min-width: 300px;
        }
        .eta {
            font-size: 24px;
            font-weight: bold;
            color: #0BBFA0;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-card">
        <div class="eta" id="eta">⏱️ 3 min</div>
        <div id="driver-info">Jean K. 🏍️ Moto</div>
        <div id="distance">1.2 km</div>
    </div>

    <script>
        const ORDER_TOKEN = new URLSearchParams(window.location.search).get('token');
        const API_URL = `https://mantota.com/api/order/${ORDER_TOKEN}/live`;

        // Initialiser la carte
        const map = L.map('map').setView([6.357, 2.417], 14);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);

        // Marqueurs
        let driverMarker, clientMarker, routeLine;

        // Mettre à jour en temps réel
        setInterval(async () => {
            try {
                const response = await fetch(API_URL);
                const data = await response.json();

                // Mettre à jour le livreur
                if (!driverMarker) {
                    driverMarker = L.marker([data.driver_lat, data.driver_lon], {
                        icon: L.divIcon({
                            className: 'custom-icon',
                            html: '🚚',
                            iconSize: [40, 40]
                        })
                    }).addTo(map);
                } else {
                    driverMarker.setLatLng([data.driver_lat, data.driver_lon]);
                }

                // Mettre à jour le client
                if (!clientMarker) {
                    clientMarker = L.marker([data.client_lat, data.client_lon], {
                        icon: L.divIcon({
                            className: 'custom-icon',
                            html: '📍',
                            iconSize: [40, 40]
                        })
                    }).addTo(map);
                }

                // Dessiner l'itinéraire
                if (data.route) {
                    if (routeLine) map.removeLayer(routeLine);
                    routeLine = L.polyline(data.route, { color: '#0BBFA0', weight: 4 }).addTo(map);
                }

                // Mettre à jour les infos
                document.getElementById('eta').textContent = `⏱️ ${data.eta} min`;
                document.getElementById('distance').textContent = `${data.distance.toFixed(1)} km`;

                // Centrer la carte
                map.fitBounds([driverMarker.getLatLng(), clientMarker.getLatLng()], { padding: [50, 50] });

            } catch (e) {
                console.error('Erreur:', e);
            }
        }, 3000); // Toutes les 3 secondes
    </script>
</body>
</html>
```

---

### 3. Backend Laravel - Gestion Tracking

#### Endpoint: `POST /api/driver/location`
```php
Route::post('/driver/location', function (Request $request) {
    $token = $request->input('token');
    $latitude = $request->input('latitude');
    $longitude = $request->input('longitude');

    // Valider le token
    $driver = DeliveryDriver::where('tracking_token', $token)->first();

    if (!$driver) {
        return response()->json(['error' => 'Invalid token'], 401);
    }

    // Mettre à jour la position
    $driver->update([
        'current_latitude' => $latitude,
        'current_longitude' => $longitude,
        'last_location_update' => now(),
    ]);

    // Enregistrer dans l'historique
    DriverLocationHistory::create([
        'driver_id' => $driver->id,
        'latitude' => $latitude,
        'longitude' => $longitude,
        'recorded_at' => now(),
    ]);

    return response()->json(['status' => 'updated']);
});
```

#### Endpoint: `GET /api/order/{token}/live`
```php
Route::get('/order/{token}/live', function ($token) {
    $assignment = DeliveryAssignment::where('live_token', $token)
        ->with(['driver', 'order'])
        ->first();

    if (!$assignment) {
        return response()->json(['error' => 'Not found'], 404);
    }

    // Calculer la distance
    $distance = calculateDistance(
        $assignment->driver->current_latitude,
        $assignment->driver->current_longitude,
        $assignment->order->delivery_latitude,
        $assignment->order->delivery_longitude
    );

    // Estimer l'ETA
    $eta = estimateEta($distance, $assignment->driver->vehicle_type);

    // Calculer l'itinéraire (OSRM API)
    $route = calculateRoute(
        $assignment->driver->current_latitude,
        $assignment->driver->current_longitude,
        $assignment->order->delivery_latitude,
        $assignment->order->delivery_longitude
    );

    return response()->json([
        'driver_lat' => $assignment->driver->current_latitude,
        'driver_lon' => $assignment->driver->current_longitude,
        'client_lat' => $assignment->order->delivery_latitude,
        'client_lon' => $assignment->order->delivery_longitude,
        'distance' => $distance,
        'eta' => $eta,
        'route' => $route,
        'driver_name' => $assignment->driver->full_name,
        'vehicle_type' => $assignment->driver->vehicle_type,
    ]);
});
```

---

### 4. Base de Données - Ajustements

#### Migration `delivery_drivers`
```php
$table->string('tracking_token')->unique(); // Token pour la PWA
$table->timestamp('tracking_started_at')->nullable(); // Quand le tracking a commencé
$table->boolean('tracking_active')->default(false); // Tracking en cours
```

#### Migration `delivery_assignments`
```php
$table->string('live_token')->unique(); // Token pour la vue client
```

---

### 5. Tracy Core - Intégration

#### Nouveau Tool: `activate_tracking.py`
```python
class ActivateTrackingTool(Tool):
    """Génère le lien de tracking pour le livreur"""

    async def execute(self, context: ToolContext) -> ToolResult:
        driver_id = context.get('driver_id')

        # Générer un token unique
        tracking_token = generate_unique_token()

        # Mettre à jour le livreur
        await self.mantota_client.update_driver_tracking(
            driver_id,
            tracking_token=tracking_token,
            tracking_active=True,
            tracking_started_at=now()
        )

        # Construire l'URL
        tracking_url = f"https://mantota.com/track?token={tracking_token}"

        return ToolResult.success(data={
            'tracking_url': tracking_url,
            'tracking_token': tracking_token
        })
```

#### Message Tracy
```python
# Quand le livreur dit "je suis disponible"
tracking_result = await activate_tracking_tool.execute(context)

reply = f"""✅ Tu es maintenant DISPONIBLE

📱 Clique sur ce lien pour activer le tracking GPS:
🔗 {tracking_result['tracking_url']}

Une fois activé, ferme la page et reviens sur WhatsApp.
Ton téléphone continuera à envoyer ta position automatiquement.

💡 Garde l'onglet ouvert en arrière-plan pour un tracking optimal."""
```

---

### 6. Flow Complet

#### Flow Livreur (Simple et moderne)
```
1. Livreur: "je suis disponible"
2. Tracy: Génère token unique
3. Tracy: Envoie lien PWA tracking
4. Livreur: Clique sur lien
5. PWA: Demande permission GPS
6. PWA: Commence tracking (toutes les 30s)
7. Livreur: Ferme l'onglet, revient sur WhatsApp
8. Tracking continue en arrière-plan
9. Livreur reçoit commandes dans sa zone
```

#### Flow Client (Visuel et moderne)
```
1. Client: "je veux être livré"
2. Tracy: Demande position
3. Client: Envoie position
4. Tracy: Trouve livreurs disponibles
5. Tracy: Affiche options avec temps réel
6. Client: Choisis un livreur
7. Tracy: Génère token live view
8. Tracy: Envoie lien carte interactive
9. Client: Voit livreur en temps réel
10. Tracking toutes les 3 secondes
```

---

## 🎨 DESIGN ULTRA-MODERNE

### PWA Tracking - Design
- 🎨 Fond dégradé (Mantota teal)
- ✨ Animation pulse (vert = actif)
- 📱 Interface minimaliste
- 🔋 Icône batterie
- 📊 Statut tracking en temps réel

### PWA Live View - Design
- 🗺️ Carte Leaflet (OpenStreetMap)
- 🚚 Emoji livreur animé
- 📍 Emoji client
- 🟢 Ligne itinéraire verte
- ⏱️ Card info flottante
- 🎨 Palette Mantota (teal #0BBFA0)

---

## ⚡ OPTIMISATIONS PERFORMANCE

### Batterie
- Position toutes les 30 secondes (pas 5 secondes)
- Accuracy "high" uniquement pour la première position
- Accuracy "balanced" ensuite
- Background fetch quand possible

### Données
- Compression des positions
- Nettoyage historique (> 30 jours)
- Index sur coordonnées GPS

### UX
- Notification si tracking s'arrête
- Rappel automatique après 1 heure inactivité
- Bouton "Stop tracking" visible

---

## 🔒 SÉCURITÉ ET CONFIDENTIALITÉ

### Tokens
- Token unique par session (UUID)
- Expiration après 24h
- Régénéré à chaque activation

### Permissions
- Demande explicite GPS
- Message clair d'utilisation
- Possibilité de refuser

### Données
- Position stockée chiffrée
- Accès limité aux commandes actives
- Suppression automatique après livraison

---

## 🌟 INNOVATIONS "JAMAIS VUES"

### 1. WhatsApp + PWA Hybride
- WhatsApp pour la communication
- PWA pour le tracking GPS
- Les deux travaillent ensemble

### 2. Tracking continu sans app lourde
- PWA < 50 KB vs App > 50 MB
- Installation en 2 secondes
- Compatible tous les téléphones

### 3. Carte interactive pour client
- Pas besoin d'installer quoi que ce soit
- Lien WhatsApp → Carte live
- Temps réel sans friction

### 4. Expérience fluide
- "je suis disponible" → Tracking actif
- Pas de configuration complexe
- Pas de compte à créer pour le tracking

---

## 📋 PLAN D'IMPLÉMENTATION

### Phase 1: PWA Tracking (2-3 jours)
- [ ] Créer PWA tracking
- [ ] Intégration GPS
- [ ] Backend endpoint
- [ ] Tests sur mobile

### Phase 2: PWA Live View (2-3 jours)
- [ ] Créer PWA live view
- [ ] Intégration Leaflet
- [ ] Backend endpoint
- [ ] OSRM routing

### Phase 3: Tracy Core (1-2 jours)
- [ ] Tool activate_tracking
- [ ] Flows WhatsApp
- [ ] Messages automatisés

### Phase 4: Backend Laravel (2-3 jours)
- [ ] Endpoints tracking
- [ ] Endpoints live view
- [ ] Token management
- [ ] Background jobs

### Phase 5: Tests (2-3 jours)
- [ ] Tests tracking continu
- [ ] Tests live view
- [ ] Tests batterie
- [ ] Tests end-to-end

**Total:** 9-14 jours

---

## 🎯 POURQUOI C'EST RÉVOLUTIONNAIRE

### Pour les Livreurs
- ✅ Ultra simple: "je suis disponible" → Clique lien → C'est tout
- ✅ Pas d'app à installer
- ✅ Fonctionne sur tous les téléphones
- ✅ Tracking automatique
- ✅ Peuvent continuer à utiliser WhatsApp

### Pour les Clients
- ✅ Carte interactive temps réel
- ✅ Voir le livreur arriver
- ✅ Pas d'app à installer
- ✅ Expérience type Uber/Gozem
- ✅ Lien direct depuis WhatsApp

### Pour Mantota
- ✅ Technologie moderne (PWA)
- ✅ Pas de dépendance tierce
- ✅ Coût de développement réduit
- ✅ Scalable
- ✅ Unique en Afrique

---

## 💡 PROCHAINES ÉTAPES

1. **Valider l'architecture** - Cette solution vous convient-elle ?
2. **Choisir le design** - Style minimaliste ou plus détaillé ?
3. **Tester PWA** - Je peux créer une démo immédiatement
4. **Intégration** - Commencer Phase 1
5. **Beta test** - 5-10 livreurs pour valider

---

## 🚀 C'EST LE FUTUR DE LA LIVRAISON EN AFRIQUE

WhatsApp + PWA + GPS = Révolution

Simple. Moderne. Accessible. Africain.
