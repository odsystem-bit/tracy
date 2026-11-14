<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

/**
 * ProductAuthenticityCheck — Résultat de vérification d'authenticité d'une photo produit.
 *
 * Détecte: watermark, duplication, photo trop pro, résolution/upscale suspects.
 * Trust score [0-100]: 100 = totalement authentique.
 */
class ProductAuthenticityCheck extends Model
{
    use HasFactory;

    protected $table = 'product_authenticity_checks';

    /** @var list<string> */
    protected $fillable = [
        'product_id',
        'vendor_id',
        'trust_score',
        'flags',
        'has_watermark',
        'is_duplicate',
        'duplicate_of',
        'is_too_professional',
        'resolution_suspicious',
        'is_upscaled',
        'recommendation',
    ];

    /** @var array<string, string> */
    protected function casts(): array
    {
        return [
            'trust_score' => 'decimal:1',
            'flags' => 'array',
            'has_watermark' => 'boolean',
            'is_duplicate' => 'boolean',
            'is_too_professional' => 'boolean',
            'resolution_suspicious' => 'boolean',
            'is_upscaled' => 'boolean',
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
}
