# Module Security

## Rôle

Le module security centralise la gestion des permissions, rôles, sessions, appareils, tokens, chiffrement, secrets et détection de fraude pour Tracy Core.

## Fonctionnement futur

```
Requête entrante
  │
TokenManager.validate_token() → TokenInfo
  │
RoleChecker.get_user_role() → Role
  │
PermissionEngine.check_permission() → bool
  │
SessionManager.create_session() → Session
  │
Agent/Tool (si autorisé)
  │
FraudDetector.analyze_request() → FraudSignal | None
```

**Règle fondamentale** : Tracy ne décide jamais. Le `PermissionEngine` vérifie les permissions, mais la décision finale d'autorisation appartient toujours à Mantota. Le `FraudDetector` signale mais ne bloque jamais seul.

## Composants prévus

| Composant | Rôle | Statut | Version cible |
|---|---|---|---|
| PermissionEngine | Vérification des permissions par utilisateur/rôle | Non implémenté | V2 |
| RoleChecker | Détermination du rôle (client, vendeur, partenaire) | Non implémenté | V2 |
| SessionManager | Création/invalidation de sessions (Redis) | Non implémenté | V2 |
| DeviceManager | Suivi des appareils connectés | Non implémenté | V2 |
| TokenManager | Émission/validation/révocation de tokens | Non implémenté | V2 |
| EncryptionService | Chiffrement AES-256-GCM + hashing | Non implémenté | V2 |
| SecretManager | Centralisation des secrets (Vault) | Non implémenté | V2 |
| FraudDetector | Détection de patterns suspects | Non implémenté | V3 |

## Dépendances futures

- `cryptography` pour AES-256-GCM et hashing.
- `redis` (déjà présent) pour les sessions.
- HashiCorp Vault ou AWS Secrets Manager pour le SecretManager (V2).
- Aucune de ces dépendances n'est ajoutée en V1.

## État actuel

**Module préparé. Aucune implémentation dans la V1.**

Les interfaces abstraites (`PermissionEngine`, `RoleChecker`, `SessionManager`, `DeviceManager`, `TokenManager`, `EncryptionService`, `SecretManager`, `FraudDetector`) et les schémas Pydantic (`Permission`, `Role`, `Session`, `DeviceInfo`, `TokenInfo`, `FraudSignal`) sont créés. Aucune logique n'est implémentée.

En V1, l'authentification est gérée par la Gateway (clé API statique) via `app/gateway/auth.py`.

## Fichiers

```
app/security/
├── __init__.py
├── base.py          # 8 interfaces abstraites
├── schemas.py       # Modèles Pydantic
└── README.md        # Ce fichier
```

## TODO pour les futures versions

- [ ] Implémenter PermissionEngine avec cache Redis (V2)
- [ ] Implémenter RoleChecker avec cache local + invalidation (V2)
- [ ] Implémenter SessionManager avec Redis (V2)
- [ ] Implémenter DeviceManager avec stockage Mantota (V2)
- [ ] Implémenter TokenManager avec rotation et révocation (V2)
- [ ] Implémenter EncryptionService avec AES-256-GCM (V2)
- [ ] Implémenter SecretManager avec Vault (V2)
- [ ] Implémenter FraudDetector avec règles + ML (V3)
- [ ] Intégrer le PermissionEngine dans le middleware Gateway
- [ ] Ajouter des tests unitaires pour chaque composant
