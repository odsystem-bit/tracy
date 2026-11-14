<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class KnowledgeGap extends Model
{
    protected $table = 'knowledge_gaps';

    protected $fillable = [
        'query_text',
        'country_id',
        'category_guess',
        'occurrence_count',
        'first_seen_at',
        'last_seen_at',
        'status',
        'resolved_document_id',
    ];

    protected $casts = [
        'occurrence_count' => 'integer',
        'first_seen_at'    => 'datetime',
        'last_seen_at'     => 'datetime',
    ];

    public function country(): BelongsTo
    {
        return $this->belongsTo(Country::class);
    }

    public function resolvedDocument(): BelongsTo
    {
        return $this->belongsTo(KnowledgeDocument::class, 'resolved_document_id');
    }
}
