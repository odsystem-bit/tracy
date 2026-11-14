<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Enums\OrderStatus;
use App\Http\Controllers\Controller;
use App\Models\Order;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class BotOrderTrackingController extends Controller
{
    /**
     * GET /bot/orders/{id}/track
     * Suivi d'une commande avec historique des statuts.
     */
    public function track(string $id): JsonResponse
    {
        // PostgreSQL : 'id' est bigint — ne le comparer que si $id est numérique,
        // sinon la requête échoue (22P02) sur une référence CMD-XXX.
        $order = Order::with(['product', 'vendor'])
            ->where('reference', $id)
            ->when(is_numeric($id), fn ($q) => $q->orWhere('id', $id))
            ->firstOrFail();

        $historique = collect();

        if ($order->created_at) {
            $historique->push([
                'statut' => 'pending',
                'date' => $order->created_at->toIso8601String(),
                'note' => 'Commande créée',
            ]);
        }

        if ($order->status !== OrderStatus::PENDING) {
            $historique->push([
                'statut' => $order->status->value,
                'date' => $order->updated_at->toIso8601String(),
                'note' => $order->status->label(),
            ]);
        }

        return response()->json([
            'order_id' => (string) $order->id,
            'statut' => $order->status->value,
            'historique' => $historique,
            'date_estimee_livraison' => $order->delivery_deadline?->toIso8601String(),
        ]);
    }

    /**
     * POST /bot/orders/{id}/cancel
     * Annule une commande (uniquement si PENDING).
     */
    public function cancel(Request $request, string $id): JsonResponse
    {
        $validated = $request->validate([
            'reason' => 'required|string|max:500',
        ]);

        // Même garde PostgreSQL : id bigint vs référence texte.
        $order = Order::where('reference', $id)
            ->when(is_numeric($id), fn ($q) => $q->orWhere('id', $id))
            ->firstOrFail();

        if (! in_array($order->status, [OrderStatus::PENDING, OrderStatus::DISPUTED])) {
            return response()->json([
                'error' => 'Commande non annulable (statut: ' . $order->status->value . ')',
            ], 422);
        }

        $order->update([
            'status' => OrderStatus::CANCELLED,
            'cancel_reason' => $validated['reason'],
        ]);

        // Libérer le stock si produit physique
        if ($order->product && $order->product->isPhysical()) {
            $order->product->increment('stock');
        }

        return response()->json([
            'success' => true,
            'order_id' => (string) $order->id,
            'statut' => 'cancelled',
        ]);
    }
}
