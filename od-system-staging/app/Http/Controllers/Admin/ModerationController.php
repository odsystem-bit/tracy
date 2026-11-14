<?php

declare(strict_types=1);

namespace App\Http\Controllers\Admin;

use App\Enums\CampaignTier;
use App\Http\Controllers\Controller;
use App\Models\Campaign;
use App\Models\KycLog;
use App\Models\Transaction;
use App\Models\User;
use App\Models\Wallet;
use App\Notifications\KycStatusUpdatedNotification;
use App\Notifications\TierClassifiedNotification;
use App\Notifications\WithdrawalProcessedNotification;
use App\Services\AuditLogService;
use App\Services\Payment\PaymentService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Inertia\Inertia;
use Inertia\Response as InertiaResponse;

/**
 * ModerationController — Actions de moderation administrateur MANTOTA.
 *
 * Trois axes de moderation :
 *  1. KYC   : Approuver / rejeter les documents d'identite.
 *  2. VIP   : Approuver / rejeter le statut VIP d'un createur de contenu
 *             apres verification manuelle de ses reseaux sociaux.
     *  3. Retraits : Approuver (payout automatique Moneroo)
     *               ou rejeter (recrediter le solde principal).
 *
 * Toutes les operations financieres utilisent DB::transaction() + lockForUpdate()
 * pour garantir l'integrite comptable.
 */
class ModerationController extends Controller
{

    // ══════════════════════════════════════════════
    //  1. MODERATION KYC
    // ══════════════════════════════════════════════

    /**
     * Approuve la verification KYC d'un utilisateur.
     * Passe kyc_status de 'pending' a 'approved'.
     */
    public function approveKyc(User $user): RedirectResponse
    {
        if ($user->kyc_status !== 'pending') {
            return back()->withErrors(['kyc' => 'Ce dossier KYC n\'est pas en attente de validation.']);
        }

        $updateData = ['kyc_status' => 'approved'];

        // Robot : classification automatique du palier selon les abonnes
        if ($user->role === 'influencer') {
            $computedTier = CampaignTier::fromFollowers($user->total_followers);
            $updateData['tier'] = $computedTier->value;
        }

        $user->update($updateData);

        KycLog::create([
            'user_id'  => $user->id,
            'admin_id' => auth()->id(),
            'action'   => 'approved',
        ]);

        AuditLogService::log('approve_kyc', 'User', $user->id,
            ['kyc_status' => 'pending'],
            $updateData
        );

        $user->notify(new KycStatusUpdatedNotification('approved'));

        // Notifier l'utilisateur de sa classification de tier
        if ($user->role === 'influencer' && isset($computedTier)) {
            $user->notify(new TierClassifiedNotification($computedTier->value));
        }

        Cache::forget('admin.dashboard');
        return back()->with('success', 'KYC approuve pour ' . $user->name . '.');
    }

    /**
     * Rejette la verification KYC d'un utilisateur.
     * Passe kyc_status de 'pending' a 'rejected'.
     * Accepte une raison optionnelle de rejet (visible par l'utilisateur).
     */
    public function rejectKyc(Request $request, User $user): RedirectResponse
    {
        if ($user->kyc_status !== 'pending') {
            return back()->withErrors(['kyc' => 'Ce dossier KYC n\'est pas en attente de validation.']);
        }

        $validated = $request->validate([
            'reason' => ['required', 'string', 'max:1000'],
        ]);

        $reason = $validated['reason'] ?? null;

        $user->update(['kyc_status' => 'rejected']);

        KycLog::create([
            'user_id'  => $user->id,
            'admin_id' => auth()->id(),
            'action'   => 'rejected',
            'reason'   => $reason,
        ]);

        AuditLogService::log('reject_kyc', 'User', $user->id,
            ['kyc_status' => 'pending'],
            ['kyc_status' => 'rejected', 'reason' => $reason]
        );

        $user->notify(new KycStatusUpdatedNotification('rejected', $reason));

        Cache::forget('admin.dashboard');
        return back()->with('success', 'KYC rejete pour ' . $user->name . '.');
    }

