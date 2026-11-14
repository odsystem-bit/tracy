# Tracy — Règles de développement

## Objectif

Ce document doit être lu avant tout développement sur Tracy Core, les Agents ou les Tools. Il s'applique à Claude, Copilot, ou tout autre assistant/développeur travaillant sur le projet.

Ces règles ne sont pas des suggestions : elles sont obligatoires.

---

## Règle fondamentale

> **Tracy ne décide jamais. Mantota décide.**
> **Tracy comprend. Mantota exécute.**

Toute logique métier (calcul de prix, validation de commande, règles de remboursement, permissions) vit exclusivement dans Mantota. Tracy Core, les Agents et les Tools ne font qu'orchestrer des appels vers Mantota.

---

## Règles obligatoires

1. **Aucune logique métier** dans Tracy Core, les Agents ou les Tools. Si une règle métier est nécessaire, elle doit être implémentée dans Mantota et exposée via une API.

2. **Tout passe par Mantota.** Aucune action réelle (créer, modifier, supprimer, payer) ne peut être exécutée sans passer par une API Mantota.

3. **Aucun accès direct à la base de données.** Ni Tracy Core, ni les Agents, ni les Tools ne se connectent directement à PostgreSQL. Seule Mantota possède cet accès.

4. **Toujours utiliser les Tools.** Un Agent n'appelle jamais une API externe ou Mantota directement : il passe systématiquement par un Tool déclaré (voir `04-TOOLS.md`).

5. **Architecture DDD.** Le code est organisé par domaine métier, avec une séparation claire entre couche applicative, domaine et infrastructure.

6. **Code SOLID.** Chaque classe a une responsabilité unique. Les dépendances sont injectées, jamais codées en dur.

7. **Pydantic obligatoire.** Toute entrée et sortie de fonction publique (Tool, endpoint, Agent) est typée et validée via des modèles Pydantic.

8. **Tests obligatoires.** Aucune fonctionnalité n'est mergée sans tests couvrant son comportement nominal et ses cas d'erreur.

9. **Type hints obligatoires.** Tout le code Python déclare explicitement ses types (paramètres et retours).

10. **Aucun `print`.** Toute sortie de diagnostic passe par un logger structuré.

11. **Logs structurés.** Chaque log contient un contexte exploitable (ID de corrélation, agent, tool, durée, résultat) sous un format structuré (JSON).

12. **Pas de dépendance circulaire.** Un module ne peut jamais dépendre, directement ou indirectement, d'un module qui dépend de lui.

13. **100% asynchrone.** Tout code d'entrée/sortie (réseau, base de données, appel IA) est écrit en `async`/`await`. Aucun appel bloquant synchrone dans le chemin critique.

14. **Python 3.12.** Version de référence unique pour Tracy Core, les Agents et les Tools.

15. **Aucun système de facturation propre à Tracy.** Aucune table de plans, quotas ou abonnements ne doit exister côté Tracy Core. La facturation Tracy passe exclusivement par le Wallet et les Transactions de Mantota (voir `02-ARCHITECTURE.md`, section Facturation).

16. **Aucune base de données dupliquée.** Tracy Core ne recrée jamais localement une copie des vendeurs, produits, commandes ou conversations. Mantota reste la seule source de vérité, y compris pour l'historique conversationnel durable.

---

## Avant de développer une nouvelle fonctionnalité

- Vérifier si la logique métier nécessaire existe déjà dans Mantota. Si non, elle doit y être ajoutée avant toute chose.
- Vérifier si un Tool existant peut couvrir le besoin avant d'en créer un nouveau.
- Documenter tout nouveau Tool dans `04-TOOLS.md` et tout nouvel Agent dans `03-AGENTS.md` avant de merger le code.
- Écrire les tests avant ou en même temps que l'implémentation.

---

## Revue de code — points de blocage automatiques

Un changement doit être rejeté s'il :
- introduit une règle métier hors de Mantota,
- accède directement à une base de données depuis Tracy Core, un Agent ou un Tool,
- contourne le système de Tools pour exécuter une action,
- contient du code synchrone bloquant dans un chemin async,
- ne contient pas de type hints ou de validation Pydantic,
- ne contient pas de tests pour le nouveau comportement.

---

## Modules préparés (extensions futures)

Les modules suivants existent sous forme d'interfaces et de schémas uniquement. Ils sont préparés pour un développement futur sans casser Tracy Core.

| Module | Chemin | Rôle | Version cible |
|---|---|---|---|
| Notifications | `app/notifications/` | Notifications multi-canal (FCM, APNS, Email, SMS, WhatsApp) | V2+ |
| Security | `app/security/` | Permissions, sessions, tokens, chiffrement, fraude | V2+ |
| Audit | `app/audit/` | Journal d'audit métier (traçabilité des actions) | V2+ |
| Events | `app/events/` | EventBus interne (couplage faible entre composants) | V2+ |

Règles applicables à ces modules :

17. **Aucune logique métier dans les modules transverses.** Le `PermissionEngine` vérifie mais Mantota autorise. Le `FraudDetector` signale mais Mantota décide. L'`AuditLogger` trace mais ne modifie rien.

18. **Aucune dépendance externe ajoutée en V1.** Les modules préparés ne doivent introduire aucune nouvelle dépendance dans `pyproject.toml`. Les dépendances futures (cryptography, aio-pika, etc.) seront ajoutées au moment de l'implémentation.

19. **Aucune connexion à un provider externe.** Les stubs de providers (notifications) lèvent `NotImplementedError`. Aucun appel réseau n'est effectué.

20. **L'EventBus est le point de communication interne.** Quand les modules seront implémentés, ils communiqueront via l'EventBus plutôt que par appels directs, garantissant un couplage faible.
