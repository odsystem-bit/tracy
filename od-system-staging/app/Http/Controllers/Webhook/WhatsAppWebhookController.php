<?php

declare(strict_types=1);

namespace App\Http\Controllers\Webhook;

use App\Http\Controllers\Controller;
use App\Models\Customer;
use App\Models\WhatsappConnection;
use App\Services\WhatsAppCloudService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class WhatsAppWebhookController extends Controller
{
    public function verify(Request $request): JsonResponse
    {
        $mode = $request->query('hub_mode');
        $token = $request->query('hub_verify_token');
        $challenge = $request->query('hub_challenge');

        $expectedToken = config('services.whatsapp.webhook_verify_token', 'mantota_verify_2026');

        if ($mode === 'subscribe' && $token === $expectedToken) {
            return response()->json((int) $challenge);
        }

        return response()->json(['message' => 'Verification failed'], 403);
    }

    public function handle(Request $request): JsonResponse
    {
        $payload = $request->all();

        Log::info('WhatsApp webhook received', ['payload' => $payload]);

        if (!isset($payload['entry'])) {
            return response()->json(['status' => 'no_entry']);
        }

        foreach ($payload['entry'] as $entry) {
            if (!isset($entry['changes'])) {
                continue;
            }

            foreach ($entry['changes'] as $change) {
                if (($change['field'] ?? null) !== 'messages') {
                    continue;
                }

                $value = $change['value'] ?? [];

                $this->processMessages($value);
            }
        }

        return response()->json(['status' => 'received']);
    }

    private function processMessages(array $value): void
    {
        $messages = $value['messages'] ?? [];
        $contacts = $value['contacts'] ?? [];
        $metadata = $value['metadata'] ?? [];

        if (empty($messages)) {
            return;
        }

        $phoneNumberId = $metadata['phone_number_id'] ?? null;

        $connection = WhatsappConnection::where('phone_number_id', $phoneNumberId)
            ->where('status', 'connected')
            ->first();

        if (!$connection || !$connection->canReceiveMessages()) {
            Log::info('WhatsApp message ignored — connection not active or limit reached', [
                'phone_number_id' => $phoneNumberId,
            ]);
            return;
        }

        $contactMap = [];
        foreach ($contacts as $contact) {
            $contactMap[$contact['wa_id']] = $contact;
        }

        foreach ($messages as $message) {
            $from = $message['from'] ?? null;
            $type = $message['type'] ?? 'unknown';
            $messageId = $message['id'] ?? null;

            if (!$from) {
                continue;
            }

            $contact = $contactMap[$from] ?? null;
            $customerName = $contact['profile']['name'] ?? null;

            $customer = Customer::findOrCreateByPhone($from, $connection->vendor_id, 'whatsapp');

            if ($customerName && !$customer->display_name) {
                $customer->update(['display_name' => $customerName]);
            }

            $customer->update(['last_seen_at' => now()]);

            $connection->increment('monthly_conversation_count');

            $textContent = $this->extractTextContent($message, $type);

            if ($textContent) {
                $this->forwardToTracyCore($connection, $customer, $textContent, $messageId);
            }
        }
    }

    private function extractTextContent(array $message, string $type): ?string
    {
        return match ($type) {
            'text' => $message['text']['body'] ?? null,
            'button' => $message['button']['text'] ?? null,
            'interactive' => $message['interactive']['button_reply']['id']
                ?? $message['interactive']['list_reply']['id']
                ?? null,
            'image' => '[Image reçue]', // TODO: télécharger et transcrire
            'audio' => '[Audio reçu]', // TODO: télécharger et transcrire via STT
            'voice' => '[Message vocal reçu]', // TODO: STT
            default => null,
        };
    }

    private function forwardToTracyCore(WhatsappConnection $connection, Customer $customer, string $text, ?string $waMessageId): void
    {
        $tracyCoreUrl = config('services.tracy_core.url', 'http://127.0.0.1:8001');
        $apiKey = config('services.tracy_core.api_key', '');

        try {
            $response = Http::withToken($apiKey)
                ->timeout(30)
                ->post("{$tracyCoreUrl}/chat", [
                    'message' => $text,
                    'customer_id' => $customer->customer_id,
                    'customer_name' => $customer->display_name,
                    'store_id' => (string) $connection->vendor_id,
                    'channel' => 'whatsapp',
                    'conversation_id' => 'wa_' . $customer->customer_id . '_' . $connection->vendor_id,
                ]);

            if ($response->successful()) {
                $reply = $response->json();
                $replyText = $reply['reply'] ?? $reply['message'] ?? null;

                if ($replyText) {
                    $whatsapp = app(WhatsAppCloudService::class);
                    $whatsapp->sendText($customer->phone, $replyText, $connection->phone_number_id);
                    $this->sendProductCards($whatsapp, $connection, $customer, $reply['cards'] ?? []);
                }
            } else {
                Log::error('Tracy Core request failed', [
                    'status' => $response->status(),
                    'body' => $response->body(),
                ]);
            }
        } catch (\Exception $e) {
            Log::error('Tracy Core connection error', [
                'error' => $e->getMessage(),
            ]);
        }
    }

    /**
     * Envoie les produits retournés par Tracy (catalogue) sur WhatsApp :
     * - 1 produit → fiche produit texte avec aperçu d'image
     * - plusieurs → liste interactive "Voir les produits"
     */
    private function sendProductCards(
        WhatsAppCloudService $whatsapp,
        WhatsappConnection $connection,
        Customer $customer,
        array $cards,
    ): void {
        if (empty($cards)) {
            return;
        }

        $phoneNumberId = $connection->phone_number_id;

        if (count($cards) === 1) {
            $c = $cards[0];
            $whatsapp->sendProductCard(
                $customer->phone,
                $c['name'] ?? 'Produit',
                $c['price'] ?? ($c['raw_price'] ?? '') . ' FCFA',
                $c['image_url'] ?? null,
                $c['description'] ?? null,
                $phoneNumberId,
            );
            return;
        }

        $rows = [];
        foreach (array_slice($cards, 0, 10) as $c) {
            $rows[] = [
                'id' => 'product_' . ($c['id'] ?? count($rows)),
                'title' => mb_substr($c['name'] ?? 'Produit', 0, 24),
                'description' => mb_substr(($c['price'] ?? '') . ' — tape le nom pour commander', 0, 72),
            ];
        }

        $whatsapp->sendInteractiveList(
            $customer->phone,
            'Catalogue',
            'Voici les produits trouvés. Télécharge l\'app Mantota pour commander directement : https://mantota.com/app',
            $rows,
            $phoneNumberId,
        );
    }
}
