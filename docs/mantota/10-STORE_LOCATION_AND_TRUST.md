# Store Location & Trust — Spécification Fonctionnelle

> **Statut** : Documentation fonctionnelle (V1). Aucun code, aucune API, aucune base de données.
> **Objectif** : Servir de référence pour le développement futur du module Store Location & Trust dans Mantota.

---

## Sommaire

1. [Vision](#1-vision)
2. [Types de boutiques](#2-types-de-boutiques)
3. [Enregistrement de la localisation](#3-enregistrement-de-la-localisation)
4. [Photo de façade](#4-photo-de-façade)
5. [Description du lieu](#5-description-du-lieu)
6. [Référentiel géographique](#6-référentiel-géographique)
7. [Rayon de livraison](#7-rayon-de-livraison)
8. [Recherche géographique](#8-recherche-géographique)
9. [Dashboard Mantota](#9-dashboard-mantota)
10. [Store Score](#10-store-score)
11. [Intégration avec Tracy](#11-intégration-avec-tracy)
12. [Roadmap](#12-roadmap)

---

## 1. Vision

### Pourquoi ce module existe

En Afrique francophone, le commerce se fait d'abord en personne. Le client veut savoir **où** se trouve la boutique, **à quoi** elle ressemble, et **si** il peut lui faire confiance. Le e-commerce classique échoue souvent parce qu'il ignore cette dimension humaine et locale.

Le module **Store Location & Trust** répond à ce besoin fondamental : **donner à chaque boutique une présence géographique vérifiable et un score de confiance transparent**.

### Pourquoi la géolocalisation est stratégique

- **Le client cherche proximité** : « pharmacie près de moi », « boutique téléphone Dakar » — la distance est le premier critère de choix.
- **Le livreur a besoin de coordonnées exactes** : sans GPS précis, la livraison échoue ou prend trop de temps.
- **La couverture géographique détermine le marché** : Mantota doit savoir quelles zones sont couvertes et quelles zones ne le sont pas.
- **La découverte locale** : un client qui ne connaît pas Mantota peut découvrir une boutique à 200 m de chez lui grâce à la recherche géographique.

### Pourquoi la confiance est un élément central de Mantota

- **Le client achète s'il trust** : sans confiance, pas de paiement en ligne, pas de commande à distance, pas de fidélisation.
- **Le vendeur mérite d'être distingué** : un vendeur sérieux, avec une boutique vérifiée, une photo de façade et un catalogue à jour doit être mis en avant par rapport à un vendeur incomplet.
- **L'écosystème Mantota repose sur la réputation** : le Store Score récompense les bons comportements et signale les risques sans pénaliser publiquement.
- **La confiance se construit avec des faits, pas des promesses** : GPS vérifié, photo réelle, commandes honorées, clients satisfaits — ce sont des éléments mesurables, pas des avis subjectifs.

---

## 2. Types de boutiques

Mantota distingue trois types de boutiques. Le type détermine les exigences (photo, GPS, rayon de livraison) et les fonctionnalités disponibles.

### 2.1 Boutique physique

- **Définition** : Le vendeur possède un point de vente physique (magasin, étalage, kiosque, boutique de quartier).
- **Exigences** :
  - Localisation GPS obligatoire.
  - Photo de façade obligatoire.
  - Description du lieu recommandée.
  - Rayon de livraison configurable (retrait sur place minimum).
- **Cas d'usage** : Commerçant de quartier, pharmacie, boutique de téléphonie, magasin de vêtements.
- **Avantage Mantota** : Apparaît dans la recherche géographique « près de moi ». Retrait sur place disponible.

### 2.2 Boutique en ligne

- **Définition** : Le vendeur vend uniquement en ligne, sans point de vente physique. Stockage chez le vendeur ou en dropshipping.
- **Exigences** :
  - Localisation GPS non obligatoire (ville/pays de référence requis).
  - Photo de façade non obligatoire.
  - Rayon de livraison obligatoire (ville, pays, ou international).
- **Cas d'usage** : Vendeur e-commerce, dropshipping, artisan qui vend à distance.
- **Avantage Mantota** : Apparaît dans la recherche par ville/pays. Pas de retrait sur place.

### 2.3 Boutique physique + en ligne (hybride)

- **Définition** : Le vendeur possède une boutique physique ET vend aussi en ligne. C'est le cas le plus fréquent en Afrique francophone.
- **Exigences** :
  - Localisation GPS obligatoire.
  - Photo de façade obligatoire.
  - Description du lieu recommandée.
  - Rayon de livraison configurable (retrait sur place + livraison).
- **Cas d'usage** : Boutique de téléphonie qui vend en boutique et sur WhatsApp, magasin de vêtements avec livraison à domicile.
- **Avantage Mantota** : Apparaît dans la recherche géographique ET par ville/pays. Retrait sur place + livraison disponibles. Store Score maximal si toutes les informations sont complètes.

---

## 3. Enregistrement de la localisation

### Principe fondamental

> **Le vendeur ne saisit jamais latitude ni longitude.** La position est captée automatiquement via le GPS de l'appareil.

### 3.1 Parcours d'enregistrement (conversation Tracy)

1. **Tracy demande** : « Tu es dans ta boutique actuellement ? »
2. **Le vendeur répond oui** :
   - Tracy lance automatiquement la demande de permission GPS (via l'APK Mantota).
   - L'appareil capture la position (latitude, longitude, précision en mètres).
   - Tracy confirme : « C'est noté ! Ta boutique est localisée. Je l'ai enregistrée sur la carte. »
3. **Le vendeur répond non** :
   - Tracy propose : « Pas de souci. Tu peux activer la localisation quand tu y seras. Tu peux aussi saisir l'adresse manuellement pour commencer. »
   - Le vendeur peut saisir une adresse textuelle (ville, quartier, rue) en attendant.
   - Dès qu'il est dans la boutique, il active le GPS et la position est mise à jour.

### 3.2 Données enregistrées

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `latitude` | float | Oui (boutique physique) | Latitude GPS en degrés décimaux. |
| `longitude` | float | Oui (boutique physique) | Longitude GPS en degrés décimaux. |
| `accuracy` | float | Non | Précision du GPS en mètres (indicateur de qualité). |
| `city` | string | Oui | Ville déduite ou saisie. |
| `district` | string | Non | Quartier / arrondissement. |
| `address_text` | string | Non | Adresse textuelle libre (rue, repère). |
| `location_verified` | bool | Auto | `true` si le GPS a été utilisé. `false` si saisie manuelle. |
| `location_updated_at` | datetime | Auto | Date de dernière mise à jour de la position. |

### 3.3 Mise à jour de la position

- Le vendeur peut mettre à jour sa position à tout moment via Tracy : « Mets à jour ma localisation ».
- Tracy relance le GPS et remplace l'ancienne position.
- L'horodatage (`location_updated_at`) est mis à jour.
- L'ancienne position est conservée dans l'historique (audit) mais n'est plus utilisée.

### 3.4 Cas particuliers

- **GPS indisponible** : Tracy propose la saisie manuelle de l'adresse. La position sera vérifiée plus tard.
- **Vendeur déménage** : Mise à jour de la position + nouvelle photo de façade recommandée.
- **Boutique en ligne uniquement** : Pas de GPS requis. Ville/pays de référence saisis manuellement.

---

## 4. Photo de façade

### Principe

> **La photo de façade est obligatoire pour les boutiques physiques.** Elle est facultative pour les boutiques en ligne.

### 4.1 Objectifs

1. **Rassurer les clients** : Le client voit à quoi ressemble la boutique avant de s'y déplacer. Une boutique avec une photo de façade inspire plus de confiance qu'une boutique sans photo.
2. **Aider les livreurs** : Le livreur peut visualiser la boutique pour la retrouver plus facilement, surtout dans les quartiers sans adresse précise.
3. **Vérifier la boutique** : Mantota peut (futur) utiliser la photo pour vérifier que la boutique existe réellement à l'adresse déclarée.

### 4.2 Spécifications

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `facade_photo_url` | string (URL) | Oui (boutique physique) | URL de la photo de façade stockée par Mantota. |
| `facade_photo_uploaded_at` | datetime | Auto | Date d'upload de la photo. |
| `facade_photo_verified` | bool | Auto | `false` par défaut. `true` si vérifiée par Mantota (futur). |

### 4.3 Règles

- Une seule photo en V2. Plusieurs photos prévues en V3 (façade, intérieur, comptoir, stock).
- La photo doit montrer l'entrée / la devanture de la boutique.
- Taille maximale : 5 Mo. Format : JPG, PNG, WebP.
- Mantota stocke la photo et sert l'URL au client via l'API.
- La photo est visible par les clients dans la fiche boutique.

### 4.4 Parcours (conversation Tracy)

1. **Tracy demande** : « Tu peux prendre une photo de la façade de ta boutique ? Ça aide les clients à te trouver. »
2. **Le vendeur envoie la photo** : Tracy la transmet à Mantota, qui la stocke et renvoie l'URL.
3. **Tracy confirme** : « Parfait ! Ta photo est en ligne. Les clients peuvent voir ta boutique. »

---

## 5. Description du lieu

### Principe

> **Un champ libre permet au vendeur de décrire l'emplacement de sa boutique avec ses propres mots.** Cette description complète le GPS et la photo de façade.

### 5.1 Objectifs

- **Aider le client à retrouver la boutique** quand le GPS n'est pas suffisant (quartiers sans rue nommée, marchés, centres commerciaux).
- **Donner des repères locaux** compréhensibles par les clients du quartier.
- **Compléter la photo de façade** avec des détails visuels ou contextuels.

### 5.2 Spécifications

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `place_description` | string (max 500) | Non (recommandé) | Description libre du lieu. |

### 5.3 Exemples

- « En face du marché Sandaga, à côté de la pharmacie. »
- « Immeuble bleu, 2e étage, porte gauche. »
- « Boutique 12, allée centrale du centre commercial. »
- « Sur la route principale, après la station Total, 100 m à droite. »
- « Derrière la mosquée, dans la ruelle des tailleurs. »

### 5.4 Affichage

- La description est affichée dans la fiche boutique, sous la photo de façade.
- Elle est visible par les clients et les livreurs.
- Elle est facultative mais **fortement recommandée** pour les boutiques physiques (impact sur le Store Score).

---

## 6. Référentiel géographique

### Principe

> **Le référentiel géographique est une hiérarchie de noms et d'identifiants (pas de polygones GPS).** Elle permet de normaliser les noms de lieux saisis par les vendeurs et clients, et de résoudre les requêtes géographiques en langage naturel.

### 6.1 Hiérarchie

La hiérarchie du référentiel est la suivante :

| Niveau | Exemple (Bénin) | Description |
|---|---|---|
| **Département** | Littoral, Atlantique, Ouémé | Première subdivision administrative. |
| **Commune (Ville)** | Cotonou, Abomey-Calavi, Porto-Novo | Subdivision du département. Correspond à une ville ou agglomération. |
| **Arrondissement** | Ganhi, Akpakpa, Ouando | Subdivision de la commune. Peut correspondre à un quartier ou un groupe de quartiers. |
| **Quartier** | Dantokpa, Fidjrossè, Ganhi | Niveau le plus fin. Unité de base pour la livraison. |

### 6.2 Extensibilité

- Le référentiel est initialisé pour le Bénin (données seedées en base).
- L'extension à d'autres pays se fait via le Country Registry existant (`countries` table) : chaque pays peut avoir sa propre hiérarchie de communes et quartiers.
- La structure des tables (`villes`, `quartiers`) est générique et supporte n'importe quel pays via `country_id`.

### 6.3 Pas de polygones GPS

- Le référentiel stocke uniquement des **noms et identifiants** (hiérarchie nominale).
- Aucune colonne géométrique (pas de PostGIS, pas de polygone) à ce stade.
- Le géofencing par polygone GPS reste en **V3** (voir section 12 — Roadmap).
- La recherche de proximité GPS (boutiques « près de moi ») utilise les coordonnées GPS de la boutique et du client, pas le référentiel — cela reste inchangé.

### 6.4 Utilisation

Le référentiel est utilisé par :
- **Le rayon de livraison** (section 7) : la liste `delivery_quartiers` référence des quartiers du référentiel.
- **La recherche géographique** (section 8) : la requête « tu livres à X ? » résout X dans le référentiel avant de vérifier la couverture du vendeur.
- **L'interface admin/vendeur** : sélection de quartiers par ville, recherche et filtrage.

---

## 7. Rayon de livraison

### Principe

> **Chaque boutique définit son rayon de livraison.** Cela détermine où elle accepte de livrer et apparaît dans les résultats de recherche géographique.

### 7.1 Options disponibles

| Option | Description | Cas d'usage |
|---|---|---|
| **Retrait uniquement** | Le client vient chercher le produit en boutique. Pas de livraison. | Boutique de quartier, client proche, produit encombrant. |
| **Quartiers** | Livraison dans une liste de quartiers précis desservis (pas seulement le quartier de la boutique). | Commerçant de quartier, livraison à pied ou moto. |
| **Ville (raccourci)** | Pré-coche tous les quartiers de la ville — reste éditable quartier par quartier ensuite. La donnée de vérité stockée est toujours la liste de quartiers, jamais la ville seule. | Boutique urbaine avec livreur(s). |
| **Plusieurs villes** | Livraison dans plusieurs villes spécifiées. | Vendeur avec réseau de livreurs ou transporteur. |
| **Tout le pays** | Livraison partout dans le pays. | Vendeur avec transporteur national, poste. |
| **International** | Livraison dans d'autres pays. | Vendeur export, dropshipping international. |

### 7.2 Expédition partout

Certains vendeurs peuvent expédier partout (tout le pays + international). Cette option est disponible pour :
- Les boutiques en ligne.
- Les boutiques hybrides avec capacité d'expédition.
- Les vendeurs partenaires de services logistiques (DHL, postes nationales, transporteurs privés).

### 7.3 Spécifications

| Champ | Type | Description |
|---|---|---|
| `delivery_mode` | enum | `pickup_only`, `quartiers`, `multi_city`, `national`, `international` |
| `delivery_quartiers` | list[int] | Requis si `quartiers`. IDs des quartiers desservis (référence le référentiel géographique, section 6). |
| `delivery_cities` | list[string] | Requis si `multi_city`. Liste des villes desservies (résolues en quartiers via le référentiel). |
| `delivery_countries` | list[string] | Requis si `international`. Liste des pays desservis. |
| `pickup_available` | bool | `true` si le retrait sur place est disponible. |

### 7.4 Impact sur la recherche

- Un client qui cherche « près de moi » ne verra que les boutiques dont le rayon couvre sa position.
- Un client qui cherche par ville ne verra que les boutiques qui livrent dans au moins un quartier de cette ville.
- Le retrait sur place est toujours proposé si la boutique est physique et `pickup_available = true`.

---

## 8. Recherche géographique

### Principe

> **Le client peut rechercher des boutiques par proximité géographique, par ville, ou par type de produit + localisation.**
>
> **Résolution géographique** : quand un client demande « tu livres à [ville/quartier X] ? », Tracy résout d'abord X dans le référentiel géographique (section 6) pour connaître son quartier/ville canonique, puis vérifie si ce quartier est dans la liste `delivery_quartiers` du vendeur. La résolution est insensible à la casse et aux accents.

### 8.1 Parcours client

#### Recherche par GPS (« près de moi »)

1. Le client envoie : « Je cherche une pharmacie près de moi. »
2. Tracy demande la permission GPS (via l'APK Mantota).
3. L'appareil capture la position du client.
4. Mantota renvoie les boutiques les plus proches, triées par distance, dans le rayon de livraison du vendeur.
5. Tracy présente les résultats : « J'ai trouvé 3 pharmacies à moins de 2 km de toi. La plus proche est Pharmacie du Marché, à 500 m. »

#### Recherche par ville

1. Le client envoie : « Je cherche des vêtements à Dakar. »
2. Mantota renvoie les boutiques de vêtements à Dakar, triées par Store Score puis par distance.
3. Tracy présente les résultats.

#### Recherche avec filtre « retrait sur place »

1. Le client envoie : « Je veux retirer un téléphone en boutique. »
2. Mantota filtre les boutiques avec `pickup_available = true` et proches du client.
3. Tracy présente les résultats avec l'adresse et la photo de façade.

#### Recherche avec filtre « boutiques vérifiées »

1. Le client envoie : « Je cherche uniquement des boutiques vérifiées. »
2. Mantota filtre les boutiques avec un Store Score élevé (badges de confiance).
3. Tracy présente les résultats avec les badges affichés.

### 8.2 Types de recherche supportés

| Recherche | Exemple | Source de position | Filtre |
|---|---|---|---|
| Produit + proximité | « téléphone près de moi » | GPS client | Catégorie produit + distance |
| Boutique + proximité | « pharmacie proche » | GPS client | Type de boutique + distance |
| Produit + ville | « vêtements à Dakar » | Ville saisie | Catégorie produit + ville |
| Retrait sur place | « retirer en boutique » | GPS client | `pickup_available = true` |
| Boutiques vérifiées | « boutiques vérifiées près de moi » | GPS client | Store Score élevé |
| Livraison par quartier | « tu livres à Ganhi ? » | Quartier saisi | Résolution référentiel + `delivery_quartiers` |
| Livraison par ville | « tu livres à Cotonou ? » | Ville saisie | Résolution référentiel + quartiers de la ville |
| Boutiques par catégorie | « électronique à Thiès » | Ville saisie | Catégorie + ville |

### 8.3 Tri des résultats

1. **Distance** (si GPS client disponible) — du plus proche au plus lointain.
2. **Store Score** — en cas d'égalité de distance, la boutique avec le meilleur score apparaît en premier.
3. **Disponibilité** — les boutiques avec des produits en stock apparaissent avant les boutiques sans stock.

### 8.4 Affichage des résultats

Chaque résultat affiche :
- Nom de la boutique
- Photo de façade (si disponible)
- Distance (si GPS client disponible)
- Badges de confiance (vérifié, photo, GPS)
- Description du lieu (si disponible)
- Rayon de livraison
- Disponibilité retrait sur place

---

## 9. Dashboard Mantota

### Principe

> **Le Dashboard Mantota offre une vue d'ensemble de la couverture géographique et de l'activité des boutiques.**

### 9.1 Carte des boutiques

- Carte interactive affichant toutes les boutiques enregistrées.
- Filtres : par ville, par catégorie, par type (physique / en ligne / hybride), par Store Score.
- Chaque point représente une boutique. La couleur indique le type ou le score.
- Cliquer sur un point affiche la fiche boutique (nom, photo, adresse, score, catégorie).

### 9.2 Statistiques par ville

- Nombre de boutiques par ville.
- Nombre de boutiques actives (commandes récentes) par ville.
- Nombre de boutiques vérifiées par ville.
- Évolution mensuelle (nouvelles boutiques, boutiques inactives).

### 9.3 Statistiques par catégorie

- Nombre de boutiques par catégorie de produits.
- Répartition géographique par catégorie (ex : 80% des pharmacies à Dakar, 20% en banlieue).
- Catégories sous-représentées (opportunités).

### 9.4 Zones non couvertes

- Identification des villes / quartiers sans boutique.
- Identification des catégories manquantes par zone (ex : pas de pharmacie dans tel quartier).
- Recommandations d'expansion (où ouvrir une boutique aurait le plus d'impact).

### 9.5 Boutiques actives

- Liste des boutiques actives (commandes dans les 30 derniers jours).
- Liste des boutiques inactives (alerte : relancer le vendeur).
- Taux d'activité par ville et par catégorie.
- Boutiques récemment enregistrées (nouvelles inscriptions).

---

## 10. Store Score

### Principe

> **Le Store Score est un score interne calculé par Mantota. Le client ne voit jamais le score numérique — il voit uniquement des badges.**

### 10.1 Critères du Store Score

| Critère | Description | Poids indicatif |
|---|---|---|
| **GPS vérifié** | La position GPS a été captée via l'appareil (pas de saisie manuelle). | Élevé |
| **Photo de façade** | Une photo de façade est uploadée et visible. | Élevé |
| **Boutique vérifiée** | Mantota a vérifié l'existence de la boutique (futur : vérification documentaire ou terrain). | Très élevé |
| **Informations complètes** | Nom, description, catégorie, horaires, contact, rayon de livraison — tous renseignés. | Moyen |
| **Catalogue à jour** | Le catalogue est maintenu à jour (produits, prix, stock). Pénalité si produits indisponibles depuis longtemps. | Moyen |
| **Respect des engagements** | Taux de commandes honorées vs annulées. Pénalité si annulations fréquentes sans raison valide. | Très élevé |
| **Satisfaction client** | Taux de clients satisfaits (évaluations implicites : retour, re-commande, pas de réclamation). | Élevé |
| **Ancienneté** | Durée d'inscription sur Mantota. Plus la boutique est ancienne, plus le score augmente. | Faible |
| **Produits disponibles** | Nombre de produits disponibles en stock. Pénalité si catalogue vide ou tout en rupture. | Moyen |
| **Participation à l'écosystème Mantota** | Utilisation active de Tracy, campagnes, paiements via Moneroo, abonnement actif. | Moyen |

### 10.2 Badges visibles par le client

Le client ne voit jamais le score numérique. Il voit des badges :

| Badge | Condition d'affichage |
|---|---|
| ✅ **Boutique vérifiée** | `boutique_verifiée = true` (vérification Mantota). |
| 📍 **Localisation vérifiée** | `location_verified = true` (GPS capté). |
| 📸 **Photo de façade** | `facade_photo_url` est présent. |
| ⭐ **Boutique de confiance** | Store Score élevé (respect des engagements + satisfaction client). |
| 🏪 **Boutique physique** | Type = physique ou hybride. |
| 🚚 **Livraison disponible** | `delivery_mode` ≠ `pickup_only`. |
| 🎯 **Retrait sur place** | `pickup_available = true`. |

### 10.3 Comment Mantota aide les vendeurs à respecter leurs engagements

Mantota ne se contente pas de noter — il **aide activement** le vendeur à maintenir un bon score :

- **Rappels de commande** : Tracy rappelle au vendeur les commandes en attente de traitement ou d'expédition.
- **Suivi des commandes** : Mantota suit le statut de chaque commande et alerte le vendeur si un délai est dépassé.
- **Alertes de stock** : Mantota signale les produits en rupture et propose de mettre à jour le catalogue.
- **Notifications d'échéance** : Pour les paiements échelonnés (contrats), Mantota rappelle au client les échéances à venir.
- **Relances automatiques** : Tracy peut relancer un vendeur inactif (« Tu n'as pas traité la commande #123 depuis 2 jours. Tout va bien ? »).
- **Tableau de bord vendeur** : Le vendeur voit son Store Score (lui seul) et les axes d'amélioration (« Ajoute une photo de façade pour augmenter ta confiance »).
- **Formation continue** : Tracy peut conseiller le vendeur sur les bonnes pratiques (« Mets à jour ton catalogue chaque semaine pour garder ton badge »).

### 10.4 Calcul du score

- Le score est calculé périodiquement (quotidiennement ou à chaque événement significatif).
- Le score est compris entre 0 et 100.
- Un score en dessous d'un seuil minimal déclenche des alertes internes Mantota (pas de pénalité publique).
- Un score élevé déclenche des avantages : mise en avant dans les recherches, badges affichés, priorité dans les recommandations.

### 10.5 Transparence

- Le vendeur voit son propre score et le détail des critères dans son tableau de bord.
- Le client ne voit jamais le score — uniquement les badges.
- Mantota ne publie jamais de classement public des boutiques par score.
- Un vendeur peut demander à Mantota pourquoi son score a baissé (futur : explication détaillée par critère).

---

## 11. Intégration avec Tracy

### Principe

> **Tracy est l'interface principale entre le vendeur/client et le module Store Location & Trust.** Toutes les interactions se font par conversation naturelle.

### 11.1 Conversations vendeur

| Message du vendeur | Action de Tracy |
|---|---|
| « Je suis dans ma boutique. » | Lance le GPS, enregistre la position, confirme. |
| « Mets à jour ma localisation. » | Relance le GPS, remplace l'ancienne position. |
| « Je veux ajouter une photo de ma boutique. » | Demande la photo, l'envoie à Mantota, confirme. |
| « Je livre dans toute la ville. » | Pré-coche tous les quartiers de la ville dans `delivery_quartiers` (raccourci de saisie). |
| « Je veux expédier partout. » | Met à jour le rayon de livraison (`national` ou `international`). |
| « Mon score a baissé ? » | Explique les critères et propose des actions pour améliorer. |
| « Comment je peux avoir le badge boutique vérifiée ? » | Explique le processus de vérification. |
| « Je déménage ma boutique. » | Lance la mise à jour GPS + propose de changer la photo de façade. |
| « Active ma localisation. » | Lance le GPS et enregistre la position. |
| « Je veux mettre à jour ma boutique. » | Propose un menu : localisation, photo, description, rayon, horaires. |

### 11.2 Conversations client

| Message du client | Action de Tracy |
|---|---|
| « Je cherche une boutique près de moi. » | Lance le GPS du client, recherche les boutiques proches. |
| « Pharmacie proche. » | Filtre par catégorie + proximité GPS. |
| « Vêtements à Dakar. » | Filtre par catégorie + ville. |
| « Je cherche uniquement des boutiques vérifiées. » | Filtre par Store Score élevé + badges. |
| « Je veux retirer en boutique. » | Filtre `pickup_available = true` + proximité. |
| « Boutique téléphone près de moi. » | Filtre par catégorie produit + proximité GPS. |
| « Qu'est-ce qu'il y a autour de moi ? » | Recherche toutes catégories + proximité GPS. |
| « Livraison à Pikine ? » | Filtre par ville de livraison + boutiques qui couvrent Pikine. |

### 11.3 Flux de conversation type — Enregistrement boutique

```
Vendeur : Bonjour Tracy, je veux enregistrer ma boutique.
Tracy : Super ! Tu es dans ta boutique actuellement ?
Vendeur : Oui.
Tracy : Parfait, je lance la localisation. [...] C'est noté ! Ta boutique est à Dakar, Plateau. Je l'ai mise sur la carte.
Tracy : Tu peux prendre une photo de la façade ? Ça aide les clients à te trouver.
Vendeur : [envoie la photo]
Tracy : Nickel ! Ta photo est en ligne. Les clients peuvent voir ta boutique.
Tracy : Tu livres dans quel rayon ? Quartier, ville, ou plus ?
Vendeur : Je livre dans toute Dakar.
Tracy : C'est enregistré. Tu proposes aussi le retrait sur place ?
Vendeur : Oui.
Tracy : Parfait. Ta boutique est presque complète. Tu veux ajouter une description du lieu pour aider les clients à te trouver ?
Vendeur : En face du marché Sandaga, à côté de la pharmacie.
Tracy : C'est noté. Ta boutique est maintenant visible par les clients qui cherchent près de chez eux. Bienvenue sur Mantota !
```

### 11.4 Flux de conversation type — Recherche client

```
Client : Je cherche une pharmacie près de moi.
Tracy : J'active ta localisation. [...] Tu es à Dakar, Médina. J'ai trouvé 2 pharmacies à moins de 1 km.
Tracy : La plus proche c'est Pharmacie du Marché, à 300 m. Boutique vérifiée, retrait sur place disponible. Tu veux y aller ?
Client : Oui, ils ont du paracétamol ?
Tracy : Je vérifie leur catalogue. [...] Oui, paracétamol 500 mg disponible, 500 FCFA. Tu veux que je leur envoie ta commande ?
```

---

## 12. Roadmap

### V1 — Documentation uniquement

- Spécification fonctionnelle complète (ce document).
- Aucun code, aucune API, aucune base de données.
- Le document sert de référence pour le développement futur.

### V2 — Développement

- Implémentation du module dans Mantota.
- Enregistrement de la localisation via GPS (APK Mantota).
- Upload de photo de façade.
- Description du lieu.
- Rayon de livraison configurable.
- Recherche géographique (par GPS et par ville).
- Store Score V1 (critères de base : GPS, photo, informations, catalogue).
- Badges de confiance affichés au client.
- Dashboard Mantota (carte, statistiques de base).
- Intégration avec Tracy (conversations vendeur et client).

### V3 — Optimisations

- Analyse géographique avancée : zones non couvertes, recommandations d'expansion, heatmaps.
- Recommandations locales : « Tu es à Dakar, voici les boutiques recommandées dans ton quartier. »
- Multi-photos : façade, intérieur, comptoir, stock.
- Vérification terrain de la boutique (agent Mantota ou partenaire).
- Store Score V2 : critères avancés (satisfaction client détaillée, participation écosystème).
- Optimisation des livraisons : calcul d'itinéraire, estimation de temps.
- Géofencing : alertes quand un client entre dans le rayon d'une boutique.
- Statistiques avancées : conversion par zone, panier moyen par ville, saisonnalité.
- API publique de recherche géographique (pour partenaires externes).