    // ══════════════════════════════════════════════
    //  2. MODERATION VIP
    // ══════════════════════════════════════════════

    /**
     * Approuve le statut VIP d'un createur de contenu.
     * L'admin a manuellement verifie les comptes sociaux de l'utilisateur.
     */
    public function approveVip(User $user): RedirectResponse
    {
        if ($user->is_vip) {
            return back()->withErrors(['vip' => 'Cet utilisateur possede deja le statut VIP.']);
        }

        $user->forceFill(['is_vip' => true, 'vip_requested_at' => null])->save();

        AuditLogService::log('approve_vip', 'User', $user->id,
            ['is_vip' => false],
            ['is_vip' => true]
        );

        Cache::forget('admin.dashboard');
        return back()->with('success', 'Statut VIP accorde a ' . $user->name . '.');
    }

    /**
     * Rejette la demande VIP d'un createur de contenu.
     * Remet vip_requested_at a null pour qu'il puisse refaire une demande.
     */
    public function rejectVip(User $user): RedirectResponse
    {
        $user->forceFill(['is_vip' => false, 'vip_requested_at' => null])->save();

        AuditLogService::log('reject_vip', 'User', $user->id,
            ['is_vip' => false, 'vip_requested_at' => $user->vip_requested_at],
            ['is_vip' => false, 'vip_requested_at' => null]
        );

        Cache::forget('admin.dashboard');
        return back()->with('success', 'Demande VIP rejetee pour ' . $user->name . '.');
    }

    // ══════════════════════════════════════════════
    //  3. MODERATION RETRAITS
    // ══════════════════════════════════════════════

    /**
     * Approuve un retrait — payout automatique via Moneroo Mobile Money.
     *
     * Flux comptable :
     *  - Payout Moneroo envoye au numero MoMo de l'utilisateur.
     *  - La Transaction passe en 'pending' en attendant le webhook de confirmation,
     *    puis le pending_balance est debite definitivement.
     *
     * Securite : DB::transaction() + lockForUpdate() pour eviter les conditions de concurrence.
     */
    public function approveWithdrawal(Transaction $transaction): RedirectResponse
    {
        // ── Verifications prealables ──
        if ($transaction->type !== 'withdrawal') {
            return back()->withErrors(['withdrawal' => 'Cette transaction n\'est pas un retrait.']);
        }

        if ($transaction->status !== 'pending') {
            return back()->withErrors(['withdrawal' => 'Ce retrait n\'est pas en attente de validation.']);
        }

        // ── Payout automatique via Mobile Money ──
        $user = $transaction->user;
        $phone = $transaction->momo_number ?: ($user->phone ?? '');

        if (! $phone) {
            return back()->withErrors(['withdrawal' => 'Aucun numero Mobile Money associe a ce retrait. Impossible d\'effectuer le payout.']);
        }

        $country = $user->country ?? 'BJ';
        $network = PaymentService::detectNetwork($phone, $country);

        if (! $network) {
            return back()->withErrors(['withdrawal' => 'Réseau Mobile Money non détecté pour ce numéro.']);
        }

        $method = PaymentService::resolveMobileMoneyMethod($country, $network);
        if (! $method) {
            return back()->withErrors(['withdrawal' => 'Méthode de payout Moneroo non disponible pour ce pays / réseau.']);
        }

        $netPayout = (int) round((float) $transaction->amount_total);

        if ($netPayout <= 0) {
            return back()->withErrors(['withdrawal' => 'Montant net du payout invalide.']);
        }

        $service = app(PaymentService::class);

        if (! $service->isConfigured()) {
            return back()->withErrors(['withdrawal' => 'Configuration Moneroo manquante.']);
        }

        $normalizedPhone = PaymentService::normalizePhone($phone, $country);

        $payoutResult = $service->initializePayout([
            'amount'      => $netPayout,
            'description' => 'Retrait ' . $transaction->reference,
            'customer'    => [
                'email'      => $user->email ?? '',
                'first_name' => $user->name ?? 'Client',
            ],
            'method'      => $method[0],
            'recipient'   => [
                $method[1] => $normalizedPhone,
            ],
            'metadata'    => [
                'type'      => 'payout',
                'reference' => $transaction->reference,
            ],
        ]);

        if (! $payoutResult['success']) {
            Log::warning('Payout Moneroo failed', [
                'tx_id'   => $transaction->id,
                'user_id' => $user->id,
                'phone'   => $phone,
                'amount'  => $netPayout,
                'reason'  => $payoutResult['message'],
            ]);
            return back()->withErrors(['withdrawal' => 'Payout automatique echoue : ' . $payoutResult['message']]);
        }

        // ── Mise a jour du gateway_ref en attendant le webhook de confirmation ──
        $transaction->update([
            'gateway_ref' => $payoutResult['id'],
            'payment_gateway' => 'moneroo',
        ]);

        AuditLogService::log('approve_withdrawal', 'Transaction', $transaction->id,
            ['status' => 'pending'],
            ['status' => 'pending', 'amount' => (float) $transaction->amount_target, 'net_payout' => $netPayout, 'payout_phone' => $phone]
        );

        Cache::forget('admin.dashboard');
        return back()->with('success', 'Payout Moneroo initié — ' . number_format($netPayout, 0, ',', ' ') . ' FCFA vers le ' . $phone . '. Le statut sera mis a jour par webhook.');
    }

