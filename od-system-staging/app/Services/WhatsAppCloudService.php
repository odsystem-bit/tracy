<?php

declare(strict_types=1);

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class WhatsAppCloudService
{
    private string $accessToken;
    private string $phoneNumberId;
    private string $apiVersion;
    private string $baseUrl;

    public function __construct()
    {
        $this->accessToken = config('services.whatsapp.access_token', '');
        $this->phoneNumberId = config('services.whatsapp.phone_number_id', '');
        $this->apiVersion = config('services.whatsapp.api_version', 'v21.0');
        $this->baseUrl = "https://graph.facebook.com/{$this->apiVersion}";
    }

    public function sendText(string $to, string $message, ?string $phoneNumberId = null): array
    {
        // phoneNumberId = numéro du vendeur lié (whatsapp_connections) ; fallback = numéro global Mantota.
        $senderId = $phoneNumberId ?: $this->phoneNumberId;

        $response = Http::withToken($this->accessToken)
            ->post("{$this->baseUrl}/{$senderId}/messages", [
                'messaging_product' => 'whatsapp',
                'recipient_type' => 'individual',
                'to' => $to,
                'type' => 'text',
                'text' => [
                    'preview_url' => false,
                    'body' => $message,
                ],
            ]);

        if (!$response->successful()) {
            Log::error('WhatsApp sendText failed', [
                'to' => $to,
                'response' => $response->json(),
            ]);
        }

        return $response->json();
    }

    public function sendProductCard(string $to, string $productName, string $price, ?string $imageUrl = null, ?string $description = null, ?string $phoneNumberId = null): array
    {
        $body = $productName;
        if ($description) {
            $body .= "\n\n" . $description;
        }
        $body .= "\n\n💰 Prix : " . $price;
        // preview_url=true + URL dans le body → aperçu image de la fiche produit.
        if ($imageUrl) {
            $body .= "\n\n" . $imageUrl;
        }

        $payload = [
            'messaging_product' => 'whatsapp',
            'recipient_type' => 'individual',
            'to' => $to,
            'type' => 'text',
            'text' => [
                'preview_url' => true,
                'body' => $body,
            ],
        ];

        $response = Http::withToken($this->accessToken)
            ->post("{$this->baseUrl}/" . ($phoneNumberId ?: $this->phoneNumberId) . "/messages", $payload);

        return $response->json();
    }

    public function sendInteractiveList(string $to, string $headerText, string $bodyText, array $rows, ?string $phoneNumberId = null): array
    {
        $response = Http::withToken($this->accessToken)
            ->post("{$this->baseUrl}/" . ($phoneNumberId ?: $this->phoneNumberId) . "/messages", [
                'messaging_product' => 'whatsapp',
                'recipient_type' => 'individual',
                'to' => $to,
                'type' => 'interactive',
                'interactive' => [
                    'type' => 'list',
                    'header' => ['type' => 'text', 'text' => $headerText],
                    'body' => ['text' => $bodyText],
                    'action' => [
                        'button' => 'Voir les produits',
                        'sections' => [
                            [
                                'title' => 'Produits disponibles',
                                'rows' => $rows,
                            ],
                        ],
                    ],
                ],
            ]);

        return $response->json();
    }

    public function sendTemplate(string $to, string $templateName, array $components = []): array
    {
        $payload = [
            'messaging_product' => 'whatsapp',
            'recipient_type' => 'individual',
            'to' => $to,
            'type' => 'template',
            'template' => [
                'name' => $templateName,
                'language' => ['code' => 'fr'],
            ],
        ];

        if (!empty($components)) {
            $payload['template']['components'] = $components;
        }

        $response = Http::withToken($this->accessToken)
            ->post("{$this->baseUrl}/{$this->phoneNumberId}/messages", $payload);

        return $response->json();
    }

    public function markMessageRead(string $messageId): array
    {
        $response = Http::withToken($this->accessToken)
            ->post("{$this->baseUrl}/{$this->phoneNumberId}/messages", [
                'messaging_product' => 'whatsapp',
                'status' => 'read',
                'message_id' => $messageId,
            ]);

        return $response->json();
    }
}
