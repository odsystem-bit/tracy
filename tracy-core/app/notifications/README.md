# Module Notifications

## Rôle

Le module notifications permet à Tracy d'envoyer des notifications aux clients, vendeurs et partenaires via plusieurs canaux : push mobile (FCM, APNS), web push, email, SMS, et WhatsApp.

## Fonctionnement futur

```
Agent/Orchestrateur
  │
NotificationService.notify(event, template)
  │
NotificationDispatcher.dispatch(message)
  │
NotificationProvider (FCM / APNS / WebPush / Email / SMS / WhatsApp)
  │
Canal de destination
```

1. Un agent ou l'orchestrateur émet un `NotificationEvent` (ex: `order_confirmed`).
2. Le `NotificationService` sélectionne un `NotificationTemplate` et génère un `NotificationMessage`.
3. Le `NotificationDispatcher` route le message vers le `NotificationProvider` du canal approprié.
4. Le provider envoie la notification et retourne un `NotificationResult`.
5. En V2, une `NotificationQueue` (Redis/RabbitMQ) découple l'émission de l'envoi effectif.

## Providers prévus

| Provider | Canal | Statut | Version cible |
|---|---|---|---|
| FirebaseCloudMessagingProvider | fcm | Non implémenté | V2 |
| ApplePushNotificationProvider | apns | Non implémenté | V2 |
| WebPushProvider | web_push | Non implémenté | V2 |
| EmailProvider | email | Non implémenté | V2 |
| SmsProvider | sms | Non implémenté | V2 |
| WhatsAppProvider | whatsapp | Non implémenté | V3 |

## Dépendances futures

- `httpx` (déjà présent) pour les appels API.
- `google-auth` pour FCM.
- `cryptography` pour APNS (JWT) et Web Push (VAPID).
- `aiosmtplib` pour Email SMTP.
- Aucune de ces dépendances n'est ajoutée en V1.

## État actuel

**Module préparé. Aucune implémentation dans la V1.**

Les interfaces (`NotificationProvider`, `NotificationService`, `NotificationDispatcher`, `NotificationQueue`), les schémas Pydantic (`NotificationEvent`, `NotificationTemplate`, `NotificationMessage`, `NotificationResult`, `NotificationChannel`) et les stubs de providers sont créés. Aucune logique d'envoi n'est implémentée.

## Fichiers

```
app/notifications/
├── __init__.py
├── base.py          # Interfaces abstraites
├── schemas.py       # Modèles Pydantic
├── providers.py     # Stubs des 6 providers
└── README.md        # Ce fichier
```

## TODO pour les futures versions

- [ ] Implémenter FirebaseCloudMessagingProvider (V2)
- [ ] Implémenter ApplePushNotificationProvider (V2)
- [ ] Implémenter WebPushProvider (V2)
- [ ] Implémenter EmailProvider (V2)
- [ ] Implémenter SmsProvider (V2)
- [ ] Implémenter WhatsAppProvider (V3)
- [ ] Implémenter NotificationDispatcher avec fallback multi-provider
- [ ] Implémenter NotificationQueue (Redis en V2, RabbitMQ en V3)
- [ ] Implémenter NotificationService avec résolution de templates
- [ ] Ajouter la gestion des préférences de notification par utilisateur
- [ ] Ajouter le rate limiting par canal et par destinataire
