<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Mobile;

use App\Http\Controllers\Controller;
use App\Models\Product;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

/**
 * MobileStoreController — API boutique vendeur pour l'application mobile MANTOTA.
 *
 * Gère :
 *  - Récupération de la boutique du vendeur connecté
 *  - Mise à jour des informations de boutique
 *  - Génération et partage du lien de boutique
 *  - Produits du vendeur (catalogue)
 *  - Statistiques de la boutique
 */
class MobileStoreController extends Controller
{
    /**
     * GET /vendor/store — Boutique du vendeur connecté.
     */
    public function show(Request $request): JsonResponse
    {
        $user = $request->user();

        $store = $this->buildStoreData($user);
        $products = $this->getVendorProducts($user->id);

        return response()->json([
            'store'    => $store,
            'products' => $products,
        ]);
    }

    /**
     * PUT /vendor/store — Met à jour les informations de la boutique.
     */
    public function update(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'shop_name'        => 'nullable|string|max:255',
            'shop_type'        => 'nullable|string|in:physical,digital,hybrid',
            'shop_address'     => 'nullable|string|max:500',
            'shop_logo_path'   => 'nullable|string|max:500',
            'shop_theme'       => 'nullable|string|max:50',
            'shop_display_format' => 'nullable|string|max:50',
            'business_name'    => 'nullable|string|max:255',
            'ifu_or_rccm'      => 'nullable|string|max:100',
            'shop_latitude'    => 'nullable|numeric',
            'shop_longitude'   => 'nullable|numeric',
        ]);

        $user = $request->user();

        // Générer un slug si le shop_name change et n'a pas encore de slug
        if (isset($validated['shop_name']) && empty($user->slug)) {
            $validated['slug'] = $this->generateUniqueSlug($validated['shop_name']);
        } elseif (isset($validated['shop_name']) && $user->slug) {
            // Régénérer le slug si le nom change significativement
            $newSlug = $this->generateUniqueSlug($validated['shop_name'], $user->id);
            if ($newSlug !== $user->slug) {
                $validated['slug'] = $newSlug;
            }
        }

        $user->update($validated);

        return response()->json([
            'store' => $this->buildStoreData($user->fresh()),
        ]);
    }

    /**
     * GET /vendor/store/share — Génère et retourne le lien partageable de la boutique.
     */
    public function shareLink(Request $request): JsonResponse
    {
        $user = $request->user();

        // S'assurer qu'un slug existe
        if (empty($user->slug)) {
            $slug = $this->generateUniqueSlug($user->shop_name ?? $user->display_name ?? $user->name, $user->id);
            $user->update(['slug' => $slug]);
            $user->refresh();
        }

        $storeUrl = config('app.url') . '/store/' . $user->slug;

        $shareText = "🛍️ Découvrez ma boutique « {$user->shop_name} » sur MANTOTA !\n"
            . "Consultez mes produits et commandez en toute sécurité.\n"
            . "👉 {$storeUrl}";

        return response()->json([
            'store_url'  => $storeUrl,
            'store_slug' => $user->slug,
            'share_text' => $shareText,
            'qr_code_url'=> "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=" . urlencode($storeUrl),
        ]);
    }

    /**
     * GET /vendor/store/stats — Statistiques de la boutique.
     */
    public function stats(Request $request): JsonResponse
    {
        $user = $request->user();

        $totalProducts = Product::where('vendor_id', $user->id)->count();
        $activeProducts = Product::where('vendor_id', $user->id)
            ->where('status', 'active')
            ->count();

        $totalOrders = \App\Models\Order::where('vendor_id', $user->id)->count();
        $pendingOrders = \App\Models\Order::where('vendor_id', $user->id)
            ->where('status', 'pending')
            ->count();
        $deliveredOrders = \App\Models\Order::where('vendor_id', $user->id)
            ->where('status', 'delivered')
            ->count();

        $revenue = \App\Models\Order::where('vendor_id', $user->id)
            ->where('status', 'delivered')
            ->sum('vendor_earnings');

        $escrowAmount = \App\Models\Order::where('vendor_id', $user->id)
            ->whereIn('status', ['pending', 'shipped'])
            ->sum('vendor_earnings');

        // Rating moyen (si table de reviews existe)
        $rating = 5.0; // TODO: implémenter reviews

        return response()->json([
            'total_products'   => $totalProducts,
            'active_products'  => $activeProducts,
            'total_orders'     => $totalOrders,
            'pending_orders'   => $pendingOrders,
            'delivered_orders' => $deliveredOrders,
            'revenue'          => (float) $revenue,
            'escrow_amount'    => (float) $escrowAmount,
            'rating'           => $rating,
            'plan'             => $user->bot_plan ?? 'free',
        ]);
    }

    /**
     * GET /stores/{slug} — Boutique publique par slug (pour l'APK et le web).
     */
    public function publicStore(string $slug): JsonResponse
    {
        $vendor = User::where('slug', $slug)
            ->whereHas('modes', function ($q) {
                $q->where('mode', 'vendor')->where('is_active', true);
            })
            ->first();

        if (!$vendor) {
            return response()->json(['message' => 'Boutique introuvable.'], 404);
        }

        $store = $this->buildStoreData($vendor);
        $products = $this->getVendorProducts($vendor->id);

        return response()->json([
            'store'    => $store,
            'products' => $products,
        ]);
    }

    /**
     * Construit les données de la boutique à partir du modèle User.
     */
    private function buildStoreData(User $user): array
    {
        $productCount = Product::where('vendor_id', $user->id)->count();

        return [
            'id'              => $user->id,
            'name'            => $user->shop_name ?? $user->display_name ?? $user->name,
            'slug'            => $user->slug,
            'type'            => $user->shop_type ?? 'physical',
            'address'         => $user->shop_address,
            'latitude'        => $user->shop_latitude,
            'longitude'       => $user->shop_longitude,
            'logo_path'       => $user->shop_logo_path,
            'theme'           => $user->shop_theme ?? 'default',
            'display_format'  => $user->shop_display_format ?? 'grid',
            'business_name'   => $user->business_name,
            'ifu_or_rccm'     => $user->ifu_or_rccm,
            'rating'          => 5.0,
            'product_count'   => $productCount,
            'plan'            => $user->bot_plan ?? 'free',
            'store_url'       => $user->slug ? config('app.url') . '/store/' . $user->slug : null,
            'vendor_phone'    => $user->phone,
            'vendor_name'     => $user->display_name ?? $user->name,
        ];
    }

    /**
     * Récupère les produits actifs du vendeur.
     */
    private function getVendorProducts(int $vendorId): array
    {
        return Product::where('vendor_id', $vendorId)
            ->where('status', 'active')
            ->with('images')
            ->orderByDesc('created_at')
            ->get()
            ->map(fn ($p) => [
                'id'            => $p->id,
                'name'          => $p->name,
                'description'   => $p->description,
                'price'         => (float) $p->price,
                'type'          => $p->type,
                'stock'         => $p->stock,
                'delivery_fee'  => (float) ($p->delivery_fee ?? 0),
                'image_path'    => $p->image_path,
                'images'        => $p->images->pluck('path')->toArray(),
            ])
            ->toArray();
    }

    /**
     * Génère un slug unique pour la boutique.
     */
    private function generateUniqueSlug(string $name, ?int $excludeId = null): string
    {
        $base = Str::slug($name);
        if (empty($base)) {
            $base = 'store-' . Str::lower(Str::random(6));
        }

        $slug = $base;
        $counter = 1;

        $query = User::where('slug', $slug);
        if ($excludeId) {
            $query->where('id', '!=', $excludeId);
        }

        while ($query->exists()) {
            $slug = $base . '-' . $counter++;
            $query = User::where('slug', $slug);
            if ($excludeId) {
                $query->where('id', '!=', $excludeId);
            }
        }

        return $slug;
    }
}
