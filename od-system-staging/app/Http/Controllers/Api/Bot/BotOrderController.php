<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Enums\OrderStatus;
use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\Product;
use App\Models\ShopNegotiationConfig;
use App\Models\User;
use App\Models\Wallet;
use App\Services\Payment\MonerooService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

class BotOrderController extends Controller
{
    /**
     * Crée une nouvelle commande depuis le bot Tracy
     *
     * @param Request $request
     * @return \Illuminate\Http\JsonResponse
     */
    public function store(Request $request): \Illuminate\Http\JsonResponse
    {
        // Validation des champs
        $validated = $request->validate([
            'vendor_id' => 'required|exists:users,id',
            'product_id' => 'required|exists:products,id',
            'customer_name' => 'required|string|max:255',
            'customer_phone' => 'required|string|max:30',
            'customer_whatsapp' => 'required|string|max:30',
            'customer_email' => 'nullable|email',
            'country' => 'required|string|max:5',
            'city' => 'required|string|max:100',
            'landmark_indication' => 'nullable|string|max:500',
            'agreed_price' => 'nullable|numeric|min:0',
        ]);

        return DB::transaction(function () use ($validated, $request) {
            // Charger le produit
            $product = Product::findOrFail($validated['product_id']);

            // Vérifier que le produit est actif
            if ($product->status !== 'actif') {
                return response()->json(['error' => 'Produit non disponible'], 422);
            }

            // Vérifier le stock si produit physique
            if ($product->type === 'physical' && $product->stock <= 0) {
                return response()->json(['error' => 'Produit en rupture de stock'], 422);
            }

            // Charger le vendeur
            $vendor = User::findOrFail($validated['vendor_id']);

            // Prix unitaire : prix catalogue, ou prix négocié par Tracy.
            // Le prix négocié n'est JAMAIS cru sur parole : il doit rester entre
            // le plancher (prix - max_discount_percent du vendeur) et le prix catalogue.
            $unitPrice = (float) $product->price;
            if (isset($validated['agreed_price'])) {
                $maxDiscount = (float) (ShopNegotiationConfig::where('store_id', $product->vendor_id)->value('max_discount_percent') ?? 15.0);
                $floor = $unitPrice * (1 - $maxDiscount / 100);
                $agreed = (float) $validated['agreed_price'];
                if ($agreed > $unitPrice + 0.5 || $agreed < $floor - 0.5) {
                    return response()->json(['error' => 'Prix négocié non autorisé par le vendeur'], 422);
                }
                $unitPrice = round($agreed, 2);
            }

            // Calculer les montants
            $commissionPercent = $vendor->commission_percent ?? 10; // 10% par défaut
            $commissionAmount = $unitPrice * ($commissionPercent / 100);
            $vendorEarnings = $unitPrice - $commissionAmount;
            $deliveryFee = 0; // Tracy gère la livraison séparément

            // Créer la commande
            $order = Order::create([
                'reference' => Order::generateReference(),
                'vendor_id' => $validated['vendor_id'],
                'product_id' => $validated['product_id'],
                'customer_name' => $validated['customer_name'],
                'customer_phone' => $validated['customer_phone'],
                'customer_whatsapp' => $validated['customer_whatsapp'],
                'customer_email' => $validated['customer_email'] ?? null,
                'country' => $validated['country'],
                'city' => $validated['city'],
                'landmark_indication' => $validated['landmark_indication'] ?? null,
                'amount_paid' => $unitPrice,
                'commission_amount' => $commissionAmount,
                'vendor_earnings' => $vendorEarnings,
                'delivery_fee_paid' => $deliveryFee,
                'status' => OrderStatus::PENDING,
                'payment_status' => 'awaiting',
                'payment_gateway' => 'moneroo',
                'tracking_token' => Str::random(40),
                'delivery_pin' => str_pad((string) rand(1000, 9999), 4, '0', STR_PAD_LEFT),
            ]);

            // Décrémenter le stock si produit physique
            if ($product->type === 'physical') {
                $product->decrement('stock');
            }

            // Créer le lien de paiement Moneroo
            $paymentUrl = null;
            try {
                $result = MonerooService::createPaymentLink([
                    'amount' => $unitPrice,
                    'reference' => $order->reference,
                    'customer_name' => $validated['customer_name'],
                    'customer_phone' => $validated['customer_phone'],
                    'return_url' => config('app.url') . '/track/' . $order->id . '?token=' . $order->tracking_token,
                    'description' => 'Commande ' . $order->reference . ' — ' . $product->name,
                ]);
                $paymentUrl = $result['url'];
            } catch (\Exception $e) {
                // Pas de clé Moneroo en local — on garde la commande sans lien de paiement
                $paymentUrl = null;
            }

            return response()->json([
                'success' => true,
                'order_id' => $order->id,
                'reference' => $order->reference,
                'payment_url' => $paymentUrl,
                'tracking_url' => config('app.url') . '/track/' . $order->id . '?token=' . $order->tracking_token,
                'tracking_token' => $order->tracking_token,
                'delivery_pin' => $order->delivery_pin,
                'amount' => $unitPrice,
            ]);
        });
    }

