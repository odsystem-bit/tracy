<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class MenuItem extends Model
{
    use HasFactory;

    protected $fillable = [
        'restaurant_id',
        'category_id',
        'name',
        'description',
        'price',
        'image_path',
        'ingredients',
        'allergens',
        'preparation_time_min',
        'calories',
        'is_vegetarian',
        'is_halal',
        'is_available',
        'sort_order',
    ];

    protected function casts(): array
    {
        return [
            'price'               => 'decimal:2',
            'ingredients'         => 'array',
            'allergens'           => 'array',
            'preparation_time_min' => 'integer',
            'calories'            => 'integer',
            'is_vegetarian'       => 'boolean',
            'is_halal'            => 'boolean',
            'is_available'        => 'boolean',
            'sort_order'          => 'integer',
        ];
    }

    public function restaurant(): BelongsTo
    {
        return $this->belongsTo(User::class, 'restaurant_id');
    }

    public function category(): BelongsTo
    {
        return $this->belongsTo(MenuCategory::class, 'category_id');
    }

    public function options(): HasMany
    {
        return $this->hasMany(MenuItemOption::class, 'menu_item_id')->orderBy('sort_order');
    }

    public function imageUrl(): string
    {
        return asset('storage/' . $this->image_path);
    }
}
