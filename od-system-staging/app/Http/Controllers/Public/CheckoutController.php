<?php

declare(strict_types=1);

namespace App\Http\Controllers\Public;

use App\Enums\OrderStatus;
use App\Http\Controllers\Controller;
use App\Models\Gateway;
use App\Models\Order;
use App\Models\Product;
use App\Models\User;
use App\Models\Wallet;
use App\Notifications\NewSaleNotification;
use App\Services\Payment\PaymentService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;
use Illuminate\Validation\Rule;
use Inertia\Inertia;
use Inertia\Response as InertiaResponse;

/**
 * CheckoutController — Guest Checkout Moneroo + Escrow MANTOTA.
 *
 * Flux :
 *  1. Le client remplit ses coordonnees de livraison.
 *  2. On cree la commande (payment_status = 'awaiting'), on decremente le stock.
 *  3. On redirige vers la passerelle (PayDunya hosted page ou FeexPay USSD push).
 *  4. Le webhook confirme le paiement et credite l'escrow.
 *  5. Le client revient sur la page de succes.
 */
class CheckoutController extends Controller
{
    private const LOCATIONS = [
        'BJ' => [
            'name'  => 'Bénin',
            'cities' => ['Cotonou', 'Porto-Novo', 'Abomey-Calavi', 'Parakou', 'Bohicon', 'Autre...'],
        ],
        'CI' => [
            'name'  => 'Côte d\'Ivoire',
            'cities' => ['Abidjan', 'Bouaké', 'Daloa', 'Yamoussoukro', 'San-Pédro', 'Autre...'],
        ],
        'SN' => [
            'name'  => 'Sénégal',
            'cities' => ['Dakar', 'Thiès', 'Rufisque', 'Touba', 'Ziguinchor', 'Autre...'],
        ],
        'TG' => [
            'name'  => 'Togo',
            'cities' => ['Lomé', 'Sokodé', 'Kara', 'Kpalimé', 'Atakpamé', 'Autre...'],
        ],
        'CM' => [
            'name'  => 'Cameroun',
            'cities' => ['Douala', 'Yaoundé', 'Garoua', 'Bamenda', 'Maroua', 'Autre...'],
        ],
    ];

    private const FAST_DELIVERY_CITIES = ['Cotonou', 'Abomey-Calavi'];

    // ──────────────────────────────────────────────
    //  Formulaire de checkout (GET)
    // ──────────────────────────────────────────────

    public function show(Product $product): InertiaResponse
    {
        $product->load('vendor:id,name,business_name,shop_name,slug', 'images:id,product_id,path,sort_order');

        $targetCountry = null;
        if ($campaignId = session('campaign_id')) {
            $campaign = \App\Models\Campaign::find($campaignId);
            if ($campaign && $campaign->target_country) {
                $countries = is_array($campaign->target_country)
                    ? $campaign->target_country
                    : json_decode($campaign->target_country, true) ?? [];
                $targetCountry = is_string($countries) ? $countries : ($countries[0] ?? null);
            }
        }

        return Inertia::render('Shop/Checkout', [
            'product'         => $product,
            'target_country'  => $targetCountry,
            'influencer_id'   => session('partner_referrer'),
        ]);
    }

    // ──────────────────────────────────────────────
    //  Traitement du paiement (POST)
    // ──────────────────────────────────────────────

