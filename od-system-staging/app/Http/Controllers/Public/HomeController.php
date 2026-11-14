<?php

declare(strict_types=1);

namespace App\Http\Controllers\Public;

use App\Http\Controllers\Controller;
use App\Models\Category;
use App\Models\Order;
use App\Models\Product;
use App\Models\Testimonial;
use App\Models\User;
use Illuminate\Support\Facades\Cache;
use Inertia\Inertia;
use Inertia\Response;

class HomeController extends Controller
{
    public function index(): Response
    {
        $stats = Cache::remember('home_stats', 300, function () {
            return [
                'vendors_count'  => User::where('role', 'vendor')->count(),
                'total_buyers'   => Order::distinct('customer_phone')->count('customer_phone'),
                'products_count' => Product::count(),
            ];
        });

        $shops = Cache::remember('home_shops', 300, function () {
            return User::where('role', 'vendor')
                ->whereNotNull('shop_name')
                ->where('shop_name', '!=', '')
                ->withCount(['products as products_count' => function ($q) {
                    $q->where('stock', '>', 0);
                }])
                ->orderByDesc('created_at')
                ->limit(6)
                ->get(['id', 'shop_name', 'shop_type', 'country', 'shop_address', 'shop_logo_path'])
                ->map(fn ($u) => [
                    'name'      => $u->shop_name,
                    'category'  => $u->shop_type ?? 'Boutique',
                    'location'  => $u->country ?? $u->shop_address ?? '—',
                    'country'   => $u->country,
                    'rating'    => '4.5',
                    'slug'      => $u->id,
                    'image_url' => $u->shop_logo_path ? asset('storage/' . $u->shop_logo_path) : null,
                ])
                ->toArray();
        });

        $trending = Cache::remember('home_trending', 300, function () {
            return Product::where('stock', '>', 0)
                ->with('vendor:id,country')
                ->withCount(['orders as orders_count'])
                ->orderByDesc('orders_count')
                ->orderByDesc('created_at')
                ->limit(8)
                ->get(['id', 'name', 'price', 'type', 'vendor_id', 'image_path'])
                ->map(fn ($p) => [
                    'id'        => $p->id,
                    'name'      => $p->name,
                    'price'     => number_format((float) $p->price, 0, '', ' ') . ' F',
                    'raw_price' => (float) $p->price,
                    'category'  => $p->type ?? 'Produit',
                    'country'   => $p->vendor?->country,
                    'store_id'  => (string) $p->vendor_id,
                    'image_url' => $p->image_path ? asset('storage/' . $p->image_path) : null,
                ])
                ->toArray();
        });

        $categories = Cache::remember('home_categories', 300, function () {
            return Category::where('is_active', true)
                ->orderBy('sort_order')
                ->get(['name', 'slug', 'icon'])
                ->map(fn ($c) => [
                    'name' => $c->name,
                    'slug' => $c->slug,
                    'svg'  => $c->icon ?? 'tag',
                ])
                ->toArray();
        });

        return Inertia::render('Welcome', array_merge($stats, [
            'testimonials' => Testimonial::where('is_active', true)->orderBy('sort_order')->get(['id', 'name', 'role', 'content', 'rating']),
            'shops'        => $shops,
            'trending'     => $trending,
            'categories'   => $categories,
        ]));
    }
}
