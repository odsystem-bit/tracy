<?php

declare(strict_types=1);

namespace App\Http\Controllers\Webhook;

use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\Transaction;
use App\Models\Wallet;
use App\Services\Payment\PaymentService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

class MonerooWebhookController extends Controller
{
    /**
     * Webhook unique pour Moneroo : paiements, échecs, payouts.
     */
    public function handle(Request $request): JsonResponse
    {
        $payload = $request->getContent();
        $signature = $request->header('X-Moneroo-Signature');

        $service = app(PaymentService::class);

        if (! $service->isConfigured()) {
            Log::error('Moneroo webhook : configuration manquante');
            return response()->json(['error' => 'Configuration manquante'], 500);
        }

        if (! $service->verifyWebhookSignature($payload, (string) $signature)) {
            Log::warning('Moneroo webhook : signature invalide');
            return response()->json(['error' => 'Signature invalide'], 403);
        }

        $data = $request->json()->all();
        $event = $data['event'] ?? 'unknown';
        $paymentId = $data['data']['id'] ?? null;

        Log::info('Moneroo webhook reçu', ['event' => $event, 'payment_id' => $paymentId]);

        return match ($event) {
            'payment.success' => $this->handlePaymentSuccess($data, $service, $paymentId),
            'payment.failed', 'payment.cancelled' => $this->handlePaymentFailed($data),
            'payout.success'  => $this->handlePayoutSuccess($data, $service, $paymentId),
            'payout.failed'   => $this->handlePayoutFailed($data),
            default           => response()->json(['ok' => true]),
        };
    }

    private function handlePaymentSuccess(array $data, PaymentService $service, ?string $paymentId): JsonResponse
    {
        $metadata = $data['data']['metadata'] ?? [];
        $type = $metadata['type'] ?? null;
        $reference = $metadata['reference'] ?? null;

        if (! $paymentId) {
            return response()->json(['error' => 'ID Moneroo manquant'], 400);
        }

        // Double vérification via API
        $verification = $service->verifyPayment($paymentId);
        if (! $verification['success'] || $verification['status'] !== 'success') {
            Log::warning('Moneroo webhook : vérification API échouée', [
                'payment_id' => $paymentId,
                'verification' => $verification,
            ]);
            return response()->json(['error' => 'Vérification échouée'], 400);
        }

        return match ($type) {
            'order'   => $this->creditOrder($reference, $paymentId, $verification),
            'deposit' => $this->creditDeposit($reference, $paymentId, $verification),
            default   => response()->json(['error' => 'Type de paiement inconnu'], 400),
        };
    }

    private function handlePaymentFailed(array $data): JsonResponse
    {
        $metadata = $data['data']['metadata'] ?? [];
        $type = $metadata['type'] ?? null;
        $reference = $metadata['reference'] ?? null;

        if ($type === 'order' && $reference) {
            $order = Order::where('reference', $reference)->first();
            if ($order && $order->payment_status === 'awaiting') {
                $this->restoreOrderStock($order);
                $order->update(['payment_status' => 'failed']);
            }
        }

        if ($type === 'deposit' && $reference) {
            $transaction = Transaction::where('reference', $reference)->first();
            if ($transaction && $transaction->status === 'pending') {
                $transaction->update(['status' => 'failed']);
            }
        }

        return response()->json(['ok' => true]);
    }

