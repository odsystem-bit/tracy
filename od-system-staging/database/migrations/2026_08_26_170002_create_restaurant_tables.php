<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // ── Menu categories (entrées, plats, desserts, boissons...) ──
        Schema::create('menu_categories', function (Blueprint $table) {
            $table->id();
            $table->foreignId('restaurant_id')->constrained('users')->cascadeOnDelete();
            $table->string('name', 100);
            $table->string('slug', 120);
            $table->integer('sort_order')->default(0);
            $table->boolean('is_active')->default(true);
            $table->timestamps();

            $table->unique(['restaurant_id', 'slug']);
            $table->index(['restaurant_id', 'sort_order']);
        });

        // ── Menu items (plats) ──
        Schema::create('menu_items', function (Blueprint $table) {
            $table->id();
            $table->foreignId('restaurant_id')->constrained('users')->cascadeOnDelete();
            $table->foreignId('category_id')->constrained('menu_categories')->cascadeOnDelete();
            $table->string('name', 200);
            $table->text('description')->nullable();
            $table->decimal('price', 10, 2);
            $table->string('image_path')->nullable(false);
            $table->json('ingredients')->nullable();
            $table->json('allergens')->nullable();
            $table->integer('preparation_time_min')->default(15);
            $table->integer('calories')->nullable();
            $table->boolean('is_vegetarian')->default(false);
            $table->boolean('is_halal')->default(false);
            $table->boolean('is_available')->default(true);
            $table->integer('sort_order')->default(0);
            $table->timestamps();

            $table->index(['restaurant_id', 'category_id']);
            $table->index(['restaurant_id', 'is_available']);
        });

        // ── Menu item options (taille, suppléments, sauces...) ──
        Schema::create('menu_item_options', function (Blueprint $table) {
            $table->id();
            $table->foreignId('menu_item_id')->constrained('menu_items')->cascadeOnDelete();
            $table->string('name', 100);
            $table->enum('type', ['single_choice', 'multi_choice', 'free_text']);
            $table->boolean('is_required')->default(false);
            $table->integer('max_selections')->default(1);
            $table->integer('sort_order')->default(0);
            $table->timestamps();

            $table->index('menu_item_id');
        });

        // ── Option values (ex: Petite +0, Moyenne +500, Grande +1000) ──
        Schema::create('menu_item_option_values', function (Blueprint $table) {
            $table->id();
            $table->foreignId('option_id')->constrained('menu_item_options')->cascadeOnDelete();
            $table->string('name', 100);
            $table->decimal('price_modifier', 10, 2)->default(0);
            $table->boolean('is_default')->default(false);
            $table->integer('sort_order')->default(0);
            $table->timestamps();

            $table->index('option_id');
        });

        // ── Restaurant opening hours ──
        Schema::create('restaurant_hours', function (Blueprint $table) {
            $table->id();
            $table->foreignId('restaurant_id')->constrained('users')->cascadeOnDelete();
            $table->tinyInteger('day_of_week'); // 0=Dimanche, 1=Lundi, ..., 6=Samedi
            $table->time('open_time');
            $table->time('close_time');
            $table->boolean('is_closed')->default(false);
            $table->timestamps();

            $table->unique(['restaurant_id', 'day_of_week']);
        });

        // ── Restaurant orders (panier multi-plats) ──
        Schema::create('restaurant_orders', function (Blueprint $table) {
            $table->id();
            $table->string('order_number', 50)->unique();
            $table->foreignId('restaurant_id')->constrained('users')->cascadeOnDelete();
            $table->foreignId('customer_id')->constrained('users')->cascadeOnDelete();
            $table->enum('order_type', ['delivery', 'pickup']);
            $table->enum('status', ['pending', 'preparing', 'ready', 'on_delivery', 'delivered', 'picked_up', 'cancelled'])
                ->default('pending');
            $table->decimal('subtotal', 10, 2);
            $table->decimal('delivery_fee', 10, 2)->default(0);
            $table->decimal('total', 10, 2);
            $table->text('delivery_address')->nullable();
            $table->decimal('delivery_latitude', 10, 7)->nullable();
            $table->decimal('delivery_longitude', 10, 7)->nullable();
            $table->string('customer_phone', 20);
            $table->text('notes')->nullable();
            $table->timestamp('estimated_delivery_at')->nullable();
            $table->timestamp('delivered_at')->nullable();
            $table->timestamps();

            $table->index(['restaurant_id', 'status']);
            $table->index(['customer_id', 'status']);
        });

        // ── Restaurant order items (plats dans le panier) ──
        Schema::create('restaurant_order_items', function (Blueprint $table) {
            $table->id();
            $table->foreignId('restaurant_order_id')->constrained('restaurant_orders')->cascadeOnDelete();
            $table->foreignId('menu_item_id')->constrained('menu_items')->cascadeOnDelete();
            $table->string('menu_item_name');
            $table->decimal('unit_price', 10, 2);
            $table->integer('quantity')->default(1);
            $table->decimal('total_price', 10, 2);
            $table->json('selected_options')->nullable();
            $table->text('special_instructions')->nullable();
            $table->timestamps();

            $table->index('restaurant_order_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('restaurant_order_items');
        Schema::dropIfExists('restaurant_orders');
        Schema::dropIfExists('restaurant_hours');
        Schema::dropIfExists('menu_item_option_values');
        Schema::dropIfExists('menu_item_options');
        Schema::dropIfExists('menu_items');
        Schema::dropIfExists('menu_categories');
    }
};
