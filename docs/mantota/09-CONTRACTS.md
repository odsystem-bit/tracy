# Mantota — Module Contracts

## 1. Vision

### Le constat

En Afrique, une part importante des transactions commerciales ne se fait pas en un seul paiement immédiat. Les vendeurs sont régulièrement confrontés à trois situations :

- Un client veut **réserver** un produit avant de le payer (peur qu'il soit vendu à quelqu'un d'autre).
- Un client veut **payer en plusieurs fois** parce que le montant est élevé pour lui.
- Un vendeur veut **sécuriser une vente** sans prendre de risque (impayés, désistements, litiges).

Aujourd'hui, ces situations se gèrent de bouche à oreille, par WhatsApp, par des accords verbaux — sans trace, sans garantie, sans recours en cas de problème. Le vendeur n'a aucun moyen simple de formaliser un engagement, et le client n'a aucune preuve de ce qu'il a payé ou doit payer.

### Le problème central

**Il n'existe aucun outil simple et accessible pour formaliser un engagement de paiement entre un vendeur et un client en Afrique.** Les solutions existantes (contrats notariés, accords bancaires) sont lourdes, coûteuses, et inaccessibles au commerce de proximité ou en ligne.

### La réponse : le module Contracts de Mantota

Mantota propose un module Contracts qui permet à n'importe quel vendeur de proposer trois modes d'engagement à ses clients :

1. **Paiement comptant** — le client paye intégralement au moment de la commande.
2. **Réservation** — le client verse un acompte pour bloquer le produit, puis paye le reste avant la livraison.
3. **Paiement échelonné** — le client paye en plusieurs échéances sur une durée définie, avec un contrat officiel généré automatiquement.

Le vendeur configure ses préférences une fois. Mantota génère le contrat, gère les échéances, les signatures, les statuts, les paiements et les documents PDF. Le client discute avec Tracy, qui l'accompagne tout au long du processus — mais Tracy ne décide jamais, Mantota décide toujours.

---

## 2. Philosophie

### Règle d'or

> **Le contrat appartient à Mantota. Tracy n'est jamais responsable du contrat.**

Tracy accompagne la conversation. Mantota exécute la logique.

### Responsabilités de Tracy

Tracy peut :

- **Expliquer** les modes de paiement disponibles pour une boutique.
- **Résumer** un contrat existant (montant, échéances, statut).
- **Répondre** aux questions du client sur son contrat.
- **Rappeler** les échéances à venir.
- **Accompagner** le client dans la signature et les paiements.

Tracy ne peut **jamais** :

- Générer ou modifier un contrat.
- Décider des conditions (acompte, nombre d'échéances, durée).
- Valider une signature sans Mantota.
- Annuler un contrat sans validation Mantota.
- Promettre un délai ou une condition non confirmée par Mantota.

### Responsabilités de Mantota

Mantota est responsable de :

- **Générer** le contrat officiel (PDF, version, horodatage).
- **Gérer** les échéances (création, recalcul, statuts).
- **Gérer** les signatures (PIN, OTP, compte Mantota).
- **Gérer** les statuts du contrat (pending, active, completed, cancelled, overdue).
- **Gérer** les paiements liés au contrat (via Moneroo).
- **Gérer** les documents PDF (génération, stockage, téléchargement).

---

## 3. Modes disponibles

### 3.1 Paiement comptant

#### Fonctionnement

Le client paye la totalité du montant au moment de la commande. Le contrat est généré, signé (par confirmation de paiement), et immédiatement marqué comme `completed`.

#### Avantages

- Simplicité maximale : aucune échéance à gérer.
- Aucun risque d'impayé pour le vendeur.
- Le client reçoit immédiatement son contrat et son reçu.

#### Limitations

- Le client doit disposer du montant total immédiatement.
- Aucune flexibilité pour les achats importants.

#### Conditions

- Le paiement doit être validé par Moneroo avant que le contrat ne passe en `completed`.
- Si le paiement échoue, le contrat reste en `pending` et expire après un délai configurable.

---

### 3.2 Réservation

#### Fonctionnement

Le client verse un **acompte** (pourcentage ou montant fixe défini par le vendeur) pour bloquer le produit. Le solde doit être payé avant la livraison. Le contrat passe en statut `active` dès que l'acompte est confirmé.

#### Avantages

- Sécurise la vente pour le vendeur (le produit est bloqué).
- Permet au client de réserver sans payer la totalité immédiatement.
- Formalise l'engagement des deux parties.

#### Limitations

- Le produit est bloqué : il n'est plus disponible à la vente pour d'autres clients.
- Si le client ne finalise pas dans le délai imparti, l'acompte peut être perdu (selon les conditions du vendeur).
- Le vendeur doit définir un acompte minimum et une durée de validité.

#### Conditions

- **Acompte minimum** : configurable par le vendeur (pourcentage du montant total ou montant fixe).
- **Durée de validité** : délai maximum pour finaliser le paiement (ex: 7 jours, 14 jours).
- **Pénalité** : si le client ne finalise pas à temps, l'acompte est conservé ou remboursé selon la configuration du vendeur.
- Le produit est décrémenté du stock dès la réservation confirmée.

---

### 3.3 Paiement échelonné

#### Fonctionnement

Le client paye en **plusieurs échéances** sur une durée définie. Un contrat officiel est généré, signé par les deux parties, et les paiements sont automatiquement déclenchés (ou manuels, selon la configuration) à chaque échéance.

#### Avantages

- Rend accessibles des achats importants (électroménager, véhicule, matériel professionnel).
- Formalise un engagement clair avec un contrat officiel.
- Le vendeur est protégé par le contrat signé.

#### Limitations

- Risque d'impayé sur les échéances futures.
- Nécessite une configuration plus détaillée (nombre d'échéances, durée, jours de tolérance).
- Le vendeur doit accepter de livrer après un paiement partiel (ou à la fin, selon sa configuration).

#### Conditions

- **Acompte minimum** : un acompte est généralement requis à la signature.
- **Nombre maximum d'échéances** : configurable par le vendeur (ex: 2, 3, 6, 12).
- **Durée maximale** : durée totale du contrat (ex: 3 mois, 6 mois, 12 mois).
- **Jours de tolérance** : délai accordé après une échéance avant de marquer le contrat en `overdue` (ex: 3 jours, 7 jours).
- **Livraison** : configurable — livraison après acompte, après 50% payé, ou après paiement complet.
- **Produits concernés** : le vendeur peut limiter le paiement échelonné à certains produits ou catégories.

---

## 4. Paramètres vendeur

Le vendeur configure ses préférences de contrats depuis son tableau de bord Mantota. Ces paramètres sont lus par le module Contracts lors de chaque génération de contrat.

### 4.1 Paramètres généraux

| Paramètre | Description | Valeur par défaut |
|---|---|---|
| `cash_payment_enabled` | Autorise le paiement comptant | `true` |
| `reservation_enabled` | Autorise la réservation | `false` |
| `installment_enabled` | Autorise le paiement échelonné | `false` |

### 4.2 Paramètres de réservation

| Paramètre | Description | Valeur par défaut |
|---|---|---|
| `reservation_deposit_min` | Acompte minimum (pourcentage du total) | `20%` |
| `reservation_deposit_fixed` | Acompte fixe (montant absolu, si défini) | `null` |
| `reservation_validity_days` | Durée de validité de la réservation | `7` |
| `reservation_penalty_policy` | Politique en cas de non-finalisation (`keep_deposit` ou `refund_deposit`) | `keep_deposit` |

### 4.3 Paramètres de paiement échelonné

| Paramètre | Description | Valeur par défaut |
|---|---|---|
| `installment_max_count` | Nombre maximum d'échéances | `3` |
| `installment_max_duration_months` | Durée maximale du contrat (en mois) | `3` |
| `installment_deposit_min` | Acompte minimum à la signature | `30%` |
| `installment_grace_days` | Jours de tolérance après une échéance | `3` |
| `installment_delivery_trigger` | Condition de déclenchement de la livraison (`after_deposit`, `after_50_percent`, `after_full_payment`) | `after_full_payment` |
| `installment_allowed_products` | Liste des IDs produits/categorys éligibles (`null` = tous) | `null` |
| `installment_auto_charge` | Déclencher automatiquement les paiements (`true`) ou attendre le paiement manuel (`false`) | `false` |

### 4.4 Conditions particulières

Le vendeur peut définir des **conditions particulières** (texte libre) qui seront incluses dans le contrat généré par Mantota. Ces conditions sont ajoutées au PDF du contrat et sont visibles par le client avant signature.

Exemples :
- « En cas de retard de plus de 7 jours, le contrat est annulé et l'acompte est conservé. »
- « La livraison est effectuée après le paiement de la 2ème échéance. »
- « Les produits soldés ne sont pas éligibles au paiement échelonné. »

---

## 5. Contrat universel Mantota

### Principe

Le vendeur ne rédige jamais un contrat. Mantota génère automatiquement un **contrat officiel** à partir des informations de la commande, des paramètres du vendeur et du mode de paiement choisi.

### Format

Le contrat est un document PDF officiel, horodaté, versionné et stocké côté Mantota. Il est accessible au vendeur et au client via l'API Mantota et le tableau de bord.

### Informations présentes dans le contrat

#### Identification

- **Référence du contrat** : identifiant unique généré par Mantota (ex: `CTR-2025-000001`).
- **Version** : numéro de version du contrat (incrémenté à chaque modification).
- **Date de création** : date et heure de génération.
- **Date de signature** : date et heure de signature par les deux parties.

#### Parties

- **Vendeur** : nom, nom de la boutique, adresse, contact, identifiant Mantota.
- **Client** : nom, contact, identifiant Mantota (ou invité si non inscrit).

#### Objet

- **Produit(s)** : nom, description, quantité, prix unitaire.
- **Montant total** : somme totale de la commande.
- **Mode de paiement** : comptant, réservation, ou échelonné.

#### Conditions financières

- **Acompte** : montant et pourcentage (si applicable).
- **Échéances** : tableau détaillé (numéro, date prévue, montant, statut).
- **Jours de tolérance** : délai accordé après chaque échéance.
- **Pénalités** : conditions en cas de retard ou de non-paiement.

#### Livraison

- **Adresse de livraison** : adresse complète.
- **Condition de livraison** : quand la livraison est déclenchée (selon la configuration vendeur).
- **Date estimée** : calculée par Mantota en fonction des échéances.

#### Conditions particulières

- Texte libre défini par le vendeur (section 4.4).

#### Signatures

- **Signature vendeur** : méthode, date, IP, horodatage.
- **Signature client** : méthode, date, IP, horodatage.
- **Version du contrat signé** : référence de version.

#### Mentions légales

- Clause de résolution des litiges.
- Politique de confidentialité (RGPD / loi locale).
- Droit de rétractation (si applicable).
- Contact support Mantota.

---

## 6. Signature

### Principe

Un contrat n'est valide qu'après signature des deux parties. La signature est gérée entièrement par Mantota — Tracy ne fait qu'accompagner le client dans le processus.

### Méthodes de signature

#### 6.1 PIN

Le client saisit un code PIN à 4 ou 6 chiffres (défini lors de la création de son compte Mantota). La signature est validée si le PIN correspond.

- **Sécurité** : le PIN n'est jamais stocké en clair, ni transmis à Tracy.
- **Tentatives** : après 3 échecs, la signature est bloquée pendant 15 minutes.

#### 6.2 OTP (One-Time Password)

Mantota envoie un code à usage unique par SMS ou WhatsApp au client. Le client saisit ce code pour valider sa signature.

- **Validité** : le code expire après 5 minutes.
- **Tentatives** : après 3 échecs, un nouveau code doit être demandé.

#### 6.3 Compte Mantota

Si le client est connecté à son compte Mantota (via l'APK ou le web), la signature peut être validée par une simple confirmation dans l'interface — équivalent d'une signature électronique.

- **Sécurité** : nécessite une session active et authentifiée.
- **Horodatage** : la signature est horodatée à la seconde.

### Traçabilité de la signature

Chaque signature enregistre les informations suivantes :

| Information | Description |
|---|---|
| **Méthode** | `pin`, `otp`, ou `mantota_account` |
| **Date et heure** | Horodatage UTC précis à la seconde |
| **Adresse IP** | IP du client au moment de la signature |
| **Version du contrat** | Numéro de version signé |
| **User-agent** | Navigateur ou application utilisée |
| **Statut** | `signed` ou `rejected` |

### Signature du vendeur

Le vendeur peut signer automatiquement (paramètre par défaut) ou manuellement. En signature automatique, le contrat est considéré comme signé par le vendeur dès sa génération, sous réserve que les paramètres vendeur autorisent le mode de paiement demandé.

---

## 7. Intégration Tracy

### Principe

Tracy accompagne le client dans ses interactions avec les contrats, mais ne fait qu'appeler les Tools correspondants via l'API Mantota. Aucune logique de contrat n'est embedded dans Tracy.

### Conversations possibles

#### Demande d'information

| Message client | Intention | Tool appelé |
|---|---|---|
| « Je veux payer en plusieurs fois. » | Demande de paiement échelonné | `get_installment_options` |
| « Je veux réserver ce produit. » | Demande de réservation | `create_reservation` |
| « Quels sont les modes de paiement disponibles ? » | Consultation des options | `get_payment_options` |

#### Consultation de contrat

| Message client | Intention | Tool appelé |
|---|---|---|
| « Télécharge mon contrat. » | Demande de PDF | `get_contract_pdf` |
| « Quand est ma prochaine échéance ? » | Consultation d'échéance | `get_contract_schedule` |
| « Combien me reste-t-il à payer ? » | Consultation du solde | `get_contract_balance` |
| « Quel est le statut de mon contrat ? » | Consultation du statut | `get_contract_status` |

#### Action de paiement

| Message client | Intention | Tool appelé |
|---|---|---|
| « Je veux payer maintenant. » | Paiement d'échéance | `pay_installment` |
| « Je veux payer l'acompte. » | Paiement d'acompte | `pay_deposit` |
| « Je veux finaliser ma réservation. » | Paiement du solde | `pay_reservation_balance` |

#### Annulation

| Message client | Intention | Tool appelé |
|---|---|---|
| « Je veux annuler mon contrat. » | Demande d'annulation | `cancel_contract` |

### Règles pour Tracy

- Tracy **vérifie toujours** les options disponibles pour la boutique avant de proposer un mode de paiement.
- Tracy **ne promet jamais** un mode de paiement non autorisé par les paramètres vendeur.
- Tracy **ne génère jamais** un contrat — elle demande à Mantota de le faire.
- Tracy **ne valide jamais** une signature — elle oriente le client vers le processus Mantota.
- Tracy **rappelle** les échéances à venir si le client le demande, mais ne déclenche pas de notification elle-même.
- Tracy **résume** le contrat si le client demande des clarifications, en se basant sur les données retournées par Mantota.

### Tools futurs (non implémentés en V1)

Les Tools suivants seront développés en V2, lors de l'implémentation du module Contracts :

- `get_payment_options` — retourne les modes de paiement disponibles pour une boutique.
- `get_installment_options` — retourne les options d'échéances pour un montant et une boutique.
- `create_reservation` — crée une réservation (acompte + blocage produit).
- `pay_deposit` — paie l'acompte d'une réservation ou d'un échelonné.
- `pay_installment` — paie une échéance d'un contrat échelonné.
- `pay_reservation_balance` — paie le solde d'une réservation.
- `get_contract_status` — retourne le statut d'un contrat.
- `get_contract_schedule` — retourne le calendrier des échéances.
- `get_contract_balance` — retourne le solde restant à payer.
- `get_contract_pdf` — retourne l'URL de téléchargement du PDF.
- `cancel_contract` — demande l'annulation d'un contrat (validation Mantota requise).

---

## 8. Notifications

### Principe

Les notifications sont gérées par Mantota (et le module notifications de Tracy Core, prévu en V2+). Tracy ne déclenche pas de notifications elle-même — elle s'appuie sur les événements émis par Mantota.

### Notifications prévues

#### Échéances

| Événement | Destinataire | Canal | Contenu |
|---|---|---|---|
| **Échéance demain** | Client | WhatsApp / SMS | « Rappel : votre échéance de {montant} FCFA est due demain pour le contrat {référence}. » |
| **Échéance aujourd'hui** | Client | WhatsApp / SMS | « Votre échéance de {montant} FCFA est due aujourd'hui. Payez via ce lien : {url}. » |
| **Échéance en retard** | Client | WhatsApp / SMS | « Votre échéance de {montant} FCFA est en retard de {jours} jours. Merci de régulariser. » |
| **Échéance en retard** | Vendeur | WhatsApp / Dashboard | « Le client {nom} a un retard de {jours} jours sur le contrat {référence}. » |

#### Paiements

| Événement | Destinataire | Canal | Contenu |
|---|---|---|---|
| **Paiement reçu** | Client | WhatsApp / SMS | « Paiement de {montant} FCFA reçu pour le contrat {référence}. Solde restant : {solde} FCFA. » |
| **Paiement reçu** | Vendeur | WhatsApp / Dashboard | « Paiement de {montant} FCFA reçu de {client} pour le contrat {référence}. » |
| **Paiement échoué** | Client | WhatsApp / SMS | « Le paiement de {montant} FCFA a échoué. Veuillez réessayer : {url}. » |

#### Statuts du contrat

| Événement | Destinataire | Canal | Contenu |
|---|---|---|---|
| **Contrat signé** | Vendeur + Client | WhatsApp / Dashboard | « Le contrat {référence} a été signé par les deux parties. » |
| **Contrat terminé** | Vendeur + Client | WhatsApp / Dashboard | « Le contrat {référence} est entièrement payé. Merci ! » |
| **Contrat annulé** | Vendeur + Client | WhatsApp / Dashboard | « Le contrat {référence} a été annulé. {raison}. » |
| **Contrat en retard** | Vendeur | Dashboard | « Le contrat {référence} est en retard de {jours} jours. Action requise. » |

### Canaux supportés (V2+)

- WhatsApp (principal)
- SMS (secours)
- Notifications in-app (APK Mantota)
- Email (optionnel)

---

## 9. Tableau vendeur

### Écrans futurs du tableau de bord Mantota (côté vendeur)

#### 9.1 Vue d'ensemble — Contrats

| Écran | Description |
|---|---|
| **Tous les contrats** | Liste paginée de tous les contrats du vendeur, avec filtres par statut, date, mode de paiement. |
| **En cours** | Contrats actifs (acompte payé, échéances en cours). |
| **Terminés** | Contrats entièrement payés (`completed`). |
| **Annulés** | Contrats annulés (`cancelled`), avec raison. |
| **En retard** | Contrats avec au moins une échéance en retard (`overdue`), avec nombre de jours de retard. |

#### 9.2 Détail d'un contrat

| Information | Description |
|---|---|
| **Référence** | Identifiant unique du contrat. |
| **Client** | Nom, contact, historique d'achats. |
| **Produit(s)** | Liste des produits concernés. |
| **Mode de paiement** | Comptant, réservation, échelonné. |
| **Montant total** | Somme totale. |
| **Acompte payé** | Montant et date. |
| **Échéances** | Tableau avec statut de chaque échéance (paid, pending, overdue). |
| **Solde restant** | Montant restant à payer. |
| **Statut** | Statut global du contrat. |
| **PDF** | Bouton de téléchargement du contrat. |
| **Historique** | Journal des événements (création, signature, paiements, notifications). |

#### 9.3 Réservations

| Écran | Description |
|---|---|
| **Réservations actives** | Réservations avec acompte payé, en attente de finalisation. |
| **Réservations expirées** | Réservations dont le délai de validité est dépassé. |
| **Réservations finalisées** | Réservations converties en vente (solde payé). |

#### 9.4 Paramètres

Écran de configuration des paramètres décrits en section 4.

---

## 10. Tableau client

### Écrans futurs du tableau de bord Mantota (côté client)

#### 10.1 Vue d'ensemble

| Écran | Description |
|---|---|
| **Mes contrats** | Liste de tous les contrats du client, avec statut et solde restant. |
| **Mes réservations** | Réservations actives et expirées. |
| **Paiements** | Historique de tous les paiements liés aux contrats. |
| **Historique** | Journal complet des événements (création, signature, paiements, notifications). |

#### 10.2 Détail d'un contrat

| Information | Description |
|---|---|
| **Référence** | Identifiant unique du contrat. |
| **Vendeur** | Nom de la boutique, contact. |
| **Produit(s)** | Liste des produits concernés. |
| **Mode de paiement** | Comptant, réservation, échelonné. |
| **Montant total** | Somme totale. |
| **Échéances** | Tableau avec dates, montants et statuts. |
| **Prochaine échéance** | Date et montant de la prochaine échéance. |
| **Solde restant** | Montant restant à payer. |
| **Statut** | Statut global du contrat. |
| **Télécharger PDF** | Bouton de téléchargement du contrat officiel. |
| **Payer maintenant** | Bouton pour payer une échéance ou le solde restant. |

#### 10.3 Téléchargement PDF

Le client peut télécharger le PDF de son contrat à tout moment, depuis le tableau de bord ou via Tracy (« Télécharge mon contrat. »). Le PDF est généré par Mantota et inclut toutes les informations décrites en section 5.

---

## 11. Architecture

### Flux complet

```
Client (WhatsApp / APK Mantota)
    ↓
Tracy Core (conversation, accompagnement)
    ↓
Contracts Tools (get_payment_options, create_reservation, pay_installment, etc.)
    ↓
Contracts Module Mantota (logique métier, génération contrat, échéances)
    ↓
Moneroo (paiements)
    ↓
Base de données Mantota (contrats, échéances, signatures, statuts)
```

### Règles architecturales

1. **Tracy ne décide jamais.** Tracy transmet la demande du client via un Tool, et Mantota décide si l'action est autorisée, possible, et sous quelles conditions.
2. **Mantota décide toujours.** Toute logique de contrat (éligibilité, calcul d'échéances, pénalités, statuts) est gérée par le module Contracts de Mantota.
3. **Aucun accès direct à la base.** Tracy et ses Tools passent par l'API bot de Mantota, jamais par la base de données.
4. **Aucune logique métier dans Tracy.** Les Tools ne font que valider les paramètres et transmettre à Mantota.
5. **Moneroo est appelé par Mantota.** Tracy ne parle jamais directement à Moneroo — c'est Mantota qui initie les paiements via Moneroo.
6. **Les documents PDF sont générés par Mantota.** Tracy ne génère jamais de PDF — elle demande l'URL de téléchargement à Mantota.

### Séparation des responsabilités

| Couche | Responsabilité |
|---|---|
| **Client** | Initie la conversation, reçoit les réponses. |
| **Tracy Core** | Classifie l'intention, sélectionne l'agent, appelle les Tools, formule la réponse. |
| **Contracts Tools** | Valident les paramètres, appellent l'API Mantota, retournent un `ToolResult` structuré. |
| **Contracts Module Mantota** | Génère le contrat, calcule les échéances, gère les signatures, les statuts, les pénalités. |
| **Moneroo** | Exécute les transactions de paiement. |
| **Base de données Mantota** | Stocke les contrats, échéances, signatures, historiques. |

---

## 12. Roadmap

### V1 — Documentation uniquement

- ✅ Ce document.
- Aucun code, aucune migration, aucune API, aucune table.
- Le document sert de référence pour le développement futur.

### V2 — Développement du module

- Implémentation du module Contracts côté Mantota (modèles, API bot, génération PDF, gestion des échéances).
- Implémentation des Tools côté Tracy Core (`get_payment_options`, `create_reservation`, `pay_installment`, etc.).
- Implémentation d'un nouvel agent `ContractAgent` (ou extension de `OrderAgent` / `PaymentAgent`).
- Notifications d'échéances et de paiements (via le module notifications de Tracy Core).
- Tableaux de bord vendeur et client (côté Mantota).

### V3 — Extensions

- **Crédit partenaire** :允许 les partenaires (influenceurs, affiliés) de financer des contrats pour leurs clients parrainés.
- **Financement bancaire** : intégration avec des institutions financières pour proposer du crédit formel.
- **Scoring** : évaluation du risque client basée sur l'historique de paiement (score de fiabilité).
- **Assurance contrat** : protection du vendeur contre les impayés via un mécanisme d'assurance.
- **Contrats récurrents** : abonnements et paiements récurrents automatiques.

---

> **Règle d'or** : Tracy ne décide jamais. Mantota décide toujours. Le contrat appartient à Mantota.
