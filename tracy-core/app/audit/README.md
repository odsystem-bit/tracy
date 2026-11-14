# Module Audit

## Rôle

Le module audit fournit une journalisation d'audit pour traçabilité métier et conformité. Il est distinct des logs techniques (structlog) : l'audit trace les actions métier (connexions, commandes, paiements, modifications) pour audit ultérieur.

## Fonctionnement futur

```
Agent / Tool / Orchestrateur
  │
AuditLogger.log(event_type, context, description)
  │
AuditEvent construit (immuable, horodaté)
  │
AuditRepository.save(event)
  │
Mantota API (V2) / Base dédiée (V3)
```

L'`AuditLogger` est l'interface de haut niveau utilisée par le reste de Tracy. L'`AuditRepository` gère le stockage (délégué à Mantota en V2).

## Événements prévus

| Type | Description | Exemple |
|---|---|---|
| `connexion` | Connexion/déconnexion utilisateur | "Vendeur connecté à la boutique X" |
| `commande` | Création, modification, annulation | "Commande #123 créée pour 50 000 FCFA" |
| `paiement` | Initiation, confirmation, échec | "Paiement initié via Moneroo pour #123" |
| `wallet` | Consultation, retrait, dépôt | "Retrait de 100 000 FCFA demandé" |
| `outil_ia` | Appel à un tool, réponse d'agent | "search_products appelé par CommercialAgent" |
| `conversation` | Début/fin, transfert d'agent | "Conversation transférée à NegotiationAgent" |
| `erreur` | Erreur technique, exception | "MantotaApiError sur /bot/orders" |
| `modification` | Modification catalogue, prix, règle | "Prix du riz modifié : 600 → 650 FCFA" |

## Composants prévus

| Composant | Rôle | Statut | Version cible |
|---|---|---|---|
| AuditLogger | Interface de log d'audit de haut niveau | Non implémenté | V2 |
| AuditEvent | Schéma d'événement d'audit (immuable) | Défini | — |
| AuditRepository | Dépôt de stockage (Mantota) | Non implémenté | V2 |
| AuditContext | Contexte d'audit (qui, où, quand) | Défini | — |

## Dépendances futures

- Aucune dépendance externe supplémentaire (utilise httpx via MantotaClient).
- En V3 : Elasticsearch ou ClickHouse pour requêtes analytiques.

## État actuel

**Module préparé. Aucune implémentation dans la V1.**

Les interfaces abstraites (`AuditLogger`, `AuditRepository`) et les schémas Pydantic (`AuditEvent`, `AuditContext`) sont créés. Les 8 types d'événements sont définis. Aucune logique de stockage ou de log n'est implémentée.

En V1, les logs techniques (structlog) suffisent pour l'observabilité. L'audit métier sera ajouté en V2.

## Fichiers

```
app/audit/
├── __init__.py
├── base.py          # AuditLogger + AuditRepository (interfaces)
├── schemas.py       # AuditEvent + AuditContext (Pydantic)
└── README.md        # Ce fichier
```

## TODO pour les futures versions

- [ ] Implémenter AuditRepository via API Mantota (V2)
- [ ] Implémenter AuditLogger avec construction automatique d'AuditEvent (V2)
- [ ] Intégrer AuditLogger dans les agents (log après chaque action)
- [ ] Intégrer AuditLogger dans les tools (log après chaque exécution)
- [ ] Intégrer AuditLogger dans l'orchestrateur (log des transitions d'agent)
- [ ] Ajouter l'audit des connexions via Gateway middleware (V2)
- [ ] Ajouter l'audit des modifications de catalogue (V2)
- [ ] Implémenter AuditRepository avec Elasticsearch/ClickHouse (V3)
- [ ] Ajouter des tests unitaires pour chaque type d'événement
