<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Mobile;

use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\OrderDisputeMessage;
use App\Enums\OrderStatus;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;

/**
 * MobileDisputeController — API litiges pour l'application mobile MANTOTA.
 *
 * Gère :
 *  - Ouverture de litige sur une commande
 *  - Liste des litiges de l'utilisateur
 *  - Détail d'un litige avec messages
 *  - Envoi de messages / preuves dans le litige
 *  - Défense du vendeur
 */
class MobileDisputeController extends Controller
{
    /**
     * GET /disputes — Liste des litiges de l'utilisateur (acheteur ou vendeur).
     */
    public function index(Request $request): JsonResponse
    {
        $user = $request->user();

        $query = Order::query()
            ->where('status', OrderStatus::DISPUTED)
            ->where(function ($q) use ($user) {
                $q->where('vendor_id', $user->id)
                  ->orWhere('influencer_id', $user->id)
                  ->orWhere('customer_phone', $user->phone);
            })
            ->with(['product:id,name', 'vendor:id,name,shop_name', 'influencer:id,name'])
            ->orderByDesc('updated_at');

        $disputes = $query->paginate(20);

        return response()->json([
            'data' => $disputes->items(),
            'meta' => [
                'current_page' => $disputes->currentPage(),
                'last_page'    => $disputes->lastPage(),
                'total'        => $disputes->total(),
            ],
        ]);
    }

    /**
     * GET /disputes/{orderId} — Détail d'un litige avec les messages.
     */
    public function show(Request $request, string $orderId): JsonResponse
    {
        $user = $request->user();

        $order = Order::where('id', $orderId)
            ->orWhere('reference', $orderId)
            ->with(['product', 'vendor:id,name,shop_name,phone', 'influencer:id,name'])
            ->first();

        if (!$order) {
            return response()->json(['message' => 'Commande introuvable.'], 404);
        }

        $isInvolved = $order->vendor_id === $user->id
            || $order->influencer_id === $user->id
            || $order->customer_phone === $user->phone;

        if (!$isInvolved) {
            return response()->json(['message' => 'Accès non autorisé.'], 403);
        }

        $messages = $order->disputeMessages()
            ->orderBy('created_at')
            ->get()
            ->map(fn ($msg) => [
                'id'         => $msg->id,
                'sender_id'  => $msg->sender_id,
                'sender_role'=> $msg->sender_role,
                'message'    => $msg->message,
                'attachment' => $msg->attachment_path ? Storage::url($msg->attachment_path) : null,
                'is_flagged' => $msg->is_flagged ?? false,
                'created_at' => $msg->created_at?->toIso8601String(),
            ]);

        return response()->json([
            'order'    => $order,
            'dispute_reason'  => $order->dispute_reason,
            'dispute_opened_at' => $order->updated_at?->toIso8601String(),
            'vendor_defense' => $order->vendor_defense_message,
            'messages' => $messages,
        ]);
    }

    /**
     * POST /disputes/{orderId}/messages — Envoie un message dans le litige.
     */
    public function sendMessage(Request $request, string $orderId): JsonResponse
    {
        $validated = $request->validate([
            'message'     => 'required|string|min:1|max:2000',
            'attachment'  => 'nullable|file|max:5120', // 5MB max
        ]);

        $user = $request->user();

        $order = Order::where('id', $orderId)
            ->orWhere('reference', $orderId)
            ->first();

        if (!$order) {
            return response()->json(['message' => 'Commande introuvable.'], 404);
        }

        if ($order->status !== OrderStatus::DISPUTED) {
            return response()->json(['message' => 'Aucun litige actif sur cette commande.'], 422);
        }

        $isInvolved = $order->vendor_id === $user->id
            || $order->influencer_id === $user->id
            || $order->customer_phone === $user->phone;

        if (!$isInvolved) {
            return response()->json(['message' => 'Accès non autorisé.'], 403);
        }

        $senderRole = $order->vendor_id === $user->id ? 'vendor' : 'buyer';

        $attachmentPath = null;
        if ($request->hasFile('attachment')) {
            $attachmentPath = $request->file('attachment')->store('dispute-attachments', 'public');
        }

        $message = OrderDisputeMessage::create([
            'order_id'        => $order->id,
            'sender_id'       => $user->id,
            'sender_role'     => $senderRole,
            'message'         => $validated['message'],
            'attachment_path' => $attachmentPath,
        ]);

        // Si c'est le vendeur qui répond pour la première fois, enregistrer sa défense
        if ($senderRole === 'vendor' && empty($order->vendor_defense_message)) {
            $order->update(['vendor_defense_message' => $validated['message']]);
        }

        return response()->json([
            'id'         => $message->id,
            'message'    => $message->message,
            'sender_role'=> $message->sender_role,
            'attachment' => $attachmentPath ? Storage::url($attachmentPath) : null,
            'created_at' => $message->created_at?->toIso8601String(),
        ], 201);
    }

    /**
     * POST /disputes/{orderId}/resolve — L'acheteur accepte de résoudre (fermer) le litige.
     */
    public function resolve(Request $request, string $orderId): JsonResponse
    {
        $user = $request->user();

        $order = Order::where('id', $orderId)
            ->orWhere('reference', $orderId)
            ->first();

        if (!$order) {
            return response()->json(['message' => 'Commande introuvable.'], 404);
        }

        if ($order->status !== OrderStatus::DISPUTED) {
            return response()->json(['message' => 'Aucun litige actif.'], 422);
        }

        $isBuyer = $order->influencer_id === $user->id || $order->customer_phone === $user->phone;
        if (!$isBuyer) {
            return response()->json(['message' => 'Seul l\'acheteur peut clôturer le litige.'], 403);
        }

        $order->update(['status' => OrderStatus::DISPUTED_RESOLVED]);

        return response()->json([
            'message' => 'Litige clôturé. L\'équipe MANTOTA finalisera le traitement.',
            'order'   => $order->fresh(),
        ]);
    }
}
