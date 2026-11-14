<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class RestaurantHour extends Model
{
    use HasFactory;

    protected $fillable = [
        'restaurant_id',
        'day_of_week',
        'open_time',
        'close_time',
        'is_closed',
    ];

    protected function casts(): array
    {
        return [
            'day_of_week' => 'integer',
            'is_closed'   => 'boolean',
        ];
    }

    public function restaurant(): BelongsTo
    {
        return $this->belongsTo(User::class, 'restaurant_id');
    }

    public static function isOpenNow(int $restaurantId): bool
    {
        $day = (int) now()->dayOfWeek;
        $hour = self::where('restaurant_id', $restaurantId)
            ->where('day_of_week', $day)
            ->where('is_closed', false)
            ->first();

        if (!$hour) {
            return false;
        }

        $now = now()->format('H:i:s');
        return $now >= $hour->open_time && $now <= $hour->close_time;
    }
}
