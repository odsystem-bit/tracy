<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('currencies', function (Blueprint $table) {
            $table->id();
            $table->string('code', 3)->unique();
            $table->string('name');
            $table->string('symbol', 10);
            $table->decimal('rate_to_xof', 12, 4)->default(1.0000);
            $table->json('country_codes')->nullable();
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });

        // Seed devises de base
        DB::table('currencies')->insert([
            [
                'code' => 'XOF',
                'name' => 'Franc CFA (BCEAO)',
                'symbol' => 'FCFA',
                'rate_to_xof' => 1.0000,
                'country_codes' => json_encode(['BJ', 'TG', 'SN', 'CI', 'BF', 'ML', 'NE', 'GW']),
                'is_active' => true,
                'created_at' => now(),
                'updated_at' => now(),
            ],
            [
                'code' => 'XAF',
                'name' => 'Franc CFA (BEAC)',
                'symbol' => 'FCFA',
                'rate_to_xof' => 1.0000,
                'country_codes' => json_encode(['CM', 'GA', 'CG', 'TD', 'CF', 'GQ']),
                'is_active' => true,
                'created_at' => now(),
                'updated_at' => now(),
            ],
            [
                'code' => 'GHS',
                'name' => 'Cedi ghanéen',
                'symbol' => 'GH₵',
                'rate_to_xof' => 41.67,
                'country_codes' => json_encode(['GH']),
                'is_active' => true,
                'created_at' => now(),
                'updated_at' => now(),
            ],
            [
                'code' => 'NGN',
                'name' => 'Naira nigérian',
                'symbol' => '₦',
                'rate_to_xof' => 0.39,
                'country_codes' => json_encode(['NG']),
                'is_active' => true,
                'created_at' => now(),
                'updated_at' => now(),
            ],
            [
                'code' => 'USD',
                'name' => 'Dollar américain',
                'symbol' => '$',
                'rate_to_xof' => 615.00,
                'country_codes' => json_encode(['US']),
                'is_active' => true,
                'created_at' => now(),
                'updated_at' => now(),
            ],
            [
                'code' => 'EUR',
                'name' => 'Euro',
                'symbol' => '€',
                'rate_to_xof' => 655.957,
                'country_codes' => json_encode(['FR', 'DE', 'BE']),
                'is_active' => true,
                'created_at' => now(),
                'updated_at' => now(),
            ],
        ]);
    }

    public function down(): void
    {
        Schema::dropIfExists('currencies');
    }
};
