# Documentation — OD Système / Tracy / Mantota

## Documentation officielle

À partir de la version Tracy Core v1, toute la documentation de référence se trouve dans :

```
docs/tracy/
```

C'est la **seule source de vérité** à utiliser pour développer, décider ou répondre à une question sur Tracy — que ce soit par un humain, Claude ou Copilot.

Structure :

```
docs/
├── architecture/   ← Documentation historique (lecture seule)
├── tracy/          ← Nouvelle documentation officielle (source de vérité)
├── archive/        ← Anciennes versions, si nécessaire un jour
└── README.md       ← Ce fichier
```

---

## docs/tracy/ — Référence officielle

| Fichier | Contenu |
|---|---|
| `01-VISION.md` | Pourquoi Tracy existe, ses objectifs, ses rôles, ses principes. |
| `02-ARCHITECTURE.md` | Architecture technique complète et flux de communication. |
| `03-AGENTS.md` | Tous les agents : rôle, entrées, sorties, outils, limites. |
| `04-TOOLS.md` | Tous les outils disponibles pour les agents. |
| `05-AI_BEHAVIOR.md` | Personnalité, ton, stratégies de vente/négociation, limites comportementales. |
| `06-MEMORY.md` | Fonctionnement de la mémoire de Tracy. |
| `07-DEVELOPMENT_RULES.md` | Règles obligatoires de développement. |
| `08-ROADMAP.md` | V1, V2, V3, fonctionnalités reportées. |
| `09-TEST_SCENARIOS.md` | Scénarios de test fonctionnels de référence. |

---

## docs/architecture/ — Historique (lecture seule)

Les documents présents dans `docs/architecture/` (et `docs/technical/`) sont conservés **uniquement à titre historique**. Ils retracent les réflexions et décisions antérieures à la consolidation de la documentation officielle.

Ils ne doivent **plus** être utilisés comme source principale lors du développement. En cas de conflit entre `docs/architecture/` et `docs/tracy/`, **`docs/tracy/` fait toujours foi**.

Rien n'est supprimé : cette documentation reste consultable pour comprendre l'historique d'une décision si nécessaire.

---

## Règle pour les contributeurs (humains et IA)

Avant tout développement sur Tracy :
1. Lire `docs/tracy/07-DEVELOPMENT_RULES.md`.
2. Vérifier que la fonctionnalité est déjà décrite dans `docs/tracy/`. Si non, documenter d'abord, développer ensuite.
3. Ne jamais recréer un nouveau fichier `.md` à la racine de `docs/tracy/` sans concertation — enrichir les documents existants.
