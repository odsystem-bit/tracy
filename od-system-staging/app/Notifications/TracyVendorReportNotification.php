<?php

declare(strict_types=1);

namespace App\Notifications;

use App\Channels\WhatsappChannel;
use App\Channels\WhatsappMessage;
use Illuminate\Notifications\Notification;

/**
 * Compte-rendu de Tracy au vendeur (résumé de discussion client, demande de contact).
 *
 * Canal "database" toujours ; WhatsApp pour les demandes de contact et les ventes —
 * le vendeur reçoit le message sur son numéro lié (whatsapp_connections) ou son
 * téléphone de compte, via User::routeNotificationForWhatsapp().
 */
class TracyVendorReportNotification extends Notification
{
    public const KIND_NEGOTIATION = 'negotiation';
    public const KIND_SALE = 'sale';
    public const KIND_CONTACT_REQUEST = 'contact_request';
    public const KIND_SUMMARY = 'summary';

    /**
     * @param  array<string, mixed>  $payload
     */
    public function __construct(
        private string $kind,
        private string $summary,
        private array $payload = [],
    ) {}

    public function via(object $notifiable): array
    {
        return ['database'];
    }

    public function toArray(object $notifiable): array
    {
        $titles = [
            self::KIND_NEGOTIATION => 'Négociation en cours',
            self::KIND_SALE => 'Accord conclu avec un client',
            self::KIND_CONTACT_REQUEST => 'Un client veut vous parler',
            self::KIND_SUMMARY => 'Compte-rendu de Tracy',
        ];

        return [
            'type' => 'tracy_report',
            'kind' => $this->kind,
            'title' => $titles[$this->kind] ?? 'Compte-rendu de Tracy',
            'message' => $this->summary,
            'customer_name' => $this->payload['customer_name'] ?? null,
            'customer_phone' => $this->payload['customer_phone'] ?? null,
            'product_name' => $this->payload['product_name'] ?? null,
            'conversation_id' => $this->payload['conversation_id'] ?? null,
            'color' => $this->kind === self::KIND_CONTACT_REQUEST ? 'orange' : 'blue',
        ];
    }
}
