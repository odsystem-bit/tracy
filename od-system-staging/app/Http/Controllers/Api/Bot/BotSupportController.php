<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Enums\OrderStatus;
use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\OrderDisputeMessage;
use App\Notifications\DisputeOpenedNotification;
use App\Models\SupportTicket;
use App\Models\TicketMessage;
use App\Services\ChatModeratorService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class BotSupportController extends Controller
{
    /**
     * POST /bot/support/tickets
     * Créer un ticket support (guest ou connecté) depuis Tracy Core.
     */
    public function store(Request $request): JsonResponse
    {
        $validated = Validator::make($request->all(), [
            'subject'       => ['required', 'string', 'max:255'],
            'category'      => ['required', 'in:bug,paiement,question,litige,signalement,autre'],
            'message'       => ['required', 'string', 'max:5000'],
            'guest_name'    => ['nullable', 'string', 'max:100'],
            'guest_email'   => ['nullable', 'email', 'max:255'],
            'customer_id'   => ['nullable', 'string', 'max:255'],
            'store_id'      => ['nullable', 'string', 'max:255'],
        ])->validate();

        $guestName = $validated['guest_name'] ?? 'Visiteur';
        $guestEmail = $validated['guest_email'] ?? 'guest@chat.mantota';
        $customerId = $validated['customer_id'] ?? null;

        $moderation = app(ChatModeratorService::class)->moderate(
            $validated['message'],
            'Support (chat)',
            $guestName
        );

        $ticket = SupportTicket::create([
            'user_id'        => null,
            'guest_name'     => $guestName,
            'guest_email'    => $guestEmail,
            'reference_code' => SupportTicket::generateReference(),
            'subject'        => $validated['subject'],
            'category'       => $validated['category'],
            'status'         => 'open',
        ]);

        TicketMessage::create([
            'support_ticket_id' => $ticket->id,
            'user_id'           => null,
            'is_admin'          => false,
            'body'              => $moderation['text'],
            'is_flagged'        => $moderation['is_flagged'],
            'original_message'  => $moderation['original_message'],
        ]);

        return response()->json([
            'success'        => true,
            'reference_code' => $ticket->reference_code,
            'ticket_id'      => $ticket->id,
            'track_url'      => url('/support/track'),
        ]);
    }

    /**
     * POST /bot/disputes
     * Créer un litige guest depuis Tracy Core.
     */
    public function createDispute(Request $request): JsonResponse
    {
        $validated = Validator::make($request->all(), [
            'order_reference' => ['required', 'string', 'max:50'],
            'reason'          => ['required', 'string', 'max:2000'],
            'customer_id'     => ['nullable', 'string', 'max:255'],
        ])->validate();

        $order = Order::where('reference', $validated['order_reference'])->first();

        if (! $order) {
            return response()->json([
                'success' => false,
                'error'   => 'Commande introuvable.',
            ], 404);
        }

        // Litige déjà ouvert → réponse idempotente
        if ($order->status === OrderStatus::DISPUTED) {
            return response()->json([
                'success'    => true,
                'dispute_id' => $order->id,
                'status'     => $order->status->value,
                'track_url'  => url("/track/{$order->id}?token={$order->tracking_token}"),
            ]);
        }

        // Le litige n'est possible que sur une commande en cours
        if (! in_array($order->status, [OrderStatus::PENDING, OrderStatus::SHIPPED], true)) {
            return response()->json([
                'success' => false,
                'error'   => 'Le signalement n\'est pas possible pour cette commande.',
            ], 422);
        }

        $order->update([
            'status'         => OrderStatus::DISPUTED,
            'dispute_reason' => $validated['reason'],
        ]);

        // Notifier le vendeur
        try {
            $order->vendor?->notify(new DisputeOpenedNotification($order));
        } catch (\Throwable $e) {
            \Illuminate\Support\Facades\Log::warning('Bot dispute vendor notify failed: ' . $e->getMessage());
        }

        // Premier message dans le chat de litige
        OrderDisputeMessage::create([
            'order_id'    => $order->id,
            'sender_type' => 'customer',
            'user_id'     => null,
            'message'     => $validated['reason'],
        ]);

        return response()->json([
            'success'    => true,
            'dispute_id' => $order->id,
            'status'     => $order->status->value,
            'track_url'  => url("/track/{$order->id}?token={$order->tracking_token}"),
        ]);
    }
}
