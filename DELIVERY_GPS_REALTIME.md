# Système de Livraison GPS Temps Réel - WhatsApp Only

**Date:** 30 octobre 2026
**Objectif:** Expérience type Gozem 100% sur WhatsApp
**Technologie:** GPS temps réel + WhatsApp

---

## 🎯 Vision Complète

### Pour les CLIENTS
- Viennent sur WhatsApp
- Disent: "je veux être livré" ou "livreur dans ma zone ?"
- Partagent leur position GPS
- Tracy trouve les livreurs disponibles DANS LEUR ZONE (basé sur GPS)
- Voient les options (livreurs disponibles, temps d'attente)
- Choisisent et la livraison est assignée

### Pour les LIVREURS
- S'inscrivent sur WhatsApp
- Partagent leur position GPS (en continu ou régulièrement)
- Système détecte automatiquement leur disponibilité basée sur GPS
- Reçoivent des commandes dans leur zone GPS
- Acceptent/Refusent sur WhatsApp
- Suivent la livraison sur WhatsApp

**IMPORTANT:** Pas de "je suis disponible" manuel - c'est basé sur le GPS !

---

## 🏗️ Architecture GPS Temps Réel

### 1. Flux Client - Type Gozem sur WhatsApp

#### Scénario A: "Je veux être livré"
```
Client: "je veux être livré"
Tracy: "Ok ! Pour te trouver le meilleur livreur, j'ai besoin de ta position.

📍 Option 1: Envoie ta position GPS via WhatsApp
   Menu > Envoyer ma position actuelle

📍 Option 2: Donne-moi ton adresse précise
   Ex: Haie Vive, Cotonou

Quelle option préfères-tu ?"
```

#### Scénario B: "Livreur dans ma zone ?"
```
Client: "livreur dans ma zone"
Tracy: "Je vais vérifier les livreurs disponibles près de chez toi.

📍 Envoie ta position GPS pour une recherche précise,
   ou donne-moi ton quartier/ville."
```

#### Client envoie position GPS
```
Client: [envoie position GPS via WhatsApp]
Tracy: "✅ Position reçue !

📍 Tu es à: Haie Vive, Cotonou

Recherche des livreurs disponibles dans ta zone...
🔍"
```

#### Tracy analyse les livreurs dans la zone
```
Tracy: "🚚 LIVREURS DISPONIBLES DANS TA ZONE

1. Jean K. 🏍️ Moto
   ⏱️ 3 min de toi
   ⭐ 4.8/5 (127 livraisons)
   💰 Livraison: 1 500 FCFA

2. Marc A. 🚗 Voiture
   ⏱️ 5 min de toi
   ⭐ 4.6/5 (89 livraisons)
   💰 Livraison: 2 000 FCFA

3. Aminata D. 🏍️ Moto
   ⏱️ 7 min de toi
   ⭐ 4.9/5 (203 livraisons)
   💰 Livraison: 1 500 FCFA

Quel livreur choisis-tu ?
Réponds: 1, 2 ou 3"
```

#### Client choisit
```
Client: "1"
Tracy: "✅ Choix enregistré

🚚 Livreur: Jean K. (Moto)
⏱️ Arrivée estimée: 3 min
💰 Livraison: 1 500 FCFA

Prépare ton colis ! Jean arrive bientôt.
Tu peux suivre sa progression en temps réel: dis-moi 'où est le livreur' 📍"
```

#### Tracking en temps réel
```
Client: "où est le livreur"
Tracy: "📍 POSITION DU LIVREUR

Jean K. est à 1.2 km de chez toi.
⏱️ Arrivée estimée: 2 min

🗺️ [Lien vers carte si disponible]

Il arrive bientôt !"
```

---

### 2. Flux Livreur - GPS Temps Réel

#### Inscription avec position initiale
```
Livreur: "je veux devenir livreur"
Tracy: "Super ! Pour t'inscrire, j'ai besoin:

1. Ton nom complet
2. Type de véhicule (moto/voiture/vélo)
3. TA POSITION GPS ACTUELLE (très important)

Commence par ton nom 👇"
```

#### Collecte infos + position
```
Livreur: "Jean Kouassi, moto" [envoie position GPS]
Tracy: "✅ Position reçue !

📍 Tu es à: Haie Vive, Cotonou

C'est ta zone de livraison principale.
Les commandes dans cette zone te seront proposées automatiquement quand tu y es.

Envoie ta pièce d'identité pour finaliser l'inscription."
```

#### Tracking GPS continu (automatique)

**Option A: Messages automatiques de rappel**
```
Tracy: "⏰ Mise à jour position requise

Pour rester visible pour les clients, envoie ta position GPS régulièrement.

Tape: 'ma position' ou envoie ta position via WhatsApp"
```

**Option B: Intégration App Mantota (Tracking continu)**
- L'application Mantota envoie la position automatiquement toutes les 2 min
- WhatsApp reste le canal de communication
- Le GPS continue via l'app en arrière-plan

**Option C: WhatsApp Location Sharing (Manuel mais fréquent)**
- Livreur envoie position manuellement
- Tracy envoie un rappel toutes les 15-30 min
- "N'oublie pas de mettre à jour ta position !"

**Recommandation MVP:** Option C (manuel avec rappels)
**Recommandation V2:** Option B (app + WhatsApp hybride)

#### Disponibilité basée sur GPS
```
# Le système calcule automatiquement:

SI (position GPS actuelle DANS zone déclarée)
  ET (dernière mise à jour < 15 min)
  ET (pas en cours de livraison)
  ALORS: "DISPONIBLE"
SINON: "INDISPONIBLE"
```

**Le livreur ne dit plus "je suis disponible" - c'est automatique !**

#### Proposition de commande (basée sur GPS)
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

#### Acceptation et tracking
```
Livreur: "oui"
Tracy: "✅ ACCEPTÉ

📍 Pickup: Boutique Élégance, Haie Vive
📍 Livraison: Fidjrossè, Cotonou
📏 Distance totale: 2.1 km
💰 Gains: 1 200 FCFA

Rends-toi au pickup. Code: #8472

⚠️ Continue à envoyer ta position pendant la livraison pour un meilleur suivi !"
```

#### En cours de livraison - Mises à jour GPS
```
Livreur: [envoie position GPS]
Tracy: "✅ Position mise à jour

📍 Tu es à 0.8 km du pickup
⏱️ Arrivée pickup: 2 min

Continue comme ça !"
```

---

### 3. Algorithme de Matching GPS

#### Service: `GpsBasedMatchingService`

```php
class GpsBasedMatchingService
{
    /**
     * Trouve les livreurs disponibles dans un rayon donné
     */
    public function findAvailableDriversInRadius(
        float $latitude,
        float $longitude,
        int $radiusKm = 5
    ): Collection {
        $now = now()->subMinutes(15); // Position mise à jour dans les 15 min

        $drivers = DeliveryDriver::where('status', 'approved')
            ->where('last_location_update', '>=', $now)
            ->whereDoesntHave('activeAssignments') // Pas en cours de livraison
            ->get();

        // Filtrer par distance GPS
        $availableDrivers = $drivers->filter(function ($driver) use ($latitude, $longitude, $radiusKm) {
            $distance = $this->calculateDistance(
                $latitude,
                $longitude,
                $driver->current_latitude,
                $driver->current_longitude
            );

            return $distance <= $radiusKm;
        });

        // Trier par distance (plus proche en premier)
        return $availableDrivers->sortBy(function ($driver) use ($latitude, $longitude) {
            return $this->calculateDistance(
                $latitude,
                $longitude,
                $driver->current_latitude,
                $driver->current_longitude
            );
        });
    }

    /**
     * Calcule la distance entre deux points GPS (Haversine formula)
     */
    private function calculateDistance(
        float $lat1,
        float $lon1,
        float $lat2,
        float $lon2
    ): float {
        $earthRadius = 6371; // km

        $dLat = deg2rad($lat2 - $lat1);
        $dLon = deg2rad($lon2 - $lon1);

        $a = sin($dLat / 2) * sin($dLat / 2) +
             cos(deg2rad($lat1)) * cos(deg2rad($lat2)) *
             sin($dLon / 2) * sin($dLon / 2);

        $c = 2 * atan2(sqrt($a), sqrt(1 - $a));

        return $earthRadius * $c;
    }

    /**
     * Estime le temps d'arrivée (basé sur distance et type véhicule)
     */
    public function estimateEta(float $distanceKm, string $vehicleType): int
    {
        $speedKmh = match($vehicleType) {
            'moto' => 25, // 25 km/h moyenne en ville
            'velo' => 15,
            'voiture' => 20,
            default => 20,
        };

        $minutes = ($distanceKm / $speedKmh) * 60;

        return (int) ceil($minutes);
    }
}
```

---

### 4. Intents Tracy Ajustés

#### Pour les CLIENTS
```python
class Intent(str, Enum):
    # GPS - Clients
    DELIVERY_REQUEST = "delivery_request"  # "je veux être livré"
    DELIVERY_CHECK_ZONE = "delivery_check_zone"  # "livreur dans ma zone"
    DELIVERY_SEND_LOCATION = "delivery_send_location"  # envoi GPS
    DELIVERY_TRACK_DRIVER = "delivery_track_driver"  # "où est le livreur"
    DELIVERY_CHOOSE_DRIVER = "delivery_choose_driver"  # choisir livreur
```

#### Pour les LIVREURS
```python
class Intent(str, Enum):
    # GPS - Livreurs
    DELIVERY_DRIVER_REGISTER = "delivery_driver_register"
    DELIVERY_DRIVER_SEND_LOCATION = "delivery_driver_send_location"  # envoi GPS
    DELIVERY_ACCEPT_ORDER = "delivery_accept_order"
    DELIVERY_PICKUP_CONFIRM = "delivery_pickup_confirm"
    DELIVERY_DELIVER_CONFIRM = "delivery_deliver_confirm"
    DELIVERY_DRIVER_STATUS = "delivery_driver_status"  # vérifier statut GPS
```

**NOTE:** Plus d'intent "available/unavailable" - c'est automatique !

---

### 5. Tools Ajustés

#### Pour les CLIENTS

##### `check_delivery_zone.py`
```python
class CheckDeliveryZoneTool(Tool):
    """Vérifie les livreurs disponibles dans la zone du client"""

    async def execute(self, context: ToolContext) -> ToolResult:
        # Récupérer position GPS du client
        latitude = context.get('latitude')
        longitude = context.get('longitude')

        # Appeler Laravel API
        drivers = await self.mantota_client.get_available_drivers_in_radius(
            latitude,
            longitude,
            radius_km=5
        )

        # Formater pour Tracy
        return ToolResult.success(data={
            'drivers': drivers,
            'count': len(drivers),
            'client_location': {'lat': latitude, 'lon': longitude}
        })
```

##### `choose_delivery_driver.py`
```python
class ChooseDeliveryDriverTool(Tool):
    """Le client choisit un livreur"""

    async def execute(self, context: ToolContext) -> ToolResult:
        driver_id = context.get('driver_id')
        order_id = context.get('order_id')

        # Assigner la livraison
        assignment = await self.mantota_client.assign_delivery(
            order_id,
            driver_id
        )

        return ToolResult.success(data=assignment)
```

##### `track_delivery_driver.py`
```python
class TrackDeliveryDriverTool(Tool):
    """Le client suit la position du livreur"""

    async def execute(self, context: ToolContext) -> ToolResult:
        assignment_id = context.get('assignment_id')

        # Récupérer position actuelle du livreur
        driver_location = await self.mantota_client.get_driver_location(
            assignment_id
        )

        # Calculer distance restante
        distance = self.calculate_distance(
            context['client_lat'],
            context['client_lon'],
            driver_location['lat'],
            driver_location['lon']
        )

        # Estimer ETA
        eta = self.estimate_eta(distance, driver_location['vehicle_type'])

        return ToolResult.success(data={
            'driver_name': driver_location['name'],
            'distance_km': distance,
            'eta_minutes': eta,
            'driver_lat': driver_location['lat'],
            'driver_lon': driver_location['lon']
        })
```

#### Pour les LIVREURS

##### `update_driver_location.py`
```python
class UpdateDriverLocationTool(Tool):
    """Le livreur met à jour sa position GPS"""

    async def execute(self, context: ToolContext) -> ToolResult:
        driver_id = context.get('driver_id')
        latitude = context.get('latitude')
        longitude = context.get('longitude')

        # Mettre à jour position
        await self.mantota_client.update_driver_location(
            driver_id,
            latitude,
            longitude
        )

        # Calculer automatiquement disponibilité
        is_available = await self.calculate_availability(driver_id)

        return ToolResult.success(data={
            'location_updated': True,
            'is_available': is_available,
            'last_update': now()
        })
```

##### `check_driver_status.py`
```python
class CheckDriverStatusTool(Tool):
    """Le livreur vérifie son statut (basé sur GPS)"""

    async def execute(self, context: ToolContext) -> ToolResult:
        driver_id = context.get('driver_id')

        status = await self.mantota_client.get_driver_gps_status(driver_id)

        return ToolResult.success(data={
            'is_available': status['is_available'],
            'current_location': status['location'],
            'last_update': status['last_update'],
            'zone': status['zone'],
            'reason_unavailable': status['reason']
        })
```

---

### 6. Rappels Automatiques Position GPS

#### Job Laravel: `SendLocationReminderJob`

```php
class SendLocationReminderJob implements ShouldQueue
{
    public function handle()
    {
        // Livreurs avec position obsolète (> 15 min)
        $drivers = DeliveryDriver::where('status', 'approved')
            ->where('last_location_update', '<', now()->subMinutes(15))
            ->get();

        foreach ($drivers as $driver) {
            $minutesSinceUpdate = now()->diffInMinutes($driver->last_location_update);

            $message = match(true) {
                $minutesSinceUpdate > 30 => "⚠️ Attention: Ta position n'a pas été mise à jour depuis {$minutesSinceUpdate} min.

Tu es maintenant INDISPONIBLE pour les commandes.
Envoie ta position GPS pour redevenir visible.",
                default => "⏰ Rappel: Mets à jour ta position GPS

Envoie 'ma position' ou partage ta localisation via WhatsApp pour rester visible pour les clients."
            };

            $whatsapp = app(WhatsAppCloudService::class);
            $whatsapp->sendText($driver->phone, $message);
        }
    }
}
```

**Schedule:** Toutes les 15 minutes

---

### 7. Interface Visualisation (Optionnel mais recommandé)

#### Carte en temps réel pour Admin
```jsx
// Admin Dashboard - Carte livreurs
- Tous les livreurs en temps réel (points sur carte)
- Couleur verte = disponible
- Couleur rouge = indisponible
- Clic sur point = détails livreur
- Voir commandes en cours
- Voir historique déplacements (last 24h)
```

#### Lien carte pour client
```
Tracy: "📍 POSITION DU LIVREUR

Jean K. est à 1.2 km de chez toi.
⏱️ Arrivée estimée: 2 min

🗺️ Voir sur carte: https://mantota.com/track/12345"
```

La carte montre:
- Position livreur (point bleu)
- Position client (point rouge)
- Itinéraire (ligne)
- ETA en temps réel

---

### 8. Cas Spéciaux

#### Cas 1: Aucun livreur dans la zone
```
Tracy: "😔 Aucun livreur disponible dans ta zone actuelle

Options:
1. Élargir la recherche à 10 km ? (oui/non)
2. Essayer dans 10 min ?
3. Demander à un ami de te livrer ?"

Désolé pour le désagrément !"
```

#### Cas 2: Livreur position obsolète
```
Tracy: "⚠️ Le livreur que tu as choisi n'a pas mis à jour sa position depuis 20 min.

Il pourrait ne plus être disponible.

Veux-tu:
1. Attendre 5 min et réessayer ?
2. Choisir un autre livreur ?"
```

#### Cas 3: Livreur quitte sa zone
```
# Automatiquement détecté
# Le livreur devient indisponible
# Les commandes en cours continuent
# Nouvelles commandes ne lui sont plus proposées
```

---

### 9. Configuration et Paramètres

#### Variables de configuration
```php
// config/delivery.php
return [
    'gps' => [
        'location_expiry_minutes' => 15, // Position obsolète après 15 min
        'reminder_interval_minutes' => 15, // Rappel toutes les 15 min
        'search_radius_km' => 5, // Rayon de recherche par défaut
        'max_search_radius_km' => 10, // Rayon maximum
    ],

    'vehicles' => [
        'moto' => ['speed_kmh' => 25, 'base_fee' => 1500],
        'velo' => ['speed_kmh' => 15, 'base_fee' => 1000],
        'voiture' => ['speed_kmh' => 20, 'base_fee' => 2000],
    ],

    'earnings' => [
        'driver_percentage' => 0.8, // 80% pour le livreur
        'distance_bonus_per_km' => 100, // 100 FCFA par km au-delà de 5km
    ],
];
```

---

### 10. Expérience Utilisateur - Comparaison

#### Gozem (App)
- Ouvrir l'app
- Entrer destination
- Voir les options
- Choisir
- Suivre sur carte

#### Mantota (WhatsApp)
- Ouvrir WhatsApp
- Écrire "je veux être livré"
- Envoyer position GPS
- Voir les options
- Choisir (1, 2, 3)
- Suivre en demandant "où est le livreur"

**Avantage Mantota:**
- Pas besoin d'installer l'app
- Fonctionne sur tous les téléphones
- Plus accessible
- WhatsApp déjà installé chez tout le monde

---

## 📋 Plan d'Implémentation (Ajusté)

### Phase 1: Base de données GPS (1 jour)
- [ ] Migration `delivery_drivers` avec champs GPS
- [ ] Migration `driver_location_history`
- [ ] Index sur coordonnées GPS pour performance

### Phase 2: Backend GPS (3-4 jours)
- [ ] `GpsBasedMatchingService`
- [ ] Algorithme Haversine distance
- [ ] API endpoints GPS
- [ ] Job rappels position
- [ ] Calcul disponibilité automatique

### Phase 3: Tracy Core GPS (2-3 jours)
- [ ] Intents clients (request, check_zone, track)
- [ ] Intents livreurs (location, status)
- [ ] Tools GPS (6 tools)
- [ ] Messages automatisés
- [ ] Flows complets

### Phase 4: WhatsApp GPS (2-3 jours)
- [ ] Extraction location depuis messages WhatsApp
- [ ] Flows client (recherche, choix, tracking)
- [ ] Flows livreur (inscription, location, livraison)
- [ ] Rappels automatiques
- [ ] Messages spéciaux (aucun livreur, position obsolète)

### Phase 5: Carte et Visualisation (2-3 jours, optionnel)
- [ ] Carte temps réel admin
- [ ] Lien carte pour client
- [ ] Tracking visuel
- [ ] Historique déplacements

### Phase 6: Tests (2-3 jours)
- [ ] Tests matching GPS
- [ ] Tests distance calcul
- [ ] Tests disponibilité automatique
- [ ] Tests rappels position
- [ ] Tests end-to-end

**Total:** 10-16 jours

---

## 🎯 MVP vs Complet

### MVP (Lancement rapide - 10 jours)
- ✅ Position GPS manuelle (livreur envoie régulièrement)
- ✅ Rappels automatiques toutes les 15 min
- ✅ Matching basé sur GPS
- ✅ Flows complets client et livreur
- ❌ Pas de carte visuelle
- ❌ Pas de tracking continu automatique

### Complet (V2 - +6 jours)
- ✅ App Mantota avec tracking continu
- ✅ Carte temps réel
- ✅ Historique déplacements
- ✅ Analytics avancés

---

## 💡 Recommandations

1. **Commencer avec MVP WhatsApp-only**
   - Position manuelle avec rappels
   - Pas d'app requise
   - Plus rapide à lancer

2. **Messages clairs et fréquents**
   - Rappels position
   - Notifications disponibilité
   - Feedback immédiat

3. **Tester avec 5-10 livreurs**
   - Valider le flux GPS
   - Ajuster les délais (15 min ? 30 min ?)
   - Feedback UX

4. **Optimiser la distance de recherche**
   - Commencer avec 5 km
   - Ajuster selon densité livreurs
   - Permettre élargissement manuelle

5. **Gérer les cas edge**
   - Aucun livreur dans la zone
   - Position obsolète
   - Livreur quitte sa zone
   - Plusieurs commandes simultanées

---

## 🚀 Avantages de cette Approche

1. **100% WhatsApp** - Accessible à tous
2. **GPS temps réel** - Expérience type Gozem
3. **Disponibilité automatique** - Pas de "je suis disponible" manuel
4. **Matching intelligent** - Basé sur distance réelle
5. **Flexible** - Fonctionne avec ou sans app
6. **Scalable** - Peut gérer des milliers de livreurs
7. **Moderne** - Expérience fluide et intuitive

---

## ❓ Questions de Validation

1. **Position GPS:** Manuelle avec rappels (MVP) ou app avec tracking continu (V2) ?

2. **Délai position obsolète:** 15 min ou 30 min avant de marquer indisponible ?

3. **Rayon de recherche:** 5 km par défaut ou autre ?

4. **Carte visuelle:** Inclure dans MVP ou V2 ?

5. **Nombre livreurs beta:** Combien pour tester ?

6. **Zone de démarrage:** Cotonou uniquement ou multi-villes ?

7. **Rappels position:** Toutes les 15 min ou autre fréquence ?
