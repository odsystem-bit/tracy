<?php

declare(strict_types=1);

namespace App\Http\Controllers\Payment;

use App\Http\Controllers\Controller;
use App\Models\Transaction;
use App\Models\Wallet;
use App\Services\Payment\PaymentService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Symfony\Component\HttpFoundation\Response as SymfonyResponse;

/**
 * DepositController — Point d'entrée unique pour les dépôts via Moneroo.
 */
class DepositController extends Controller
{
    public function __invoke(Request $request): SymfonyResponse
    {
        $validated = $request->validate([
            'amount_target' => ['required', 'numeric', 'min:' . (int) mantota_setting('min_deposit_amount', 1000)],
        ], [
            'amount_target.required' => 'Le montant est obligatoire.',
            'amount_target.numeric'  => 'Le montant doit être un nombre.',
            'amount_target.min'      => 'Le montant minimum est ' . mantota_setting('min_deposit_amount', 1000) . ' XOF.',
        ]);

        $user = auth()->user();
        $service = app(PaymentService::class);

        if (! $service->isConfigured()) {
            $msg = 'Configuration Moneroo incomplete. Contactez l\'administration.';
            return $request->wantsJson()
                ? response()->json(['message' => $msg], 422)
                : back()->withErrors(['payment' => $msg]);
        }

        try {
            $breakdown = $service->calculateDeposit((float) $validated['amount_target']);

            $transaction = Transaction::create([
                'user_id'         => $user->id,
                'type'            => 'deposit',
                'amount_target'   => $breakdown['target_amount'],
                'gateway_fee'     => $breakdown['gateway_fee'],
                'mantota_markup'  => $breakdown['mantota_markup'],
                'amount_total'    => $breakdown['amount_total'],
                'status'          => 'pending',
                'reference'       => 'DEP-' . uniqid('', true),
                'payment_gateway' => 'moneroo',
                'description'     => 'Recharge compte via Moneroo',
            ]);

            $result = $service->initializePayment([
                'amount'      => (int) ceil((float) $transaction->amount_total),
                'description' => $transaction->description,
                'customer'    => [
                    'first_name' => $user->name ?? 'Client',
                    'email'      => $user->email ?? '',
                    'phone'      => $user->phone ?? '',
                ],
                'return_url'  => route('deposit.callback', ['reference' => $transaction->reference]),
                'metadata'    => [
                    'type'      => 'deposit',
                    'reference' => $transaction->reference,
                ],
            ]);

            if (! $result['success']) {
                $transaction->update(['status' => 'failed']);
                $msg = 'Erreur Moneroo : ' . ($result['message'] ?? 'impossible d\'initier le paiement.');
                return $request->wantsJson()
                    ? response()->json(['message' => $msg], 422)
                    : back()->withErrors(['payment' => $msg]);
            }

            $transaction->update(['gateway_ref' => $result['id']]);

            if ($request->wantsJson()) {
                return response()->json([
                    'transaction_id' => $transaction->id,
                    'checkout_url'   => $result['checkout_url'],
                    'gateway'        => 'moneroo',
                ]);
            }

            return redirect()->away($result['checkout_url']);

        } catch (\Throwable $e) {
            Log::error('Deposit initiation exception', [
                'user_id' => $user->id,
                'error'   => $e->getMessage(),
                'file'    => $e->getFile() . ':' . $e->getLine(),
            ]);

            $msg = 'Une erreur technique est survenue. Veuillez réessayer.';
            return $request->wantsJson()
                ? response()->json(['message' => $msg], 422)
                : back()->withErrors(['payment' => $msg]);
        }
    }

    /**
     * Vérifie le statut d'un dépôt (polling côté client).
     */
    public function checkStatus(Request $request, Transaction $transaction): JsonResponse
    {
        if ((int) $transaction->user_id !== (int) auth()->id()) {
            return response()->json(['status' => 'not_found'], 403);
        }

        if ($transaction->status !== 'pending') {
            return response()->json(['status' => $transaction->status]);
        }

        if ($transaction->gateway_ref) {
            $credited = self::verifyAndCredit($transaction);
            if ($credited) {
                return response()->json(['status' => 'completed']);
            }
        }

        return response()->json(['status' => $transaction->status]);
    }

    /**
     * Vérification active via Moneroo + crédit wallet.
     */
    public static function verifyAndCredit(Transaction $transaction): bool
    {
        if ($transaction->status !== 'pending' || ! $transaction->gateway_ref) {
            return false;
        }

        try {
            $service = app(PaymentService::class);
            $verification = $service->verifyPayment($transaction->gateway_ref);

            if (! $verification['success'] || $verification['status'] !== 'success') {
                if ($verification['status'] === 'failed') {
                    $transaction->update(['status' => 'failed']);
                }
                return false;
            }

            $received = round((float) ($verification['amount'] ?? 0), 2);
            $expected = round((float) $transaction->amount_total, 2);
            if ($received < $expected) {
                Log::error('Deposit amount mismatch', [
                    'transaction_id' => $transaction->id,
                    'expected'       => $expected,
                    'received'       => $received,
                ]);
                return false;
            }

            self::creditWallet($transaction);
            return true;
        } catch (\Throwable $e) {
            Log::error('Moneroo deposit verification error', [
                'txn_id' => $transaction->id,
                'error'  => $e->getMessage(),
            ]);
            return false;
        }
    }

    private static function creditWallet(Transaction $transaction): void
    {
        DB::transaction(function () use ($transaction): void {
            $tx = Transaction::where('id', $transaction->id)
                ->lockForUpdate()
                ->firstOrFail();

            if ($tx->status === 'completed') {
                return;
            }

            $wallet = Wallet::where('user_id', $tx->user_id)
                ->lockForUpdate()
                ->firstOrFail();

            $wallet->balance = (float) $wallet->balance + (float) $tx->amount_target;
            $wallet->save();

            $tx->status = 'completed';
            $tx->save();
        });

        Cache::forget('admin.dashboard');

        Log::info('Deposit credited', [
            'transaction_id' => $transaction->id,
            'user_id'        => $transaction->user_id,
            'gateway'        => $transaction->payment_gateway,
            'amount'         => $transaction->amount_target,
        ]);
    }
}