    private function creditOrder(?string $reference, string $paymentId, array $verification): JsonResponse
    {
        if (! $reference) {
            return response()->json(['error' => 'Référence commande manquante'], 400);
        }

        $order = Order::where('reference', $reference)->first();

        if (! $order) {
            Log::warning('Moneroo webhook : commande introuvable', ['reference' => $reference]);
            return response()->json(['error' => 'Commande introuvable'], 404);
        }

        if ($order->payment_status === 'paid') {
            return response()->json(['ok' => true]);
        }

        DB::transaction(function () use ($order, $paymentId, $verification): void {
            $lockedOrder = Order::where('id', $order->id)->lockForUpdate()->firstOrFail();

            if ($lockedOrder->payment_status === 'paid') {
                return;
            }

            $expected = round((float) $lockedOrder->amount_paid, 2);
            $received = round((float) ($verification['amount'] ?? 0), 2);
            if ($received < $expected) {
                Log::error('Moneroo webhook : montant incorrect', [
                    'order_id' => $lockedOrder->id,
                    'expected' => $expected,
                    'received' => $received,
                ]);
                throw new \RuntimeException('Montant reçu inférieur au montant attendu');
            }

            $lockedOrder->update([
                'payment_status'      => 'paid',
                'payment_gateway'     => 'moneroo',
                'payment_gateway_ref' => $paymentId,
            ]);

            $vendorWallet = Wallet::where('user_id', $lockedOrder->vendor_id)->lockForUpdate()->firstOrFail();
            $vendorWallet->escrow_balance = (float) $vendorWallet->escrow_balance + (float) $lockedOrder->vendor_earnings;
            $vendorWallet->save();

            if ($lockedOrder->influencer_id && (float) $lockedOrder->commission_amount > 0) {
                $influencerWallet = Wallet::where('user_id', $lockedOrder->influencer_id)->lockForUpdate()->first();
                if ($influencerWallet) {
                    $influencerWallet->escrow_balance = (float) $influencerWallet->escrow_balance + (float) $lockedOrder->commission_amount;
                    $influencerWallet->save();
                }
            }

            Transaction::create([
                'user_id'        => $lockedOrder->vendor_id,
                'type'           => 'earning',
                'amount_target'  => $lockedOrder->vendor_earnings,
                'amount_total'   => $lockedOrder->vendor_earnings,
                'gateway_fee'    => 0,
                'mantota_markup' => 0,
                'status'         => 'completed',
                'reference'      => 'ESC-' . $lockedOrder->reference,
                'payment_gateway' => 'moneroo',
                'gateway_ref'     => $paymentId,
                'description'    => 'Escrow commande ' . $lockedOrder->reference,
            ]);
        });

        Cache::forget('admin.dashboard');
        Log::info('Moneroo webhook : commande payée', ['reference' => $reference]);

        return response()->json(['ok' => true]);
    }

    private function creditDeposit(?string $reference, string $paymentId, array $verification): JsonResponse
    {
        if (! $reference) {
            return response()->json(['error' => 'Référence dépôt manquante'], 400);
        }

        $transaction = Transaction::where('reference', $reference)->first();

        if (! $transaction) {
            Log::warning('Moneroo webhook : dépôt introuvable', ['reference' => $reference]);
            return response()->json(['error' => 'Dépôt introuvable'], 404);
        }

        if ($transaction->status === 'completed') {
            return response()->json(['ok' => true]);
        }

        DB::transaction(function () use ($transaction, $paymentId, $verification): void {
            $tx = Transaction::where('id', $transaction->id)->lockForUpdate()->firstOrFail();

            if ($tx->status === 'completed') {
                return;
            }

            $received = round((float) ($verification['amount'] ?? 0), 2);
            $expected = round((float) $tx->amount_total, 2);
            if ($received < $expected) {
                Log::error('Moneroo webhook : montant dépôt incorrect', [
                    'transaction_id' => $tx->id,
                    'expected' => $expected,
                    'received' => $received,
                ]);
                throw new \RuntimeException('Montant reçu inférieur au montant attendu');
            }

            $wallet = Wallet::where('user_id', $tx->user_id)->lockForUpdate()->firstOrFail();
            $wallet->balance = (float) $wallet->balance + (float) $tx->amount_target;
            $wallet->save();

            $tx->update([
                'status'          => 'completed',
                'gateway_ref'     => $paymentId,
                'payment_gateway' => 'moneroo',
            ]);
        });

        Cache::forget('admin.dashboard');
        Log::info('Moneroo webhook : dépôt crédité', ['reference' => $reference]);

        return response()->json(['ok' => true]);
    }

