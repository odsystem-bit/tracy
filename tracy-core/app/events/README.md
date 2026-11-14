# Module Events

## Rôle

Le module events fournit un système d'événements interne (EventBus) pour Tracy Core. Il permet un couplage faible entre les composants : l'orchestrateur, les agents et les tools publient des événements ; les modules (audit, notifications, security) s'y abonnent.

## Fonctionnement futur

```
Orchestrateur / Agent / Tool
  │
EventPublisher.publish(event)
  │
EventBus
  ├──→ AuditLogger (subscribe: tool_executed, order_created, ...)
  ├──→ NotificationService (subscribe: order_confirmed, payment_received, ...)
  ├──→ FraudDetector (subscribe: rapid_requests, unusual_activity, ...)
  └──→ ... (nouveaux subscribers sans modifier le code existant)
```

### Événements prévus (exemples)

| Type | Émetteur | Subscribers potentiels |
|---|---|---|
| `message_received` | Orchestrateur | Audit, Security |
| `intent_classified` | Orchestrateur | Audit |
| `agent_selected` | Orchestrateur | Audit |
| `tool_executed` | Tool / Agent | Audit, FraudDetector |
| `order_created` | OrderAgent (V2) | Audit, Notifications |
| `payment_initiated` | PaymentAgent (V2) | Audit, Notifications |
| `payment_received` | Mantota webhook (V2) | Notifications, Audit |
| `conversation_started` | Orchestrateur | Audit |
| `conversation_ended` | Orchestrateur | Audit |
| `fraud_signal_detected` | FraudDetector (V3) | Security, Audit |
| `catalog_modified` | CatalogAgent | Audit |

## Composants

| Composant | Rôle | Statut | Version cible |
|---|---|---|---|
| BaseEvent | Schéma d'événement de base (Pydantic) | Défini | — |
| EventBus | Bus d'événements central (pub/sub) | Interface | V2 |
| EventPublisher | Interface pour publier des événements | Interface | V2 |
| EventSubscriber | Interface pour s'abonner à des événements | Interface | V2 |

## Implémentations prévues

| Version | Implémentation | Description |
|---|---|---|
| V2 | InMemoryEventBus | In-process, asyncio.gather pour handlers parallèles |
| V2 | RedisEventBus | Redis Pub/Sub pour distribution multi-process |
| V3 | RabbitMQEventBus | File persistante avec retry et dead-letter queue |

## Dépendances futures

- Aucune pour InMemoryEventBus (asyncio natif).
- `redis` (déjà présent) pour RedisEventBus.
- `aio-pika` pour RabbitMQEventBus (V3).
- Aucune dépendance ajoutée en V1.

## État actuel

**Module préparé. Aucune implémentation dans la V1.**

L'interface `BaseEvent` (Pydantic), les interfaces abstraites `EventBus`, `EventPublisher`, `EventSubscriber` sont créées. Aucune implémentation concrète n'est fournie. Aucun composant de Tracy n'est encore connecté à l'EventBus.

## Fichiers

```
app/events/
├── __init__.py
├── base.py          # BaseEvent + EventBus / EventPublisher / EventSubscriber
└── README.md        # Ce fichier
```

## TODO pour les futures versions

- [ ] Implémenter InMemoryEventBus (V2)
- [ ] Définir les événements concrets (MessageReceivedEvent, ToolExecutedEvent, etc.)
- [ ] Connecter l'orchestrateur à l'EventBus (publish)
- [ ] Connecter les agents à l'EventBus (publish)
- [ ] Connecter les tools à l'EventBus (publish)
- [ ] Connecter AuditLogger à l'EventBus (subscribe)
- [ ] Connecter NotificationService à l'EventBus (subscribe)
- [ ] Connecter FraudDetector à l'EventBus (subscribe)
- [ ] Implémenter RedisEventBus pour distribution multi-process (V2)
- [ ] Implémenter RabbitMQEventBus avec retry et DLQ (V3)
- [ ] Ajouter des tests unitaires pour l'EventBus
