<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Stocke les embeddings CLIP des images produit pour la reconnaissance visuelle.
 *
 * Tracy Core calcule un embedding (vecteur 512 dimensions) pour chaque image
 * produit à l'upload, avec des variantes augmentées (rotation, luminosité, etc.).
 * Ces embeddings sont utilisés pour identifier un produit à partir d'une photo
 * envoyée par un client (ex: screenshot de live TikTok).
 *
 * Note: PostgreSQL supporte le type vector via l'extension pgvector.
 * En attendant, on stocke le vecteur en JSON (text) pour compatibilité.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('product_image_embeddings', function (Blueprint $table) {
            $table->id();
            $table->foreignId('product_id')->constrained()->cascadeOnDelete();
            $table->foreignId('vendor_id')->constrained('users')->cascadeOnDelete();
            $table->string('image_url', 500)->nullable();
            $table->text('embedding'); // JSON array of floats (CLIP ViT-B/32 = 512 dims)
            $table->boolean('is_augmented')->default(false); // true si variante augmentée
            $table->string('augmentation_type')->nullable(); // rotation, brightness, blur, crop, saturation
            $table->string('perceptual_hash', 256)->nullable(); // hash pour détection duplication
            $table->timestamps();

            $table->index(['product_id', 'is_augmented']);
            $table->index('vendor_id');
            $table->index('perceptual_hash');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('product_image_embeddings');
    }
};
