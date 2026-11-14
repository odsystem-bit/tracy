<?php

declare(strict_types=1);

namespace App\Http\Controllers\Public;

use App\Http\Controllers\Controller;
use App\Models\Product;
use App\Models\User;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response as InertiaResponse;

class ShopController extends Controller
{
    /**
     * Affiche la boutique publique d'un vendeur via son slug.
     *
     * Si l'URL contient ?ref=influencer_id, l'ID est stocke en session
     * pour crediter la commission lors d'un futur achat.
     */
    public function show(Request $request, string $vendorSlug): InertiaResponse
    {
        $vendor = User::where('slug', $vendorSlug)
            ->where('role', 'vendor')
            ->select('id', 'name', 'slug', 'business_name', 'shop_name', 'shop_logo_path', 'shop_display_format', 'shop_theme', 'is_ambassador', 'phone')
            ->firstOrFail();

        // ── Tracking partenaire ──────────────────
        $ref = $request->query('ref');
        if ($ref && is_numeric($ref)) {
            $referrerId = (int) $ref;
            // Verifier que le referent est bien un créateur de contenu existant
            $exists = User::where('id', $referrerId)
                ->where('role', 'influencer')
                ->exists();
            if ($exists) {
                session(['partner_referrer' => $referrerId]);
            }
        }

        // ── Tracking campagne (pour attribution Big Data) ──
        $campaignParam = $request->query('campaign');
        if ($campaignParam && is_numeric($campaignParam)) {
            session(['campaign_id' => (int) $campaignParam]);
        }

        $products = Product::where('vendor_id', $vendor->id)
            ->with('images:id,product_id,path,sort_order')
            ->latest()
            ->get();

        return Inertia::render('Shop/Show', [
            'vendor'   => $vendor,
            'products' => $products,
            'seo' => [
                'title' => 'Boutique ' . ($vendor->business_name ?: $vendor->name) . ' — MANTOTA',
                'description' => 'Decouvrez les produits de ' . ($vendor->business_name ?: $vendor->name) . ' sur MANTOTA. Achat securise par sequestre, livraison rapide au Benin et en Afrique.',
                'og_type' => 'profile',
                'jsonld' => [
                    '@context' => 'https://schema.org',
                    '@type' => 'Store',
                    'name' => $vendor->business_name ?: $vendor->name,
                    'url' => url('/shop/' . $vendor->slug),
                    'image' => $vendor->shop_logo_path ? url('/storage/' . $vendor->shop_logo_path) : null,
                    'description' => 'Boutique de ' . ($vendor->business_name ?: $vendor->name) . ' sur MANTOTA.',
                    'parentOrganization' => [
                        '@type' => 'Organization',
                        'name' => 'MANTOTA',
                        'url' => config('app.url'),
                    ],
                ],
            ],
        ]);
    }

    /**
     * Affiche une fiche produit individuelle publique (partageable).
     * Route: /shop/{vendorSlug}/p/{product}
     */
    public function productShow(string $vendorSlug, string $product): InertiaResponse
    {
        $vendor = User::where('slug', $vendorSlug)
            ->where('role', 'vendor')
            ->select('id', 'name', 'slug', 'business_name', 'shop_name', 'shop_logo_path', 'shop_display_format', 'shop_theme', 'is_ambassador', 'phone')
            ->firstOrFail();

        $productModel = Product::where('vendor_id', $vendor->id)
            ->where('id', $product)
            ->with('images:id,product_id,path,sort_order')
            ->firstOrFail();

        // Produits similaires du même vendeur (max 4)
        $related = Product::where('vendor_id', $vendor->id)
            ->where('id', '!=', $productModel->id)
            ->with('images:id,product_id,path,sort_order')
            ->latest()
            ->take(4)
            ->get();

        return Inertia::render('Shop/Product', [
            'vendor'   => $vendor,
            'product'  => $productModel,
            'related'  => $related,
            'seo' => [
                'title' => ($productModel->name ?? 'Produit') . ' — ' . ($vendor->shop_name ?: $vendor->business_name ?: $vendor->name) . ' | MANTOTA',
                'description' => mb_substr(strip_tags($productModel->description ?? ''), 0, 160) ?: 'Produit disponible sur MANTOTA. Achat sécurisé par séquestre.',
                'og_type' => 'product',
                'jsonld' => [
                    '@context' => 'https://schema.org',
                    '@type' => 'Product',
                    'name' => $productModel->name,
                    'description' => mb_substr(strip_tags($productModel->description ?? ''), 0, 300),
                    'image' => $productModel->images->first() ? url('/storage/' . $productModel->images->first()->path) : null,
                    'offers' => [
                        '@type' => 'Offer',
                        'price' => $productModel->price,
                        'priceCurrency' => 'XOF',
                        'availability' => ($productModel->type === 'physical' && $productModel->stock === 0)
                            ? 'https://schema.org/OutOfStock'
                            : 'https://schema.org/InStock',
                    ],
                    'seller' => [
                        '@type' => 'Store',
                        'name' => $vendor->shop_name ?: $vendor->business_name ?: $vendor->name,
                        'url' => url('/shop/' . $vendor->slug),
                    ],
                ],
            ],
        ]);
    }
}
