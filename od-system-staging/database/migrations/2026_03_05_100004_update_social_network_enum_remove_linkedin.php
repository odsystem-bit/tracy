<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

/**
 * Mise a jour de l'enum social_network sur la table campaigns.
 *
 * - Supprime linkedin (BANNI).
 * - Ajoute youtube et snapchat pour aligner avec les 5 plateformes autorisees.
 * - Les campagnes existantes avec social_network = 'linkedin' sont basculees a NULL.
 */
return new class extends Migration
{
    public function up(): void
    {
        // Nullifier les campagnes LinkedIn existantes
        DB::table('campaigns')
            ->where('social_network', 'linkedin')
            ->update(['social_network' => null]);

        $driver = DB::getDriverName();
        if ($driver === 'pgsql') {
            DB::statement("ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_social_network_check");
            DB::statement("ALTER TABLE campaigns ADD CONSTRAINT campaigns_social_network_check CHECK (social_network IN ('tiktok', 'instagram', 'facebook', 'youtube', 'snapchat'))");
        } else {
            DB::statement("ALTER TABLE campaigns MODIFY COLUMN social_network ENUM('tiktok', 'instagram', 'facebook', 'youtube', 'snapchat') NULL");
        }
    }

    public function down(): void
    {
        $driver = DB::getDriverName();
        if ($driver === 'pgsql') {
            DB::statement("ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_social_network_check");
            DB::statement("ALTER TABLE campaigns ADD CONSTRAINT campaigns_social_network_check CHECK (social_network IN ('tiktok', 'instagram', 'facebook', 'linkedin'))");
        } else {
            DB::statement("ALTER TABLE campaigns MODIFY COLUMN social_network ENUM('tiktok', 'instagram', 'facebook', 'linkedin') NULL");
        }
    }
};
