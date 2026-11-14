# Création de Boutique — Parcours Conversationnel

> **Statut** : Documentation fonctionnelle. Aucun code, aucune API, aucune base de données.
> **Objectif** : Documenter le parcours complet de création d'une boutique via conversation avec Tracy.

---

## Sommaire

1. [Principe](#1-principe)
2. [Étape 1 — Type de boutique](#2-étape-1--type-de-boutique)
3. [Parcours Boutique physique](#3-parcours-boutique-physique)
4. [Parcours Boutique en ligne](#4-parcours-boutique-en-ligne)
5. [Parcours Boutique physique + en ligne](#5-parcours-boutique-physique--en-ligne)
6. [Résumé et confirmation](#6-résumé-et-confirmation)
7. [Modifications ultérieures via Tracy](#7-modifications-ultérieures-via-tracy)

---

## 1. Principe

La création d'une boutique se fait **entièrement par conversation avec Tracy**. Le vendeur n'utilise pas de formulaire — il discute avec Tracy, qui le guide étape par étape.

Tracy pose les questions une par une, dans un ordre logique, et confirme chaque étape avant de passer à la suivante. Le vendeur peut interrompre le parcours à tout moment et reprendre plus tard.

**Règle fondamentale** : le vendeur ne saisit jamais de données techniques (latitude, longitude). Tout ce qui est technique est géré automatiquement par Tracy et l'APK Mantota.

---

## 2. Étape 1 — Type de boutique

Tracy démarre la conversation et demande au vendeur quel type de boutique il souhaite créer.

### Conversation

```
Tracy : Salut ! Tu veux créer ta boutique sur Mantota ? Quel type de boutique souhaites-tu créer ?

  ○ Boutique physique
  ○ Boutique en ligne
  ○ Boutique physique + en ligne
```

### Définitions affichées (si le vendeur demande)

- **Boutique physique** : Tu as un point de vente (magasin, kiosque, étalage). Les clients peuvent venir sur place.
- **Boutique en ligne** : Tu vends uniquement en ligne. Pas de point de vente physique.
- **Boutique physique + en ligne** : Tu as une boutique physique ET tu vends aussi en ligne. C'est le cas le plus fréquent.

### Routage

| Choix du vendeur | Parcours |
|---|---|
| Boutique physique | [Parcours Boutique physique](#3-parcours-boutique-physique) |
| Boutique en ligne | [Parcours Boutique en ligne](#4-parcours-boutique-en-ligne) |
| Boutique physique + en ligne | [Parcours hybride](#5-parcours-boutique-physique--en-ligne) |

---

## 3. Parcours Boutique physique

### 3.1 Nom de la boutique

```
Tracy : Comment s'appelle ta boutique ?
Vendeur : Pharmacie du Marché.
Tracy : Parfait, « Pharmacie du Marché ». C'est noté.
```

### 3.2 Localisation — Es-tu dans ta boutique ?

```
Tracy : Tu es dans ta boutique actuellement ?
```

#### Si OUI

1. Tracy demande l'autorisation d'accéder à la localisation :

```
Tracy : Je vais activer ta localisation pour enregistrer la position de ta boutique. Tu autorises ?
Vendeur : Oui.
```

2. Le GPS de l'appareil est activé automatiquement (via l'APK Mantota).

3. La position est captée (latitude, longitude, précision).

4. Tracy confirme :

```
Tracy : C'est noté ! Ta boutique est localisée à Dakar, Plateau. Je l'ai mise sur la carte.
```

> **Le vendeur ne saisit jamais latitude ni longitude.** La position est captée automatiquement.

#### Si NON

```
Tracy : Pas de souci. Tu peux activer la localisation quand tu seras dans ta boutique. Pour commencer, dis-moi juste la ville et le quartier.
Vendeur : Dakar, Médina.
Tracy : C'est noté. Tu pourras activer le GPS plus tard en m'envoyant « Active ma localisation ».
```

La position GPS sera captée ultérieurement. En attendant, la ville et le quartier sont enregistrés manuellement.

### 3.3 Photo de façade

```
Tracy : Maintenant, prends une photo de la façade de ta boutique. Cette photo est obligatoire — elle aide les clients à te trouver et à te faire confiance.
```

#### Objectifs de la photo

- **Rassurer les clients** : le client voit la boutique avant de s'y déplacer.
- **Aider les livreurs** : le livreur visualise la boutique pour la retrouver.
- **Vérifier la boutique** : Mantota peut vérifier que la boutique existe à l'adresse déclarée.

#### Règles

- Une seule photo en V2. Plusieurs photos prévues en V3 (façade, intérieur, comptoir).
- La photo doit montrer l'entrée / la devanture de la boutique.
- Taille maximale : 5 Mo. Formats : JPG, PNG, WebP.

#### Conversation

```
Vendeur : [envoie la photo]
Tracy : Nickel ! Ta photo est en ligne. Les clients peuvent voir ta boutique.
```

#### Si le vendeur refuse ou n'a pas de photo

```
Vendeur : Je n'ai pas de photo maintenant.
Tracy : Pas de problème, mais la photo est obligatoire pour les boutiques physiques. Tu peux me l'envoyer dès que tu l'as. Sans elle, ta boutique ne sera pas visible dans les résultats de recherche. Tu veux continuer et l'ajouter plus tard ?
Vendeur : Oui.
Tracy : D'accord. Pense à l'ajouter vite pour que ta boutique apparaisse dans les recherches.
```

La boutique est créée mais **non visible** dans les recherches tant que la photo n'est pas ajoutée.

### 3.4 Description du lieu

```
Tracy : Décris simplement comment retrouver ta boutique. Ça complète la photo et le GPS.
```

#### Exemples

- « En face du marché. »
- « Immeuble bleu, 2e étage. »
- « Boutique N°15, allée centrale. »
- « Près de la pharmacie, dans la ruelle des tailleurs. »
- « Sur la route principale, après la station Total, 100 m à droite. »

#### Conversation

```
Vendeur : En face du marché Sandaga, à côté de la pharmacie.
Tracy : C'est noté. Les clients et les livreurs verront cette description.
```

#### Règles

- Champ libre, maximum 500 caractères.
- Facultatif mais **fortement recommandé** (impact sur le Store Score).
- Affiché dans la fiche boutique, sous la photo de façade.

### 3.5 Horaires d'ouverture

```
Tracy : Quels sont tes horaires d'ouverture ?
```

#### Option 1 — Tous les jours

```
Tracy : Tu ouvres tous les jours ?
Vendeur : Oui.
Tracy : De quelle heure à quelle heure ?
Vendeur : 8h à 20h.
Tracy : C'est noté. Tu ouvres tous les jours de 8h à 20h.
```

#### Option 2 — Personnalisés

```
Tracy : Tu ouvres tous les jours ?
Vendeur : Non, pas tous les jours.
Tracy : Pas de souci. Dis-moi tes horaires jour par jour.
Vendeur : Lundi à samedi, 8h à 19h. Dimanche fermé.
Tracy : C'est noté. Lundi à samedi 8h-19h, dimanche fermé.
```

#### Données enregistrées

| Jour | Ouverture | Fermeture | Fermé |
|---|---|---|---|
| Lundi | 08:00 | 19:00 | non |
| Mardi | 08:00 | 19:00 | non |
| Mercredi | 08:00 | 19:00 | non |
| Jeudi | 08:00 | 19:00 | non |
| Vendredi | 08:00 | 19:00 | non |
| Samedi | 08:00 | 19:00 | non |
| Dimanche | — | — | oui |

### 3.6 Rayon de livraison

```
Tracy : Où peux-tu livrer ? Tu peux choisir plusieurs options.
```

#### Choix proposés

```
  ○ Retrait sur place
  ○ Mon quartier
  ○ Toute ma ville
  ○ Plusieurs villes
  ○ Tout le pays
  ○ International
```

#### Règles

- Le vendeur **peut sélectionner plusieurs zones**.
- « Retrait sur place » est sélectionné par défaut pour une boutique physique.
- Si « Plusieurs villes » est sélectionné, Tracy demande la liste des villes.
- Si « International » est sélectionné, Tracy demande la liste des pays.

#### Conversation

```
Vendeur : Retrait sur place et toute ma ville.
Tracy : C'est noté. Tu proposes le retrait sur place et la livraison dans toute ta ville (Dakar). Tu veux ajouter d'autres zones ?
Vendeur : Non, c'est bon.
Tracy : Parfait.
```

#### Conversation avec plusieurs villes

```
Vendeur : Retrait sur place et plusieurs villes.
Tracy : Super. Quelles villes ?
Vendeur : Dakar, Thiès, Saint-Louis.
Tracy : C'est noté. Tu livres à Dakar, Thiès et Saint-Louis, plus le retrait sur place.
```

### 3.7 Numéro de téléphone

```
Tracy : Quel numéro de téléphone tu utilises pour ta boutique ?
Vendeur : +221 77 123 45 67.
Tracy : C'est noté. Les clients pourront t'appeler ou te contacter sur WhatsApp.
```

### 3.8 Catégorie de boutique

```
Tracy : Qu'est-ce que tu vends ? Choisis une catégorie.
Vendeur : Pharmacie.
Tracy : C'est noté. Ta boutique est dans la catégorie « Pharmacie ».
```

### 3.9 Fin du parcours physique

Tracy passe à l'étape [Résumé et confirmation](#6-résumé-et-confirmation).

---

## 4. Parcours Boutique en ligne

### 4.1 Nom de la boutique

```
Tracy : Comment s'appelle ta boutique en ligne ?
Vendeur : TechShop SN.
Tracy : « TechShop SN », c'est noté.
```

### 4.2 Description

```
Tracy : Décris ta boutique en une ou deux phrases. Qu'est-ce que tu vends ?
Vendeur : On vend des téléphones et accessoires neufs et reconditionnés, livraison partout au Sénégal.
Tracy : C'est noté. Les clients verront cette description dans ta fiche boutique.
```

### 4.3 Logo

```
Tracy : Tu as un logo pour ta boutique ?
Vendeur : [envoie le logo]
Tracy : Parfait, ton logo est en ligne.
```

#### Si pas de logo

```
Vendeur : Je n'ai pas de logo.
Tracy : Pas grave. Tu peux l'ajouter plus tard. Un logo aide les clients à reconnaître ta boutique.
```

### 4.4 Photo de couverture

```
Tracy : Tu veux ajouter une photo de couverture ? C'est ce que les clients voient en premier sur ta fiche.
Vendeur : [envoie la photo]
Tracy : Nickel ! Ta couverture est en ligne.
```

#### Si pas de couverture

```
Vendeur : Pas maintenant.
Tracy : D'accord. Tu peux l'ajouter plus tard.
```

### 4.5 Numéro de téléphone

```
Tracy : Quel numéro de téléphone pour ta boutique ?
Vendeur : +221 77 123 45 67.
Tracy : C'est noté.
```

### 4.6 Pays

```
Tracy : Dans quel pays se trouve ta boutique ?
Vendeur : Sénégal.
Tracy : C'est noté. Ta boutique est au Sénégal.
```

### 4.7 Ville

```
Tracy : Dans quelle ville ?
Vendeur : Dakar.
Tracy : C'est noté. Ta boutique est à Dakar, Sénégal.
```

> **Note** : Pour une boutique en ligne, la ville/pays est une référence administrative, pas une localisation physique. Le GPS n'est pas demandé.

### 4.8 Zone de livraison

```
Tracy : Où peux-tu livrer ? Tu peux choisir plusieurs options.
```

#### Choix proposés

```
  ○ Mon quartier
  ○ Toute ma ville
  ○ Plusieurs villes
  ○ Tout le pays
  ○ International
```

> **Note** : « Retrait sur place » n'est pas proposé pour une boutique en ligne (pas de point de vente physique).

#### Conversation

```
Vendeur : Tout le pays et international.
Tracy : Super. Tu livres partout au Sénégal et à l'international. Quels pays ?
Vendeur : Côte d'Ivoire, Mali, Bénin.
Tracy : C'est noté. Tu livres au Sénégal, en Côte d'Ivoire, au Mali et au Bénin.
```

### 4.9 Catégorie de boutique

```
Tracy : Qu'est-ce que tu vends ? Choisis une catégorie.
Vendeur : Électronique.
Tracy : C'est noté. Ta boutique est dans la catégorie « Électronique ».
```

### 4.10 Fin du parcours en ligne

Tracy passe à l'étape [Résumé et confirmation](#6-résumé-et-confirmation).

---

## 5. Parcours Boutique physique + en ligne

### Principe

> Le parcours hybride **combine les étapes des deux parcours**. Tracy enchaîne les questions sans distinction — le vendeur ne sent pas qu'il y a deux parcours.

### 5.1 Enchaînement des étapes

| Étape | Source | Description |
|---|---|---|
| Nom de la boutique | Commun | Tracy demande le nom. |
| Localisation GPS | Boutique physique | « Tu es dans ta boutique ? » → GPS automatique. |
| Photo de façade | Boutique physique | Photo obligatoire. |
| Description du lieu | Boutique physique | Champ libre pour décrire l'emplacement. |
| Logo | Boutique en ligne | Logo de la boutique. |
| Photo de couverture | Boutique en ligne | Photo de couverture pour la fiche. |
| Horaires d'ouverture | Boutique physique | Tous les jours ou personnalisés. |
| Numéro de téléphone | Commun | Contact boutique. |
| Pays et ville | Boutique en ligne | Référence administrative. |
| Catégorie | Commun | Type de produits vendus. |
| Rayon de livraison | Commun | Retrait sur place + livraison (plusieurs zones possibles). |
| Description | Boutique en ligne | Description textuelle de la boutique. |

### 5.2 Conversation type (extrait)

```
Tracy : Super, une boutique physique et en ligne ! On commence. Comment s'appelle ta boutique ?
Vendeur : Boutique Téranga.
Tracy : « Boutique Téranga », c'est noté. Tu es dans ta boutique actuellement ?
Vendeur : Oui.
Tracy : J'active ta localisation. [...] C'est noté ! Tu es à Dakar, Plateau. Maintenant, prends une photo de la façade.
Vendeur : [envoie la photo]
Tracy : Nickel ! Décris comment retrouver ta boutique.
Vendeur : En face de la BICIS, rue 10.
Tracy : C'est noté. Tu as un logo ?
Vendeur : [envoie le logo]
Tracy : Parfait. Tes horaires d'ouverture ?
Vendeur : Lundi à samedi, 9h à 18h.
Tracy : C'est noté. Ton numéro de téléphone ?
Vendeur : +221 77 999 88 77.
Tracy : C'est noté. Où peux-tu livrer ?
Vendeur : Retrait sur place, toute la ville, et tout le pays.
Tracy : Super. Tu proposes le retrait sur place, la livraison à Dakar et partout au Sénégal. Tu veux ajouter l'international ?
Vendeur : Non.
Tracy : D'accord. Qu'est-ce que tu vends ?
Vendeur : Vêtements et accessoires.
Tracy : C'est noté, catégorie « Mode et vêtements ». Tu veux ajouter une description ?
Vendeur : Vêtements pour homme et femme, qualité import, livraison rapide.
Tracy : Parfait. Voici le résumé de ta boutique.
```

### 5.3 Fin du parcours hybride

Tracy passe à l'étape [Résumé et confirmation](#6-résumé-et-confirmation).

---

## 6. Résumé et confirmation

### Principe

> À la fin du parcours, Tracy affiche un **résumé complet** de toutes les informations saisies. Le vendeur **confirme** avant que la boutique ne soit créée.

### 6.1 Affichage du résumé

Tracy présente le résumé sous forme de texte conversationnel (pas de liste à puces — Tracy parle naturellement) :

#### Exemple — Boutique physique

```
Tracy : Voici le résumé de ta boutique. Dis-moi si tout est correct.

Nom : Pharmacie du Marché
Type : Boutique physique
Localisation : Dakar, Plateau (GPS vérifié)
Photo de façade : ✅
Description du lieu : En face du marché Sandaga, à côté de la pharmacie.
Horaires : Tous les jours, 8h à 20h
Téléphone : +221 77 123 45 67
Catégorie : Pharmacie
Livraison : Retrait sur place + toute la ville (Dakar)

Tout est bon ?
```

#### Exemple — Boutique en ligne

```
Tracy : Voici le résumé de ta boutique.

Nom : TechShop SN
Type : Boutique en ligne
Description : Téléphones et accessoires neufs et reconditionnés, livraison partout au Sénégal.
Logo : ✅
Couverture : ✅
Téléphone : +221 77 123 45 67
Pays : Sénégal
Ville : Dakar
Catégorie : Électronique
Livraison : Tout le pays + international (Côte d'Ivoire, Mali, Bénin)

Tout est bon ?
```

#### Exemple — Boutique hybride

```
Tracy : Voici le résumé de ta boutique.

Nom : Boutique Téranga
Type : Boutique physique + en ligne
Localisation : Dakar, Plateau (GPS vérifié)
Photo de façade : ✅
Description du lieu : En face de la BICIS, rue 10.
Logo : ✅
Horaires : Lundi à samedi, 9h à 18h. Dimanche fermé.
Téléphone : +221 77 999 88 77
Pays : Sénégal
Ville : Dakar
Catégorie : Mode et vêtements
Description : Vêtements pour homme et femme, qualité import, livraison rapide.
Livraison : Retrait sur place + toute la ville (Dakar) + tout le pays (Sénégal)

Tout est bon ?
```

### 6.2 Confirmation

#### Si le vendeur confirme

```
Vendeur : Oui, tout est bon.
Tracy : Ta boutique « Pharmacie du Marché » est créée ! Bienvenue sur Mantota. Les clients peuvent déjà te trouver. Tu veux ajouter des produits à ton catalogue maintenant ?
```

La boutique est **créée et active**.

#### Si le vendeur veut modifier

```
Vendeur : Non, mes horaires sont wrong.
Tracy : Pas de souci. Quels sont tes bons horaires ?
Vendeur : Lundi à vendredi, 9h à 18h. Samedi 9h à 13h. Dimanche fermé.
Tracy : C'est corrigé. Voici le résumé mis à jour. [...] Tout est bon maintenant ?
```

Tracy met à jour le résumé et redemande confirmation.

### 6.3 État de la boutique après création

| Élément | État |
|---|---|
| Boutique créée | ✅ |
| Visible dans les recherches | ✅ si photo de façade présente (boutique physique). ❌ si photo manquante. |
| Store Score initial | Calculé avec les informations disponibles. |
| Catalogue | Vide — Tracy propose d'ajouter des produits. |
| Badges | GPS vérifié ✅ (si GPS capté), Photo ✅ (si uploadée). |

---

## 7. Modifications ultérieures via Tracy

### Principe

> **Toutes les informations saisies lors de la création peuvent être modifiées plus tard directement depuis Tracy**, par simple conversation.

### 7.1 Commandes de modification

| Message du vendeur | Action de Tracy |
|---|---|
| « Mets à jour ma position. » | Relance le GPS, remplace l'ancienne position, confirme. |
| « Je change de boutique. » | Demande si c'est un déménagement (nouveau GPS + nouvelle photo) ou un nouveau type. |
| « Modifie mes horaires. » | Demande les nouveaux horaires (tous les jours ou personnalisés). |
| « Ajoute une nouvelle photo. » | Demande la photo, l'envoie à Mantota, confirme. |
| « Je livre maintenant dans tout le Bénin. » | Met à jour le rayon de livraison (ajoute le Bénin si international, ou passe en international). |
| « Change ma description. » | Demande la nouvelle description, remplace l'ancienne. |
| « Je veux changer mon logo. » | Demande le nouveau logo, remplace l'ancien. |
| « Mon numéro a changé. » | Demande le nouveau numéro, remplace l'ancien. |
| « Je veux ajouter l'international. » | Demande les pays, met à jour le rayon de livraison. |
| « Je ne livre plus le dimanche. » | Met à jour les horaires ou le rayon selon le contexte. |
| « Désactive le retrait sur place. » | Met à jour `pickup_available = false`. |
| « Active le retrait sur place. » | Met à jour `pickup_available = true`. |
| « Je veux changer de catégorie. » | Demande la nouvelle catégorie, met à jour. |
| « Supprime ma photo. » | Supprime la photo de façade. Avertit que la boutique ne sera plus visible dans les recherches (boutique physique). |

### 7.2 Conversation type — Mise à jour position

```
Vendeur : Mets à jour ma position.
Tracy : Tu es dans ta boutique actuellement ?
Vendeur : Oui.
Tracy : J'active la localisation. [...] C'est mis à jour ! Ta boutique est maintenant localisée à Dakar, Médina. L'ancienne position a été remplacée.
```

### 7.3 Conversation type — Changement de rayon

```
Vendeur : Je livre maintenant dans tout le Bénin.
Tracy : Super ! Tu veux dire que tu ajoutes le Bénin à tes zones de livraison, ou tu remplaces tout ?
Vendeur : J'ajoute.
Tracy : C'est noté. Tu livres maintenant au Sénégal et au Bénin. Tu veux ajouter d'autres pays ?
Vendeur : Non.
Tracy : Parfait. Ta zone de livraison est mise à jour.
```

### 7.4 Conversation type — Déménagement

```
Vendeur : Je déménage ma boutique.
Tracy : D'accord. Tu déménages dans une nouvelle adresse ? Tu es déjà dans le nouveau local ?
Vendeur : Oui.
Tracy : J'active la localisation pour la nouvelle position. [...] C'est noté ! Ta boutique est maintenant à Dakar, Yoff. Tu veux prendre une nouvelle photo de façade ?
Vendeur : [envoie la nouvelle photo]
Tracy : Parfait ! Ta nouvelle photo est en ligne. Ta boutique est à jour.
```

### 7.5 Règles de modification

- Toute modification est **immédiate** — pas de validation Mantota pour les modifications de base (horaires, description, rayon).
- Les modifications sensibles (changement de pays, suppression de photo de façade) déclenchent un **avertissement** de Tracy sur l'impact (visibilité, Store Score).
- L'horodatage de chaque modification est enregistré (`location_updated_at`, `facade_photo_uploaded_at`, etc.).
- L'ancienne valeur est conservée dans l'historique d'audit Mantota.
- Le Store Score est **recalculé** après chaque modification.

---

## 8. Récapitulatif des parcours

### Boutique physique

| Étape | Donnée | Obligatoire | Saisie |
|---|---|---|---|
| 1. Type de boutique | `store_type = physical` | Oui | Choix |
| 2. Nom | `name` | Oui | Texte |
| 3. Localisation GPS | `latitude`, `longitude` | Oui | Automatique (GPS) |
| 4. Photo de façade | `facade_photo_url` | Oui | Upload |
| 5. Description du lieu | `place_description` | Non (recommandé) | Texte libre |
| 6. Horaires | `opening_hours` | Oui | Choix + texte |
| 7. Rayon de livraison | `delivery_radius` | Oui | Choix multiple |
| 8. Téléphone | `phone` | Oui | Texte |
| 9. Catégorie | `category` | Oui | Choix |

### Boutique en ligne

| Étape | Donnée | Obligatoire | Saisie |
|---|---|---|---|
| 1. Type de boutique | `store_type = online` | Oui | Choix |
| 2. Nom | `name` | Oui | Texte |
| 3. Description | `description` | Oui | Texte libre |
| 4. Logo | `logo_url` | Non | Upload |
| 5. Photo de couverture | `cover_photo_url` | Non | Upload |
| 6. Téléphone | `phone` | Oui | Texte |
| 7. Pays | `country` | Oui | Choix |
| 8. Ville | `city` | Oui | Texte |
| 9. Zone de livraison | `delivery_radius` | Oui | Choix multiple |
| 10. Catégorie | `category` | Oui | Choix |

### Boutique physique + en ligne

| Étape | Donnée | Obligatoire | Saisie |
|---|---|---|---|
| 1. Type de boutique | `store_type = hybrid` | Oui | Choix |
| 2. Nom | `name` | Oui | Texte |
| 3. Localisation GPS | `latitude`, `longitude` | Oui | Automatique (GPS) |
| 4. Photo de façade | `facade_photo_url` | Oui | Upload |
| 5. Description du lieu | `place_description` | Non (recommandé) | Texte libre |
| 6. Logo | `logo_url` | Non | Upload |
| 7. Photo de couverture | `cover_photo_url` | Non | Upload |
| 8. Horaires | `opening_hours` | Oui | Choix + texte |
| 9. Téléphone | `phone` | Oui | Texte |
| 10. Pays | `country` | Oui | Choix |
| 11. Ville | `city` | Oui | Texte |
| 12. Catégorie | `category` | Oui | Choix |
| 13. Description | `description` | Non | Texte libre |
| 14. Rayon de livraison | `delivery_radius` | Oui | Choix multiple |
