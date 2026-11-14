<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\Quartier;
use App\Models\ShopDeliveryQuartier;
use App\Models\ShopNegotiationConfig;
use App\Models\User;
use App\Models\Ville;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

class BotStoreController extends Controller
{
    /**
     * GET /bot/stores/search
     * Recherche de boutiques par nom, ville ou type.
     */
    public function search(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'query' => 'nullable|string',
            'city' => 'nullable|string',
        ]);

        $q = $validated['query'] ?? '';
        $query = User::where('role', 'vendor')
            ->where('bot_status', 'active');

        if ($q !== '') {
            $query->where(function ($sub) use ($q) {
                $sub->where('shop_name', 'ILIKE', '%' . $q . '%')
                    ->orWhere('name', 'ILIKE', '%' . $q . '%')
                    ->orWhere('shop_address', 'ILIKE', '%' . $q . '%')
                    ->orWhere('shop_type', 'ILIKE', '%' . $q . '%')
                    ->orWhere('niches', 'ILIKE', '%' . $q . '%')
                    ->orWhereRaw("unaccent(COALESCE(shop_name, '') || ' ' || COALESCE(name, '') || ' ' || COALESCE(shop_address, '') || ' ' || COALESCE(niches, '')) ILIKE unaccent(?)", ['%' . $q . '%']);
            });
        }

        if (! empty($validated['city'])) {
            $query->where('shop_address', 'ILIKE', '%' . $validated['city'] . '%');
        }

        $stores = $query->limit(20)->get();

        return response()->json([
            'stores' => $stores->map(fn (User $u) => [
                'id' => (string) $u->id,
                'nom' => $u->shop_name ?? $u->name,
                'note' => 0.0,
                'ville' => $u->shop_address,
                'logo_url' => $u->shop_logo_path ? asset('storage/' . $u->shop_logo_path) : null,
            ]),
            'total' => $stores->count(),
        ]);
    }

    /**
     * POST /bot/stores
     * Crée une boutique (physique ou en ligne) pour un vendeur.
     *
     * Règles :
     * - type "physique" → latitude, longitude et storefront_photo_url obligatoires.
     * - type "en_ligne" → pas besoin de GPS ni de photo.
     * - Mappe les types Tracy Core (physique/en_ligne) vers Laravel (physical/digital).
     */
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'vendor_id' => 'required|integer|exists:users,id',
            'nom' => 'required|string|min:2|max:255',
            'type' => 'required|string|in:physique,en_ligne',
            'category' => 'nullable|string|max:255',
            'latitude' => 'nullable|numeric',
            'longitude' => 'nullable|numeric',
            'storefront_photo_url' => 'nullable|string|max:500',
            'logo_url' => 'nullable|string|max:500',
        ]);

        $vendor = User::find($validated['vendor_id']);

        if ($vendor->role !== 'vendor') {
            return response()->json([
                'message' => 'Cet utilisateur n\'est pas un vendeur.',
            ], 403);
        }

        // Mapping des types Tracy Core → Laravel
        $shopType = $validated['type'] === 'physique' ? 'physical' : 'digital';

        // Boutique physique → GPS obligatoire
        if ($validated['type'] === 'physique') {
            if (!isset($validated['latitude']) || !isset($validated['longitude'])) {
                return response()->json([
                    'message' => 'Une boutique physique nécessite les coordonnées GPS (latitude, longitude).',
                ], 422);
            }
            if (!isset($validated['storefront_photo_url'])) {
                return response()->json([
                    'message' => 'Une boutique physique nécessite une photo de la devanture.',
                ], 422);
            }
        }

        $vendor->shop_name = $validated['nom'];
        $vendor->shop_type = $shopType;

        if (isset($validated['latitude'])) {
            $vendor->shop_latitude = $validated['latitude'];
        }
        if (isset($validated['longitude'])) {
            $vendor->shop_longitude = $validated['longitude'];
        }
        if (isset($validated['logo_url'])) {
            $vendor->shop_logo_path = $validated['logo_url'];
        }

        $vendor->save();

        return response()->json([
            'store_id' => (string) $vendor->id,
            'nom' => $vendor->shop_name,
            'type' => $validated['type'],
            'statut' => 'active',
        ], 201);
    }

    /**
     * GET /bot/stores/{store_id}/info
     * Récupère les infos publiques d'une boutique par son ID.
     */
    public function getInfo(string $storeId): JsonResponse
    {
        // PostgreSQL : 'id' est bigint — un store_id non numérique ('public', slug)
        // ferait planter la requête ; on renvoie 404 proprement à la place.
        $store = is_numeric($storeId)
            ? User::where('id', $storeId)->where('role', 'vendor')->first()
            : null;

        if (!$store) {
            return response()->json(['error' => 'Boutique non trouvée'], 404);
        }

        return response()->json([
            'id' => (string) $store->id,
            'nom' => $store->shop_name ?? $store->name,
            'ville' => $store->shop_address,
            'logo_url' => $store->shop_logo_path ? asset('storage/' . $store->shop_logo_path) : null,
            'shop_type' => $store->shop_type,
            'niches' => $store->niches,
            'latitude' => $store->shop_latitude !== null ? (float) $store->shop_latitude : null,
            'longitude' => $store->shop_longitude !== null ? (float) $store->shop_longitude : null,
        ]);
    }

    /**
     * GET /bot/stores/{store_id}/config
     * Récupère la configuration de négociation d'une boutique.
     */
    public function getConfig(string $storeId): JsonResponse
    {
        $config = ShopNegotiationConfig::where('store_id', $storeId)->first();

        if (!$config) {
            // Retourne config par défaut
            return response()->json([
                'store_id' => $storeId,
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

    /**
     * POST /bot/stores/{store_id}/config
     * Met à jour la configuration de négociation d'une boutique.
     */
    public function updateConfig(Request $request, string $storeId): JsonResponse
    {
        $validated = $request->validate([
            'min_margin_percent' => 'nullable|numeric|min:0|max:100',
            'first_order_discount_percent' => 'nullable|numeric|min:0|max:100',
            'max_discount_percent' => 'nullable|numeric|min:0|max:100',
            'free_shipping_threshold' => 'nullable|numeric|min:0',
            'auto_accept_below' => 'nullable|numeric|min:0|max:100',
            'custom_rules' => 'nullable|string|max:1000',
            'currency' => 'nullable|string|size:3',
            'address_form' => 'nullable|in:tu,vous',
        ]);

        $config = ShopNegotiationConfig::updateOrCreate(
            ['store_id' => $storeId],
            array_filter($validated, fn ($v) => $v !== null),
        );

        return response()->json([
            'success' => true,
            'store_id' => (string) $config->store_id,
            'message' => 'Configuration mise à jour',
        ]);
    }

    /**
     * GET /bot/stores/{store_id}/delivery-quartiers
     * Retourne les quartiers de livraison du vendeur.
     */
    public function getDeliveryQuartiers(string $storeId): JsonResponse
    {
        $user = is_numeric($storeId) ? User::find($storeId) : null;
        if (!$user) {
            return response()->json(['message' => 'Boutique introuvable.'], 404);
        }

        $quartiers = $user->deliveryQuartiers()
            ->with('ville:id,name,department_name')
            ->get(['quartiers.id', 'quartiers.name', 'quartiers.arrondissement_name', 'quartiers.ville_id']);

        return response()->json([
            'store_id'      => $storeId,
            'delivery_mode' => $user->delivery_mode,
            'pickup_available' => (bool) $user->pickup_available,
            'delivery_cities' => $user->delivery_cities ?? [],
            'delivery_countries' => $user->delivery_countries ?? [],
            'shop_address'  => $user->shop_address,
            'quartiers'     => $quartiers,
        ]);
    }

    /**
     * POST /bot/stores/{store_id}/delivery-quartiers
     * Ajoute des quartiers de livraison (par IDs ou par "toute la ville").
     *
     * Body :
     *   { "quartier_ids": [1, 2, 3] }               — ajoute des quartiers précis
     *   { "ville_id": 1 }                           — pré-coche tous les quartiers de la ville
     *   { "ville_id": 1, "exclude_quartier_ids": [5] } — toute la ville sauf certains quartiers
     */
    public function setDeliveryQuartiers(Request $request, string $storeId): JsonResponse
    {
        $user = is_numeric($storeId) ? User::find($storeId) : null;
        if (!$user) {
            return response()->json(['message' => 'Boutique introuvable.'], 404);
        }

        $validated = $request->validate([
            'quartier_ids'          => 'nullable|array',
            'quartier_ids.*'        => 'integer|exists:quartiers,id',
            'ville_id'              => 'nullable|integer|exists:villes,id',
            'exclude_quartier_ids'  => 'nullable|array',
            'exclude_quartier_ids.*'=> 'integer|exists:quartiers,id',
            'replace'               => 'nullable|boolean',
        ]);

        $replace = $request->boolean('replace', false);
        $quartierIds = $validated['quartier_ids'] ?? [];

        // Mode "toute la ville" : récupère tous les quartiers de la ville
        if (!empty($validated['ville_id'])) {
            $villeQuartierIds = Quartier::where('ville_id', $validated['ville_id'])->pluck('id')->toArray();
            $exclude = $validated['exclude_quartier_ids'] ?? [];
            $quartierIds = array_values(array_diff($villeQuartierIds, $exclude));
        }

        if (empty($quartierIds)) {
            return response()->json([
                'message' => 'Aucun quartier à ajouter. Spécifiez quartier_ids ou ville_id.',
            ], 422);
        }

        DB::transaction(function () use ($user, $quartierIds, $replace) {
            if ($replace) {
                ShopDeliveryQuartier::where('shop_id', $user->id)->delete();
            }

            $existing = ShopDeliveryQuartier::where('shop_id', $user->id)
                ->whereIn('quartier_id', $quartierIds)
                ->pluck('quartier_id')
                ->toArray();

            $newIds = array_diff($quartierIds, $existing);
            $rows = array_map(fn ($qid) => [
                'shop_id'     => $user->id,
                'quartier_id' => $qid,
                'created_at'  => now(),
                'updated_at'  => now(),
            ], $newIds);

            if (!empty($rows)) {
                ShopDeliveryQuartier::insert($rows);
            }

            // Met à jour le delivery_mode si nécessaire
            if ($user->delivery_mode === 'pickup_only') {
                $user->delivery_mode = 'quartiers';
                $user->save();
            }
        });

        $count = ShopDeliveryQuartier::where('shop_id', $user->id)->count();

        return response()->json([
            'success'   => true,
            'store_id'  => $storeId,
            'added'     => count($quartierIds),
            'total'     => $count,
            'message'   => 'Quartiers de livraison mis à jour.',
        ]);
    }

    /**
     * DELETE /bot/stores/{store_id}/delivery-quartiers/{quartier_id}
     * Retire un quartier précis de la liste de livraison ("sauf [quartier]").
     */
    public function removeDeliveryQuartier(string $storeId, int $quartierId): JsonResponse
    {
        $user = is_numeric($storeId) ? User::find($storeId) : null;
        if (!$user) {
            return response()->json(['message' => 'Boutique introuvable.'], 404);
        }

        $deleted = ShopDeliveryQuartier::where('shop_id', $user->id)
            ->where('quartier_id', $quartierId)
            ->delete();

        if (!$deleted) {
            return response()->json([
                'message' => 'Ce quartier n\'est pas dans la liste de livraison.',
            ], 404);
        }

        $remaining = ShopDeliveryQuartier::where('shop_id', $user->id)->count();

        // Si plus aucun quartier, repasse en pickup_only
        if ($remaining === 0 && $user->delivery_mode === 'quartiers') {
            $user->delivery_mode = 'pickup_only';
            $user->save();
        }

        return response()->json([
            'success'  => true,
            'store_id' => $storeId,
            'removed_quartier_id' => $quartierId,
            'remaining' => $remaining,
        ]);
    }
}
