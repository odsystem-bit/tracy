<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Customer extends Model
{
    protected $table = 'customers';

    protected $fillable = [
        'customer_id',
        'phone',
        'display_name',
        'store_id',
        'channel_origin',
        'last_seen_at',
    ];

    protected function casts(): array
    {
        return [
            'last_seen_at' => 'datetime',
        ];
    }

    public function store(): BelongsTo
    {
        return $this->belongsTo(User::class, 'store_id');
    }

    public static function findOrCreateByPhone(string $phone, ?int $storeId = null, string $channel = 'app'): self
    {
        $customerId = preg_replace('/[^0-9]/', '', $phone);

        if (!str_starts_with($customerId, '229') && strlen($customerId) <= 10) {
            $customerId = '229' . $customerId;
        }

        return self::firstOrCreate(
            ['customer_id' => $customerId],
            [
                'phone' => $phone,
                'store_id' => $storeId,
                'channel_origin' => $channel,
                'last_seen_at' => now(),
            ]
        );
    }
}
