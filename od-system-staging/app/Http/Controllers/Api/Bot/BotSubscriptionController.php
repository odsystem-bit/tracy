<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\BotSubscription;
use App\Models\Transaction;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class BotSubscriptionController extends Controller
{
    /**
     * POST /bot/subscriptions/tracy
     * Active ou renouvelle un abonnement Tracy pour un vendeur.
     */
    public function activate(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'vendor_id' => 'required|exists:users,id',
            'plan' => 'required|string|in:starter,standard,pro,tpf',
        ]);

        $planDurations = [
            'starter' => 30,
            'standard' => 30,
            'pro' => 30,
            'tpf' => 365,
        ];

        $planPrices = [
            'starter' => 2500,
            'standard' => 12000,
            'pro' => 25000,
            'tpf' => 50000,
        ];

        $days = $planDurations[$validated['plan']] ?? 30;
        $price = $planPrices[$validated['plan']] ?? 0;

        $reference = 'SUB-' . strtoupper(Str::random(10));

        $subscription = BotSubscription::create([
            'vendor_id' => $validated['vendor_id'],
            'plan' => $validated['plan'],
            'status' => 'active',
            'reference_transaction' => $reference,
            'expires_at' => now()->addDays($days),
        ]);

        Transaction::create([
            'user_id' => $validated['vendor_id'],
            'type' => 'subscription',
            'amount_target' => $price,
            'gateway_fee' => 0,
            'mantota_markup' => $price,
            'amount_total' => $price,
            'status' => 'paid',
            'reference' => $reference,
            'description' => 'Abonnement Tracy ' . $validated['plan'],
        ]);

        return response()->json([
            'statut' => 'active',
            'date_expiration' => $subscription->expires_at->toIso8601String(),
            'reference_transaction' => $reference,
        ]);
    }
}
