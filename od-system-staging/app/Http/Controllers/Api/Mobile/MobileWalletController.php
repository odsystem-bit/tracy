<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Mobile;

use App\Http\Controllers\Controller;
use App\Models\Transaction;
use App\Models\Wallet;
use App\Services\Payment\PaymentService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

/**
 * MobileWalletController — API wallet pour l'application mobile MANTOTA.
 *
 * Gère :
 *  - Solde du wallet (balance, pending, escrow, withdrawable)
 *  - Historique des transactions
 *  - Demande de retrait (payout Moneroo)
 *  - Dépôt sur wallet (initialisation paiement Moneroo)
 */
class MobileWalletController extends Controller
{
    /**
     * GET /wallet/balance — Solde du wallet de l'utilisateur connecté.
     */
    public function balance(Request $request): JsonResponse
    {
        $user = $request->user();
        $wallet = $this->getOrCreateWallet($user->id);

        $withdrawable = (float) $wallet->balance;
        $pending = (float) $wallet->pending_balance;
        $escrow = (float) ($wallet->escrow_balance ?? 0);

        return response()->json([
            'balance'      => (float) $wallet->balance,
            'pending'      => $pending,
            'escrow'       => $escrow,
            'withdrawable' => $withdrawable,
            'is_locked'    => (bool) $wallet->is_locked,
            'lock_reason'  => $wallet->lock_reason,
        ]);
    }

    /**
     * GET /wallet/transactions — Historique des transactions.
     */
    public function transactions(Request $request): JsonResponse
    {
        $user = $request->user();

        $query = Transaction::where('user_id', $user->id)
            ->orderByDesc('created_at');

        if ($type = $request->input('type')) {
            $query->where('type', $type);
        }

        $transactions = $query->paginate(25);

        return response()->json([
            'data' => $transactions->items(),
            'meta' => [
                'current_page' => $transactions->currentPage(),
                'last_page'    => $transactions->lastPage(),
                'total'        => $transactions->total(),
            ],
        ]);
    }

