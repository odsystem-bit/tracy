<?php

declare(strict_types=1);

namespace App\Notifications;

use Illuminate\Notifications\Notification;

/**
 * Relance proactive de Tracy envoyée au client in-app (post-négociation).
 */
class TracyFollowUpNotification extends Notification
{
    public function __construct(
        private string $message,
        private string $vendorId,
    ) {}

    public function via(object $notifiable): array
    {
        return ['database'];
    }

    public function toArray(object $notifiable): array
    {
        return [
            'type' => 'tracy_follow_up',
            'title' => 'Tracy reprend contact',
            'message' => $this->message,
            'vendor_id' => $this->vendorId,
            'color' => 'teal',
        ];
    }
}
