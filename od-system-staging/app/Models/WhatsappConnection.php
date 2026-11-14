<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class WhatsappConnection extends Model
{
    protected $table = 'whatsapp_connections';

    protected $fillable = [
        'vendor_id',
        'phone_number',
        'phone_number_id',
        'waba_id',
        'status',
        'tracy_active',
        'hybrid_delay',
        'monthly_conversation_count',
        'monthly_conversation_limit',
        'connected_at',
    ];

    protected function casts(): array
    {
        return [
            'tracy_active' => 'boolean',
            'connected_at' => 'datetime',
            'monthly_conversation_count' => 'integer',
            'monthly_conversation_limit' => 'integer',
        ];
    }

    public function vendor(): BelongsTo
    {
        return $this->belongsTo(User::class, 'vendor_id');
    }

    public function is_connected(): bool
    {
        return $this->status === 'connected';
    }

    public function canReceiveMessages(): bool
    {
        if (!$this->is_connected() || !$this->tracy_active) {
            return false;
        }

        if ($this->monthly_conversation_limit > 0 && $this->monthly_conversation_count >= $this->monthly_conversation_limit) {
            return false;
        }

        return true;
    }
}
