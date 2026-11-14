<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->dropColumn('shop_type');
        });

        Schema::table('users', function (Blueprint $table) {
            $table->enum('shop_type', ['physical', 'digital', 'both', 'restaurant_online', 'restaurant_physical'])
                ->default('physical')
                ->after('whatsapp_bot_number');
        });
    }

    public function down(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->dropColumn('shop_type');
        });

        Schema::table('users', function (Blueprint $table) {
            $table->enum('shop_type', ['physical', 'digital', 'both'])->nullable()->after('whatsapp_bot_number');
        });
    }
};