    public function store(Request $request, Product $product)
    {
        // ── Validation du stock (produit physique) ──
        if ($product->isPhysical()) {
            if ($product->stock === null || $product->stock <= 0) {
                return back()->withErrors(['product' => 'Ce produit est en rupture de stock.']);
            }
        }

        // ── Regles de validation differenciees par type de produit ──
        if ($product->isDigital()) {
            $validated = $request->validate([
                'customer_name'      => ['required', 'string', 'max:255'],
                'customer_phone'     => ['required', 'string', 'max:30'],
                'customer_whatsapp'  => ['required', 'string', 'max:30'],
                'customer_email'     => ['required', 'email', 'max:255'],
            ], [
                'customer_name.required'       => 'Votre nom complet est obligatoire.',
                'customer_phone.required'      => 'Le numero de telephone est obligatoire.',
                'customer_whatsapp.required'   => 'Le numero WhatsApp est obligatoire.',
                'customer_email.required'      => 'L\'adresse email est obligatoire pour les produits digitaux.',
                'customer_email.email'         => 'Veuillez saisir une adresse email valide.',
            ]);

            $finalCity = null;
        } else {
            $validCountries = array_keys(self::LOCATIONS);
            $validCities = [];
            foreach (self::LOCATIONS as $countryData) {
                $validCities = array_merge($validCities, $countryData['cities']);
            }
            $validCities = array_unique($validCities);

            $validated = $request->validate([
                'customer_name'      => ['required', 'string', 'max:255'],
                'customer_phone'     => ['required', 'string', 'max:30'],
                'customer_whatsapp'  => ['required', 'string', 'max:30'],
                'country'            => ['required', 'string', Rule::in($validCountries)],
                'city'               => ['required', 'string', Rule::in($validCities)],
                'custom_city'        => ['nullable', 'string', 'max:255'],
                'landmark_indication' => ['required', 'string', 'max:1000'],
            ], [
                'customer_name.required'       => 'Votre nom complet est obligatoire.',
                'customer_phone.required'      => 'Le numero de telephone est obligatoire.',
                'customer_whatsapp.required'   => 'Le numero WhatsApp est obligatoire pour le suivi de livraison.',
                'country.required'             => 'Veuillez selectionner un pays.',
                'country.in'                   => 'Pays non supporte.',
                'city.required'                => 'Veuillez selectionner une ville.',
                'city.in'                      => 'Ville non reconnue.',
                'landmark_indication.required' => 'Le quartier et le repere precis sont obligatoires pour la livraison.',
            ]);

            // ── Verrouillage pays campagne ──
            if ($campaignId = session('campaign_id')) {
                $campaign = \App\Models\Campaign::find($campaignId);
                if ($campaign && $campaign->target_country) {
                    $countries = is_array($campaign->target_country)
                        ? $campaign->target_country
                        : (json_decode($campaign->target_country, true) ?? []);
                    $locked = is_string($countries) ? $countries : ($countries[0] ?? null);
                    if ($locked && $validated['country'] !== $locked) {
                        return back()->withErrors([
                            'country' => 'Cette campagne est reservee au pays : ' . $locked . '.',
                        ]);
                    }
                }
            }

            // ── Filet de Securite "Autre..." ──
            if ($validated['city'] === 'Autre...') {
                if (!$validated['custom_city']) {
                    return back()->withErrors([
                        'custom_city' => 'Precisez votre ville ou quartier si vous choisissez "Autre..."'
                    ]);
                }
                $finalCity = $validated['custom_city'];
            } else {
                $finalCity = $validated['city'];
            }
        }

        // ── Calcul du split financier ──
        $productPrice     = (float) $product->price;
        $commissionRate   = (float) $product->commission_percent;
        $influencerId     = $request->session()->get('partner_referrer');
        $commissionAmount = $influencerId ? round($productPrice * ($commissionRate / 100), 2) : 0.00;

        $deliveryFeePaid = 0.00;
        if ($product->isPhysical() && $product->delivery_type === 'fixed' && $product->delivery_fee) {
            $deliveryFeePaid = (float) $product->delivery_fee;
        }

        $vendorEarnings = round($productPrice - $commissionAmount + $deliveryFeePaid, 2);
        $amountPaid = round($productPrice + $deliveryFeePaid, 2);

        $deliveryHours = $product->isPhysical() && $finalCity
            ? (in_array($finalCity, self::FAST_DELIVERY_CITIES) ? 24 : 72)
            : null;

        // ── Cree la commande atomiquement (payment_status = awaiting) ──
        $order = null;

        try {
            $order = DB::transaction(function () use (
                $product, $validated, $finalCity, $amountPaid, $commissionAmount, $vendorEarnings,
                $deliveryFeePaid, $influencerId, $deliveryHours
            ) {
                // Verrouiller le produit pour eviter l'oversell
                if ($product->isPhysical()) {
                    $lockedProduct = Product::where('id', $product->id)->lockForUpdate()->first();
                    if (!$lockedProduct || $lockedProduct->stock === null || $lockedProduct->stock <= 0) {
                        throw new \RuntimeException('stock_exhausted');
                    }
                    $lockedProduct->decrement('stock');
                }

                return Order::create([
                    'reference'           => Order::generateReference(),
                    'vendor_id'           => $product->vendor_id,
                    'product_id'          => $product->id,
                    'influencer_id'       => $influencerId,
                    'campaign_id'         => session('campaign_id'),
                    'customer_name'       => $validated['customer_name'],
                    'customer_phone'      => $validated['customer_phone'],
                    'customer_whatsapp'   => $validated['customer_whatsapp'],
                    'customer_email'      => $validated['customer_email'] ?? null,
                    'city'                => $finalCity,
                    'country'             => $validated['country'] ?? null,
                    'landmark_indication' => $validated['landmark_indication'] ?? null,
                    'amount_paid'         => $amountPaid,
                    'commission_amount'   => $commissionAmount,
                    'vendor_earnings'     => $vendorEarnings,
                    'delivery_fee_paid'   => $deliveryFeePaid,
                    'status'              => OrderStatus::PENDING,
                    'payment_status'      => 'awaiting',
                    'delivery_deadline'   => $deliveryHours ? now()->addHours($deliveryHours) : null,
                    'tracking_token'      => Str::random(64),
                    'delivery_pin'        => $product->isPhysical() ? str_pad((string) random_int(0, 9999), 4, '0', STR_PAD_LEFT) : null,
                ]);
            });
        } catch (\RuntimeException $e) {
            if ($e->getMessage() === 'stock_exhausted') {
                return back()->withErrors(['product' => 'Ce produit est en rupture de stock.']);
            }
            throw $e;
        }

        // ── Initier le paiement via Moneroo ──
        $service = app(PaymentService::class);

        if (! $service->isConfigured()) {
            return $this->restoreStockAndFail($order, 'Configuration Moneroo incomplete. Contactez l\'administration.');
        }

        $result = $service->initializePayment([
            'amount'      => (int) $order->amount_paid,
            'currency'    => $order->currency ?? 'XOF',
            'description' => 'Paiement commande ' . $order->reference,
            'customer'    => [
                'first_name' => $order->customer_name ?? 'Client',
                'email'      => $order->customer_email ?? '',
                'phone'      => $order->customer_phone ?? '',
            ],
            'return_url'  => route('shop.checkout.payment-return', [
                'order' => $order->id,
                'token' => $order->tracking_token,
            ]),
            'metadata'    => [
                'type'      => 'order',
                'reference' => $order->reference,
            ],
        ]);

        if (! $result['success']) {
            Log::error('Moneroo checkout: erreur initiation', [
                'order_id' => $order->id,
                'message'  => $result['message'] ?? 'inconnu',
            ]);
            return $this->restoreStockAndFail($order, 'Erreur paiement : ' . ($result['message'] ?? 'Veuillez reessayer.'));
        }

        $order->update([
            'payment_gateway_ref' => $result['id'],
            'payment_gateway'     => 'moneroo',
        ]);

        Log::info('Moneroo checkout: redirection vers paiement', [
            'order_id'  => $order->id,
            'reference' => $order->reference,
            'amount'    => $order->amount_paid,
        ]);

        return Inertia::location($result['checkout_url']);
    }

