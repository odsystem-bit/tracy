# Système de Livreurs Mantota - Architecture WhatsApp

**Date:** 30 octobre 2026
**Objectif:** Système de livreurs on-demande via WhatsApp
**Canal:** WhatsApp exclusivement + Application Mantota

---

## 🎯 Vision

Un système propriétaire Mantota où:
- Les livreurs s'inscrivent via WhatsApp
- Ils définissent leur zone de livraison
- Ils gèrent leur disponibilité (ON/OFF) via WhatsApp
- Tracy IA gère le matching livreurs ↔ commandes
- Fiable, robuste, sans dépendance externe

---

## 🏗️ Architecture Complète

### 1. Base de Données

#### Table `delivery_drivers`
```php
Schema::create('delivery_drivers', function (Blueprint $table) {
    $table->id();
    $table->foreignId('user_id')->constrained('users')->cascadeOnDelete();
    $table->string('phone')->unique(); // Numéro WhatsApp
    $table->string('full_name');
    $table->string('vehicle_type'); // moto, voiture, vélo
    $table->string('vehicle_plate')->nullable();
    $table->string('id_document')->nullable(); // Pièce d'identité
    $table->string('id_document_path')->nullable(); // Photo pièce
    $table->enum('status', ['pending', 'approved', 'rejected', 'suspended'])->default('pending');
    $table->boolean('is_available')->default(false); // Disponible maintenant
    $table->json('delivery_zones'); // Zones: [{city: "Cotonou", quartiers: ["Haie Vive", "Fidjrossè"]}]
    $table->decimal('current_latitude', 10, 8)->nullable();
    $table->decimal('current_longitude', 11, 8)->nullable();
    $table->timestamp('last_location_update')->nullable();
    $table->integer('completed_deliveries')->default(0);
    $table->decimal('rating', 2, 1)->default(0); // Note moyenne
    $table->integer('total_ratings')->default(0);
    $table->timestamp('approved_at')->nullable();
    $table->timestamps();
});
```

#### Table `delivery_assignments`
```php
Schema::create('delivery_assignments', function (Blueprint $table) {
    $table->id();
    $table->foreignId('order_id')->constrained('orders')->cascadeOnDelete();
    $table->foreignId('driver_id')->constrained('delivery_drivers')->cascadeOnDelete();
    $table->enum('status', ['assigned', 'picked_up', 'in_transit', 'delivered', 'cancelled', 'failed']);
    $table->timestamp('assigned_at');
    $table->timestamp('picked_up_at')->nullable();
    $table->timestamp('delivered_at')->nullable();
    $table->decimal('pickup_latitude', 10, 8)->nullable();
    $table->decimal('pickup_longitude', 11, 8)->nullable();
    $table->decimal('delivery_latitude', 10, 8)->nullable();
    $table->decimal('delivery_longitude', 11, 8)->nullable();
    $table->text('delivery_notes')->nullable();
    $table->text('failure_reason')->nullable();
    $table->string('proof_photo_path')->nullable(); // Photo livraison
    $table->decimal('distance_km', 8, 2)->nullable();
    $table->decimal('delivery_fee', 10, 2)->default(0);
    $table->decimal('driver_earnings', 10, 2)->default(0);
    $table->timestamps();
});
```

#### Table `driver_location_history`
```php
Schema::create('driver_location_history', function (Blueprint $table) {
    $table->id();
    $table->foreignId('driver_id')->constrained('delivery_drivers')->cascadeOnDelete();
    $table->decimal('latitude', 10, 8);
    $table->decimal('longitude', 11, 8);
    $table->timestamp('recorded_at');
    $table->index(['driver_id', 'recorded_at']);
});
```

---

### 2. Intents Tracy pour Livreurs

Nouveaux intents dans `app/core/intent.py`:

```python
class Intent(str, Enum):
    # ... intents existants ...

    # Livraison - Livreurs
    DELIVERY_DRIVER_REGISTER = "delivery_driver_register"
    DELIVERY_DRIVER_ZONE = "delivery_driver_zone"
    DELIVERY_DRIVER_AVAILABLE = "delivery_driver_available"
    DELIVERY_DRIVER_UNAVAILABLE = "delivery_driver_unavailable"
    DELIVERY_DRIVER_LOCATION = "delivery_driver_location"
    DELIVERY_DRIVER_STATUS = "delivery_driver_status"
    DELIVERY_DRIVER_EARNINGS = "delivery_driver_earnings"
    DELIVERY_ACCEPT_ORDER = "delivery_accept_order"
    DELIVERY_PICKUP_CONFIRM = "delivery_pickup_confirm"
    DELIVERY_DELIVER_CONFIRM = "delivery_deliver_confirm"
```

