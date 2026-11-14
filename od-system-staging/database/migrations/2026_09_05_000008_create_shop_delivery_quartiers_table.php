<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('shop_delivery_quartiers', function (Blueprint $table) {
            $table->id();
            $table->foreignId('shop_id')->constrained('users')->cascadeOnDelete();
            $table->foreignId('quartier_id')->constrained('quartiers')->cascadeOnDelete();
            $table->timestamps();

            $table->unique(['shop_id', 'quartier_id']);
            $table->index('quartier_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('shop_delivery_quartiers');
    }
};
