<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class ShopNegotiationConfig extends Model
{
    protected $table = 'shop_negotiation_configs';

    protected $fillable = [
        'store_id',
        'min_margin_percent',
        'first_order_discount_percent',
        'max_discount_percent',
        'free_shipping_threshold',
        'auto_accept_below',
        'custom_rules',
        'currency',
        'address_form',
    ];

    protected $casts = [
        'min_margin_percent' => 'float',
        'first_order_discount_percent' => 'float',
        'max_discount_percent' => 'float',
        'free_shipping_threshold' => 'float',
        'auto_accept_below' => 'float',
    ];

    public function store(): BelongsTo
    {
        return $this->belongsTo(\App\Models\Product::class, 'store_id');
    }
}