---

### 3. Agent: DeliveryDriverAgent

Créer `app/agents/delivery_driver_agent.py`:

```python
from app.agents.base import BaseAgent
from app.tools import (
    register_driver,
    set_driver_zone,
    set_driver_availability,
    update_driver_location,
    get_driver_status,
    get_driver_earnings,
    accept_delivery,
    confirm_pickup,
    confirm_delivery,
)

class DeliveryDriverAgent(BaseAgent):
    """Agent spécialisé pour les livreurs sur WhatsApp"""

    def __init__(self, tools_registry, mantota_client, ai_gateway):
        super().__init__(
            name="DeliveryDriverAgent",
            system_prompt="""Tu es l'assistant des livreurs Mantota sur WhatsApp.

RÔLE:
- Aider les livreurs à s'inscrire
- Gérer leur disponibilité
- Définir leurs zones de livraison
- Accepter/refuser les commandes
- Confirmer pickup et livraison

TON:
- Professional mais accessible
- Clair et concis
- Sécuritaire (vérifier identité)

IMPORTANT:
- Un livreur NE peut s'inscrire que via WhatsApp
- Demander toujours la pièce d'identité
- Vérifier la zone de livraison
- Confirmer chaque action importante
""",
            tools_registry=tools_registry,
            mantota_client=mantota_client,
            ai_gateway=ai_gateway,
        )

    async def handle(self, message: str, context: ConversationContext) -> str:
        # Logique spécifique livreurs
        # ...
```

---

### 4. Tools pour Livreurs

Créer les tools dans `app/tools/`:

#### `register_driver.py`
```python
class RegisterDriverTool(Tool):
    """Inscription d'un nouveau livreur"""

    async def execute(self, context: ToolContext) -> ToolResult:
        # Valider données
        # Créer livreur en pending
        # Demander pièce d'identité
        # ...
```

#### `set_driver_zone.py`
```python
class SetDriverZoneTool(Tool):
    """Définir les zones de livraison du livreur"""

    async def execute(self, context: ToolContext) -> ToolResult:
        # Récupérer villes/quartiers
        # Stocker en JSON
        # Valider zones existantes
        # ...
```

#### `set_driver_availability.py`
```python
class SetDriverAvailabilityTool(Tool):
    """Basculer disponibilité ON/OFF"""

    async def execute(self, context: ToolContext) -> ToolResult:
        # Toggle is_available
        # Envoyer confirmation
        # Notifier admin si changement
        # ...
```

#### `update_driver_location.py`
```python
class UpdateDriverLocationTool(Tool):
    """Mettre à jour la position GPS du livreur"""

    async def execute(self, context: ToolContext) -> ToolResult:
        # Parser location (latitude, longitude)
        # Stocker dans driver_location_history
        # Mettre à jour current_location
        # ...
```

#### `accept_delivery.py`
```python
class AcceptDeliveryTool(Tool):
    """Le livreur accepte une commande"""

    async def execute(self, context: ToolContext) -> ToolResult:
        # Vérifier disponibilité
        # Vérifier compatibilité zone
        # Créer assignment
        # Notifier client
        # ...
```

#### `confirm_pickup.py`
```python
class ConfirmPickupTool(Tool):
    """Le livreur confirme avoir récupéré le colis"""

    async def execute(self, context: ToolContext) -> ToolResult:
        # Marquer picked_up
        # Enregistrer location pickup
        # Notifier client
        # ...
```

#### `confirm_delivery.py`
```python
class ConfirmDeliveryTool(Tool):
    """Le livreur confirme la livraison"""

    async def execute(self, context: ToolContext) -> ToolResult:
        # Marquer delivered
        # Demander photo preuve
        # Calculer earnings
        # Notifier client
        # Libérer escrow
        # ...
```

---

### 5. Flow d'Inscription Livreur (WhatsApp)

#### Étape 1: Initialisation
```
User: "Je veux devenir livreur"
Tracy: "Super ! Pour t'inscrire comme livreur Mantota, j'ai besoin de quelques infos :

1. Ton nom complet
2. Type de véhicule (moto/voiture/vélo)
3. Numéro de plaque (optionnel)
4. Ta ville et quartiers de livraison

Commençons par ton nom complet 👇"
```

