# Guide Résolution Problèmes Vérification Meta WhatsApp

## Problèmes Courants de Vérification

### 1. Webhook Verify Token ne fonctionne pas

**Symptôme:** Meta renvoie 403 lors de la vérification webhook

**Solutions:**

#### A. Vérifier le token dans .env
```env
WHATSAPP_WEBHOOK_VERIFY_TOKEN=mantota_verify_2026
```

#### B. Vérifier le controller Laravel
Dans `app/Http/Controllers/Webhook/WhatsAppWebhookController.php`:

```php
public function verify(Request $request): JsonResponse
{
    $mode = $request->query('hub_mode');
    $token = $request->query('hub_verify_token');
    $challenge = $request->query('hub_challenge');

    $expectedToken = config('services.whatsapp.webhook_verify_token', 'mantota_verify_2026');

    // Debug: log les valeurs reçues
    Log::info('Webhook verify attempt', [
        'mode' => $mode,
        'token_received' => $token,
        'token_expected' => $expectedToken,
        'challenge' => $challenge,
    ]);

    if ($mode === 'subscribe' && $token === $expectedToken) {
        return response()->json((int) $challenge);
    }

    return response()->json(['message' => 'Verification failed'], 403);
}
```

#### C. Vérifier que le webhook est accessible publiquement
```bash
curl -X GET "https://votre-domaine.com/api/whatsapp/webhook?hub_mode=subscribe&hub_verify_token=mantota_verify_2026&hub_challenge=123456"
```

Devrait retourner: `123456`

---

### 2. URL Webhook non accessible

**Symptôme:** Meta dit "Unable to validate URL"

**Solutions:**

#### A. Vérifier SSL
```bash
curl -I https://votre-domaine.com/api/whatsapp/webhook
```

Doit retourner: `HTTP/2 200` avec certificate valide

#### B. Vérifier que le domaine est public
- Pas en localhost
- Pas derrière VPN
- Pas bloqué par firewall

#### C. Tester avec ngrok (pour développement)
```bash
ngrok http 8000
```
Puis utiliser l'URL ngrok dans Meta Dashboard

---

### 3. Permissions Insuffisantes

**Symptôme:** Webhook configuré mais messages non reçus

**Solutions:**

#### A. Vérifier les permissions de l'Access Token
Dans Meta for Developers > App Settings > WhatsApp:

Permissions requises:
- `whatsapp_business_messaging`
- `whatsapp_business_management`

#### B. Vérifier les Webhook Subscriptions
Dans Meta Dashboard > Webhooks:
- ✅ `messages` doit être coché
- ✅ `message_status` (optionnel)

---

### 4. Phone Number ID manquant

**Symptôme:** Erreur "Phone Number ID not found"

**Solutions:**

#### A. Obtenir le Phone Number ID
1. Meta for Developers > WhatsApp > Configuration
2. Scrollez vers "Phone numbers"
3. Cliquez sur votre numéro
4. Copiez le "Phone Number ID"

#### B. Configurer dans .env
```env
WHATSAPP_PHONE_NUMBER_ID=123456789
```

---

### 5. Access Token expiré ou invalide

**Symptôme:** 401 Unauthorized lors de l'envoi de messages

**Solutions:**

#### A. Régénérer l'Access Token
1. Meta for Developers > App Settings > Advanced
2. Scrollez vers "Security"
3. Cliquez "Generate" sous "Access Token"
4. Sélectionnez les permissions
5. Copiez le token (il ne sera plus affiché !)

#### B. Configurer dans .env
```env
WHATSAPP_ACCESS_TOKEN=EAABwz...
```

#### C. Vérifier l'expiration
Les tokens temporaires expirent en 24-60 jours.
Pour la production, utiliser un token permanent (needs approval).

---

## Checklist Dépannage

1. [ ] Webhook accessible publiquement (curl test OK)
2. [ ] SSL certificate valide
3. [ ] Verify token match entre Meta et .env
4. [ ] Route Laravel correcte: `/api/whatsapp/webhook`
4. [ ] Phone Number ID configuré
5. [ ] Access Token valide et non expiré
6. [ ] Permissions correctes
7. [ ] Webhook subscriptions activées (messages)
8. [ ] Logs Laravel activés pour debug

---

## Script de Test Automatique

Créer `test-webhook.php` à la racine du projet Laravel:

```php
<?php

require __DIR__.'/vendor/autoload.php';

$app = require_once __DIR__.'/bootstrap/app.php';

$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

echo "=== Test Webhook WhatsApp ===\n\n";

// Test 1: Verify endpoint
echo "Test 1: Verify endpoint\n";
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, "http://localhost:8000/api/whatsapp/webhook?hub_mode=subscribe&hub_verify_token=mantota_verify_2026&hub_challenge=12345");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
curl_close($ch);

echo "Response: $response\n";
echo ($response === '12345') ? "✅ PASS\n\n" : "❌ FAIL\n\n";

// Test 2: SSL check
echo "Test 2: SSL check\n";
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, "https://votre-domaine.com/api/whatsapp/webhook");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HEADER, true);
$response = curl_exec($ch);
curl_close($ch);

echo "Response headers:\n$response\n\n";

// Test 3: Config check
echo "Test 3: Config check\n";
echo "WHATSAPP_ACCESS_TOKEN: " . (env('WHATSAPP_ACCESS_TOKEN') ? 'SET' : 'NOT SET') . "\n";
echo "WHATSAPP_PHONE_NUMBER_ID: " . (env('WHATSAPP_PHONE_NUMBER_ID') ? 'SET' : 'NOT SET') . "\n";
echo "WHATSAPP_WEBHOOK_VERIFY_TOKEN: " . env('WHATSAPP_WEBHOOK_VERIFY_TOKEN') . "\n\n";
```

Exécuter: `php test-webhook.php`

---

## Contact Support Meta

Si tout échoue:
- Meta for Developers > Support
- Fournir: App ID, Phone Number ID, screenshot erreur
- Délai réponse: 1-3 jours ouvrés
