<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        // Récupère l'ID du Bénin (code = 'BJ')
        $benin = DB::table('countries')->where('code', 'BJ')->first();
        if (!$benin) {
            return; // La migration countries doit avoir été exécutée
        }
        $beninId = $benin->id;

        $documents = [
            [
                'title'       => 'Quartiers et villes principales du Bénin',
                'category'    => 'benin_quartiers',
                'content'     => <<<'TEXT'
# Quartiers et villes principales du Bénin

## Cotonou (capitale économique)
Cotonou est la plus grande ville du Bénin et son centre économique. Les quartiers principaux sont :

- Ganhi : le quartier des affaires, banques, boutiques, restaurants.
- Dantokpa : le quartier du plus grand marché d'Afrique de l'Ouest.
- Akpakpa : quartier populaire sur la rive est de la lagune.
- Fidjrossè : quartier résidentiel et balnéaire.
- Cadjèhoun : quartier résidentiel, proche de l'aéroport.

## Porto-Novo (capitale officielle)
Porto-Novo est la capitale officielle du Bénin, située à l'est de Cotonou.
Quartiers principaux : Ouando, Avotrou, Zounkpa.

## Parakou (nord)
Parakou est la plus grande ville du nord du Bénin. Marché important pour le commerce de transit vers le Niger.

## Autres villes importantes
- Abomey : ville historique, ancienne capitale du royaume Dahomey.
- Ouidah : ville côtière, centre historique de la traite négrière.
- Natitingou : ville du nord-ouest, proche des monts Atacora.
- Kandi : ville du nord, carrefour commercial.
TEXT,
            ],
            [
                'title'       => 'Marchés du Bénin',
                'category'    => 'benin_marches',
                'content'     => <<<'TEXT'
# Marchés du Bénin

## Dantokpa (Cotonou)
Dantokpa est le plus grand marché à ciel ouvert d'Afrique de l'Ouest. Il se trouve à Cotonou, dans le quartier éponyme. On y trouve absolument de tout : tissus, vêtements, alimentation, électronique, cosmétiques, ustensiles, meubles. C'est le centre névralgique du commerce béninois. Ouvert tous les jours, principalement de 6h à 20h.

## Ganhi (Cotonou)
Ganhi est le quartier des affaires de Cotonou. On y trouve des boutiques plus modernes, des banques, des pharmacies, des restaurants et des commerces de produits importés. C'est le quartier des commerçants qui vendent des produits de marque et de l'électronique.

## Arzèkè (Cotonou)
Arzèkè est un marché de quartier à Cotonou, spécialisé dans l'alimentation et les produits de première nécessité. Moins touristique que Dantokpa, il est fréquenté par les locaux pour les courses quotidiennes.

## Ouando (Porto-Novo)
Ouando est le principal marché de Porto-Novo. On y trouve des produits agricoles, de l'artisanat, des tissus et des produits manufacturés. C'est le centre commercial de la capitale officielle.

## Marchés de quartier
Chaque quartier de Cotonou a son petit marché : Aïlassa, Mènontin, Gbégamey, Sainte-Rita. Ces marchés de proximité vendent principalement de l'alimentation et des produits du quotidien.
TEXT,
            ],
            [
                'title'       => 'Moyens de paiement locaux au Bénin',
                'category'    => 'benin_paiements',
                'content'     => <<<'TEXT'
# Moyens de paiement locaux au Bénin

## Mobile Money (MoMo)
Le Mobile Money est le moyen de paiement le plus répandu au Bénin. Deux opérateurs dominent le marché :

### MTN MoMo
MTN MoMo est le service de paiement mobile de MTN Bénin. C'est l'opérateur le plus utilisé. On peut envoyer et recevoir de l'argent, payer des factures, recharger son compte. Le plafond de transaction dépend du niveau de vérification KYC.

### Moov Money
Moov Money est le service de paiement mobile de Moov Africa Bénin. Moins répandu que MTN MoMo mais largement utilisé. Mêmes fonctionnalités : transfert d'argent, paiement de factures, recharge.

## Carte bancaire
Les cartes bancaires (Visa, Mastercard) sont acceptées dans les grandes boutiques, supermarchés et hôtels. Les terminaux de paiement (TPE) sont communs à Cotonou, moins dans les autres villes.

## Espèces (FCFA)
Le Franc CFA (XOF) reste le moyen de paiement le plus courant, surtout dans les marchés et petits commerces. La monnaie est le FCFA (Franc CFA BCEAO).

## Paiement en ligne
Sur Mantota, le paiement se fait via Moneroo qui supporte Mobile Money (MTN MoMo, Moov Money) et carte bancaire. Le client reçoit un lien de paiement après avoir passé commande.
TEXT,
            ],
            [
                'title'       => 'Livraison au Bénin (Zem et coursiers)',
                'category'    => 'benin_livraison',
                'content'     => <<<'TEXT'
# Livraison au Bénin

## Zem (moto-taxi)
Le Zem (ou Zémidjan) est le moyen de transport le plus courant au Bénin. Ces motos-taxis sont omniprésents à Cotonou, Porto-Novo, Parakou et dans toutes les villes. Pour la livraison de petits colis, le Zem est rapide et économique. Le tarif se négocie à l'avance, généralement entre 500 et 2000 FCFA selon la distance.

## Coursiers locaux
Des services de coursiers existent à Cotonou, notamment pour les boutiques en ligne. Ils utilisent des motos ou des tricycles. Les tarifs varient entre 1000 et 5000 FCFA selon la zone.

## Livraison en véhicule
Pour les colis volumineux ou les livraisons inter-villes, des transporteurs en véhicule (pick-up, camionnette) sont disponibles. Tarifs variables selon le volume et la distance.

## Délais de livraison
- Dans Cotonou : 1 à 3 heures en Zem, 2 à 6 heures en véhicule.
- Inter-villes (Cotonou → Porto-Novo) : 1 à 2 heures.
- Inter-villes (Cotonou → Parakou) : 4 à 6 heures.
- Vers le nord (Natitingou, Kandi) : 8 à 12 heures.

## Zones de livraison
La livraison est plus rapide et moins chère dans les grandes villes (Cotonou, Porto-Novo, Parakou). En zone rurale, les délais sont plus longs et les tarifs plus élevés.
TEXT,
            ],
            [
                'title'       => 'Expressions courantes du commerce béninois',
                'category'    => 'benin_expressions',
                'content'     => <<<'TEXT'
# Expressions courantes du commerce béninois

## Salutations et politesse
- "Akwaba" : bienvenue (souvent utilisé pour accueillir un client).
- "Yovo" : terme familier pour désigner un étranger (à utiliser avec précaution).
- "Na tchin" : comment ça va ? (en fon, langue locale du sud Bénin).

## Négociation
- "C'est combien ?" : question de prix standard.
- "Tu peux faire un effort ?" : demande de réduction.
- "C'est le dernier prix ?" : demande si le prix est négociable.
- "Je vais chez le voisin" : moyen de pression pour obtenir un meilleur prix.
- "C'est donné" : le prix est très bas, presque un cadeau.

## Paiement
- "Je vais faire le MoMo" : je vais payer par Mobile Money.
- "Tu as le compte MoMo ?" : as-tu un compte Mobile Money ?
- "Faire le transfert" : envoyer de l'argent via MoMo.

## Livraison
- "Je prends un Zem" : je vais livrer par moto-taxi.
- "C'est à quelle zone ?" : dans quel quartier faut-il livrer ?

## Expressions à éviter en vente
- "C'est cher" : préférer "C'est au-dessus de mon budget".
- "Je n'ai pas d'argent" : préférer "Je vais réfléchir".
TEXT,
            ],
        ];

        foreach ($documents as $doc) {
            DB::table('knowledge_documents')->insert([
                'title'      => $doc['title'],
                'content'    => $doc['content'],
                'country_id' => $beninId,
                'category'   => $doc['category'],
                'status'     => 'draft',  // Reste draft jusqu'à validation manuelle
                'version'    => 1,
                'created_by' => null,
                'created_at' => now(),
                'updated_at' => now(),
            ]);
        }
    }

    public function down(): void
    {
        DB::table('knowledge_documents')
            ->where('category', 'like', 'benin_%')
            ->delete();
    }
};
