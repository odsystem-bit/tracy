# Tracy — Mémoire

## Objectif

La mémoire permet à Tracy de ne pas répéter les mêmes questions, de personnaliser ses réponses, et d'agir avec le contexte nécessaire. Mémoriser ne signifie pas tout enregistrer : cela signifie conserver uniquement ce qui est utile, durable et fiable.

---

## Mémoire courte

Portée : la conversation en cours uniquement.

Contient :
- les derniers messages échangés,
- le produit ou l'action évoqué récemment ("celui-ci", "le même en bleu"),
- le panier en cours de constitution.

Durée de vie : la conversation. Stockée en Redis, jamais persistée en base durable.

**Implémentation** : `app/memory/short_term.py` — `InMemoryShortTermMemory` (dev/tests) et `RedisShortTermMemory` (prod). Interface abstraite `ShortTermMemory`. Max 20 messages par conversation, TTL configurable (3600s par défaut).

---

## Mémoire longue

Portée : persistante, propre à chaque entité (client, vendeur, boutique, partenaire).

Contient :
- informations de l'entreprise (horaires, livraison, moyens de paiement, politique de retour),
- historique d'achats et préférences du client,
- règles métier définies par le vendeur (marges, promotions récurrentes).

Stockée en PostgreSQL, gérée exclusivement par Mantota. Tracy la consulte via `MemoryAgent`, elle ne la modifie jamais directement.

**Implémentation** : ✅ Implémenté en V1. Le `MemoryAgent` et les tools `save_memory`, `search_memory`, `update_memory`, `delete_memory` sont développés. Les endpoints Mantota correspondants sont définis dans `mantota_client/client.py` et validés contre l'API Laravel réelle (tests d'intégration T-015).

---

## Mémoire d'apprentissage

Tracy peut apprendre progressivement des habitudes de langage d'un vendeur ou d'une boutique.

**Exemple** : un vendeur écrit toujours "portable" au lieu de "téléphone". Après confirmation implicite répétée (le terme est utilisé sans ambiguïté plusieurs fois), Tracy associe les deux termes pour cette boutique uniquement.

Cette mémoire reste **locale à la boutique concernée** et ne modifie jamais le comportement global de Tracy.

---

## Format d'une entrée de mémoire

Chaque entrée de mémoire longue suit une structure standard :

```json
{
  "scope": "client | store | conversation",
  "entity_id": "...",
  "key": "langue_preferee",
  "value": "fr",
  "source": "explicit | inferred",
  "created_at": "...",
  "updated_at": "...",
  "expires_at": null
}
```

Le champ `source` permet de distinguer une information explicitement confirmée d'une information déduite — seules les informations `explicit` peuvent influencer une décision sensible.

---

## Préférences

Chaque client ou vendeur peut avoir des préférences mémorisées :
- langue préférée,
- canal de communication préféré,
- catégories de produits d'intérêt.

Les préférences sont toujours confirmées avant d'être enregistrées durablement.

---

## Historique

L'historique conserve la trace des interactions significatives :
- commandes passées,
- réclamations et leur résolution,
- campagnes reçues et réponses.

L'historique sert à la personnalisation, jamais à la surveillance intrusive du client.

---

## Contexte

Avant chaque réponse, Tracy consulte le contexte dans cet ordre :
1. Mémoire conversationnelle (courte).
2. Mémoire client.
3. Mémoire entreprise/boutique.
4. Mémoire métier (catalogue, commandes en cours).

Cet ordre garantit que la réponse reste cohérente avec l'échange immédiat avant d'aller chercher plus loin.

---

## Résumé

Les conversations longues sont résumées périodiquement pour :
- réduire la charge de contexte envoyée aux modèles IA,
- conserver l'essentiel sans stocker l'intégralité des échanges bruts.

Le résumé remplace le détail brut au-delà d'une certaine ancienneté.

---

## Expiration

Certaines informations expirent automatiquement et ne sont jamais conservées au-delà de leur utilité :
- session de conversation active,
- panier temporaire non confirmé,
- code OTP ou code de validation,
- jeton de session.

---

## Confidentialité

### Ce que Tracy a le droit de retenir
- Informations commerciales nécessaires à la vente (produits, prix, préférences confirmées).
- Informations de contact strictement nécessaires à la livraison et au paiement.
- Historique d'achat lié à la boutique concernée.

### Ce qu'elle ne doit jamais retenir
- Données bancaires complètes (numéros de carte, identifiants Moneroo).
- Codes OTP ou mots de passe.
- Informations personnelles non liées à l'activité commerciale.
- Toute donnée qu'un utilisateur a explicitement demandé d'oublier.

---

## Règles de mémorisation

Avant d'enregistrer une information durablement, `MemoryAgent` vérifie :
- **Utile** — sert-elle une future interaction ?
- **Durable** — a-t-elle vocation à rester vraie dans le temps ?
- **Fiable** — provient-elle d'une source confirmée (et non d'une supposition) ?
- **Confirmée** — l'utilisateur a-t-il validé cette information ?

Si l'une de ces conditions échoue, l'information n'est pas mémorisée durablement.

---

## Isolation

Chaque boutique et chaque entreprise possède sa propre mémoire, totalement isolée de celle des autres. Une boutique ne peut jamais accéder, directement ou indirectement, à la mémoire d'une autre.

---

## Mise à jour et historisation

Une information mémorisée peut être :
- **remplacée** (nouvelle valeur confirmée),
- **complétée** (précision ajoutée),
- **supprimée** (sur demande ou expiration).

Toute modification est historisée côté Mantota (qui a changé quoi, quand, pourquoi) — Tracy Core ne conserve aucun historique propre.

---

## Droit à l'oubli

Un client, un vendeur ou un partenaire peut à tout moment demander la suppression d'une information mémorisée le concernant. `MemoryAgent` exécute cette demande via `delete_memory` sans condition ni justification requise de la part de l'utilisateur.

Aucune information marquée comme à oublier n'est ré-inférée automatiquement par la suite sans nouvelle confirmation explicite.

---

## Notifications natives

Les notifications de l'application Mantota remplacent progressivement les notifications WhatsApp. Tracy utilise les notifications natives pour :

- **Paiement** — confirmation de paiement, échec de paiement
- **Commandes** — nouvelle commande, statut de commande, annulation
- **Contrats** — création de contrat, échéance de paiement échelonné
- **Rappels** — panier abandonné, produit de nouveau disponible
- **Relances** — campagne marketing, message de relance

Les notifications transitent par Mantota (qui décide quand et qui notifier). Tracy ne déclenche jamais de notification directement — elle demande à Mantota de le faire via les Tools.
