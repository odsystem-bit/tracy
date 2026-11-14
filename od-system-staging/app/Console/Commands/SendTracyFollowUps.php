<?php

declare(strict_types=1);

namespace App\Console\Commands;

use App\Models\TracyFollowUp;
use App\Models\User;
use App\Models\WhatsappConnection;
use App\Notifications\TracyFollowUpNotification;
use App\Services\WhatsAppCloudService;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Log;

/**
 * Envoie les relances client planifiées par Tracy (post-négociation).
 * - channel "whatsapp" : message envoyé au téléphone du client depuis le numéro
 *   WhatsApp Business lié du vendeur (whatsapp_connections.phone_number_id).
 * - channel "app" : notification in-app au client connecté (id utilisateur).
 */
class SendTracyFollowUps extends Command
{
    protected $signature = 'mantota:send-tracy-follow-ups';

    protected $description = 'Envoie les relances client Tracy arrivées à échéance';

    public function handle(WhatsAppCloudService $whatsapp): int
    {
        $due = TracyFollowUp::where('status', 'pending')
            ->where('send_at', '<=', now())
            ->orderBy('send_at')
            ->limit(50)
            ->get();

        if ($due->isEmpty()) {
            return self::SUCCESS;
        }

        foreach ($due as $followUp) {
            try {
                $ok = $followUp->channel === 'whatsapp'
                    ? $this->sendWhatsapp($whatsapp, $followUp)
                    : $this->sendAppNotification($followUp);

                $followUp->update([
                    'status' => $ok ? 'sent' : 'failed',
                    'sent_at' => $ok ? now() : null,
                ]);
            } catch (\Throwable $e) {
                Log::error('TracyFollowUp send failed', [
                    'id' => $followUp->id,
                    'error' => $e->getMessage(),
                ]);
                $followUp->update(['status' => 'failed']);
            }
        }

        return self::SUCCESS;
    }

    private function sendWhatsapp(WhatsAppCloudService $whatsapp, TracyFollowUp $followUp): bool
    {
        $connection = WhatsappConnection::where('vendor_id', $followUp->vendor_id)
            ->where('status', 'connected')
            ->first();

        if (! $connection || ! $connection->phone_number_id) {
            Log::info('TracyFollowUp skipped — pas de numéro WhatsApp lié', [
                'id' => $followUp->id,
                'vendor_id' => $followUp->vendor_id,
            ]);
            return false;
        }

        $result = $whatsapp->sendText(
            $followUp->customer_id,
            $followUp->message,
            $connection->phone_number_id,
        );

        return isset($result['messages'][0]['id']);
    }

    private function sendAppNotification(TracyFollowUp $followUp): bool
    {
        $client = User::find((int) $followUp->customer_id);
        if (! $client) {
            return false;
        }

        $client->notify(new TracyFollowUpNotification(
            $followUp->message,
            (string) $followUp->vendor_id,
        ));

        return true;
    }
}
