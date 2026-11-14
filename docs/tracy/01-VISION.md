# Tracy — Vision

## 1. Pourquoi Tracy existe

### Le constat

En Afrique, la très grande majorité du commerce ne se fait pas dans des logiciels de gestion : elle se fait dans la conversation. WhatsApp, appels téléphoniques, messages vocaux, bouche-à-oreille. C'est là que le client pose sa question, que le vendeur négocie, que la commande se conclut. Mantota replace progressivement cette conversation vers son propre canal — l'application Mantota — tout en gardant WhatsApp comme canal de transition et d'acquisition.

Les commerçants africains — du petit vendeur de rue au créateur de marque en ligne — partagent les mêmes contraintes :
- Ils n'ont pas le temps de répondre à tous les clients, tout le temps.
- Ils n'ont pas les compétences ni l'envie d'apprendre un logiciel de gestion complexe.
- Ils perdent des ventes simplement parce qu'ils n'ont pas répondu à temps.
- Ils gèrent leur activité "dans leur tête" : stock, prix, clients fidèles, promesses faites — rien n'est structuré.
- Les outils e-commerce existants (boutiques en ligne classiques, ERP) sont pensés pour des marchés où le client remplit lui-même un formulaire — pas pour un marché où le client discute.

### Le problème central

**Le commerce conversationnel n'a jamais eu son propre outil.** Il a fallu forcer la conversation dans des outils faits pour autre chose (sites e-commerce, tableurs, cahiers), ou embaucher quelqu'un à temps plein pour répondre aux clients — un coût que la majorité des commerçants ne peuvent pas se permettre.

### L'opportunité

Un modèle de langage capable de comprendre une conversation en français (et dans les langues locales), combiné à une plateforme commerciale structurée (Mantota) et un moyen de paiement mobile fiable (Moneroo), rend possible ce qui ne l'était pas avant : une employée qui **parle** la langue du commerce africain, disponible pour tous, à un coût qu'aucun humain équivalent ne pourrait proposer.

### La réponse : Tracy

Tracy existe pour combler cet écart : une employée IA qui parle avec les clients, gère la boutique, et fait vivre le commerce du vendeur, sans que celui-ci ait besoin de savoir utiliser un logiciel.

Tracy n'est pas un produit technique destiné aux développeurs. C'est une collègue de travail destinée aux commerçants — elle doit pouvoir être "embauchée" en quelques minutes, sans formation.

---

## 2. Mission

Permettre à n'importe quel vendeur, quel que soit son niveau technique, de disposer d'une employée IA capable de vendre, négocier, répondre, encaisser et fidéliser à sa place, avec la même qualité qu'un bon vendeur humain — disponible 24h/24, dans la langue du client, au prix d'un abonnement plutôt que d'un salaire.

---

## 3. Vision (long terme)

Devenir l'employée IA de référence pour les vendeurs, créateurs, partenaires et livreurs africains — disponible au cœur de l'application Mantota et du site web, capable de gérer l'ensemble du cycle commercial : discussion, négociation, catalogue, commande, paiement, livraison, fidélisation. WhatsApp reste un canal de transition et d'acquisition optionnel.

À terme, Tracy doit être perçue non pas comme "un chatbot installé sur ma boutique", mais comme "la personne qui s'occupe de mes clients quand je ne peux pas".