#### Étape 2: Collecte infos
```
User: "Jean Kouassi, moto, Cotonou, Haie Vive et Fidjrossè"
Tracy: "Parfait Jean ! Voici un résumé :

📝 Nom: Jean Kouassi
🏍️ Véhicule: Moto
📍 Zones: Cotonou (Haie Vive, Fidjrossè)

Est-ce correct ? (oui/non)"
```

#### Étape 3: Confirmation
```
User: "oui"
Tracy: "Excellent ! Dernière étape : envoie une photo de ta pièce d'identité (CNI, passeport, permis) pour vérification.

Cette photo restera confidentielle et servira uniquement à valider ton inscription."
```

#### Étape 4: Upload pièce
```
User: [envoie photo]
Tracy: "Photo reçue ✅

Ton inscription est en cours de validation par l'équipe Mantota. Tu recevras une notification WhatsApp dès que ton compte sera activé.

En attendant, tu peux :
- Consulter ton statut: "mon statut"
- Préparer tes zones: modifier zones

Merci de ta confiance ! 🚚"
```

#### Étape 5: Activation (par admin)
Admin approuve → notification WhatsApp:
```
Tracy: "🎉 Félicitations Jean ! Ton compte livreur est maintenant ACTIVÉ.

Tu peux maintenant :
- Te mettre disponible: "je suis disponible"
- Te mettre indisponible: "je ne suis pas disponible"
- Mettre à jour ta position: envoyer ta position GPS
- Voir tes gains: "mes gains"

Commence par te mettre disponible pour recevoir des commandes !"
```

---

### 6. Flow Gestion Disponibilité

#### Mettre disponible
```
User: "je suis disponible"
Tracy: "✅ Tu es maintenant DISPONIBLE pour les livraisons.

Les commandes dans ta zone (Cotonou - Haie Vive, Fidjrossè) te seront proposées automatiquement.

N'oublie pas de mettre à jour ta position GPS régulièrement pour un meilleur matching !"
```

#### Mettre indisponible
```
User: "je ne suis pas disponible"
Tracy: "⏸️ Tu es maintenant INDISPONIBLE.

Tu ne recevras plus de propositions de livraison.
Dis-moi quand tu seras prêt: "je suis disponible" 😉"
```

---

### 7. Flow Mise à jour Position

#### Via message texte
```
User: "ma position"
Tracy: "Pour mettre à jour ta position, envoie ta localisation GPS via WhatsApp.

📍 Sur WhatsApp: Menu > Envoyer ma position actuelle

Cela m'aidera à te proposer des commandes proches de toi !"
```

#### Via location sharing (WhatsApp)
```
User: [envoie location GPS]
Tracy: "✅ Position reçue !

📍 Latitude: 6.357
📍 Longitude: 2.417
📍 Adresse: Haie Vive, Cotonou

Ta position est mise à jour. Les commandes dans cette zone te seront proposées en priorité."
```

---

### 8. Flow Acceptation Commande

#### Proposition de commande
```
Tracy: "📦 NOUVELLE COMMANDE DISPONIBLE

🛍️ Produit: Sac à main noir
💰 Prix: 25 000 FCFA
📍 Pickup: Boutique Élégance, Cotonou
📍 Livraison: Haie Vive, Cotonou
📏 Distance: ~2 km
💵 Livraison: 1 500 FCFA
💸 Tes gains: 1 200 FCFA (80%)

Veux-tu accepter cette livraison ?
Réponds: "oui" ou "non"

Tu as 5 minutes pour répondre."
```

#### Acceptation
```
User: "oui"
Tracy: "✅ COMMANDE ACCEPTÉE

📦 Détails:
- Rends-toi à: Boutique Élégance, Haie Vive
- Code pickup: #8472
- Montre ce code au vendeur

Une fois le colis récupéré, dis-moi: "récupéré"

Bon trajet ! 🚚"
```

#### Refus
```
User: "non"
Tracy: "Compris. Cette commande sera proposée à un autre livreur.

Tu restes disponible pour les prochaines commandes."
```

---

### 9. Flow Pickup et Livraison

#### Confirmation pickup
```
User: "récupéré"
Tracy: "✅ COLIS RÉCUPÉRÉ

Adresse de livraison:
📍 Haie Vive, Cotonou
📞 Client: 01 XX XX XX XX

Une fois livré, dis-moi: "livré" et envoie une photo du colis livré."

Bon courage !"
```

