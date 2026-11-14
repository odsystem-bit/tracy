<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('shop_negotiation_configs', function (Blueprint $table) {
            $table->id();
            $table->foreignId('store_id')->constrained('users')->cascadeOnDelete();
            $table->decimal('min_margin_percent', 5, 2)->default(10.00);
            $table->decimal('first_order_discount_percent', 5, 2)->default(0.00);
            $table->decimal('max_discount_percent', 5, 2)->default(15.00);
            $table->decimal('free_shipping_threshold', 12, 2)->nullable();
            $table->decimal('auto_accept_below', 5, 2)->default(5.00);
            $table->text('custom_rules')->nullable();
            $table->string('currency', 3)->default('XOF');
            $table->timestamps();

            $table->unique('store_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('shop_negotiation_configs');
    }
};