    private function restoreOrderStock(Order $order): void
    {
        $product = $order->product;
        if ($product && $product->isPhysical() && $product->stock !== null) {
            $product->increment('stock');
        }
    }

    private function handlePayoutSuccess(array $data, PaymentService $service, ?string $payoutId): JsonResponse
    {
        $metadata = $data['data']['metadata'] ?? [];
        $reference = $metadata['reference'] ?? null;

        // Les remboursements sont aussi des payouts Moneroo, mais ils ne
        // correspondent a aucune transaction de retrait : ne pas toucher au wallet.
        if (($metadata['type'] ?? null) === 'refund') {
            Log::info('Moneroo webhook : payout de remboursement', [
                'reference' => $reference,
                'event'     => 'payout.success',
            ]);

            return response()->json(['ok' => true]);
        }
        if (! $payoutId) {
            return response()->json(['error' => 'ID payout manquant'], 400);
        }

        $verification = $service->verifyPayout($payoutId);
        if (! $verification['success'] || $verification['status'] !== 'success') {
            return response()->json(['error' => 'Vérification payout échouée'], 400);
        }

        if (! $reference) {
            return response()->json(['error' => 'Référence payout manquante'], 400);
        }

        $transaction = Transaction::where('reference', $reference)->first();

        if (! $transaction) {
            return response()->json(['error' => 'Transaction payout introuvable'], 404);
        }

        if ($transaction->status === 'completed') {
            return response()->json(['ok' => true]);
        }

        DB::transaction(function () use ($transaction, $payoutId): void {
            $tx = Transaction::where('id', $transaction->id)->lockForUpdate()->firstOrFail();
            if ($tx->status === 'completed') {
                return;
            }

            $withdrawalAmount = (float) $tx->amount_target;

            $wallet = Wallet::where('user_id', $tx->user_id)->lockForUpdate()->firstOrFail();
            $wallet->pending_balance = max(0, (float) $wallet->pending_balance - $withdrawalAmount);
            $wallet->save();

            $tx->update([
                'status'          => 'completed',
                'gateway_ref'     => $payoutId,
                'payment_gateway' => 'moneroo',
            ]);
        });

        Log::info('Moneroo webhook : payout confirmé', ['reference' => $reference]);

        return response()->json(['ok' => true]);
    }

    private function handlePayoutFailed(array $data): JsonResponse
    {
        $metadata = $data['data']['metadata'] ?? [];
        $reference = $metadata['reference'] ?? null;

        // Les remboursements sont aussi des payouts Moneroo, mais ils ne
        // correspondent a aucune transaction de retrait : ne pas toucher au wallet.
        if (($metadata['type'] ?? null) === 'refund') {
            Log::info('Moneroo webhook : payout de remboursement', [
                'reference' => $reference,
                'event'     => 'payout.failed',
            ]);

            return response()->json(['ok' => true]);
        }
        if (! $reference) {
            return response()->json(['ok' => true]);
        }

        $transaction = Transaction::where('reference', $reference)->first();

        if (! $transaction || $transaction->status !== 'pending') {
            return response()->json(['ok' => true]);
        }

        DB::transaction(function () use ($transaction): void {
            $tx = Transaction::where('id', $transaction->id)->lockForUpdate()->firstOrFail();
            if ($tx->status !== 'pending') {
                return;
            }

            $withdrawalAmount = (float) $tx->amount_target;

            $wallet = Wallet::where('user_id', $tx->user_id)->lockForUpdate()->firstOrFail();
            $wallet->pending_balance = max(0, (float) $wallet->pending_balance - $withdrawalAmount);
            $wallet->balance = (float) $wallet->balance + $withdrawalAmount;
            $wallet->save();

            $tx->update(['status' => 'failed']);
        });

        Log::warning('Moneroo webhook : payout échoué, fonds restitués', ['reference' => $reference]);

        return response()->json(['ok' => true]);
    }
}