    // ──────────────────────────────────────────────
    //  Restaurer le stock si FedaPay echoue
    // ──────────────────────────────────────────────

    private function restoreStockAndFail(Order $order, string $errorMessage): RedirectResponse
    {
        DB::transaction(function () use ($order): void {
            $order->update(['payment_status' => 'failed']);

            $product = Product::where('id', $order->product_id)->lockForUpdate()->first();
            if ($product && $product->isPhysical() && $product->stock !== null) {
                $product->increment('stock');
            }
        });

        return redirect()->route('shop.checkout.show', $order->product_id)
            ->withErrors(['payment' => $errorMessage]);
    }

    // ──────────────────────────────────────────────
    //  Retour apres paiement Moneroo (GET)
    // ──────────────────────────────────────────────

    public function paymentReturn(Request $request, Order $order): InertiaResponse|RedirectResponse
    {
        if ($request->query('token') !== $order->tracking_token) {
            abort(403, 'Lien invalide.');
        }

        // Si le webhook a deja confirme le paiement
        if ($order->payment_status === 'paid') {
            return redirect()->route('shop.checkout.success', ['order' => $order, 'token' => $order->tracking_token]);
        }

        // Verifier activement aupres de la passerelle
        if ($order->payment_gateway_ref && $order->payment_status === 'awaiting') {
            $credited = self::verifyAndCreditOrder($order);
            if ($credited) {
                return redirect()->route('shop.checkout.success', ['order' => $order, 'token' => $order->tracking_token]);
            }
        }

        // Page de traitement avec polling
        return Inertia::render('Shop/PaymentProcessing', [
            'order_id'    => $order->id,
            'reference'   => $order->reference,
            'amount_paid' => $order->amount_paid,
            'token'       => $order->tracking_token,
            'status_url'  => route('shop.checkout.payment-status', $order),
            'success_url' => route('shop.checkout.success', ['order' => $order, 'token' => $order->tracking_token]),
            'cancel_url'  => route('shop.checkout.show', $order->product_id),
        ]);
    }

