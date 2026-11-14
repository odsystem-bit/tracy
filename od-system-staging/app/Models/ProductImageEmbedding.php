<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

/**
 * ProductImageEmbedding — Embedding CLIP d'une image produit.
 *
 * Utilisé par Tracy Core pour identifier un produit à partir d'une photo client.
 * Chaque produit peut avoir plusieurs embeddings: l'original + les variantes augmentées.
 */
class ProductImageEmbedding extends Model
{
    use HasFactory;

    protected $table = 'product_image_embeddings';

    /** @var list<string> */
    protected $fillable = [
        'product_id',
        'vendor_id',
        'image_url',
        'embedding',
        'is_augmented',
        'augmentation_type',
        'perceptual_hash',
    ];

    /** @var array<string, string> */
    protected function casts(): array
    {
        return [
            'is_augmented' => 'boolean',
        ];
    }

    public function product(): BelongsTo
    {
        return $this->belongsTo(Product::class);
    }

    public function vendor(): BelongsTo
    {
        return $this->belongsTo(User::class, 'vendor_id');
    }

    /**
     * Récupère l'embedding sous forme de tableau de floats.
     */
    public function getEmbeddingArray(): array
    {
        return array_map('floatval', json_decode($this->embedding, true) ?? []);
    }
}
