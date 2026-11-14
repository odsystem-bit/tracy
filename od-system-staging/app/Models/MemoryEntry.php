<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class MemoryEntry extends Model
{
    use HasFactory;

    protected $table = 'memory_entries';

    protected $fillable = [
        'scope',
        'entity_id',
        'key',
        'value',
        'source',
        'expires_at',
    ];

    protected function casts(): array
    {
        return [
            'expires_at' => 'datetime',
        ];
    }
}