    // ──────────────────────────────────────────────
    //  API de polling du statut (JSON)
    // ──────────────────────────────────────────────

    public function checkPaymentStatus(Request $request, Order $order): JsonResponse
    {
        if ($request->query('token') !== $order->tracking_token) {
            return response()->json(['payment_status' => 'unauthorized'], 403);
        }

        // Verifier activement aupres de la passerelle si encore en attente
        if ($order->payment_status === 'awaiting' && $order->payment_gateway_ref) {
            $credited = self::verifyAndCreditOrder($order);
            if ($credited) {
                return response()->json(['payment_status' => 'paid']);
            }
            $order->refresh();
        }

        return response()->json(['payment_status' => $order->payment_status]);
    }

    // ──────────────────────────────────────────────
    //  Page de succes post-paiement (GET)
    // ──────────────────────────────────────────────

    public function success(Request $request, Order $order): InertiaResponse|RedirectResponse
    {
        if ($request->query('token') !== $order->tracking_token || $order->payment_status !== 'paid') {
            return redirect()->route('shop.checkout.show', $order->product_id);
        }

        $order->load([
            'product:id,name,image_path,price,type,access_url,digital_delivery_type,digital_file_path',
            'vendor:id,name,business_name,shop_name,slug,phone',
        ]);

        if ($order->delivery_pin) {
            $order->makeVisible('delivery_pin');
        }

        return Inertia::render('Shop/Success', [
            'order' => $order,
        ]);
    }

    // ──────────────────────────────────────────────
    //  Verification active Moneroo
    // ──────────────────────────────────────────────

    public static function verifyAndCreditOrder(Order $order): bool
    {
        if ($order->payment_status !== 'awaiting' || ! $order->payment_gateway_ref) {
            return false;
        }

        try {
            $service = app(PaymentService::class);
            $verification = $service->verifyPayment($order->payment_gateway_ref);

            if (! $verification['success'] || $verification['status'] !== 'success') {
                if ($verification['status'] === 'failed') {
                    $order->update(['payment_status' => 'failed']);
                    $product = Product::find($order->product_id);
                    if ($product && $product->isPhysical() && $product->stock !== null) {
                        $product->increment('stock');
                    }
                }
                return false;
            }

            self::creditEscrowAndNotify($order);
            return true;
        } catch (\Throwable $e) {
            Log::error('Moneroo order verification error', [
                'order_id' => $order->id,
                'error'    => $e->getMessage(),
            ]);
            return false;
        }
    }

    // ──────────────────────────────────────────────
    //  Credit escrow + notifications (commun)
    // ──────────────────────────────────────────────

    private static function creditEscrowAndNotify(Order $order): void
    {
        DB::transaction(function () use ($order): void {
            $lockedOrder = Order::where('id', $order->id)
                ->lockForUpdate()
                ->firstOrFail();

            if ($lockedOrder->payment_status !== 'awaiting') {
                return;
            }

            // Bloquer les gains vendeur en escrow
            $vendorWallet = Wallet::where('user_id', $lockedOrder->vendor_id)
                ->lockForUpdate()
                ->firstOrFail();
            $vendorWallet->escrow_balance = (float) $vendorWallet->escrow_balance + (float) $lockedOrder->vendor_earnings;
            $vendorWallet->save();

            // Bloquer la commission créateur de contenu en escrow
            if ($lockedOrder->influencer_id && (float) $lockedOrder->commission_amount > 0) {
                $influencerWallet = Wallet::where('user_id', $lockedOrder->influencer_id)
                    ->lockForUpdate()
                    ->first();
                if ($influencerWallet) {
                    $influencerWallet->escrow_balance = (float) $influencerWallet->escrow_balance + (float) $lockedOrder->commission_amount;
                    $influencerWallet->save();
                }
            }

            $lockedOrder->update(['payment_status' => 'paid']);
        });

        $order->refresh();

        // Produit digital : livraison automatique
        self::autoDeliverDigital($order);

        // Notifications
        if ($vendor = User::find($order->vendor_id)) {
            $vendor->notify(new NewSaleNotification($order, 'vendor'));
        }
        if ($order->influencer_id && $influencer = User::find($order->influencer_id)) {
            $influencer->notify(new NewSaleNotification($order, 'influencer'));
        }

        Cache::forget('admin.dashboard');

        Log::info('Checkout: paiement commande confirme', [
            'order_id'  => $order->id,
            'reference' => $order->reference,
            'gateway'   => $order->payment_gateway,
            'amount'    => $order->amount_paid,
        ]);
    }

