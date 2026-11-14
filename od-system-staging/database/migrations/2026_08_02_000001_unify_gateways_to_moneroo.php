<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    /**
     * Désactive toutes les anciennes passerelles et consolide sur Moneroo.
     */
    public function up(): void
    {
        DB::table('gateways')->where('slug', '!=', 'moneroo')->update([
            'is_active' => false,
            'updated_at' => now(),
        ]);

        $moneroo = DB::table('gateways')->where('slug', 'moneroo')->first();

        if ($moneroo) {
            DB::table('gateways')->where('slug', 'moneroo')->update([
                'is_active'   => true,
                'priority'    => 1,
                'payin_fee'   => 2.00,
                'payout_fee'  => 1.00,
                'countries'   => json_encode(['BJ', 'CI', 'SN', 'TG', 'BF', 'ML']),
                'supports_refund' => false,
                'supports_payout' => true,
                'updated_at'  => now(),
            ]);
        } else {
            DB::table('gateways')->insert([
                'name'            => 'Moneroo',
                'slug'            => 'moneroo',
                'is_active'       => true,
                'public_key'      => null,
                'secret_key'      => null,
                'webhook_secret'  => null,
                'environment'     => 'sandbox',
                'countries'       => json_encode(['BJ', 'CI', 'SN', 'TG', 'BF', 'ML']),
                'payin_fee'       => 2.00,
                'payout_fee'      => 1.00,
                'priority'        => 1,
                'supports_refund' => false,
                'supports_payout' => true,
                'extra_config'    => null,
                'created_at'      => now(),
                'updated_at'      => now(),
            ]);
        }
    }

    public function down(): void
    {
        // Aucun retour arrière automatique — les clés API sont perdues si on supprime Moneroo.
        DB::table('gateways')->where('slug', 'moneroo')->update([
            'is_active' => false,
            'updated_at' => now(),
        ]);
    }
};
