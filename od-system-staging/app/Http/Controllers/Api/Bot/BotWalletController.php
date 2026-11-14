<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\Transaction;
use App\Models\Wallet;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class BotWalletController extends Controller
{
    /**
     * GET /bot/wallet/{userId}
     * Récupère le wallet d'un utilisateur avec ses dernières transactions.
     */
    public function show(string $userId): JsonResponse
    {
        $wallet = Wallet::where('user_id', $userId)->first();

        if (! $wallet) {
            return response()->json(['error' => 'Wallet non trouvé'], 404);
        }

        $transactions = Transaction::where('user_id', $userId)
            ->orderByDesc('created_at')
            ->limit(10)
            ->get();

        return response()->json([
            'user_id' => (string) $wallet->user_id,
            'solde_disponible' => (float) $wallet->balance,
            'solde_en_attente' => (float) ($wallet->pending_balance + $wallet->escrow_balance),
            'dernieres_transactions' => $transactions->map(fn (Transaction $t) => [
                'id' => (string) $t->id,
                'type' => $t->type,
                'montant' => (float) $t->amount_total,
                'statut' => $t->status,
                'reference' => $t->reference,
                'created_at' => $t->created_at?->toIso8601String(),
            ]),
        ]);
    }

    /**
     * POST /bot/wallet/withdraw
     * Demande de retrait depuis le wallet.
     */
    public function withdraw(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'user_id' => 'required|string',
            'amount' => 'required|numeric|min:1000',
            'payout_method' => 'required|string|in:momo,bank,cash',
            'phone' => 'required|string',
            'country' => 'required|string',
        ]);

        $wallet = Wallet::where('user_id', $validated['user_id'])->first();

        if (! $wallet) {
            return response()->json(['error' => 'Wallet non trouvé'], 404);
        }

        if ((float) $wallet->balance < $validated['amount']) {
            return response()->json(['error' => 'Solde insuffisant'], 422);
        }

        if ($wallet->isLocked()) {
            return response()->json(['error' => 'Wallet verrouillé: ' . $wallet->lock_reason], 422);
        }

        $reference = 'WD-' . strtoupper(Str::random(10));

        Transaction::create([
            'user_id' => $validated['user_id'],
            'type' => 'withdrawal',
            'amount_target' => $validated['amount'],
            'gateway_fee' => 0,
            'mantota_markup' => 0,
            'amount_total' => $validated['amount'],
            'status' => 'pending',
            'reference' => $reference,
            'payment_gateway' => $validated['payout_method'],
            'momo_number' => $validated['phone'],
            'description' => 'Retrait ' . $validated['payout_method'] . ' (' . $validated['country'] . ')',
        ]);

        // Bloquer les fonds immédiatement
        $wallet->decrement('balance', $validated['amount']);
        $wallet->increment('pending_balance', $validated['amount']);

        return response()->json([
            'reference' => $reference,
            'statut' => 'pending',
            'montant' => (float) $validated['amount'],
        ]);
    }
}