    // ──────────────────────────────────────────────
    //  Auto-livraison produit digital
    // ──────────────────────────────────────────────

    public static function autoDeliverDigital(Order $order): void
    {
        $product = $order->product ?? Product::find($order->product_id);
        if (! $product || ! $product->isDigital()) {
            return;
        }

        if ($order->status !== OrderStatus::PENDING || $order->payment_status !== 'paid') {
            return;
        }

        try {
            DB::transaction(function () use ($order): void {
                $lockedOrder = Order::where('id', $order->id)->lockForUpdate()->firstOrFail();

                if ($lockedOrder->status !== OrderStatus::PENDING || $lockedOrder->payment_status !== 'paid') {
                    return;
                }

                $lockedOrder->update(['status' => OrderStatus::DELIVERED]);

                // Liberer escrow vendeur → balance
                $vendorWallet = Wallet::where('user_id', $lockedOrder->vendor_id)->lockForUpdate()->firstOrFail();
                $vendorEarnings = (float) $lockedOrder->vendor_earnings;
                $vendorWallet->escrow_balance = max(0, (float) $vendorWallet->escrow_balance - $vendorEarnings);
                $vendorWallet->balance = (float) $vendorWallet->balance + $vendorEarnings;
                $vendorWallet->save();

                \App\Models\Transaction::create([
                    'user_id'        => $lockedOrder->vendor_id,
                    'type'           => 'earning',
                    'amount_target'  => $vendorEarnings,
                    'gateway_fee'    => 0.00,
                    'mantota_markup' => 0.00,
                    'amount_total'   => $vendorEarnings,
                    'status'         => 'completed',
                    'reference'      => 'DIGITAL-VENDOR-' . $lockedOrder->reference,
                    'description'    => 'Vente digitale auto-livree — #' . $lockedOrder->reference,
                ]);

                // Liberer escrow créateur de contenu → balance
                if ($lockedOrder->influencer_id && (float) $lockedOrder->commission_amount > 0) {
                    $influencerWallet = Wallet::where('user_id', $lockedOrder->influencer_id)->lockForUpdate()->first();
                    if ($influencerWallet) {
                        $commission = (float) $lockedOrder->commission_amount;
                        $influencerWallet->escrow_balance = max(0, (float) $influencerWallet->escrow_balance - $commission);
                        $influencerWallet->balance = (float) $influencerWallet->balance + $commission;
                        $influencerWallet->save();

                        \App\Models\Transaction::create([
                            'user_id'        => $lockedOrder->influencer_id,
                            'type'           => 'earning',
                            'amount_target'  => $commission,
                            'gateway_fee'    => 0.00,
                            'mantota_markup' => 0.00,
                            'amount_total'   => $commission,
                            'status'         => 'completed',
                            'reference'      => 'DIGITAL-COMM-' . $lockedOrder->reference,
                            'description'    => 'Commission digitale auto-livree — #' . $lockedOrder->reference,
                        ]);
                    }
                }
            });

            $order->refresh();
            Log::info('Digital auto-delivery done', ['order_id' => $order->id, 'reference' => $order->reference]);

            // Envoyer le produit digital par email au client
            if ($order->customer_email) {
                $product = $order->product;
                if ($product && $product->digital_delivery_type === 'file' && $product->digital_file_path) {
                    // Mode fichier : envoyer un lien de telechargement securise
                    $downloadUrl = route('order.track.download', [
                        'order' => $order->id,
                        'token' => $order->tracking_token,
                    ]);
                    \Illuminate\Support\Facades\Notification::route('mail', $order->customer_email)
                        ->notify(new \App\Notifications\DigitalProductDeliveredNotification($order, $downloadUrl, true));
                } elseif ($product && $product->access_url) {
                    // Mode lien : envoyer l'URL externe
                    \Illuminate\Support\Facades\Notification::route('mail', $order->customer_email)
                        ->notify(new \App\Notifications\DigitalProductDeliveredNotification($order, $product->access_url));
                }
            }
        } catch (\Throwable $e) {
            Log::error('Digital auto-delivery failed', ['order_id' => $order->id, 'error' => $e->getMessage()]);
        }
    }
}
