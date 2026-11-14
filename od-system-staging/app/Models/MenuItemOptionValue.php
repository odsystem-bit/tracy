<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class MenuItemOptionValue extends Model
{
    use HasFactory;

    protected $fillable = [
        'option_id',
        'name',
        'price_modifier',
        'is_default',
        'sort_order',
    ];

    protected function casts(): array
    {
        return [
            'price_modifier' => 'decimal:2',
            'is_default'     => 'boolean',
            'sort_order'     => 'integer',
        ];
    }

    public function option(): BelongsTo
    {
        return $this->belongsTo(MenuItemOption::class, 'option_id');
    }
}
