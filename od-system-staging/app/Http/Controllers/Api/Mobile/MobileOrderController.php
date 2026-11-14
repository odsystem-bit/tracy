<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Mobile;

use App\Enums\OrderStatus;
use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\Product;
use App\Services\Payment\PaymentService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;
use Illuminate\Validation\Rule;

/**
 * MobileOrderController — API pour l'application mobile MANTOTA.
 *
 * Gère le cycle de vie complet des commandes depuis l'APK :
 *  - Liste des commandes (acheteur & vendeur)
 *  - Création de commande après négociation Tracy
 *  - Détail d'une commande
 *  - Mise à jour du statut (vendeur)
 *  - Confirmation de réception (code PIN client)
 *  - Ouverture de litige
 *  - Initialisation de paiement (Moneroo)
 */
class MobileOrderController extends Controller
{
    /**
     * GET /orders — Commandes de l'utilisateur connecté (acheteur).
     */
    public function index(Request $request): JsonResponse
    {
        $user = $request->user();

        $query = Order::query()
            ->where('influencer_id', $user->id)
            ->orWhere('customer_phone', $user->phone)
            ->with(['product:id,name,image_path', 'vendor:id,name,shop_name,shop_logo_path'])
            ->orderByDesc('created_at');

        if ($status = $request->input('status')) {
            $query->where('status', $status);
        }

        $orders = $query->paginate(20);

        return response()->json([
            'data' => $orders->items(),
            'meta' => [
                'current_page' => $orders->currentPage(),
                'last_page'    => $orders->lastPage(),
                'total'        => $orders->total(),
            ],
        ]);
    }

    /**
     * GET /vendor/orders — Commandes reçues par le vendeur.
     */
    public function vendorOrders(Request $request): JsonResponse
    {
        $user = $request->user();

        $query = Order::query()
            ->where('vendor_id', $user->id)
            ->with(['product:id,name,image_path', 'influencer:id,name'])
            ->orderByDesc('created_at');

        if ($status = $request->input('status')) {
            $query->where('status', $status);
        }

        $orders = $query->paginate(20);

        return response()->json([
            'data' => $orders->items(),
            'meta' => [
                'current_page' => $orders->currentPage(),
                'last_page'    => $orders->lastPage(),
                'total'        => $orders->total(),
            ],
        ]);
    }

    /**
     * GET /orders/{id} — Détail d'une commande.
     */
    public function show(Request $request, string $id): JsonResponse
    {
        $user = $request->user();

        $order = Order::where('id', $id)
            ->orWhere('reference', $id)
            ->with(['product', 'vendor:id,name,shop_name,shop_logo_path,phone', 'influencer:id,name'])
            ->first();

        if (!$order) {
            return response()->json(['message' => 'Commande introuvable.'], 404);
        }

        // Vérifier que l'utilisateur est impliqué (acheteur, vendeur ou admin)
        $isInvolved = $order->vendor_id === $user->id
            || $order->influencer_id === $user->id
            || $order->customer_phone === $user->phone;

        if (!$isInvolved) {
            return response()->json(['message' => 'Accès non autorisé.'], 403);
        }

        return response()->json($order);
    }

