<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('quartiers', function (Blueprint $table) {
            $table->id();
            $table->foreignId('ville_id')->constrained('villes')->cascadeOnDelete();
            $table->string('name');
            $table->string('arrondissement_name')->nullable();
            $table->timestamps();

            $table->index(['ville_id', 'name']);
        });

        // Seed des quartiers principaux du Bénin
        $benin = DB::table('countries')->where('code', 'BJ')->first();
        if (!$benin) {
            return;
        }

        // Récupère les villes du Bénin par nom
        $villes = DB::table('villes')
            ->where('country_id', $benin->id)
            ->pluck('id', 'name');

        $quartiersByVille = [
            // Cotonou (Littoral)
            'Cotonou' => [
                ['name' => 'Ganhi', 'arrondissement' => 'Cotonou I'],
                ['name' => 'Dantokpa', 'arrondissement' => 'Cotonou I'],
                ['name' => 'Akpakpa', 'arrondissement' => 'Cotonou II'],
                ['name' => 'Fidjrossè', 'arrondissement' => 'Cotonou III'],
                ['name' => 'Cadjèhoun', 'arrondissement' => 'Cotonou III'],
                ['name' => 'Jéricho', 'arrondissement' => 'Cotonou III'],
                ['name' => 'Zongo', 'arrondissement' => 'Cotonou I'],
                ['name' => 'Agla', 'arrondissement' => 'Cotonou V'],
                ['name' => 'Gbégamey', 'arrondissement' => 'Cotonou II'],
                ['name' => 'Mènontin', 'arrondissement' => 'Cotonou II'],
                ['name' => 'Sainte-Rita', 'arrondissement' => 'Cotonou II'],
                ['name' => 'Vossa', 'arrondissement' => 'Cotonou I'],
                ['name' => 'Ladjì', 'arrondissement' => 'Cotonou I'],
                ['name' => 'Houénoussou', 'arrondissement' => 'Cotonou II'],
                ['name' => 'Aïlassa', 'arrondissement' => 'Cotonou II'],
                ['name' => 'Sèkandji', 'arrondissement' => 'Cotonou V'],
                ['name' => 'Pahou', 'arrondissement' => 'Cotonou V'],
                ['name' => 'Zogbo', 'arrondissement' => 'Cotonou III'],
                ['name' => 'Bouëniko', 'arrondissement' => 'Cotonou V'],
                ['name' => 'Kpèkpanmè', 'arrondissement' => 'Cotonou V'],
            ],
            // Porto-Novo (Ouémé)
            'Porto-Novo' => [
                ['name' => 'Ouando', 'arrondissement' => 'Porto-Novo I'],
                ['name' => 'Avotrou', 'arrondissement' => 'Porto-Novo II'],
                ['name' => 'Zounkpa', 'arrondissement' => 'Porto-Novo III'],
                ['name' => 'Dowa', 'arrondissement' => 'Porto-Novo I'],
                ['name' => 'Gbégamey', 'arrondissement' => 'Porto-Novo II'],
                ['name' => 'Tankpà', 'arrondissement' => 'Porto-Novo III'],
                ['name' => 'Akonabè', 'arrondissement' => 'Porto-Novo I'],
                ['name' => 'Zinsè', 'arrondissement' => 'Porto-Novo II'],
                ['name' => 'Houèdomè', 'arrondissement' => 'Porto-Novo III'],
                ['name' => 'Gbagla', 'arrondissement' => 'Porto-Novo I'],
            ],
            // Parakou (Borgou)
            'Parakou' => [
                ['name' => 'Banikani', 'arrondissement' => 'Parakou I'],
                ['name' => 'Barei', 'arrondissement' => 'Parakou I'],
                ['name' => 'Zongo', 'arrondissement' => 'Parakou II'],
                ['name' => 'Albarika', 'arrondissement' => 'Parakou II'],
                ['name' => 'Yépa', 'arrondissement' => 'Parakou III'],
                ['name' => 'Kparo', 'arrondissement' => 'Parakou III'],
                ['name' => 'Arafani', 'arrondissement' => 'Parakou I'],
                ['name' => 'Madina', 'arrondissement' => 'Parakou II'],
                ['name' => 'Tournès', 'arrondissement' => 'Parakou III'],
            ],
            // Abomey-Calavi (Atlantique)
            'Abomey-Calavi' => [
                ['name' => 'Godomey', 'arrondissement' => 'Abomey-Calavi I'],
                ['name' => 'Zinvié', 'arrondissement' => 'Abomey-Calavi I'],
                ['name' => 'Togba', 'arrondissement' => 'Abomey-Calavi II'],
                ['name' => 'Hêvié', 'arrondissement' => 'Abomey-Calavi I'],
                ['name' => 'Kpèkpanmè', 'arrondissement' => 'Abomey-Calavi II'],
                ['name' => 'Dèkoungbé', 'arrondissement' => 'Abomey-Calavi I'],
                ['name' => 'Glo-Djigbé', 'arrondissement' => 'Abomey-Calavi II'],
            ],
            // Ouidah (Atlantique)
            'Ouidah' => [
                ['name' => 'Savi', 'arrondissement' => 'Ouidah I'],
                ['name' => 'Pahou', 'arrondissement' => 'Ouidah II'],
                ['name' => 'Dakpa', 'arrondissement' => 'Ouidah I'],
                ['name' => 'Gomè', 'arrondissement' => 'Ouidah II'],
                ['name' => 'Hêvié', 'arrondissement' => 'Ouidah I'],
            ],
            // Abomey (Zou)
            'Abomey' => [
                ['name' => 'Bohicon', 'arrondissement' => 'Abomey I'],
                ['name' => 'Agboglo', 'arrondissement' => 'Abomey II'],
                ['name' => 'Dètohou', 'arrondissement' => 'Abomey I'],
                ['name' => 'Sègboya', 'arrondissement' => 'Abomey II'],
                ['name' => 'Hounli', 'arrondissement' => 'Abomey I'],
            ],
            // Kandi (Alibori)
            'Kandi' => [
                ['name' => 'Kandi I', 'arrondissement' => 'Kandi I'],
                ['name' => 'Kandi II', 'arrondissement' => 'Kandi II'],
                ['name' => 'Kandi III', 'arrondissement' => 'Kandi III'],
                ['name' => 'Angaradébou', 'arrondissement' => 'Kandi I'],
            ],
            // Natitingou (Atacora)
            'Natitingou' => [
                ['name' => 'Natitingou I', 'arrondissement' => 'Natitingou I'],
                ['name' => 'Natitingou II', 'arrondissement' => 'Natitingou II'],
                ['name' => 'Natitingou III', 'arrondissement' => 'Natitingou III'],
                ['name' => 'Kouandé', 'arrondissement' => 'Natitingou I'],
            ],
            // Bohicon (Zou)
            'Bohicon' => [
                ['name' => 'Bohicon I', 'arrondissement' => 'Bohicon I'],
                ['name' => 'Bohicon II', 'arrondissement' => 'Bohicon II'],
                ['name' => 'Adjrah', 'arrondissement' => 'Bohicon I'],
                ['name' => 'Lokogba', 'arrondissement' => 'Bohicon II'],
            ],
            // Djougou (Atacora/Donga)
            'Djougou' => [
                ['name' => 'Djougou I', 'arrondissement' => 'Djougou I'],
                ['name' => 'Djougou II', 'arrondissement' => 'Djougou II'],
                ['name' => 'Djougou III', 'arrondissement' => 'Djougou III'],
                ['name' => 'Barei', 'arrondissement' => 'Djougou I'],
            ],
        ];

        foreach ($quartiersByVille as $villeName => $quartiers) {
            $villeId = $villes[$villeName] ?? null;
            if (!$villeId) {
                continue;
            }
            foreach ($quartiers as $q) {
                DB::table('quartiers')->insert([
                    'ville_id' => $villeId,
                    'name' => $q['name'],
                    'arrondissement_name' => $q['arrondissement'],
                    'created_at' => now(),
                    'updated_at' => now(),
                ]);
            }
        }
    }

    public function down(): void
    {
        Schema::dropIfExists('quartiers');
    }
};
