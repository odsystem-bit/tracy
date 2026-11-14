<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Mobile;

use App\Http\Controllers\Controller;
use App\Models\BotSubscription;
use App\Models\Transaction;
use App\Models\User;
use App\Services\Payment\PaymentService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

/**
 * MobileSubscriptionController — API abonnements vendeur pour l'application mobile MANTOTA.
 *
 * Gère les plans freemium :
 *  - Free    : 0 FCFA / mois (commission 5%)
 *  - Starter : 2 500 FCFA / mois (commission 4%)
 *  - Standard: 12 000 FCFA / mois (commission 3%)
 *  - Pro     : 25 000 FCFA / mois (commission 2%)
 *  - TPF     : 50 000 FCFA / an (commission 2%, pas de commission transaction)
 *
 * Le plan détermine le taux de commission prélevé sur chaque vente.
 */
class MobileSubscriptionController extends Controller
{
    private const array PLANS = [
        'free' => [
            'name'        => 'Free',
            'price'       => 0,
            'duration'    => 0,
            'commission'  => 0.05,
            'features'    => [
                'Jusqu\'à 10 produits',
                'Commission 5% par vente',
                'Support communautaire',
                'Boutique en ligne basique',
            ],
            'product_limit' => 10,
        ],
        'starter' => [
            'name'        => 'Starter',
            'price'       => 2500,
            'duration'    => 30,
            'commission'  => 0.04,
            'features'    => [
                'Jusqu\'à 50 produits',
                'Commission 4% par vente',
                'Statistiques de vente',
                'Lien de boutique partageable',
                'Support email',
            ],
            'product_limit' => 50,
        ],
        'standard' => [
            'name'        => 'Standard',
            'price'       => 12000,
            'duration'    => 30,
            'commission'  => 0.03,
            'features'    => [
                'Produits illimités',
                'Commission 3% par vente',
                'Statistiques avancées',
                'Personnalisation de la boutique',
                'Négociation automatique Tracy',
                'Support prioritaire',
            ],
            'product_limit' => null,
        ],
        'pro' => [
            'name'        => 'Pro',
            'price'       => 25000,
            'duration'    => 30,
            'commission'  => 0.02,
            'features'    => [
                'Produits illimités',
                'Commission 2% par vente',
                'Statistiques avancées + exports',
                'Boutique personnalisée (logo, thème)',
                'Négociation automatique Tracy',
                'API d\'intégration',
                'Support dédié 7j/7',
                'Mise en avant dans les recherches',
            ],
            'product_limit' => null,
        ],
        'tpf' => [
            'name'        => 'TPF (Tracy Partner Forever)',
            'price'       => 50000,
            'duration'    => 365,
            'commission'  => 0.02,
            'features'    => [
                'Tous les avantages Pro',
                'Abonnement annuel (économie 2 mois)',
                'Commission 2% par vente',
                'Badge partenaire officiel',
                'Accès anticipé aux nouvelles fonctionnalités',
                'Accompagnement business personnalisé',
            ],
            'product_limit' => null,
        ],
    ];

    /**
     * GET /subscriptions/plans — Liste tous les plans disponibles.
     */
    public function plans(): JsonResponse
    {
        $plans = collect(self::PLANS)->map(fn ($plan, $key) => [
            'id'            => $key,
            'name'          => $plan['name'],
            'price'         => $plan['price'],
            'duration_days' => $plan['duration'],
            'commission_rate' => $plan['commission'],
            'features'      => $plan['features'],
            'product_limit' => $plan['product_limit'],
            'is_free'       => $key === 'free',
        ])->values();

        return response()->json(['plans' => $plans]);
    }

    /**
     * GET /subscriptions/current — Plan actuel du vendeur.
     */
    public function current(Request $request): JsonResponse
    {
        $user = $request->user();
        $planKey = $user->bot_plan ?? 'free';
        $plan = self::PLANS[$planKey] ?? self::PLANS['free'];

        // Récupérer l'abonnement actif le plus récent
        $subscription = BotSubscription::where('vendor_id', $user->id)
            ->where('status', 'active')
            ->where('expires_at', '>', now())
            ->latest()
            ->first();

        $isActive = $subscription !== null;
        $expiresAt = $subscription?->expires_at;

        return response()->json([
            'plan'          => $planKey,
            'plan_name'     => $plan['name'],
            'is_active'     => $isActive || $planKey === 'free',
            'expires_at'    => $expiresAt?->toIso8601String(),
            'commission_rate' => $plan['commission'],
            'product_limit' => $plan['product_limit'],
            'features'      => $plan['features'],
        ]);
    }

