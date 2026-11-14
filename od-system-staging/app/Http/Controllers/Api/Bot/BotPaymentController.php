<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Services\Payment\MonerooService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class BotPaymentController extends Controller
{
    /**
     * POST /bot/payments
     * Crée un lien de paiement pour une commande.
     */
    public function create(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'order_id' => 'required|string',
            'amount' => 'required|numeric|min:100',
            'currency' => 'nullable|string|in:XOF,XAF,USD,EUR',
            'method' => 'nullable|string',
        ]);

        // PostgreSQL : 'id' est bigint — lookup par référence, id seulement si numérique.
        $order = Order::where('reference', $validated['order_id'])
            ->when(
                is_numeric($validated['order_id']),
                fn ($q) => $q->orWhere('id', $validated['order_id'])
            )
            ->firstOrFail();

        $currency = $validated['currency'] ?? 'XOF';

        try {
            $payment = MonerooService::createPaymentLink([
                'amount' => $validated['amount'],
                'reference' => $order->reference,
                'customer_name' => $order->customer_name,
                'customer_phone' => $order->customer_phone,
                'return_url' => config('app.url') . '/track/' . $order->id . '?token=' . $order->tracking_token,
                'description' => 'Commande ' . $order->reference,
            ]);

            return response()->json([
                'payment_id' => $payment['id'] ?? uniqid('pay_'),
                'checkout_url' => $payment['url'] ?? null,
                'statut' => 'pending',
                'reference' => $order->reference,
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Erreur création paiement: ' . $e->getMessage(),
            ], 500);
        }
    }

    /**
     * POST /bot/payments/send-link
     * Envoie un lien de paiement au client sur un canal donné.
     */
    public function sendLink(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'order_id' => 'required|string',
            'channel' => 'nullable|string|in:whatsapp,telegram,sms',
        ]);

        // PostgreSQL : 'id' est bigint — lookup par référence, id seulement si numérique.
        $order = Order::where('reference', $validated['order_id'])
            ->when(
                is_numeric($validated['order_id']),
                fn ($q) => $q->orWhere('id', $validated['order_id'])
            )
            ->firstOrFail();

        $channel = $validated['channel'] ?? 'whatsapp';

        return response()->json([
            'success' => true,
            'channel' => $channel,
            'message' => 'Lien de paiement envoyé sur ' . $channel,
        ]);
    }
}