    /**
     * POST /orders — Crée une commande après négociation Tracy.
     */
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'product_id'       => 'required|exists:products,id',
            'quantity'         => 'nullable|integer|min:1|max:999',
            'negotiated_price' => 'nullable|numeric|min:100',
            'customer_name'    => 'nullable|string|max:255',
            'customer_phone'   => 'nullable|string|max:20',
            'customer_whatsapp'=> 'nullable|string|max:20',
            'customer_email'   => 'nullable|email|max:255',
            'country'          => 'nullable|string|max:5',
            'city'             => 'nullable|string|max:100',
            'landmark_indication' => 'nullable|string|max:500',
            'delivery_address' => 'nullable|string|max:500',
        ]);

        $user = $request->user();
        $product = Product::findOrFail($validated['product_id']);

        if ($product->status !== 'active' && $product->status !== 'published') {
            return response()->json(['message' => 'Ce produit n\'est plus disponible.'], 422);
        }

        $quantity = $validated['quantity'] ?? 1;
        $unitPrice = (float) ($validated['negotiated_price'] ?? $product->price);
        $amountPaid = $unitPrice * $quantity;
        $deliveryFee = (float) ($product->delivery_fee ?? 0);
        $totalAmount = $amountPaid + $deliveryFee;

        // Commission MANTOTA (2-5% selon le plan du vendeur)
        $commissionRate = $this->getVendorCommissionRate($product->vendor_id);
        $commissionAmount = round($amountPaid * $commissionRate, 2);
        $vendorEarnings = $amountPaid - $commissionAmount;

        $order = DB::transaction(function () use (
            $user, $product, $validated, $quantity, $amountPaid,
            $deliveryFee, $totalAmount, $commissionAmount, $vendorEarnings
        ) {
            $order = Order::create([
                'reference'         => Order::generateReference(),
                'vendor_id'         => $product->vendor_id,
                'product_id'        => $product->id,
                'influencer_id'     => $user->id,
                'customer_name'     => $validated['customer_name'] ?? $user->display_name ?? $user->name,
                'customer_phone'    => $validated['customer_phone'] ?? $user->phone,
                'customer_whatsapp' => $validated['customer_whatsapp'] ?? $user->phone,
                'customer_email'    => $validated['customer_email'] ?? $user->email,
                'country'           => $validated['country'] ?? $user->country ?? 'BJ',
                'city'              => $validated['city'] ?? null,
                'landmark_indication' => $validated['landmark_indication'] ?? null,
                'amount_paid'       => $totalAmount,
                'commission_amount' => $commissionAmount,
                'vendor_earnings'   => $vendorEarnings,
                'delivery_fee_paid' => $deliveryFee,
                'status'            => OrderStatus::PENDING,
                'payment_status'    => 'pending',
                'delivery_pin'      => str_pad((string) random_int(0, 9999), 4, '0', STR_PAD_LEFT),
                'tracking_token'    => Str::uuid()->toString(),
                'delivery_deadline' => now()->addDays(3),
            ]);

            // Décrémenter le stock si produit physique
            if ($product->isPhysical() && $product->stock > 0) {
                $product->decrement('stock', $quantity);
            }

            return $order;
        });

        $order->load(['product', 'vendor:id,name,shop_name']);

        return response()->json($order, 201);
    }

    /**
     * PATCH /orders/{id}/status — Met à jour le statut (vendeur).
     */
    public function updateStatus(Request $request, string $id): JsonResponse
    {
        $validated = $request->validate([
            'status' => ['required', 'string', Rule::in([
                'shipped', 'delivered', 'cancelled',
            ])],
            'cancel_reason' => 'nullable|string|max:500',
            'delivery_guy_name'  => 'nullable|string|max:255',
            'delivery_guy_phone' => 'nullable|string|max:20',
            'delivery_company'   => 'nullable|string|max:255',
        ]);

        $user = $request->user();
        $order = Order::where('id', $id)->orWhere('reference', $id)->first();

        if (!$order) {
            return response()->json(['message' => 'Commande introuvable.'], 404);
        }

        if ($order->vendor_id !== $user->id) {
            return response()->json(['message' => 'Seul le vendeur peut modifier le statut.'], 403);
        }

        $newStatus = OrderStatus::from($validated['status']);

        // Transitions autorisées
        $allowedTransitions = [
            OrderStatus::PENDING => [OrderStatus::SHIPPED, OrderStatus::CANCELLED],
            OrderStatus::SHIPPED => [OrderStatus::DELIVERED, OrderStatus::CANCELLED],
        ];

        $currentStatus = $order->status;
        if (!isset($allowedTransitions[$currentStatus]) ||
            !in_array($newStatus, $allowedTransitions[$currentStatus], true)) {
            return response()->json([
                'message' => "Transition non autorisée : {$currentStatus->value} → {$newStatus->value}.",
            ], 422);
        }

        $updateData = ['status' => $newStatus];
        if (isset($validated['delivery_guy_name'])) {
            $updateData['delivery_guy_name'] = $validated['delivery_guy_name'];
        }
        if (isset($validated['delivery_guy_phone'])) {
            $updateData['delivery_guy_phone'] = $validated['delivery_guy_phone'];
        }
        if (isset($validated['delivery_company'])) {
            $updateData['delivery_company'] = $validated['delivery_company'];
        }
        if ($newStatus === OrderStatus::CANCELLED && isset($validated['cancel_reason'])) {
            $updateData['cancel_reason'] = $validated['cancel_reason'];
        }

        $order->update($updateData);

        return response()->json($order->fresh(['product', 'vendor:id,name']));
    }

    /**
     * POST /orders/{id}/confirm-delivery — Le client confirme la réception (code PIN).
     */
    public function confirmDelivery(Request $request, string $id): JsonResponse
    {
        $validated = $request->validate([
            'pin_code' => 'required|string|size:4',
        ]);

        $user = $request->user();
        $order = Order::where('id', $id)->orWhere('reference', $id)->first();

        if (!$order) {
            return response()->json(['message' => 'Commande introuvable.'], 404);
        }

        $isBuyer = $order->influencer_id === $user->id || $order->customer_phone === $user->phone;
        if (!$isBuyer) {
            return response()->json(['message' => 'Seul l\'acheteur peut confirmer la réception.'], 403);
        }

        if ($order->status !== OrderStatus::SHIPPED && $order->status !== OrderStatus::PENDING) {
            return response()->json([
                'message' => 'Cette commande ne peut plus être confirmée (statut: ' . $order->status->value . ').',
            ], 422);
        }

        if ($order->delivery_pin !== $validated['pin_code']) {
            return response()->json(['message' => 'Code PIN incorrect.'], 422);
        }

        DB::transaction(function () use ($order) {
            $order->update(['status' => OrderStatus::DELIVERED]);

            // Libérer l'escrow → créditer le vendeur
            $vendorWallet = \App\Models\Wallet::firstOrCreate(
                ['user_id' => $order->vendor_id],
                ['balance' => 0, 'pending_balance' => 0, 'escrow_balance' => 0, 'referral_balance' => 0],
            );

            $vendorWallet->increment('balance', (float) $order->vendor_earnings);
            $vendorWallet->decrement('escrow_balance', (float) $order->vendor_earnings);

            // Transaction d'earning pour le vendeur
            \App\Models\Transaction::create([
                'user_id'         => $order->vendor_id,
                'type'            => 'earning',
                'amount_target'   => $order->vendor_earnings,
                'gateway_fee'     => 0,
                'mantota_markup'  => 0,
                'amount_total'    => $order->vendor_earnings,
                'status'          => 'paid',
                'reference'       => 'EARN-' . $order->reference,
                'description'     => 'Vente confirmée — ' . $order->reference,
            ]);
        });

        return response()->json([
            'message' => 'Livraison confirmée. Fonds libérés au vendeur.',
            'order'   => $order->fresh(),
        ]);
    }

    /**
     * POST /orders/{id}/dispute — Ouvre un litige.
     */
    public function openDispute(Request $request, string $id): JsonResponse
    {
        $validated = $request->validate([
            'reason' => 'required|string|min:10|max:1000',
        ]);

        $user = $request->user();
        $order = Order::where('id', $id)->orWhere('reference', $id)->first();

        if (!$order) {
            return response()->json(['message' => 'Commande introuvable.'], 404);
        }

        $isBuyer = $order->influencer_id === $user->id || $order->customer_phone === $user->phone;
        if (!$isBuyer) {
            return response()->json(['message' => 'Seul l\'acheteur peut ouvrir un litige.'], 403);
        }

        if (!in_array($order->status, [OrderStatus::PENDING, OrderStatus::SHIPPED], true)) {
            return response()->json([
                'message' => 'Un litige ne peut être ouvert que sur une commande en cours.',
            ], 422);
        }

        $order->update([
            'status'         => OrderStatus::DISPUTED,
            'dispute_reason' => $validated['reason'],
        ]);

        return response()->json([
            'message' => 'Litige ouvert. L\'équipe MANTOTA va examiner votre réclamation.',
            'order'   => $order->fresh(),
        ]);
    }

    /**
     * POST /orders/{id}/pay — Initialise un paiement Moneroo pour la commande.
     */
    public function initPayment(Request $request, string $id): JsonResponse
    {
        $user = $request->user();
        $order = Order::where('id', $id)->orWhere('reference', $id)->first();

        if (!$order) {
            return response()->json(['message' => 'Commande introuvable.'], 404);
        }

        if ($order->payment_status === 'paid') {
            return response()->json(['message' => 'Cette commande est déjà payée.'], 422);
        }

        $paymentService = app(PaymentService::class);

        $result = $paymentService->initializePayment([
            'amount'      => (float) $order->amount_paid,
            'description' => 'Commande ' . $order->reference . ' — MANTOTA',
            'customer'    => [
                'first_name' => $order->customer_name ?? '',
                'email'      => $order->customer_email ?? ($user->email ?? ''),
                'phone'      => $order->customer_phone ?? $user->phone ?? '',
            ],
            'return_url'  => config('app.url') . '/track/' . $order->id . '?token=' . $order->tracking_token,
            'metadata'    => [
                'order_id'  => $order->id,
                'reference' => $order->reference,
                'type'      => 'order_payment',
            ],
        ]);

        if (!$result['success']) {
            return response()->json([
                'message'      => 'Erreur lors de l\'initialisation du paiement.',
                'error_detail' => $result['message'] ?? '',
            ], 500);
        }

        // Enregistrer la référence de paiement
        $order->update([
            'payment_gateway_ref' => $result['id'] ?? null,
            'payment_gateway'     => 'moneroo',
        ]);

        return response()->json([
            'payment_id'   => $result['id'] ?? null,
            'checkout_url' => $result['checkout_url'] ?? null,
            'reference'    => $order->reference,
            'amount'       => (float) $order->amount_paid,
        ]);
    }

    /**
     * GET /orders/{id}/track — Suivi de commande (timeline).
     */
    public function track(Request $request, string $id): JsonResponse
    {
        $user = $request->user();

        $order = Order::where('id', $id)
            ->orWhere('reference', $id)
            ->with(['product', 'vendor:id,name,shop_name,phone'])
            ->first();

        if (!$order) {
            return response()->json(['message' => 'Commande introuvable.'], 404);
        }

        $timeline = $this->buildTimeline($order);

        // Exposer le delivery_pin uniquement à l'acheteur (caché par défaut dans le modèle)
        $orderData = $order->toArray();
        $isBuyer = $order->influencer_id === $user->id || $order->customer_phone === $user->phone;
        if ($isBuyer) {
            $orderData['delivery_pin'] = $order->delivery_pin;
        }

        return response()->json([
            'order'    => $orderData,
            'timeline' => $timeline,
        ]);
    }

    /**
     * Construit la timeline chronologique d'une commande.
     */
    private function buildTimeline(Order $order): array
    {
        $timeline = [
            [
                'date'  => $order->created_at?->toIso8601String(),
                'label' => 'Commande créée',
                'detail' => 'Référence ' . $order->reference,
                'status' => 'done',
            ],
        ];

        if ($order->payment_status === 'paid') {
            $timeline[] = [
                'date'  => $order->updated_at?->toIso8601String(),
                'label' => 'Paiement confirmé',
                'detail' => number_format((float) $order->amount_paid, 0, ',', ' ') . ' FCFA — Séquestre actif',
                'status' => 'done',
            ];
        }

        if ($order->status === OrderStatus::SHIPPED || $order->status === OrderStatus::DELIVERED) {
            $timeline[] = [
                'date'  => $order->updated_at?->toIso8601String(),
                'label' => 'Expédiée',
                'detail' => $order->delivery_guy_name
                    ? 'Livreur: ' . $order->delivery_guy_name . ($order->delivery_guy_phone ? ' — ' . $order->delivery_guy_phone : '')
                    : 'Commande expédiée',
                'status' => $order->status === OrderStatus::SHIPPED ? 'active' : 'done',
            ];
        }

        if ($order->status === OrderStatus::DELIVERED) {
            $timeline[] = [
                'date'  => $order->updated_at?->toIso8601String(),
                'label' => 'Livraison confirmée',
                'detail' => 'Fonds libérés au vendeur',
                'status' => 'done',
            ];
        }

        if ($order->status === OrderStatus::DISPUTED) {
            $timeline[] = [
                'date'  => $order->updated_at?->toIso8601String(),
                'label' => 'Litige ouvert',
                'detail' => $order->dispute_reason ?: 'Litige en cours d\'examen',
                'status' => 'disputed',
            ];
        }

        if ($order->status === OrderStatus::CANCELLED) {
            $timeline[] = [
                'date'  => $order->updated_at?->toIso8601String(),
                'label' => 'Commande annulée',
                'detail' => $order->cancel_reason ?: 'Annulée',
                'status' => 'cancelled',
            ];
        }

        return $timeline;
    }

    /**
     * Récupère le taux de commission selon le plan du vendeur.
     */
    private function getVendorCommissionRate(int $vendorId): float
    {
        $vendor = \App\Models\User::find($vendorId);
        $plan = $vendor?->bot_plan ?? 'free';

        return match ($plan) {
            'pro'      => 0.02,
            'standard' => 0.03,
            'starter'  => 0.04,
            default    => 0.05, // free
        };
    }
}