#### Confirmation livraison
```
User: "livré" [envoie photo]
Tracy: "✅ LIVRAISON CONFIRMÉE

📊 Résumé:
- Distance: 2.1 km
- Livraison: 1 500 FCFA
- Tes gains: 1 200 FCFA
- Total livraisons: 15
- Note moyenne: 4.8/5

Le client a été notifié. Tes gains seront crédités dans ton wallet Mantota dans 24h.

Merci pour ton excellent travail ! ⭐

Veux-tu te remettre disponible ? (oui/non)"
```

---

### 10. Système de Matching (Backend Laravel)

#### Service: `DeliveryMatchingService`

```php
class DeliveryMatchingService
{
    /**
     * Trouve le meilleur livreur pour une commande
     */
    public function findBestDriver(Order $order): ?DeliveryDriver
    {
        // 1. Récupérer livreurs disponibles
        $availableDrivers = DeliveryDriver::where('is_available', true)
            ->where('status', 'approved')
            ->get();

        // 2. Filtrer par zone de livraison
        $driversInZone = $availableDrivers->filter(function ($driver) use ($order) {
            return $this->isInDeliveryZone($driver, $order);
        });

        // 3. Calculer distance depuis position actuelle
        $driversWithDistance = $driversInZone->map(function ($driver) use ($order) {
            $distance = $this->calculateDistance(
                $driver->current_latitude,
                $driver->current_longitude,
                $order->delivery_latitude,
                $order->delivery_longitude
            );

            $driver->distance_to_pickup = $distance;
            return $driver;
        });

        // 4. Trier par distance (plus proche en premier)
        $sortedDrivers = $driversWithDistance->sortBy('distance_to_pickup');

        // 5. Appliquer scoring (rating, completed_deliveries)
        $bestDriver = $sortedDrivers->first(function ($driver) {
            return $driver->rating >= 4.0 && $driver->completed_deliveries >= 5;
        });

        // Fallback: premier disponible si aucun ne matche les critères
        return $bestDriver ?? $sortedDrivers->first();
    }

    /**
     * Vérifie si la commande est dans la zone du livreur
     */
    private function isInDeliveryZone(DeliveryDriver $driver, Order $order): bool
    {
        $zones = $driver->delivery_zones;

        foreach ($zones as $zone) {
            if ($zone['city'] === $order->delivery_city) {
                // Si quartiers spécifiés, vérifier
                if (!empty($zone['quartiers'])) {
                    return in_array($order->delivery_quarter, $zone['quartiers']);
                }
                // Sinon, toute la ville est OK
                return true;
            }
        }

        return false;
    }

    /**
     * Propose une commande à un livreur via WhatsApp
     */
    public function proposeToDriver(Order $order, DeliveryDriver $driver): void
    {
        $message = $this->buildProposalMessage($order, $driver);

        $whatsapp = app(WhatsAppCloudService::class);
        $whatsapp->sendText($driver->phone, $message);

        // Enregistrer la proposition avec timeout 5 min
        DeliveryProposal::create([
            'order_id' => $order->id,
            'driver_id' => $driver->id,
            'expires_at' => now()->addMinutes(5),
        ]);
    }
}
```

---

### 11. Calcul Gains Livreur

#### Structure de rémunération
```php
class DeliveryEarningsCalculator
{
    /**
     * Calcule les gains du livreur
     */
    public function calculate(Order $order, float $distanceKm): array
    {
        $baseFee = $order->delivery_fee;

        // Pourcentage livreur (configurable, ex: 80%)
        $driverPercentage = config('delivery.driver_percentage', 0.8);

        $driverEarnings = $baseFee * $driverPercentage;

        // Bonus distance (si > 5 km)
        $distanceBonus = 0;
        if ($distanceKm > 5) {
            $distanceBonus = ($distanceKm - 5) * 100; // 100 FCFA par km au-delà de 5km
        }

        $totalEarnings = $driverEarnings + $distanceBonus;

        return [
            'base_fee' => $baseFee,
            'driver_percentage' => $driverPercentage * 100,
            'driver_earnings' => $driverEarnings,
            'distance_bonus' => $distanceBonus,
            'total_earnings' => $totalEarnings,
        ];
    }
}
```

---

### 12. Dashboard Admin Livreurs

#### Page React: `DriversManagement.jsx`

```jsx
// Liste des livreurs
- Nom, téléphone, véhicule
- Statut (pending/approved/rejected)
- Disponibilité (ON/OFF)
- Zones de livraison
- Position actuelle (carte)
- Rating, livraisons complétées
- Gains totaux

// Actions
- Approuver/Rejeter inscription
- Suspendre compte
- Voir historique livraisons
- Exporter données
```

