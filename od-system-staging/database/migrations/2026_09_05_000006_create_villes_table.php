<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('villes', function (Blueprint $table) {
            $table->id();
            $table->foreignId('country_id')->constrained('countries')->cascadeOnDelete();
            $table->string('name');
            $table->string('department_name')->nullable();
            $table->timestamps();

            $table->index(['country_id', 'name']);
        });

        // Seed des villes du Bénin (départements/communes principales)
        $benin = DB::table('countries')->where('code', 'BJ')->first();
        if (!$benin) {
            return;
        }

        $villes = [
            // Littoral
            ['name' => 'Cotonou', 'department_name' => 'Littoral'],
            // Atlantique
            ['name' => 'Abomey-Calavi', 'department_name' => 'Atlantique'],
            ['name' => 'Allada', 'department_name' => 'Atlantique'],
            ['name' => 'Ouidah', 'department_name' => 'Atlantique'],
            ['name' => 'Sèmè-Kpodji', 'department_name' => 'Atlantique'],
            ['name' => 'Tori-Bossito', 'department_name' => 'Atlantique'],
            ['name' => 'Zè', 'department_name' => 'Atlantique'],
            ['name' => 'Kpomassè', 'department_name' => 'Atlantique'],
            // Ouémé
            ['name' => 'Porto-Novo', 'department_name' => 'Ouémé'],
            ['name' => 'Adjara', 'department_name' => 'Ouémé'],
            ['name' => 'Aguégués', 'department_name' => 'Ouémé'],
            ['name' => 'Akpro-Missérété', 'department_name' => 'Ouémé'],
            ['name' => 'Avrankou', 'department_name' => 'Ouémé'],
            ['name' => 'Bonou', 'department_name' => 'Ouémé'],
            ['name' => 'Dangbo', 'department_name' => 'Ouémé'],
            ['name' => 'Sakété', 'department_name' => 'Ouémé'],
            ['name' => 'Ifangni', 'department_name' => 'Ouémé'],
            ['name' => 'Pobè', 'department_name' => 'Ouémé'],
            ['name' => 'Adja-Ouèrè', 'department_name' => 'Ouémé'],
            ['name' => 'Kétou', 'department_name' => 'Ouémé'],
            // Plateau
            ['name' => 'Pobè', 'department_name' => 'Plateau'],
            ['name' => 'Sakété', 'department_name' => 'Plateau'],
            ['name' => 'Ifangni', 'department_name' => 'Plateau'],
            ['name' => 'Adja-Ouèrè', 'department_name' => 'Plateau'],
            ['name' => 'Kétou', 'department_name' => 'Plateau'],
            ['name' => 'Banigbé', 'department_name' => 'Plateau'],
            // Zou
            ['name' => 'Abomey', 'department_name' => 'Zou'],
            ['name' => 'Bohicon', 'department_name' => 'Zou'],
            ['name' => 'Cana', 'department_name' => 'Zou'],
            ['name' => 'Covè', 'department_name' => 'Zou'],
            ['name' => 'Djidja', 'department_name' => 'Zou'],
            ['name' => 'Ouinhi', 'department_name' => 'Zou'],
            ['name' => 'Za-Kpota', 'department_name' => 'Zou'],
            ['name' => 'Zangnanado', 'department_name' => 'Zou'],
            ['name' => 'Zogbodomey', 'department_name' => 'Zou'],
            // Collines
            ['name' => 'Bantè', 'department_name' => 'Collines'],
            ['name' => 'Dassa-Zoumè', 'department_name' => 'Collines'],
            ['name' => 'Glazoué', 'department_name' => 'Collines'],
            ['name' => 'Savalè', 'department_name' => 'Collines'],
            ['name' => 'Savé', 'department_name' => 'Collines'],
            ['name' => 'Ouessè', 'department_name' => 'Collines'],
            // Borgou
            ['name' => 'Parakou', 'department_name' => 'Borgou'],
            ['name' => 'Tchaourou', 'department_name' => 'Borgou'],
            ['name' => "N'Dali", 'department_name' => 'Borgou'],
            ['name' => 'Pèrèrè', 'department_name' => 'Borgou'],
            ['name' => 'Sinendé', 'department_name' => 'Borgou'],
            ['name' => 'Bembèrèkè', 'department_name' => 'Borgou'],
            ['name' => 'Kalalé', 'department_name' => 'Borgou'],
            ['name' => 'Nikki', 'department_name' => 'Borgou'],
            // Alibori
            ['name' => 'Kandi', 'department_name' => 'Alibori'],
            ['name' => 'Malanville', 'department_name' => 'Alibori'],
            ['name' => 'Banikoara', 'department_name' => 'Alibori'],
            ['name' => 'Karimama', 'department_name' => 'Alibori'],
            ['name' => 'Ségbana', 'department_name' => 'Alibori'],
            ['name' => 'Gogounou', 'department_name' => 'Alibori'],
            // Atacora
            ['name' => 'Natitingou', 'department_name' => 'Atacora'],
            ['name' => 'Tanguiéta', 'department_name' => 'Atacora'],
            ['name' => 'Matéri', 'department_name' => 'Atacora'],
            ['name' => 'Cobly', 'department_name' => 'Atacora'],
            ['name' => 'Toucountouna', 'department_name' => 'Atacora'],
            ['name' => 'Boukoumbé', 'department_name' => 'Atacora'],
            ['name' => 'Kérou', 'department_name' => 'Atacora'],
            ['name' => 'Kouandé', 'department_name' => 'Atacora'],
            ['name' => 'Péhunco', 'department_name' => 'Atacora'],
            ['name' => 'Djougou', 'department_name' => 'Atacora'],
            ['name' => 'Copargo', 'department_name' => 'Atacora'],
            ['name' => 'Ouaké', 'department_name' => 'Atacora'],
            ['name' => 'Bassila', 'department_name' => 'Atacora'],
            // Donga
            ['name' => 'Donga', 'department_name' => 'Donga'],
            ['name' => 'Copargo', 'department_name' => 'Donga'],
            ['name' => 'Ouaké', 'department_name' => 'Donga'],
            ['name' => 'Bassila', 'department_name' => 'Donga'],
        ];

        // Déduplique les communes qui apparaissent dans plusieurs départements
        $seen = [];
        foreach ($villes as $ville) {
            $key = $ville['name'] . '|' . $ville['department_name'];
            if (isset($seen[$key])) {
                continue;
            }
            $seen[$key] = true;
            DB::table('villes')->insert([
                'country_id' => $benin->id,
                'name' => $ville['name'],
                'department_name' => $ville['department_name'],
                'created_at' => now(),
                'updated_at' => now(),
            ]);
        }
    }

    public function down(): void
    {
        Schema::dropIfExists('villes');
    }
};