    /**
     * Affiche les détails d'une commande par référence
     *
     * @param Request $request
     * @param string $reference
     * @return \Illuminate\Http\JsonResponse
     */
    public function show(Request $request, string $reference): \Illuminate\Http\JsonResponse
    {
        $order = Order::with(['product', 'vendor'])
            ->where('reference', $reference)
            ->firstOrFail();

        return response()->json([
            'order_id' => $order->id,
            'reference' => $order->reference,
            'status' => $order->status->value,
            'payment_status' => $order->payment_status,
            'customer_name' => $order->customer_name,
            'product_name' => $order->product->name,
            'amount_paid' => (float) $order->amount_paid,
            'tracking_url' => config('app.url') . '/track/' . $order->id . '?token=' . $order->tracking_token,
            'delivery_guy_name' => $order->delivery_guy_name,
            'delivery_guy_phone' => $order->delivery_guy_phone,
            'delivery_company' => $order->delivery_company,
            'is_overdue' => $order->isOverdue(),
        ]);
    }

    /**
     * Retourne les statistiques du mois en cours pour un vendeur
     *
     * @param Request $request
     * @param int $vendorId
     * @return \Illuminate\Http\JsonResponse
     */
    public function vendorStats(Request $request, int $vendorId): \Illuminate\Http\JsonResponse
    {
        // Vérifier que le vendeur existe
        $vendor = User::findOrFail($vendorId);

        // Début du mois en cours
        $startOfMonth = now()->startOfMonth();

        // Compter les commandes du mois groupées par statut
        $orders = Order::where('vendor_id', $vendorId)
            ->where('created_at', '>=', $startOfMonth)
            ->get();

        $stats = [
            'total_orders' => $orders->count(),
            'delivered' => $orders->where('status', OrderStatus::DELIVERED)->count(),
            'shipped' => $orders->where('status', OrderStatus::SHIPPED)->count(),
            'pending' => $orders->where('status', OrderStatus::PENDING)->count(),
            'disputed' => $orders->where('status', OrderStatus::DISPUTED)->count(),
        ];

        // Charger le wallet du vendeur
        $wallet = Wallet::where('user_id', $vendorId)->first();
        $available = $wallet ? (float) $wallet->balance : 0;
        $inEscrow = $wallet ? (float) $wallet->escrow_balance : 0;

        // Calculer les revenus gagnés ce mois (commandes livrées)
        $earnedThisMonth = $orders
            ->where('status', OrderStatus::DELIVERED)
            ->sum('vendor_earnings');

        // Top 3 produits vendus ce mois
        $topProducts = Order::where('vendor_id', $vendorId)
            ->where('created_at', '>=', $startOfMonth)
            ->where('status', '!=', OrderStatus::CANCELLED)
            ->selectRaw('product_id, COUNT(*) as orders_count, SUM(vendor_earnings) as total_revenue')
            ->groupBy('product_id')
            ->orderBy('orders_count', 'desc')
            ->limit(3)
            ->with('product')
            ->get()
            ->map(function ($item) {
                return [
                    'name' => $item->product->name,
                    'orders' => $item->orders_count,
                    'revenue' => (float) $item->total_revenue,
                ];
            });

        return response()->json([
            'this_month' => $stats,
            'revenue' => [
                'available' => $available,
                'in_escrow' => $inEscrow,
                'earned_this_month' => (float) $earnedThisMonth,
            ],
            'top_products' => $topProducts,
        ]);
    }
}