---

### 13. Application Mantota (Vue Livreur)

L'application Mantota permettra aussi aux livreurs de:
- Voir leur position sur carte
- Accepter/refuser commandes avec interface visuelle
- Voir itinéraire (Google Maps)
- Scanner code pickup
- Prendre photo livraison
- Voir historique et gains

**Important:** WhatsApp reste le canal PRINCIPAL, l'app est un complément premium.

---

### 14. Sécurité et Fiabilité

#### Vérifications obligatoires
1. ✅ Pièce d'identité requise
2. ✅ Validation manuelle par admin
3. ✅ Zones de livraison validées
4. ✅ Tracking position en temps réel
5. ✅ Photo preuve livraison
6. ✅ Système de rating
7. ✅ Historique complet

#### Protection contre fraude
1. Limite de commandes par jour (nouveau livreur)
2. Vérification location (GPS) vs adresse livraison
3. Photo obligatoire pour livraison
4. Système de dispute (client peut contester)
5. Suspension automatique si taux d'échec > 20%

#### Backup et redondance
1. Location history stockée (last 30 days)
2. Logs de toutes les actions
3. Notifications admin en cas d'anomalie
4. Mode dégradé (proposition manuelle si auto échoue)

---

### 15. Messages Automatiques

#### Rappels disponibilité
```
Tracy: "⏰ Rappel: Tu es marqué INDISPONIBLE depuis 2h.

Des commandes sont en attente dans ta zone !
Dis-moi "je suis disponible" pour les recevoir."
```

#### Rapport quotidien
```
Tracy: "📊 RAPPORT JOURNALIER

Aujourd'hui:
- Livraisons: 3
- Gains: 3 600 FCFA
- Distance totale: 12 km
- Note moyenne: 4.9/5

Continue comme ça ! 🚀"
```

#### Notification nouvelle commande (premium)
```
Tracy: "🔔 NOUVELLE COMMANDE DANS TA ZONE !

Vite, elle expire dans 2 min.
Réponds "details" pour voir."
```

---

## 📋 Plan d'Implémentation

### Phase 1: Base de données (1 jour)
- [ ] Créer migrations
- [ ] Créer models
- [ ] Créer seeders (zones villes/quartiers)

### Phase 2: Backend Laravel (3-4 jours)
- [ ] DeliveryMatchingService
- [ ] DeliveryEarningsCalculator
- [ ] API endpoints (CRUD drivers, assignments)
- [ ] Job proposal automatique
- [ ] Admin panel Laravel

### Phase 3: Tracy Core (2-3 jours)
- [ ] DeliveryDriverAgent
- [ ] 10 tools (register, zone, availability, location, etc.)
- [ ] Intents classification
- [ ] Tests

### Phase 4: WhatsApp Integration (1-2 jours)
- [ ] Update WhatsAppWebhookController
- [ ] Messages automatisés
- [ ] Flow complet inscription
- [ ] Flow disponibilité
- [ ] Flow livraison

### Phase 5: Application Mantota (optionnel, 3-5 jours)
- [ ] Screen Livreur
- [ ] Carte position
- [ ] Interface acceptation commande
- [ ] Itinéraire Google Maps
- [ ] Photo pickup/delivery

### Phase 6: Tests (2-3 jours)
- [ ] Tests unitaires
- [ ] Tests intégration WhatsApp
- [ ] Tests end-to-end
- [ ] Tests charge (multiple livreurs)

**Total estimé:** 10-14 jours

---

## 🎯 Avantages de ce Système

1. **100% WhatsApp** - Pas besoin d'installer l'app
2. **Propriétaire** - Pas de dépendance Gozem/Yango
3. **Flexible** - Zones personnalisables par livreur
4. **Fiable** - Vérifications multiples, tracking GPS
5. **Scalable** - Peut gérer des milliers de livreurs
6. **Économique** - Pas de frais API externes
7. **Contrôle total** - Règles, tarifs, zones configurables

---

## 🚀 Lancement MVP

Pour un lancement rapide:
1. Phase 1-4 uniquement (10 jours)
2. Application Mantota optionnelle (V2)
3. Commencer avec 5-10 livreurs beta
4. Zones limitées (Cotonou uniquement)
5. Validation manuelle initiale
6. Feedback et itération

---

## 💡 Prochaines Étapes

1. Résoudre problème vérification Meta WhatsApp
2. Valider l'architecture avec vous
3. Commencer Phase 1 (Base de données)
4. Tester avec livreurs réels
5. Itérer basé sur feedback
