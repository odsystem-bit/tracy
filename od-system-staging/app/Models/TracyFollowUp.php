<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

/**
 * Relance proactive de Tracy vers un client (2-3h après une négociation sans achat).
 * Canal "whatsapp" : envoyé depuis le numéro lié du vendeur. Canal "app" : notification.
 */
class TracyFollowUp extends Model
{
    protected $fillable = [
        'vendor_id',
        'customer_id',
        'channel',
        'context_key',
        'message',
        'send_at',
        'sent_at',
        'status',
    ];

    protected function casts(): array
    {
        return [
            'send_at' => 'datetime',
            'sent_at' => 'datetime',
        ];
    }

    public function vendor(): BelongsTo
    {
        return $this->belongsTo(User::class, 'vendor_id');
    }
}
