<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

/**
 * ShopQualitySignal — Signal de qualité (positif ou négatif) pour une boutique.
 *
 * Types positifs: photo_confirmed, good_rating, repeat_customer, fast_delivery
 * Types négatifs: photo_non_conform, watermark_detected, duplicate_photo, etc.
 *
 * Le score d'une boutique = 100 + somme des poids des 30 derniers jours.
 */
class ShopQualitySignal extends Model
{
    use HasFactory;

    protected $table = 'shop_quality_signals';

    /** @var list<string> */
    protected $fillable = [
        'store_id',
        'signal_type',
        'weight',
        'description',
        'product_id',
        'order_id',
        'admin_notified',
    ];

    /** @var array<string, string> */
    protected function casts(): array
    {
        return [
            'weight' => 'integer',
        ];
    }

    public function store(): BelongsTo
    {
        return $this->belongsTo(User::class, 'store_id');
    }

    public function product(): BelongsTo
    {
        return $this->belongsTo(Product::class);
    }

    public function order(): BelongsTo
    {
        return $this->belongsTo(Order::class);
    }

    /**
     * Poids des signaux (doit matcher Tracy Core: app/vision/shop_quality.py).
     */
    public static function getWeight(string $signalType): int
    {
        return match ($signalType) {
            'photo_confirmed' => 1,
            'good_rating' => 2,
            'repeat_customer' => 3,
            'fast_delivery' => 2,
            'photo_partial' => -2,
            'photo_non_conform' => -5,
            'watermark_detected' => -10,
            'duplicate_photo' => -5,
            'too_professional' => -5,
            'low_resolution' => -5,
            'upscaled_image' => -5,
            'bad_rating' => -5,
            'late_delivery' => -3,
            'dispute_opened' => -5,
            'dispute_lost' => -10,
            default => 0,
        };
    }
}
