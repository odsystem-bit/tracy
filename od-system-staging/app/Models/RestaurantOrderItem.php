<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class RestaurantOrderItem extends Model
{
    use HasFactory;

    protected $fillable = [
        'restaurant_order_id',
        'menu_item_id',
        'menu_item_name',
        'unit_price',
        'quantity',
        'total_price',
        'selected_options',
        'special_instructions',
    ];

    protected function casts(): array
    {
        return [
            'unit_price'  => 'decimal:2',
            'quantity'    => 'integer',
            'total_price' => 'decimal:2',
            'selected_options' => 'array',
        ];
    }

    public function order(): BelongsTo
    {
        return $this->belongsTo(RestaurantOrder::class, 'restaurant_order_id');
    }

    public function menuItem(): BelongsTo
    {
        return $this->belongsTo(MenuItem::class, 'menu_item_id');
    }
}