    /**
     * POST /subscriptions/activate — Active un plan payant (initie le paiement Moneroo).
     */
    public function activate(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'plan' => 'required|string|in:starter,standard,pro,tpf',
        ]);

        $user = $request->user();
        $planKey = $validated['plan'];
        $plan = self::PLANS[$planKey];

        // Vérifier qu'il n'a pas déjà un plan actif supérieur
        $currentSub = BotSubscription::where('vendor_id', $user->id)
            ->where('status', 'active')
            ->where('expires_at', '>', now())
            ->latest()
            ->first();

        if ($currentSub && $currentSub->plan === $planKey) {
            return response()->json([
                'message' => 'Vous êtes déjà abonné au plan ' . $plan['name'] . '.',
            ], 422);
        }

        $reference = 'SUB-' . strtoupper(Str::random(10));

        // Créer la transaction en pending
        $transaction = Transaction::create([
            'user_id'         => $user->id,
            'type'            => 'subscription',
            'amount_target'   => $plan['price'],
            'gateway_fee'     => 0,
            'mantota_markup'  => $plan['price'],
            'amount_total'    => $plan['price'],
            'status'          => 'pending',
            'reference'       => $reference,
            'description'     => 'Abonnement MANTOTA ' . $plan['name'],
        ]);

        // Initialiser le paiement Moneroo
        $paymentService = app(PaymentService::class);
        $result = $paymentService->initializePayment([
            'amount'      => $plan['price'],
            'description' => 'Abonnement MANTOTA ' . $plan['name'] . ' — ' . $reference,
            'customer'    => [
                'first_name' => $user->display_name ?? $user->name ?? '',
                'email'      => $user->email ?? '',
                'phone'      => $user->phone ?? '',
            ],
            'return_url' => config('app.url') . '/subscriptions?ref=' . $reference,
            'metadata'   => [
                'type'       => 'subscription',
                'plan'       => $planKey,
                'user_id'    => $user->id,
                'reference'  => $reference,
            ],
        ]);

        if (!$result['success']) {
            $transaction->update(['status' => 'failed']);

            return response()->json([
                'message'      => 'Erreur lors du paiement de l\'abonnement.',
                'error_detail' => $result['message'] ?? '',
            ], 500);
        }

        $transaction->update([
            'gateway_ref'     => $result['id'] ?? null,
            'payment_gateway' => 'moneroo',
        ]);

        return response()->json([
            'payment_id'   => $result['id'] ?? null,
            'checkout_url' => $result['checkout_url'] ?? null,
            'reference'    => $reference,
            'plan'         => $planKey,
            'plan_name'    => $plan['name'],
            'amount'       => $plan['price'],
        ]);
    }

    /**
     * POST /subscriptions/activate-free — Active le plan gratuit.
     */
    public function activateFree(Request $request): JsonResponse
    {
        $user = $request->user();
        $plan = self::PLANS['free'];

        $user->update(['bot_plan' => 'free']);

        return response()->json([
            'message' => 'Plan Free activé.',
            'plan'    => 'free',
            'plan_name' => $plan['name'],
            'commission_rate' => $plan['commission'],
            'product_limit' => $plan['product_limit'],
        ]);
    }

    /**
     * POST /subscriptions/confirm — Confirme un abonnement après paiement (webhook ou callback).
     */
    public function confirm(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'reference' => 'required|string',
        ]);

        $transaction = Transaction::where('reference', $validated['reference'])
            ->where('user_id', $request->user()->id)
            ->where('type', 'subscription')
            ->first();

        if (!$transaction) {
            return response()->json(['message' => 'Transaction introuvable.'], 404);
        }

        if ($transaction->status === 'paid') {
            return response()->json(['message' => 'Abonnement déjà confirmé.'], 422);
        }

        // Vérifier le paiement via Moneroo
        $paymentService = app(PaymentService::class);
        if ($transaction->gateway_ref) {
            $verification = $paymentService->verifyPayment($transaction->gateway_ref);

            if (!$verification['success'] || $verification['status'] !== 'success') {
                return response()->json([
                    'message' => 'Paiement non confirmé. Statut: ' . ($verification['status'] ?? 'inconnu'),
                ], 422);
            }
        }

        $planKey = $transaction->metadata['plan'] ?? null;
        if (!$planKey || !isset(self::PLANS[$planKey])) {
            return response()->json(['message' => 'Plan invalide.'], 422);
        }

        $plan = self::PLANS[$planKey];

        DB::transaction(function () use ($transaction, $planKey, $plan, $request) {
            $transaction->update(['status' => 'paid']);

            $subscription = BotSubscription::create([
                'vendor_id'            => $request->user()->id,
                'plan'                 => $planKey,
                'status'               => 'active',
                'reference_transaction'=> $transaction->reference,
                'expires_at'           => now()->addDays($plan['duration']),
            ]);

            $request->user()->update(['bot_plan' => $planKey]);
        });

        return response()->json([
            'message'     => 'Abonnement ' . $plan['name'] . ' activé avec succès.',
            'plan'        => $planKey,
            'plan_name'   => $plan['name'],
            'expires_at'  => now()->addDays($plan['duration'])->toIso8601String(),
            'commission_rate' => $plan['commission'],
        ]);
    }
}
