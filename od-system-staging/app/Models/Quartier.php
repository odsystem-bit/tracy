<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Quartier extends Model
{
    protected $fillable = ['ville_id', 'name', 'arrondissement_name'];

    public function ville(): BelongsTo
    {
        return $this->belongsTo(Ville::class);
    }
}
