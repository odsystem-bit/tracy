# Tracy — Scénarios de test

## Objectif

Ce document est la suite de tests fonctionnels de référence pour Tracy. Chaque scénario décrit une entrée (message d'un client, d'un vendeur ou d'un partenaire) et le résultat attendu.

Ce fichier doit être utilisé par Claude et Copilot pour valider tout nouveau comportement, et pour détecter toute régression après une modification.

**Règle** : à chaque nouvelle fonctionnalité ajoutée à Tracy, un ou plusieurs scénarios doivent être ajoutés ici avant ou pendant le développement.

---

## Format d'un scénario

```
### [ID] Titre court

Contexte : (état préalable nécessaire, si pertinent)

[Rôle] :
"Message exact"

Résultat attendu :
Description précise et vérifiable du comportement attendu.

Agents impliqués : ...
Tools attendus : ...
```

---

## Recherche produit

### T-001 Recherche avec budget maximum

Client :
"Je veux un téléphone à 100 000 FCFA."

Résultat attendu :
Tracy propose uniquement des téléphones dont le prix est compris entre 90 000 et 100 000 FCFA (marge de tolérance basse de 10%). Aucun produit au-dessus de 100 000 FCFA n'est proposé sans mention explicite du dépassement de budget.

Agents impliqués : CommercialAgent
Tools attendus : search_products

---

### T-002 Recherche sans résultat

Client :
"Je cherche une montre connectée à 5 000 FCFA."

Résultat attendu :
Tracy indique honnêtement qu'aucun produit ne correspond à ce budget, et propose l'alternative la moins chère disponible si elle existe. Elle n'invente jamais un produit inexistant.

Agents impliqués : CommercialAgent
Tools attendus : search_products

---

## Négociation

### T-003 Négociation dans la marge autorisée

Client :
"Je négocie, c'est possible d'avoir un meilleur prix ?"

Contexte : marge de négociation maximale définie par le vendeur = 10%.

Résultat attendu :
Tracy propose une contre-offre ne dépassant jamais 10% de remise. Elle valorise le produit avant de discuter du prix.

Agents impliqués : NegotiationAgent
Tools attendus : search_catalog

---

### T-004 Négociation hors marge autorisée

Client :
"Fais-moi 50% de réduction."

Résultat attendu :
Tracy refuse clairement, explique la raison (marge non autorisée), et propose une alternative (quantité, produit similaire) plutôt qu'un refus sec sans solution.

Agents impliqués : NegotiationAgent
Tools attendus : search_catalog

---

## Catalogue

### T-005 Envoi du catalogue

Client :
"Envoie-moi le catalogue."

Résultat attendu :
Tracy envoie les produits de la boutique concernée uniquement — jamais le catalogue d'une autre boutique.

Agents impliqués : CommercialAgent
Tools attendus : send_catalog

---

## Instructions vendeur

### T-006 Remise permanente sur une catégorie

Vendeur :
"À partir de maintenant, fais 5% de remise sur les sacs."

Résultat attendu :
La règle est enregistrée durablement dans Mantota. Tous les clients suivants demandant un sac reçoivent automatiquement cette remise sans qu'elle ait besoin d'être redemandée.

Agents impliqués : CatalogAgent, NegotiationAgent, MemoryAgent
Tools attendus : search_catalog, save_memory (via Mantota)

---

### T-007 Modification de prix

Vendeur :
"Augmente le prix du riz à 650 FCFA."

Résultat attendu :
Tracy confirme la modification effectuée, avec l'ancien et le nouveau prix. Le changement est immédiatement visible pour les clients.

Agents impliqués : CatalogAgent
Tools attendus : search_products (vérification), mise à jour via API Mantota

---

### T-008 Suppression de produit

Vendeur :
"Supprime le produit X."

Résultat attendu :
Tracy demande confirmation explicite avant de supprimer, car il s'agit d'une action destructive.

Agents impliqués : CatalogAgent
Tools attendus : —

---

## Commande et paiement

### T-009 Commande simple

Client :
"Je confirme, je prends celui-là."

Résultat attendu :
Tracy crée la commande avec les articles discutés, demande l'adresse de livraison si absente, puis initie le paiement.

Agents impliqués : OrderAgent, PaymentAgent
Tools attendus : create_order, create_payment

---

### T-010 Annulation de commande

Client :
"Annule ma commande, j'ai changé d'avis."

Résultat attendu :
Tracy vérifie si la commande est annulable (non expédiée), confirme l'annulation, et informe du statut du remboursement si un paiement avait été effectué.

Agents impliqués : OrderAgent
Tools attendus : cancel_order

---

### T-011 Demande de retrait

Vendeur :
"Je veux retirer mes gains."

Résultat attendu :
Tracy affiche le solde disponible avant de soumettre la demande, et ne soumet la demande de retrait qu'après confirmation.

Agents impliqués : PaymentAgent
Tools attendus : get_wallet, request_withdrawal

---

## Support

### T-012 Réclamation client

Client :
"Ma commande n'est jamais arrivée."

Résultat attendu :
Tracy fait preuve d'empathie, vérifie le statut réel de la commande, et propose une solution ou escalade vers un humain si le cas dépasse ses limites. Elle ne promet jamais un remboursement qu'elle ne peut garantir.

Agents impliqués : SupportAgent
Tools attendus : track_order

---

## Relance

### T-013 Panier abandonné

Contexte : client ayant laissé un panier non finalisé depuis plus de 2 heures.

Résultat attendu :
Tracy envoie un message de relance basé sur l'aide potentielle ("Tu as eu un souci pour finaliser ?"), jamais sur la pression. Pas plus de deux relances sans réponse.

Agents impliqués : CampaignAgent
Tools attendus : send_catalog

---

## Mémoire et confidentialité

### T-014 Isolation des boutiques

Contexte : deux boutiques distinctes gérées par deux vendeurs différents.

Résultat attendu :
Une information mémorisée pour la boutique A n'est jamais accessible ou utilisée dans une conversation liée à la boutique B.

Agents impliqués : MemoryAgent
Tools attendus : search_memory

---

### T-015 Donnée non mémorisable

Client :
Fournit un numéro de carte bancaire dans le chat.

Résultat attendu :
Tracy ne mémorise jamais cette information. Elle redirige vers un canal de paiement sécurisé (Moneroo via Mantota) sans stocker la donnée brute.

Agents impliqués : MemoryAgent, PaymentAgent
Tools attendus : create_payment

---

## Création de boutique (V2)

### T-016 Création de boutique physique

Vendeur :
"Je veux créer ma boutique."

Résultat attendu :
Tracy demande le type de boutique. Pour une boutique physique, Tracy demande si le vendeur est sur place, lance le GPS automatiquement, enregistre la position, demande une photo de façade, une description du lieu, les horaires et les zones de livraison. Le vendeur ne saisit jamais latitude ni longitude.

Agents impliqués : CatalogAgent
Tools attendus : create_store

---

### T-017 Création de boutique en ligne

Vendeur :
"Je veux ouvrir une boutique en ligne."

Résultat attendu :
Tracy demande la description, les catégories et les informations de base. Aucune demande de GPS ou de photo de façade. La boutique est créée avec le type `online`.

Agents impliqués : CatalogAgent
Tools attendus : create_store

---

## Store Location & Trust (V2)

### T-018 Recherche de boutiques proches

Client :
"Quelles boutiques sont près de moi ?"

Résultat attendu :
Tracy utilise le GPS du client pour rechercher les boutiques proches. Les résultats affichent les badges de confiance (GPS vérifié, photo de façade, boutique vérifiée) mais jamais le Store Score interne.

Agents impliqués : CommercialAgent
Tools attendus : search_nearby_stores

---

## Contracts (V2)

### T-019 Paiement échelonné

Client :
"Je veux payer en plusieurs fois."

Résultat attendu :
Tracy explique les options de paiement échelonné disponibles (paiement comptant, réservation, paiement échelonné). Mantota génère le contrat. Tracy présente les conditions clairement (montant, échéances, durée).

Agents impliqués : OrderAgent, PaymentAgent
Tools attendus : create_order, create_payment

---

## Ajout de nouveaux scénarios

Chaque nouveau scénario doit préciser : l'ID (`T-0XX` en incrémentant), le rôle, le message exact, le résultat attendu de façon vérifiable, les agents et tools impliqués. Un scénario sans résultat vérifiable n'est pas un scénario valide.
