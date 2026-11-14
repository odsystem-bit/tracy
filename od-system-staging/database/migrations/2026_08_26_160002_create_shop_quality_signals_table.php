<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Stocke les signaux de qualité (positifs et négatifs) pour le Shop Quality Score.
 *
 * Chaque signal a un poids (ex: +1 photo confirmée, -10 watermark détecté).
 * Le score d'une boutique = 100 + somme des poids des 30 derniers jours.
 *
 * Niveaux:
 *  ≥ 80 = excellent  |  ≥ 60 = good  |  ≥ 40 = warning
 *  ≥ 20 = risk       |  < 20 = suspended (auto-suspension + review admin)
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('shop_quality_signals', function (Blueprint $table) {
            $table->id();
            $table->foreignId('store_id')->constrained('users')->cascadeOnDelete(); // vendor_id
            $table->string('signal_type', 50); // photo_confirmed, watermark_detected, etc.
            $table->integer('weight'); // impact sur le score (positif ou négatif)
            $table->string('description', 500)->nullable();
            $table->foreignId('product_id')->nullable()->constrained()->nullOnDelete();
            $table->foreignId('order_id')->nullable()->constrained()->nullOnDelete();
            $table->string('admin_notified', 100)->nullable(); // null si pas notifié, sinon niveau
            $table->timestamps();

            $table->index(['store_id', 'created_at']);
            $table->index('signal_type');
        });

        // Table pour les vérifications d'authenticité des photos
        Schema::create('product_authenticity_checks', function (Blueprint $table) {
            $table->id();
            $table->foreignId('product_id')->constrained()->cascadeOnDelete();
            $table->foreignId('vendor_id')->constrained('users')->cascadeOnDelete();
            $table->decimal('trust_score', 5, 1)->default(100.0); // 0-100
            $table->json('flags')->nullable(); // ["watermark_detected", "duplicate_photo", ...]
            $table->boolean('has_watermark')->default(false);
            $table->boolean('is_duplicate')->default(false);
            $table->string('duplicate_of')->nullable(); // product_id
            $table->boolean('is_too_professional')->default(false);
            $table->boolean('resolution_suspicious')->default(false);
            $table->boolean('is_upscaled')->default(false);
            $table->text('recommendation')->nullable();
            $table->timestamps();

            $table->index(['vendor_id', 'trust_score']);
            $table->index('product_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('product_authenticity_checks');
        Schema::dropIfExists('shop_quality_signals');
    }
};
