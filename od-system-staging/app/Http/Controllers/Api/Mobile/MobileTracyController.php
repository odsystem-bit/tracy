<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Mobile;

use App\Http\Controllers\Controller;
use App\Models\Product;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

/**
 * MobileTracyController — Proxy Tracy Core pour l'application mobile MANTOTA.
 *
 * Relaye les requêtes vers Tracy Core (FastAPI) et enrichit les réponses
 * avec les données de la base Laravel (produits, prix, stock).
 *
 * Endpoints :
 *  - POST /tracy/chat        → Conversation avec Tracy
 *  - POST /tracy/search      → Recherche de produits
 *  - POST /tracy/negotiate   → Négociation de prix
 */
class MobileTracyController extends Controller
{
    /**
     * POST /tracy/chat — Envoie un message à Tracy Core.
     */
    public function chat(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'conversation_id' => 'required|string|max:100',
            'message'         => 'required|string|min:1|max:5000',
            'context'         => 'nullable|array',
            'context.store_id'     => 'nullable|string|max:50',
            'context.mode'         => 'nullable|string|in:buyer,vendor',
            'context.country_code' => 'nullable|string|size:2',
            'context.city'         => 'nullable|string|max:100',
            'context.latitude'     => 'nullable|numeric|between:-90,90',
            'context.longitude'    => 'nullable|numeric|between:-180,180',
        ]);

        $user = $request->user();
        $ctx = $validated['context'] ?? [];

        // Mode vendeur : Tracy gère la boutique de l'utilisateur.
        // Mode acheteur : recherche sur la boutique choisie, sinon catalogue public.
        $isVendor = ($ctx['mode'] ?? null) === 'vendor' || $validated['conversation_id'] === 'vendor';
        $storeId = $isVendor ? (string) $user->id : ($ctx['store_id'] ?? 'public');

        // Le conversation_id de l'app ('tracy', 'search'...) n'est pas unique :
        // on le préfixe par l'utilisateur pour isoler la mémoire de chaque client.
        $conversationId = "app:{$user->id}:{$validated['conversation_id']}";

        $countryCode = isset($ctx['country_code'])
            ? strtoupper($ctx['country_code'])
            : (is_string($user->country) && strlen($user->country) === 2 ? strtoupper($user->country) : null);

        $tracyUrl = config('services.tracy_core.url', 'http://127.0.0.1:8001');
        $tracyApiKey = config('services.tracy_core.api_key', '');

        try {
            $response = Http::withHeaders([
                'Content-Type' => 'application/json',
                'X-Api-Key' => $tracyApiKey,
            ])->timeout(30)->post($tracyUrl . '/chat', array_filter([
                'text'             => $validated['message'],
                'store_id'         => $storeId,
                'customer_id'      => (string) $user->id,
                'conversation_id'  => $conversationId,
                'country_code'     => $countryCode,
                'city'             => $ctx['city'] ?? null,
                'latitude'         => isset($ctx['latitude']) ? (float) $ctx['latitude'] : null,
                'longitude'        => isset($ctx['longitude']) ? (float) $ctx['longitude'] : null,
            ], fn ($v) => $v !== null));

            if (!$response->successful()) {
                return $this->fallbackChat($validated['message']);
            }

            $tracyReply = $response->json();

            // Tracy Core returns {text, correlation_id, agent, tools_used}
            // Map to Flutter app format {type, text}
            $cards = collect($tracyReply['cards'] ?? [])->map(fn ($c) => [
                'id'        => (string) ($c['id'] ?? ''),
                'name'      => $c['name'] ?? '',
                'shop'      => $c['shop'] ?? '',
                'price'     => (string) ($c['price'] ?? ''),
                'raw_price' => (float) ($c['raw_price'] ?? 0),
                'image_url' => $c['image_url'] ?? null,
                'store_id'  => (string) ($c['store_id'] ?? ''),
            ])->values()->all();

            return response()->json([
                'type' => $cards ? 'search' : 'text',
                'text' => $tracyReply['text'] ?? '',
                'products' => $cards,
                'correlation_id' => $tracyReply['correlation_id'] ?? null,
                'agent' => $tracyReply['agent'] ?? null,
                'data' => $tracyReply['data'] ?? null,
            ]);
        } catch (\Exception $e) {
            return $this->fallbackChat($validated['message']);
        }
    }

    /**
     * POST /tracy/search — Recherche de produits via Tracy.
     */
    public function search(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'query'     => 'required|string|min:1|max:255',
            'category'  => 'nullable|string|max:100',
            'min_price' => 'nullable|numeric|min:0',
            'max_price' => 'nullable|numeric|min:0',
            'limit'     => 'nullable|integer|min:1|max:50',
        ]);

        $limit = $validated['limit'] ?? 20;

        // Recherche directe dans la base (fallback robuste si Tracy Core est down)
        $query = Product::query()
            ->where('status', 'actif')
            ->where(function ($q) use ($validated) {
                $q->where('name', 'ILIKE', "%{$validated['query']}%")
                  ->orWhere('description', 'ILIKE', "%{$validated['query']}%");
            })
            ->with('vendor:id,name,shop_name,shop_logo_path,slug');

        if (isset($validated['min_price'])) {
            $query->where('price', '>=', $validated['min_price']);
        }
        if (isset($validated['max_price'])) {
            $query->where('price', '<=', $validated['max_price']);
        }

        $products = $query->orderByDesc('created_at')->limit($limit)->get();

        $results = $products->map(fn ($p) => [
            'id'         => (string) $p->id,
            'name'       => $p->name,
            'shop'       => $p->vendor?->shop_name ?? $p->vendor?->name ?? '',
            'shop_slug'  => $p->vendor?->slug,
            'price'      => number_format((float) $p->price, 0, ',', ' ') . ' F',
            'price_raw'  => (float) $p->price,
            'image'      => $p->image_path,
            'type'       => $p->type,
            'delivery_fee' => (float) ($p->delivery_fee ?? 0),
        ]);

        return response()->json([
            'message'  => $results->isEmpty()
                ? 'Aucun produit trouvé pour "' . $validated['query'] . '".'
                : $results->count() . ' produit(s) trouvé(s).',
            'products' => $results,
        ]);
    }

    /**
     * POST /tracy/negotiate — Lance une négociation de prix.
     */
    public function negotiate(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'product_id'    => 'required|exists:products,id',
            'offered_price' => 'required|numeric|min:100',
        ]);

        $product = Product::with('vendor:id,name,shop_name,bot_plan')->findOrFail($validated['product_id']);
        $originalPrice = (float) $product->price;
        $offeredPrice = (float) $validated['offered_price'];

        // Règles de négociation selon le plan du vendeur
        $vendorPlan = $product->vendor?->bot_plan ?? 'free';
        $maxDiscountPercent = match ($vendorPlan) {
            'pro'      => 15.0,
            'standard' => 12.0,
            'starter'  => 8.0,
            default    => 5.0,
        };

        $maxDiscount = $originalPrice * ($maxDiscountPercent / 100);
        $minAcceptablePrice = $originalPrice - $maxDiscount;

        // Si le prix offert est acceptable
        if ($offeredPrice >= $minAcceptablePrice) {
            $discountPercent = round((($originalPrice - $offeredPrice) / $originalPrice) * 100, 1);
            return response()->json([
                'message' => "Tracy a négocié pour vous ! Le vendeur accepte {$offeredPrice} F (−{$discountPercent}%).",
                'offer' => [
                    'price'            => (int) $offeredPrice,
                    'original_price'   => (int) $originalPrice,
                    'discount_percent' => $discountPercent,
                    'is_best_price'    => true,
                ],
            ]);
        }

        // Contre-offre : prix minimum du vendeur
        $counterOffer = (int) ceil($minAcceptablePrice);
        $discountPercent = round((($originalPrice - $counterOffer) / $originalPrice) * 100, 1);

        return response()->json([
            'message' => "Le vendeur propose {$counterOffer} F (−{$discountPercent}%). C'est son meilleur prix. Ça vous va ?",
            'offer' => [
                'price'            => $counterOffer,
                'original_price'   => (int) $originalPrice,
                'discount_percent' => $discountPercent,
                'is_best_price'    => true,
            ],
        ]);
    }

    /**
     * Fallback chat quand Tracy Core est indisponible.
     */
    private function fallbackChat(string $message): JsonResponse
    {
        $messageLower = strtolower($message);

        // Détection d'intention basique
        if (str_contains($messageLower, 'bonjour') || str_contains($messageLower, 'salut') || str_contains($messageLower, 'hello')) {
            return response()->json([
                'type' => 'text',
                'text' => 'Bonjour ! Je suis Tracy, votre assistante shopping MANTOTA. Que recherchez-vous aujourd\'hui ?',
            ]);
        }

        if (str_contains($messageLower, 'chercher') || str_contains($messageLower, 'recherche') || str_contains($messageLower, 'je veux')) {
            return response()->json([
                'type' => 'text',
                'text' => 'Dites-moi quel produit vous cherchez et je le trouverai pour vous parmi toutes les boutiques MANTOTA !',
            ]);
        }

        if (str_contains($messageLower, 'commande') || str_contains($messageLower, 'livraison')) {
            return response()->json([
                'type' => 'text',
                'text' => 'Vous pouvez suivre vos commandes dans l\'onglet "Commandes". Les fonds sont sécurisés en escrow jusqu\'à confirmation de réception.',
            ]);
        }

        return response()->json([
            'type' => 'text',
            'text' => 'Je suis là pour vous aider à trouver les meilleurs produits sur MANTOTA. Décrivez-moi ce que vous cherchez !',
        ]);
    }

    /**
     * POST /tracy/config — Sauvegarde la configuration Tracy du vendeur.
     */
    public function saveConfig(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'mode'             => 'required|string|in:discovery,active,pro',
            'personality_tags' => 'nullable|array',
            'auto_messages'    => 'nullable|array',
        ]);

        $user = $request->user();

        // Stocker la config dans les settings du user (ou table dédiée)
        // Pour l'instant, on utilise les colonnes existantes ou une approche JSON
        $config = [
            'tracy_mode'          => $validated['mode'],
            'tracy_personality'   => $validated['personality_tags'] ?? [],
            'tracy_auto_messages' => $validated['auto_messages'] ?? [],
        ];

        // Sauvegarder via un champ JSON sur l'utilisateur ou une table
        // On utilise les user_settings existantes si disponibles
        \DB::table('user_settings')->updateOrInsert(
            ['user_id' => $user->id, 'key' => 'tracy_config'],
            ['value' => json_encode($config), 'updated_at' => now()],
        );

        return response()->json([
            'ok'     => true,
            'config' => $config,
        ]);
    }

    /**
     * GET /tracy/config — Récupère la configuration Tracy du vendeur.
     */
    public function getConfig(Request $request): JsonResponse
    {
        $user = $request->user();

        $setting = \DB::table('user_settings')
            ->where('user_id', $user->id)
            ->where('key', 'tracy_config')
            ->first();

        if ($setting) {
            $config = json_decode($setting->value, true);
            return response()->json(['config' => $config]);
        }

        // Config par défaut
        return response()->json([
            'config' => [
                'mode'             => 'active',
                'personality_tags' => ['Amicale', 'Directe'],
                'auto_messages'    => ['Message de bienvenue', 'Confirmation commande'],
            ],
        ]);
    }

    /**
     * POST /tracy/identify-product — Identifie un produit à partir d'une photo.
     *
     * Le client envoie une photo (ex: screenshot de live TikTok), Tracy Core
     * la compare avec le catalogue du vendeur via CLIP + YOLOv8.
     */
    public function identifyProduct(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'image_base64' => 'required|string',
            'vendor_id'    => 'required|integer|exists:users,id',
        ]);

        $tracyUrl = config('services.tracy_core.url', 'http://127.0.0.1:8001');
        $tracyApiKey = config('services.tracy_core.api_key', '');

        // Récupérer les embeddings du vendeur depuis la base
        $embeddings = \App\Models\ProductImageEmbedding::where('vendor_id', $validated['vendor_id'])
            ->with('product:id,name,price,image_path')
            ->get();

        if ($embeddings->isEmpty()) {
            return response()->json([
                'matched' => false,
                'not_found' => true,
                'message' => "Ce vendeur n'a pas encore de catalogue avec photos. Je ne peux pas identifier le produit.",
            ]);
        }

        // Construire les embeddings pour Tracy Core
        $catalogEmbeddings = $embeddings->map(fn ($e) => [
            'product_id' => (string) $e->product_id,
            'store_id' => (string) $e->vendor_id,
            'embedding' => $e->embedding,
            'image_url' => $e->product?->image_path
                ? asset('storage/' . $e->product->image_path)
                : ($e->image_url ?? ''),
            'augmented' => $e->is_augmented,
        ])->toArray();

        try {
            $response = Http::withHeaders([
                'Content-Type' => 'application/json',
                'X-Api-Key' => $tracyApiKey,
            ])->timeout(30)->post($tracyUrl . '/vision/identify-product', [
                'image_base64' => $validated['image_base64'],
                'store_id' => (string) $validated['vendor_id'],
                'catalog_embeddings' => $catalogEmbeddings,
            ]);

            if (!$response->successful()) {
                return response()->json([
                    'matched' => false,
                    'not_found' => true,
                    'message' => "Désolé, je n'ai pas pu analyser la photo. Pouvez-vous la renvoyer ?",
                ], 500);
            }

            $result = $response->json();

            // Enrichir avec les vraies infos produits depuis la base
            if (!empty($result['top_matches'])) {
                foreach ($result['top_matches'] as &$match) {
                    $product = Product::find($match['product_id']);
                    if ($product) {
                        $match['product_name'] = $product->name;
                        $match['price'] = (float) $product->price;
                        $match['image_url'] = $product->image_path
                            ? asset('storage/' . $product->image_path)
                            : null;
                        $match['stock'] = (int) ($product->stock ?? 0);
                    }
                }
            }

            // Générer le message pour le client
            if ($result['matched'] && !empty($result['top_matches'])) {
                $best = $result['top_matches'][0];
                $result['message'] = "Je vois ce produit : \"{$best['product_name']}\" à " . number_format($best['price'], 0, ',', ' ') . " FCFA. C'est bien ce que vous cherchez ?";
            } elseif ($result['needs_confirmation'] && !empty($result['top_matches'])) {
                $best = $result['top_matches'][0];
                $result['message'] = "Je pense que c'est \"{$best['product_name']}\" à " . number_format($best['price'], 0, ',', ' ') . " FCFA. Est-ce bien le produit que vous voulez ?";
            } elseif ($result['not_found']) {
                $result['message'] = "Je n'ai pas trouvé ce produit dans la boutique. Voulez-vous que je demande au vendeur ? Ou décrivez-moi ce que vous cherchez.";
            }

            return response()->json($result);
        } catch (\Exception $e) {
            return response()->json([
                'matched' => false,
                'not_found' => true,
                'message' => "Je n'ai pas pu analyser la photo pour le moment. Pouvez-vous décrire le produit que vous cherchez ?",
            ], 500);
        }
    }

    /**
     * POST /tracy/check-conformity — Vérifie la conformité post-livraison.
     *
     * Après livraison, Tracy demande au client si le produit correspond à la photo.
     * Si non, le client envoie une photo du produit reçu pour comparaison.
     */
    public function checkConformity(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'order_id'              => 'required|string',
            'product_id'            => 'required|integer|exists:products,id',
            'store_id'              => 'required|integer|exists:users,id',
            'verdict'               => 'required|string|in:conform,partial,non_conform',
            'received_photo_base64' => 'nullable|string',
            'catalog_photo_base64'  => 'nullable|string',
        ]);

        $tracyUrl = config('services.tracy_core.url', 'http://127.0.0.1:8001');
        $tracyApiKey = config('services.tracy_core.api_key', '');

        try {
            $response = Http::withHeaders([
                'Content-Type' => 'application/json',
                'X-Api-Key' => $tracyApiKey,
            ])->timeout(30)->post($tracyUrl . '/vision/check-conformity', $validated);

            if (!$response->successful()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Erreur lors de la vérification de conformité.',
                ], 500);
            }

            $result = $response->json();

            // Enregistrer le signal côté Laravel aussi (double-write pour cohérence)
            $signalType = match ($validated['verdict']) {
                'conform' => 'photo_confirmed',
                'partial' => 'photo_partial',
                'non_conform' => 'photo_non_conform',
                default => 'photo_confirmed',
            };

            \App\Models\ShopQualitySignal::create([
                'store_id' => $validated['store_id'],
                'signal_type' => $signalType,
                'weight' => \App\Models\ShopQualitySignal::getWeight($signalType),
                'product_id' => $validated['product_id'],
                'description' => "Verdict client: {$validated['verdict']}, order: {$validated['order_id']}",
            ]);

            // Si admin notifié, on stocke l'info
            if (!empty($result['admin_notification'])) {
                \Log::warning('conformity_admin_alert', [
                    'order_id' => $validated['order_id'],
                    'store_id' => $validated['store_id'],
                    'notification' => $result['admin_notification'],
                ]);
            }

            return response()->json($result);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Service de vérification indisponible. Votre retour a été enregistré.',
                'client_verdict' => $validated['verdict'],
            ], 500);
        }
    }

    /**
     * GET /tracy/shop-quality — Récupère le score de qualité de la boutique du vendeur.
     */
    public function getShopQuality(Request $request): JsonResponse
    {
        $user = $request->user();
        $storeId = $user->id;

        $signals = \App\Models\ShopQualitySignal::where('store_id', $storeId)
            ->where('created_at', '>=', now()->subDays(30))
            ->orderByDesc('created_at')
            ->get();

        $score = 100 + $signals->sum('weight');
        $score = max(0, min(100, $score));

        $level = match (true) {
            $score >= 80 => 'excellent',
            $score >= 60 => 'good',
            $score >= 40 => 'warning',
            $score >= 20 => 'risk',
            default => 'suspended',
        };

        return response()->json([
            'score' => $score,
            'level' => $level,
            'positive_signals' => $signals->where('weight', '>', 0)->count(),
            'negative_signals' => $signals->where('weight', '<', 0)->count(),
            'recent_signals' => $signals->take(10)->map(fn ($s) => [
                'type' => $s->signal_type,
                'weight' => $s->weight,
                'description' => $s->description,
                'date' => $s->created_at?->toIso8601String(),
            ]),
        ]);
    }

    // ── Restaurant proxy (Tracy Core) ──────────────────────────────

    /**
     * GET /tracy/restaurants — Liste les restaurants via Tracy Core.
     */
    public function listRestaurants(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'lat' => 'nullable|numeric',
            'lng' => 'nullable|numeric',
        ]);

        $tracyUrl = config('services.tracy_core.url', 'http://127.0.0.1:8001');
        $tracyApiKey = config('services.tracy_core.api_key', '');

        try {
            $response = Http::withHeaders([
                'X-Api-Key' => $tracyApiKey,
            ])->timeout(15)->get($tracyUrl . '/restaurant/list', array_filter($validated));

            if (!$response->successful()) {
                return $this->restaurantFallbackList();
            }

            return response()->json($response->json());
        } catch (\Exception $e) {
            return $this->restaurantFallbackList();
        }
    }

    /**
     * GET /tracy/restaurants/{restaurantId}/menu — Menu d'un restaurant via Tracy Core.
     */
    public function getRestaurantMenu(int $restaurantId): JsonResponse
    {
        $tracyUrl = config('services.tracy_core.url', 'http://127.0.0.1:8001');
        $tracyApiKey = config('services.tracy_core.api_key', '');

        try {
            $response = Http::withHeaders([
                'X-Api-Key' => $tracyApiKey,
            ])->timeout(15)->get($tracyUrl . "/restaurant/menu/{$restaurantId}");

            if (!$response->successful()) {
                return $this->restaurantFallbackMenu($restaurantId);
            }

            return response()->json($response->json());
        } catch (\Exception $e) {
            return $this->restaurantFallbackMenu($restaurantId);
        }
    }

    /**
     * POST /tracy/restaurants/order — Crée une commande restaurant via Tracy Core.
     */
    public function createRestaurantOrder(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'restaurant_id'       => 'required|integer',
            'order_type'          => 'required|string|in:delivery,pickup',
            'items'               => 'required|array|min:1',
            'items.*.menu_item_id' => 'required|string',
            'items.*.quantity'     => 'required|integer|min:1',
            'items.*.selected_options' => 'nullable|array',
            'items.*.special_instructions' => 'nullable|string|max:500',
            'delivery_address'    => 'nullable|string|max:500',
            'delivery_latitude'   => 'nullable|numeric',
            'delivery_longitude'  => 'nullable|numeric',
            'notes'               => 'nullable|string|max:1000',
        ]);

        $user = $request->user();
        $tracyUrl = config('services.tracy_core.url', 'http://127.0.0.1:8001');
        $tracyApiKey = config('services.tracy_core.api_key', '');

        try {
            $response = Http::withHeaders([
                'Content-Type' => 'application/json',
                'X-Api-Key' => $tracyApiKey,
            ])->timeout(20)->post($tracyUrl . '/restaurant/order', [
                'restaurant_id'      => (string) $validated['restaurant_id'],
                'customer_id'        => (string) $user->id,
                'order_type'         => $validated['order_type'],
                'items'              => $validated['items'],
                'delivery_address'   => $validated['delivery_address'] ?? null,
                'delivery_latitude'  => $validated['delivery_latitude'] ?? null,
                'delivery_longitude' => $validated['delivery_longitude'] ?? null,
                'notes'              => $validated['notes'] ?? null,
            ]);

            if (!$response->successful()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Impossible de créer la commande pour le moment.',
                ], 500);
            }

            return response()->json($response->json());
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Service restaurant temporairement indisponible.',
            ], 500);
        }
    }

    /**
     * GET /tracy/restaurants/order/{orderId} — Statut d'une commande restaurant via Tracy Core.
     */
    public function getRestaurantOrderStatus(string $orderId): JsonResponse
    {
        $tracyUrl = config('services.tracy_core.url', 'http://127.0.0.1:8001');
        $tracyApiKey = config('services.tracy_core.api_key', '');

        try {
            $response = Http::withHeaders([
                'X-Api-Key' => $tracyApiKey,
            ])->timeout(10)->get($tracyUrl . "/restaurant/order/{$orderId}");

            if (!$response->successful()) {
                return response()->json([
                    'id' => $orderId,
                    'status' => 'unknown',
                    'message' => 'Statut de commande indisponible.',
                ], 500);
            }

            return response()->json($response->json());
        } catch (\Exception $e) {
            return response()->json([
                'id' => $orderId,
                'status' => 'unknown',
                'message' => 'Service de suivi indisponible.',
            ], 500);
        }
    }

    /**
     * POST /tracy/shop-config — Met à jour la config boutique (dont address_form).
     */
    public function updateShopConfig(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'min_margin_percent'           => 'nullable|numeric|min:0|max:100',
            'first_order_discount_percent' => 'nullable|numeric|min:0|max:100',
            'max_discount_percent'         => 'nullable|numeric|min:0|max:100',
            'free_shipping_threshold'      => 'nullable|numeric|min:0',
            'auto_accept_below'            => 'nullable|numeric|min:0|max:100',
            'custom_rules'                 => 'nullable|string|max:1000',
            'currency'                     => 'nullable|string|size:3',
            'address_form'                 => 'nullable|string|in:tu,vous',
        ]);

        $user = $request->user();

        $config = \App\Models\ShopNegotiationConfig::updateOrCreate(
            ['store_id' => $user->id],
            array_filter($validated, fn ($v) => $v !== null),
        );

        return response()->json([
            'success' => true,
            'store_id' => (string) $user->id,
            'address_form' => $config->address_form ?? 'tu',
            'message' => 'Configuration mise à jour',
        ]);
    }

    /**
     * GET /tracy/shop-config — Récupère la config boutique (dont address_form).
     */
    public function getShopConfig(Request $request): JsonResponse
    {
        $user = $request->user();

        $config = \App\Models\ShopNegotiationConfig::where('store_id', $user->id)->first();

        if (!$config) {
            return response()->json([
                'store_id' => (string) $user->id,
                'min_margin_percent' => 10.0,
                'first_order_discount_percent' => 0.0,
                'max_discount_percent' => 15.0,
                'free_shipping_threshold' => null,
                'auto_accept_below' => 5.0,
                'custom_rules' => null,
                'currency' => 'XOF',
                'address_form' => 'tu',
            ]);
        }

        return response()->json([
            'store_id' => (string) $config->store_id,
            'min_margin_percent' => $config->min_margin_percent,
            'first_order_discount_percent' => $config->first_order_discount_percent,
            'max_discount_percent' => $config->max_discount_percent,
            'free_shipping_threshold' => $config->free_shipping_threshold,
            'auto_accept_below' => $config->auto_accept_below,
            'custom_rules' => $config->custom_rules,
            'currency' => $config->currency,
            'address_form' => $config->address_form ?? 'tu',
        ]);
    }

    // ── Fallbacks restaurant ──

    private function restaurantFallbackList(): JsonResponse
    {
        $restaurants = \App\Models\User::where('role', 'vendor')
            ->whereIn('shop_type', ['restaurant_online', 'restaurant_physical'])
            ->where('bot_status', 'active')
            ->limit(30)
            ->get();

        return response()->json([
            'restaurants' => $restaurants->map(fn ($r) => [
                'id' => (string) $r->id,
                'shop_name' => $r->shop_name ?? $r->name,
                'shop_logo' => $r->shop_logo_path ? asset('storage/' . $r->shop_logo_path) : null,
                'shop_type' => $r->shop_type,
                'address' => $r->shop_address,
                'is_open_now' => \App\Models\RestaurantHour::isOpenNow($r->id),
                'rating' => 4.5,
            ]),
        ]);
    }

    private function restaurantFallbackMenu(int $restaurantId): JsonResponse
    {
        $restaurant = \App\Models\User::find($restaurantId);
        if (!$restaurant) {
            return response()->json(['error' => 'Restaurant introuvable'], 404);
        }

        $categories = \App\Models\MenuCategory::where('restaurant_id', $restaurantId)
            ->where('is_active', true)
            ->with(['items' => fn ($q) => $q->where('is_available', true)->orderBy('sort_order')])
            ->orderBy('sort_order')
            ->get();

        return response()->json([
            'restaurant_id' => (string) $restaurantId,
            'shop_name' => $restaurant->shop_name ?? $restaurant->name,
            'is_open_now' => \App\Models\RestaurantHour::isOpenNow($restaurantId),
            'categories' => $categories->map(fn ($c) => [
                'id' => (string) $c->id,
                'name' => $c->name,
                'items' => $c->items->map(fn ($i) => [
                    'id' => (string) $i->id,
                    'name' => $i->name,
                    'description' => $i->description,
                    'price' => (float) $i->price,
                    'image_url' => $i->image_path ? asset('storage/' . $i->image_path) : null,
                    'is_available' => $i->is_available,
                ]),
            ]),
        ]);
    }
}
