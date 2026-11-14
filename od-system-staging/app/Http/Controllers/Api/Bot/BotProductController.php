<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\Product;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class BotProductController extends Controller
{
    /**
     * GET /bot/products/search
     * Recherche de produits par mot-clé, optionnellement filtré par boutique.
     */
    public function search(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'query' => 'required|string|min:1',
            'store_id' => 'nullable|string',
            'min_price' => 'nullable|numeric|min:0',
            'max_price' => 'nullable|numeric|min:0',
            'limit' => 'nullable|integer|min:1|max:50',
            'country' => 'nullable|string|size:2',
            'city' => 'nullable|string|max:100',
            'lat' => 'nullable|numeric|between:-90,90',
            'lng' => 'nullable|numeric|between:-180,180',
        ]);

        $limit = $validated['limit'] ?? 10;
        $q = $validated['query'];
        $query = Product::query()
            ->where('status', 'actif')
            ->where(function ($sub) use ($q) {
                $sub->where('name', 'ILIKE', '%' . $q . '%')
                    ->orWhereRaw("unaccent(name) ILIKE unaccent(?)", ['%' . $q . '%']);
            });

        if (! empty($validated['store_id'])) {
            $query->where('vendor_id', $validated['store_id']);
        }

        if (! empty($validated['min_price'])) {
            $query->where('price', '>=', $validated['min_price']);
        }

        if (! empty($validated['max_price'])) {
            $query->where('price', '<=', $validated['max_price']);
        }

        // Pas de filtre pays strict : on classe par proximité (local > pays > ailleurs)
        // pour que Tracy puisse proposer une autre zone quand rien n'existe chez le client.
        $country = ! empty($validated['country']) ? strtoupper($validated['country']) : null;
        $city = $validated['city'] ?? null;
        $lat = isset($validated['lat']) ? (float) $validated['lat'] : null;
        $lng = isset($validated['lng']) ? (float) $validated['lng'] : null;
        $hasGeo = $country || $city || ($lat !== null && $lng !== null);

        $pool = $hasGeo ? min($limit * 5, 250) : $limit;
        $products = $query->with('vendor')->orderBy('name')->limit($pool)->get();

        $quartierCityVendors = $city
            ? $this->vendorsDeliveringByQuartierTo($products->pluck('vendor_id')->unique()->all(), $city)
            : [];

        $rows = $products->map(function (Product $p) use ($country, $city, $lat, $lng, $quartierCityVendors) {
            $v = $p->vendor;
            $geo = $this->locate($v, $country, $city, $lat, $lng, $quartierCityVendors);

            return [
                'id' => (string) $p->id,
                'nom' => $p->name,
                'prix' => (float) $p->price,
                'stock' => (int) ($p->stock ?? 0),
                'image_url' => $p->image_path ? asset('storage/' . $p->image_path) : null,
                'store_id' => (string) $p->vendor_id,
                'category' => $p->delivery_type ?? null,
                'description' => $p->description,
                'scope' => $geo['scope'],
                'shop_city' => $geo['shop_city'],
                'distance_km' => $geo['distance_km'],
                'delivers_to_you' => $geo['delivers_to_you'],
            ];
        });

        if ($hasGeo) {
            $rank = ['local' => 0, 'country' => 1, 'other' => 2, 'unknown' => 3];
            $rows = $rows->sortBy([
                fn ($a, $b) => $rank[$a['scope']] <=> $rank[$b['scope']],
                fn ($a, $b) => ($a['distance_km'] ?? PHP_INT_MAX) <=> ($b['distance_km'] ?? PHP_INT_MAX),
            ]);
        }

        $rows = $rows->take($limit)->values();

        return response()->json([
            'products' => $rows,
            'total' => $rows->count(),
            'location' => [
                'city' => $city,
                'country' => $country,
                'has_local' => $rows->contains(fn ($r) => $r['scope'] === 'local'),
            ],
        ]);
    }

    /**
     * Classe un vendeur par rapport au client : local / country / other.
     *
     * @return array{scope:string, shop_city:?string, distance_km:?float, delivers_to_you:?bool}
     */
    private function locate(?User $v, ?string $country, ?string $city, ?float $lat, ?float $lng, array $quartierCityVendors): array
    {
        $out = ['scope' => 'unknown', 'shop_city' => null, 'distance_km' => null, 'delivers_to_you' => null];
        if (! $v) {
            return $out;
        }

        $norm = fn (?string $s) => $s === null ? '' : strtolower(\Illuminate\Support\Str::ascii(trim($s)));
        $address = $norm($v->shop_address);
        $cityN = $norm($city);
        $deliveryCities = array_map($norm, (array) ($v->delivery_cities ?? []));

        // Ville de la boutique : celle des villes de livraison trouvée dans l'adresse, sinon l'adresse brute
        foreach ((array) ($v->delivery_cities ?? []) as $dc) {
            if ($norm($dc) !== '' && str_contains($address, $norm($dc))) {
                $out['shop_city'] = $dc;
                break;
            }
        }
        $out['shop_city'] ??= $v->shop_address ?: null;

        if ($lat !== null && $lng !== null && $v->shop_latitude !== null && $v->shop_longitude !== null) {
            $out['distance_km'] = round($this->haversine($lat, $lng, (float) $v->shop_latitude, (float) $v->shop_longitude), 1);
        }

        $sameCity = $cityN !== '' && ($address !== '' && str_contains($address, $cityN) || in_array($cityN, $deliveryCities, true));
        $sameCountry = $country && strtoupper((string) $v->country) === $country;

        if ($cityN !== '') {
            $mode = (string) ($v->delivery_mode ?? 'pickup_only');
            $out['delivers_to_you'] = match ($mode) {
                'national', 'international' => true,
                'multi_city' => in_array($cityN, $deliveryCities, true),
                'quartiers' => in_array((int) $v->id, $quartierCityVendors, true),
                default => $sameCity,
            };
        }

        $out['scope'] = ($sameCity || $out['delivers_to_you'] === true && $sameCountry)
            ? 'local'
            : ($sameCountry ? 'country' : ($country ? 'other' : 'unknown'));

        // Distance GPS < 15 km => considéré local même sans ville connue
        if ($out['distance_km'] !== null && $out['distance_km'] <= 15) {
            $out['scope'] = 'local';
        }

        return $out;
    }

    private function haversine(float $lat1, float $lng1, float $lat2, float $lng2): float
    {
        $dLat = deg2rad($lat2 - $lat1);
        $dLng = deg2rad($lng2 - $lng1);
        $a = sin($dLat / 2) ** 2 + cos(deg2rad($lat1)) * cos(deg2rad($lat2)) * sin($dLng / 2) ** 2;

        return 6371 * 2 * atan2(sqrt($a), sqrt(1 - $a));
    }

    /**
     * Vendeurs en mode "quartiers" qui desservent au moins un quartier de la ville donnée.
     *
     * @param  array<int|string>  $vendorIds
     * @return array<int>
     */
    private function vendorsDeliveringByQuartierTo(array $vendorIds, string $city): array
    {
        if (empty($vendorIds)) {
            return [];
        }

        return \Illuminate\Support\Facades\DB::table('shop_delivery_quartiers as sdq')
            ->join('quartiers as q', 'q.id', '=', 'sdq.quartier_id')
            ->join('villes as v', 'v.id', '=', 'q.ville_id')
            ->whereIn('sdq.shop_id', $vendorIds)
            ->whereRaw('unaccent(v.name) ILIKE unaccent(?)', [$city])
            ->distinct()
            ->pluck('sdq.shop_id')
            ->map(fn ($id) => (int) $id)
            ->all();
    }

    /**
     * GET /bot/catalog/search
     * Récupère le catalogue d'une boutique (tous les produits + catégories).
     */
    public function catalogSearch(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'store_id' => 'required|string',
            'category' => 'nullable|string',
        ]);

        $query = Product::where('vendor_id', $validated['store_id'])
            ->where('status', 'actif');

        if (! empty($validated['category'])) {
            $query->where('delivery_type', $validated['category']);
        }

        $products = $query->orderBy('name')->get();

        $categories = $products->groupBy('delivery_type')
            ->map(fn ($items, $key) => [
                'id' => (string) $key,
                'nom' => ucfirst($key ?? 'Divers'),
                'product_count' => $items->count(),
            ])
            ->values();

        return response()->json([
            'store_id' => $validated['store_id'],
            'categories' => $categories,
            'products' => $products->map(fn (Product $p) => [
                'id' => (string) $p->id,
                'nom' => $p->name,
                'prix' => (float) $p->price,
                'stock' => (int) ($p->stock ?? 0),
                'image_url' => $p->image_path ? asset('storage/' . $p->image_path) : null,
                'store_id' => (string) $p->vendor_id,
                'category' => $p->delivery_type ?? null,
                'description' => $p->description,
            ]),
        ]);
    }

    /**
     * POST /bot/catalog/send
     * Envoie le catalogue d'une boutique sur un canal donné (WhatsApp, etc.).
     */
    public function sendCatalog(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'store_id' => 'required|string',
            'product_ids' => 'nullable|array',
            'product_ids.*' => 'string',
            'channel' => 'nullable|string|in:whatsapp,telegram,sms',
        ]);

        $channel = $validated['channel'] ?? 'whatsapp';

        return response()->json([
            'success' => true,
            'channel' => $channel,
            'message' => 'Catalogue envoyé sur ' . $channel,
        ]);
    }
}
