<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->enum('delivery_mode', [
                'pickup_only',
                'quartiers',
                'multi_city',
                'national',
                'international',
            ])->default('pickup_only')->after('kyc_status');
            $table->boolean('pickup_available')->default(true)->after('delivery_mode');
            $table->json('delivery_cities')->nullable()->after('pickup_available');
            $table->json('delivery_countries')->nullable()->after('delivery_cities');
        });
    }

    public function down(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->dropColumn(['delivery_mode', 'pickup_available', 'delivery_cities', 'delivery_countries']);
        });
    }
};
