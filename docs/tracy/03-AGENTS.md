# Tracy — Agents

## Objectif

Ce document liste tous les agents de Tracy. Chaque agent est une unité spécialisée : il a un rôle précis, des entrées et sorties définies, un ensemble d'outils autorisés, et des limites strictes qu'il ne doit jamais dépasser.

Un agent ne prend jamais de décision métier finale seul : il propose, Tracy Core valide, Mantota exécute.

---

## Principe de sélection

Lorsqu'un message arrive, Tracy Core (via le graphe LangGraph) :
1. Classe l'intention du message (recherche, négociation, commande, paiement, réclamation, instruction vendeur...).
2. Sélectionne l'agent (ou les agents) dont le rôle correspond à cette intention.
3. Transmet le contexte nécessaire (conversation, mémoire, boutique) à l'agent.
4. Récupère la sortie de l'agent et décide si un autre agent doit intervenir en complément.
5. Compose la réponse finale.

Un agent n'est jamais sélectionné "par défaut" — l'absence de correspondance claire déclenche une clarification à l'utilisateur plutôt qu'un agent au hasard.

> **Note V1** : En l'état actuel (classification par mots-clés), les intentions non reconnues sont routées vers `CommercialAgent` qui demande clarification au client. Ce comportement sera remplacé en V2 par un flux de clarification dédié via le classificateur LLM (voir `02-ARCHITECTURE.md §Classification d'intention`).

---

## Niveaux d'autonomie par agent

Chaque agent opère avec un niveau d'autonomie, cohérent avec `docs/architecture/32-role-model.md` (historique) mais simplifié pour V1 :

| Agent | Autonomie V1 |
|---|---|
| CommercialAgent | Autonome pour la conversation, jamais pour conclure un paiement |
| NegotiationAgent | Autonome dans la marge définie par le vendeur uniquement |
| CatalogAgent | Autonome sauf actions destructives (confirmation requise) |
| OrderAgent | Autonome pour créer/suivre, confirmation requise pour annuler |
| PaymentAgent | Toujours validé par Mantota avant exécution finale |
| CampaignAgent | Propose, le vendeur valide avant tout envoi payant |
| SupportAgent | Autonome pour répondre, jamais pour rembourser |
| DeliveryAgent | Autonome pour le suivi, jamais pour modifier la commande |
| MemoryAgent | Autonome selon les règles strictes de `06-MEMORY.md` |
| RecommendationAgent | Propose, jamais d'action sans validation vendeur |

---

## CommercialAgent

**Rôle** : Le vendeur virtuel. Anime la conversation commerciale de bout en bout.

**Responsabilité** : Comprendre l'intention du client, présenter les produits pertinents, guider vers la commande.

**Entrées** : message du client, historique de conversation, contexte boutique.

**Sorties** : réponse conversationnelle, proposition de produit, suggestion d'action (commander, négocier, contacter le support).

**Outils autorisés** : `search_products`, `search_catalog`, `search_store`, `send_catalog`, `send_payment_link`, `search_knowledge` (RAG).

**Limites** : ne conclut jamais un paiement lui-même ; transfère à `OrderAgent`/`PaymentAgent` dès qu'une commande est confirmée (`send_payment_link` sert uniquement à relayer un lien déjà généré par `PaymentAgent`). Le tool `search_knowledge` sert uniquement à enrichir la reformulation (contexte quartiers, marchés, moyens de paiement locaux) — le LLM reformule, il ne décide jamais.

---

## NegotiationAgent

**Rôle** : Gère les demandes de réduction ou de négociation de prix.

**Responsabilité** : Évaluer une demande de rabais selon les règles définies par le vendeur (marge minimale, promotions actives) et proposer une contre-offre acceptable.

**Entrées** : produit concerné, prix demandé, historique client, règles de marge du vendeur.

**Sorties** : contre-offre, acceptation, ou refus argumenté.

**Outils autorisés** : `search_catalog`, `get_campaign`.

**Limites** : ne peut jamais accorder une réduction en dehors des marges autorisées par le vendeur ; aucune remise n'est appliquée sans validation Mantota.

---

## CatalogAgent

**Rôle** : Gestionnaire du catalogue produit et guide de création de boutique.

**Responsabilité** : Répondre aux demandes du vendeur sur son catalogue (ajout, modification, recherche, disponibilité) exprimées en langage naturel. Guide également le vendeur lors de la création de sa boutique (Store Creation Flow).

**Entrées** : instruction du vendeur, contexte boutique.

**Sorties** : confirmation de modification, résultat de recherche, alerte de rupture de stock, boutique créée.

**Outils autorisés** : `search_products`, `search_catalog`, `search_store`.

**Limites** : ne modifie jamais le catalogue sans confirmation explicite du vendeur pour les actions destructives (suppression).

### Store Creation Flow

Lors de la création d'une boutique, CatalogAgent guide entièrement le vendeur selon le type de boutique :

- **Boutique physique** :
  1. Demander si le vendeur est actuellement sur place
  2. Lancer automatiquement le GPS et enregistrer la position
  3. Demander une photo de la façade
  4. Demander une description du lieu
  5. Demander les horaires
  6. Demander les zones de livraison
  7. Le vendeur ne saisit jamais latitude ni longitude

- **Boutique en ligne** :
  1. Demander la description
  2. Demander les catégories
  3. Demander les informations de base

- **Boutique hybride (physique + en ligne)** :
  1. Combiner les deux parcours ci-dessus

Ce flux est détaillé dans `docs/mantota/11-STORE_CREATION_FLOW.md`.

---

## OrderAgent

**Rôle** : Responsable du cycle de vie de la commande.

**Responsabilité** : Créer, suivre et annuler des commandes en fonction de la conversation.

**Entrées** : panier, informations client, adresse de livraison.

**Sorties** : commande créée, statut de commande, confirmation d'annulation.

**Outils autorisés** : `create_order`, `cancel_order`, `track_order`.

**Limites** : ne déclenche jamais de paiement lui-même ; délègue systématiquement à `PaymentAgent`.

---

## PaymentAgent

**Rôle** : Responsable des paiements, retraits et remboursements.

**Responsabilité** : Initier un paiement via Moneroo (par l'intermédiaire de Mantota), vérifier le solde du wallet, traiter les demandes de retrait.

**Entrées** : commande à payer, montant, méthode de paiement, demande de retrait.

**Sorties** : lien ou statut de paiement, solde du wallet, confirmation de retrait.

**Outils autorisés** : `create_payment`, `get_wallet`, `request_withdrawal`, `send_payment_link`, `activate_tracy_subscription`.

**Limites** : n'exécute jamais une transaction sans validation Mantota ; ne stocke jamais de données bancaires sensibles.

---

## CampaignAgent

**Rôle** : Responsable des campagnes marketing et des relances.

**Responsabilité** : Proposer et suivre les campagnes promotionnelles, relancer les paniers abandonnés, informer les partenaires de leurs performances.

**Entrées** : objectif de campagne, audience cible, historique d'achats.

**Sorties** : proposition de campagne, message de relance, rapport de performance.

**Outils autorisés** : `get_campaign`, `search_partner`, `send_catalog`.

**Limites** : ne lance jamais une campagne payante sans validation du vendeur.

---

## SupportAgent

**Rôle** : Assistant après-vente.

**Responsabilité** : Traiter les réclamations, répondre aux questions après achat, escalader les cas complexes.

**Entrées** : message du client, historique de commande, motif de la demande.

**Sorties** : réponse, ticket de support, escalade vers un humain.

**Outils autorisés** : `track_order`, `get_wallet`, `cancel_order`, `search_knowledge` (RAG).

**Limites** : ne décide jamais seul d'un remboursement ; propose et transmet pour validation. Peut annuler une commande à la demande explicite du client, jamais de sa propre initiative. Le tool `search_knowledge` sert à retrouver des procédures et FAQ pour répondre au client — le LLM reformule, il ne décide jamais.

---

## DeliveryAgent

**Rôle** : Suivi logistique (V2 — Bientôt).

**Responsabilité** : Assigner une commande à un livreur, suivre le statut de la course, notifier le client.

**Entrées** : commande confirmée, zone de livraison, disponibilité des livreurs.

**Sorties** : assignation de livraison, statut de course, notification de livraison.

**Outils autorisés** : `assign_delivery`, `track_order`.

**Limites** : ne modifie jamais le prix ou le contenu de la commande.

---

## MemoryAgent

**Rôle** : Gardien de la mémoire de Tracy.

**Responsabilité** : Décider quelles informations méritent d'être mémorisées, les organiser, et les restituer aux autres agents au bon moment (voir `06-MEMORY.md`).

**Entrées** : information observée pendant une conversation, requête de contexte d'un autre agent.

**Sorties** : information enregistrée, contexte fourni, confirmation d'oubli.

**Outils autorisés** : `save_memory`, `search_memory`, `update_memory`, `delete_memory`.

**Limites** : ne mémorise jamais d'information non confirmée ou sensible sans règle explicite (voir confidentialité, `06-MEMORY.md`).

---

## RecommendationAgent (Bientôt — V2)

**Rôle** : Moteur de recommandations personnalisées.

**Responsabilité** : Proposer des produits pertinents basés sur l'historique d'achat, les préférences confirmées, et le contexte de la conversation en cours.

**Entrées** : historique client, préférences mémorisées, produits consultés, contexte boutique.

**Sorties** : liste de recommandations, explication du choix, suggestion de cross-sell/up-sell.

**Outils autorisés** : `search_products`, `search_catalog`, `search_memory`.

**Limites** : ne recommande jamais un produit indisponible ; se base uniquement sur des données réelles (historique, préférences confirmées) ; n'invente jamais de préférence.

---

## Règles communes à tous les agents

- Un agent ne communique jamais directement avec l'utilisateur final : il passe toujours par Tracy Core.
- Un agent ne possède pas de base de données propre.
- Un agent ne contourne jamais Mantota pour exécuter une action.
- Un agent signale à Tracy Core lorsqu'il atteint les limites de son rôle plutôt que d'improviser.

---

## Collaboration entre agents — exemple

Scénario : un client négocie puis confirme une commande.

```
CommercialAgent      → présente le produit
NegotiationAgent     → traite la demande de réduction
CommercialAgent      → reprend la conversation après accord sur le prix
OrderAgent           → crée la commande au prix négocié
PaymentAgent         → initie le paiement
```

Tracy Core orchestre cette séquence ; aucun agent n'appelle un autre agent directement.

---

## Gestion des conflits

Si deux agents produisent des résultats incompatibles (ex : `NegotiationAgent` propose un prix que `PaymentAgent` refuse car hors marge), **Tracy Core arbitre** en se basant sur les règles Mantota — jamais sur une préférence d'agent. En cas de doute persistant, Tracy Core informe honnêtement l'utilisateur plutôt que de deviner.

---

## Escalade vers un humain

Tout agent peut déclencher une escalade vers un humain (le vendeur, ou un support) lorsque :
- la demande dépasse ses limites déclarées,
- une information nécessaire est absente et non déductible,
- le client exprime une insatisfaction forte que `SupportAgent` ne peut résoudre seul.

L'escalade est toujours transparente : l'utilisateur est informé qu'il va être mis en relation avec une personne.

---

## Ajout d'un nouvel agent

Avant d'ajouter un agent, définir :
- son rôle et sa responsabilité unique (pas de chevauchement avec un agent existant),
- ses entrées et sorties précises,
- la liste fermée de ses Tools autorisés (voir `04-TOOLS.md`),
- ses limites explicites,
- son niveau d'autonomie,
- au moins un scénario de test dans `09-TEST_SCENARIOS.md`.

Aucun agent n'est mergé sans être documenté ici au préalable.
