<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Ville extends Model
{
    protected $fillable = ['country_id', 'name', 'department_name'];

    public function country(): BelongsTo
    {
        return $this->belongsTo(Country::class);
    }

    public function quartiers(): HasMany
    {
        return $this->hasMany(Quartier::class);
    }
}