    /**
     * POST /wallet/withdraw — Demande de retrait (payout Moneroo).
     */
    public function withdraw(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'amount'  => 'required|numeric|min:1000',
            'method'  => 'required|string|in:mtn_bj,moov_bj,mtn_ci,moov_ci,orange_ci,orange_sn,wave_ci,wave_sn,togocel,moov_tg',
            'account' => 'required|string|min:8|max:20',
        ]);

        $user = $request->user();
        $wallet = $this->getOrCreateWallet($user->id);

        if ($wallet->isLocked()) {
            return response()->json([
                'message' => 'Votre wallet est verrouillé : ' . ($wallet->lock_reason ?? 'raison non spécifiée'),
            ], 422);
        }

        $amount = (float) $validated['amount'];
        $withdrawable = (float) $wallet->balance;

        if ($amount > $withdrawable) {
            return response()->json([
                'message'      => 'Solde insuffisant pour ce retrait.',
                'withdrawable' => $withdrawable,
            ], 422);
        }

        $paymentService = app(PaymentService::class);
        $withdrawalCalc = $paymentService->calculateWithdrawal($amount);

        $reference = 'WTH-' . strtoupper(Str::random(12));

        $transaction = DB::transaction(function () use (
            $user, $amount, $validated, $withdrawalCalc, $reference, $wallet
        ) {
            // Bloquer les fonds immédiatement
            $wallet->decrement('balance', $amount);
            $wallet->increment('pending_balance', $amount);

            return Transaction::create([
                'user_id'         => $user->id,
                'type'            => 'withdrawal',
                'amount_target'   => $amount,
                'gateway_fee'     => $withdrawalCalc['gateway_fee'],
                'mantota_markup'  => $withdrawalCalc['mantota_commission'],
                'amount_total'    => $withdrawalCalc['net_payout'],
                'status'          => 'pending',
                'reference'       => $reference,
                'payment_gateway' => 'moneroo',
                'momo_number'     => $validated['account'],
                'description'     => 'Retrait vers ' . $validated['method'],
            ]);
        });

        // Initialiser le payout Moneroo
        $result = $paymentService->initializePayout([
            'amount'      => $withdrawalCalc['net_payout'],
            'currency'    => 'XOF',
            'description' => 'Retrait MANTOTA — ' . $reference,
            'customer'    => [
                'email'      => $user->email ?? '',
                'first_name' => $user->display_name ?? $user->name ?? '',
                'last_name'  => '',
            ],
            'method'    => $validated['method'],
            'recipient' => ['msisdn' => $validated['account']],
            'metadata'  => [
                'type'         => 'withdrawal',
                'transaction_id' => $transaction->id,
                'reference'    => $reference,
            ],
        ]);

        if (!$result['success']) {
            // Rembourser le wallet si le payout échoue
            $wallet->increment('balance', $amount);
            $wallet->decrement('pending_balance', $amount);
            $transaction->update(['status' => 'failed']);

            return response()->json([
                'message'      => 'Erreur lors du retrait.',
                'error_detail' => $result['message'] ?? '',
            ], 500);
        }

        $transaction->update([
            'gateway_ref' => $result['id'] ?? null,
            'status'      => 'processing',
        ]);

        return response()->json([
            'message'      => 'Demande de retrait en cours de traitement.',
            'reference'    => $reference,
            'net_payout'   => $withdrawalCalc['net_payout'],
            'fees'         => $withdrawalCalc['mantota_commission'] + $withdrawalCalc['gateway_fee'],
            'status'       => 'processing',
        ]);
    }

    /**
     * POST /wallet/deposit — Initialise un dépôt sur wallet (Moneroo).
     */
    public function deposit(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'amount' => 'required|numeric|min:1000',
        ]);

        $user = $request->user();
        $amount = (float) $validated['amount'];

        $paymentService = app(PaymentService::class);
        $depositCalc = $paymentService->calculateDeposit($amount);
        $reference = 'DEP-' . strtoupper(Str::random(12));

        $result = $paymentService->initializePayment([
            'amount'      => $depositCalc['amount_total'],
            'description' => 'Dépôt wallet MANTOTA — ' . $reference,
            'customer'    => [
                'first_name' => $user->display_name ?? $user->name ?? '',
                'email'      => $user->email ?? '',
                'phone'      => $user->phone ?? '',
            ],
            'return_url' => config('app.url') . '/wallet?status=deposit_complete',
            'metadata'   => [
                'type'         => 'wallet_deposit',
                'user_id'      => $user->id,
                'reference'    => $reference,
                'target_amount'=> $depositCalc['target_amount'],
            ],
        ]);

        if (!$result['success']) {
            return response()->json([
                'message'      => 'Erreur lors du dépôt.',
                'error_detail' => $result['message'] ?? '',
            ], 500);
        }

        // Pré-créer la transaction en pending
        Transaction::create([
            'user_id'         => $user->id,
            'type'            => 'deposit',
            'amount_target'   => $depositCalc['target_amount'],
            'gateway_fee'     => $depositCalc['gateway_fee'],
            'mantota_markup'  => $depositCalc['mantota_markup'],
            'amount_total'    => $depositCalc['amount_total'],
            'status'          => 'pending',
            'reference'       => $reference,
            'gateway_ref'     => $result['id'] ?? null,
            'payment_gateway' => 'moneroo',
            'description'     => 'Dépôt wallet',
        ]);

        return response()->json([
            'payment_id'   => $result['id'] ?? null,
            'checkout_url' => $result['checkout_url'] ?? null,
            'reference'    => $reference,
            'amount_total' => $depositCalc['amount_total'],
        ]);
    }

    /**
     * Récupère ou crée le wallet de l'utilisateur.
     */
    private function getOrCreateWallet(int $userId): Wallet
    {
        return Wallet::firstOrCreate(
            ['user_id' => $userId],
            [
                'balance'          => 0,
                'pending_balance'  => 0,
                'escrow_balance'   => 0,
                'referral_balance' => 0,
                'is_locked'        => false,
            ],
        );
    }
}