    /**
     * Rejette un retrait — recredite le solde principal du createur de contenu.
     *
     * Flux comptable (CRITIQUE — securite comptable) :
     *  - Le montant est deplace de pending_balance → balance (restitution).
     *  - La Transaction passe en 'failed'.
     *
     * Ceci garantit que le createur de contenu ne perd jamais ses fonds en cas de rejet.
     * Securite : DB::transaction() + lockForUpdate().
     */
    public function rejectWithdrawal(Transaction $transaction): RedirectResponse
    {
        // ── Verifications prealables ──
        if ($transaction->type !== 'withdrawal') {
            return back()->withErrors(['withdrawal' => 'Cette transaction n\'est pas un retrait.']);
        }

        if ($transaction->status !== 'pending') {
            return back()->withErrors(['withdrawal' => 'Ce retrait n\'est pas en attente de validation.']);
        }

        // ── Transaction atomique : pending_balance → balance (restitution) ──
        try {
        DB::transaction(function () use ($transaction): void {
            /** @var Wallet $lockedWallet */
            $lockedWallet = Wallet::where('user_id', $transaction->user_id)
                ->lockForUpdate()
                ->firstOrFail();

            // Montant du retrait initial (amount_target = montant brut demande)
            $withdrawalAmount = (float) $transaction->amount_target;

            // Restitution : pending_balance → balance
            $lockedWallet->pending_balance = max(0, (float) $lockedWallet->pending_balance - $withdrawalAmount);
            $lockedWallet->balance         = (float) $lockedWallet->balance + $withdrawalAmount;
            $lockedWallet->save();

            // Passage de la transaction en failed
            $transaction->update(['status' => 'failed']);
        });
        } catch (\Throwable $e) {
            \Illuminate\Support\Facades\Log::error('Withdrawal rejection failed', ['tx_id' => $transaction->id, 'error' => $e->getMessage()]);
            return back()->withErrors(['withdrawal' => 'Erreur lors du rejet du retrait.']);
        }

        AuditLogService::log('reject_withdrawal', 'Transaction', $transaction->id,
            ['status' => 'pending'],
            ['status' => 'failed', 'amount' => (float) $transaction->amount_target]
        );

        $transaction->user->notify(new WithdrawalProcessedNotification($transaction, 'failed'));

        Cache::forget('admin.dashboard');
        return back()->with('success', 'Retrait rejete. Le solde a ete recredite au createur de contenu.');
    }
}
