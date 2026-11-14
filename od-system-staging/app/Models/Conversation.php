<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Conversation extends Model
{
    protected $fillable = [
        'user1_id',
        'user2_id',
        'last_message',
        'last_message_time',
        'user1_last_read',
        'user2_last_read',
    ];

    protected $casts = [
        'last_message_time' => 'datetime',
        'user1_last_read' => 'datetime',
        'user2_last_read' => 'datetime',
    ];

    public function user1(): BelongsTo
    {
        return $this->belongsTo(User::class, 'user1_id');
    }

    public function user2(): BelongsTo
    {
        return $this->belongsTo(User::class, 'user2_id');
    }

    public function messages(): HasMany
    {
        return $this->hasMany(ConversationMessage::class)->orderBy('created_at');
    }

    public function otherUser(int $currentUserId): User
    {
        return $currentUserId === $this->user1_id ? $this->user2 : $this->user1;
    }

    public function unreadCountFor(int $userId): int
    {
        $lastRead = $userId === $this->user1_id ? $this->user1_last_read : $this->user2_last_read;
        return $this->messages()
            ->when($lastRead, fn($q) => $q->where('created_at', '>', $lastRead))
            ->where('sender_id', '!=', $userId)
            ->count();
    }
}
