<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class MenuItemOption extends Model
{
    use HasFactory;

    protected $fillable = [
        'menu_item_id',
        'name',
        'type',
        'is_required',
        'max_selections',
        'sort_order',
    ];

    protected function casts(): array
    {
        return [
            'is_required'    => 'boolean',
            'max_selections' => 'integer',
            'sort_order'     => 'integer',
        ];
    }

    public function menuItem(): BelongsTo
    {
        return $this->belongsTo(MenuItem::class, 'menu_item_id');
    }

    public function values(): HasMany
    {
        return $this->hasMany(MenuItemOptionValue::class, 'option_id')->orderBy('sort_order');
    }
}