### Ce que le succès signifie concrètement
- Un vendeur peut s'absenter une journée entière sans perdre une seule vente pour cause de non-réponse.
- Un client obtient une réponse utile en moins de quelques secondes, à toute heure.
- Un vendeur peut gérer 10 fois plus de clients qu'auparavant, sans embaucher.
- La confiance est telle que les vendeurs délèguent progressivement des décisions de plus en plus importantes à Tracy (voir niveaux d'autonomie, `03-AGENTS.md`).

---

## 4. Objectifs

- Permettre à n'importe quel vendeur de vendre sans compétence technique.
- Répondre aux clients instantanément, 24h/24, dans un langage naturel.
- Négocier, rassurer, convaincre — comme le ferait un bon vendeur humain.
- Convertir une conversation en commande, et une commande en paiement.
- Faire grandir la boutique du vendeur sans qu'il ait à s'en soucier.
- Rester une aide fiable, jamais une boîte noire incontrôlable.
- Réduire à zéro le temps de réponse perçu par le client, sans jamais sacrifier l'exactitude de la réponse.
- Donner au vendeur une visibilité claire et instantanée sur son activité, en langage naturel plutôt qu'en tableaux de bord complexes.

---

## 5. Ce que Tracy est / n'est pas

| Tracy est | Tracy n'est pas |
|---|---|
| Une employée IA au service du vendeur et du client | Un simple chatbot de réponses automatiques préprogrammées |
| Une intelligence qui **comprend** les situations commerciales | Un moteur de décision métier autonome |
| Une assistante qui agit dans des limites précises et validées | Un accès direct à la base de données ou à l'infrastructure |
| Un point de contact conversationnel unique pour toutes les tâches liées à la vente | Un remplacement du vendeur : Tracy exécute, elle ne possède jamais la boutique |
| Honnête sur sa nature d'IA si on lui demande | Une entité qui se fait passer pour un humain |
| Capable de dire non et d'expliquer pourquoi | Une IA qui accepte toute demande pour plaire |

> **Règle fondamentale : Tracy comprend. Mantota décide et exécute.**
> Tracy ne possède aucune vérité métier propre : elle interroge, propose, exécute via des Tools validés — mais la décision finale (règle de prix, autorisation, transaction) appartient toujours à Mantota.
> Voir `07-DEVELOPMENT_RULES.md` pour le détail technique de cette séparation.

---

## 6. Les rôles

### Client
**Qui** : la personne qui discute avec Tracy pour découvrir des produits, négocier un prix, passer commande, suivre sa livraison, ou poser une question après-vente.
**Besoin principal** : obtenir une réponse fiable et rapide, sans avoir à attendre une disponibilité humaine.
**Ce que Tracy lui apporte** : une expérience d'achat fluide, disponible à toute heure, avec la possibilité de négocier comme dans un commerce traditionnel.

### Vendeur
**Qui** : le commerçant propriétaire de la boutique Mantota.
**Besoin principal** : vendre plus, perdre moins de clients par manque de réponse, sans avoir à apprendre un logiciel ni embaucher.
**Ce que Tracy lui apporte** : la gestion de son catalogue, de ses commandes, de ses campagnes et de sa relation client en langage naturel — comme s'il parlait à un employé.

### Partenaire
**Qui** : un acteur tiers (apporteur d'affaires, influenceur, revendeur) qui promeut les boutiques ou produits.
**Besoin principal** : comprendre clairement ce que sa promotion rapporte, et être payé sans friction.
**Ce que Tracy lui apporte** : un suivi transparent de ses performances et de ses commissions, et un moyen simple de demander un retrait.

### Livreur (Bientôt — V2)
**Qui** : la personne chargée d'acheminer la commande jusqu'au client.
**Besoin principal** : savoir clairement quoi livrer, où, et confirmer facilement la remise.
**Ce que Tracy lui apporte** : un suivi de tournée simplifié, un statut de livraison à jour, une preuve de remise numérique.

---

## 7. Principes directeurs

- **Utilité avant tout.** Chaque réponse doit faire avancer la conversation vers une action concrète — jamais une réponse pour occuper l'espace.
- **Confiance par la transparence.** Tracy ne cache jamais qu'elle est une IA lorsqu'on le lui demande, et n'invente jamais une information qu'elle ne connaît pas.
- **Sécurité avant vitesse.** Une action sensible (paiement, remboursement, suppression, permission) est toujours validée avant exécution — la rapidité ne justifie jamais un risque.
- **Simplicité radicale.** Le vendeur ne doit jamais avoir besoin d'un manuel pour utiliser Tracy ; si une fonctionnalité nécessite une formation, elle est mal conçue.
- **Amélioration continue, jamais autonome.** Tracy apprend des interactions, mais ne décide jamais seule de changer durablement son comportement sans validation (voir `06-MEMORY.md`, `07-DEVELOPMENT_RULES.md`).
- **Le vendeur reste maître de sa boutique.** Tracy exécute les règles du vendeur ; elle ne les redéfinit jamais de son propre chef.
- **Chaque décision est traçable.** Toute action de Tracy peut être expliquée après coup : quel agent, quelle règle, quel résultat.
- **La confidentialité est non négociable.** Les informations d'un client ou d'un vendeur ne fuient jamais vers un autre (voir `06-MEMORY.md`).
- **Une réponse honnête vaut mieux qu'une vente forcée.** Tracy privilégie la relation de confiance à long terme sur la conversion immédiate à tout prix.

---

## 8. Parcours utilisateurs

### Parcours Client
1. Le client découvre la boutique (application Mantota, site web, lien partagé, réseau social, recommandation). WhatsApp reste un canal d'acquisition optionnel.
2. Il pose une question ou cherche un produit — souvent de façon vague ("je cherche un cadeau pas cher").
3. Tracy clarifie le besoin, présente le catalogue pertinent, négocie si le client le demande.
4. Le client passe commande ; Tracy récupère les informations manquantes (adresse, quantité).
5. Tracy initie le paiement via Mantota/Moneroo et confirme la réception.
6. Le client suit sa commande jusqu'à la livraison, avec des mises à jour proactives en cas de retard.
7. Tracy assure le suivi après-vente : avis, réclamation éventuelle, ou proposition de fidélisation.

**Canal principal** : la conversation native dans l'application Mantota. Le client n'a plus besoin d'utiliser WhatsApp pour communiquer avec les vendeurs.

**Cas limites pris en compte** : produit indisponible en cours de conversation, client indécis qui abandonne, demande de remboursement, client mécontent nécessitant une escalade humaine.

### Parcours Vendeur
1. Le vendeur crée sa boutique Mantota, guidé entièrement par Tracy (voir Store Creation Flow ci-dessous).
2. Il ajoute ou importe ses produits via une conversation ("ajoute ce produit à 5000 FCFA").
3. Tracy répond aux clients à sa place dès la boutique active.
4. Le vendeur consulte ses ventes, son stock et ses statistiques en langage naturel, sans tableau de bord complexe à apprendre.
5. Tracy propose proactivement des relances et des campagnes pertinentes (paniers abandonnés, clients inactifs).
6. Le vendeur définit ou ajuste ses règles (marges de négociation, promotions) — Tracy les applique fidèlement.
7. Le vendeur retire ses gains via son portefeuille Mantota, à tout moment.

**Store Creation Flow** : Tracy guide entièrement le vendeur lors de la création de sa boutique. Selon le type de boutique (physique, en ligne, ou les deux) :
- **Boutique physique** : Tracy demande si le vendeur est sur place, lance le GPS automatiquement, enregistre la position, demande une photo de façade, une description du lieu, les horaires et les zones de livraison. Le vendeur ne saisit jamais latitude ni longitude.
- **Boutique en ligne** : Tracy demande la description, les catégories, les informations de base.
- **Boutique hybride** : Tracy combine les deux parcours.

**Canal principal** : la conversation native dans l'application Mantota. Le vendeur gère sa boutique entièrement par la conversation.

**Cas limites pris en compte** : vendeur qui donne une instruction ambiguë (Tracy demande une clarification plutôt que de deviner), rupture de stock en plein pic de vente, changement de règle en cours de journée.

### Parcours Partenaire
1. Le partenaire s'inscrit dans l'application Mantota et obtient ses liens ou outils de promotion.
2. Il partage les boutiques ou produits auprès de son audience.
3. Tracy l'informe de ses performances (vues, clics, conversions) et de ses commissions cumulées.
4. Le partenaire demande un retrait de ses gains, avec confirmation avant exécution.

**Canal principal** : la conversation native dans l'application Mantota.

### Parcours Livreur (Bientôt — V2)
1. Le livreur reçoit une commande à livrer dans l'application Mantota, avec les informations nécessaires (adresse, contact, contenu).
2. Il met à jour le statut de la course via Tracy à chaque étape clé.
3. Le client et le vendeur sont notifiés automatiquement (notifications natives Mantota) des changements de statut.
4. Le livreur confirme la remise, générant une preuve de livraison.

**Canal principal** : la conversation native dans l'application Mantota.

---

## 9. Indicateurs de succès de la vision

La vision est atteinte si, mesurés dans le temps :
- Le taux de réponse aux messages clients approche 100%, à toute heure.
- Le temps moyen de première réponse tend vers l'instantané.
- Le taux de conversion conversation → commande augmente par rapport à une gestion manuelle.
- Le taux de paniers abandonnés récupérés par relance augmente.
- La satisfaction des vendeurs quant à la fiabilité de Tracy (aucune action non désirée, aucune promesse non tenue) reste élevée.
- Le nombre d'actions déléguées à Tracy par un même vendeur augmente avec le temps (signe de confiance croissante).

---

## 10. Glossaire minimal

- **Tracy** : l'employée IA perçue par l'utilisateur final.
- **Tracy Core** : le moteur d'orchestration qui fait fonctionner Tracy (détails techniques dans `02-ARCHITECTURE.md`).
- **Mantota** : la plateforme de commerce conversationnel qui détient la logique métier, les données et les décisions finales. Son canal principal est l'application Mantota et le site web.
- **Agent** : une unité spécialisée de Tracy Core dédiée à une mission (voir `03-AGENTS.md`).
- **Tool** : la seule porte d'action réelle utilisée par un agent (voir `04-TOOLS.md`).

Ce document reste volontairement non technique. Pour l'architecture, voir `02-ARCHITECTURE.md`.
