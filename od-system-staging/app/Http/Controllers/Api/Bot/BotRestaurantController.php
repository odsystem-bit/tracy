<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\MenuCategory;
use App\Models\MenuItem;
use App\Models\RestaurantHour;
use App\Models\RestaurantOrder;
use App\Models\RestaurantOrderItem;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

class BotRestaurantController extends Controller
{
    // ── Menu Management ──

    public function createCategory(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'restaurant_id' => 'required|exists:users,id',
            'name'          => 'required|string|max:100',
            'sort_order'    => 'nullable|integer|min:0',
        ]);

        $restaurant = User::find($validated['restaurant_id']);
        if (!$this->isRestaurant($restaurant)) {
            return response()->json(['error' => 'Cet utilisateur n\'est pas un restaurant'], 422);
        }

        $category = MenuCategory::create([
            'restaurant_id' => $validated['restaurant_id'],
            'name'          => $validated['name'],
            'slug'          => Str::slug($validated['name']),
            'sort_order'    => $validated['sort_order'] ?? 0,
        ]);

        return response()->json(['success' => true, 'category_id' => $category->id]);
    }

    public function listCategories(Request $request, int $restaurantId): JsonResponse
    {
        $categories = MenuCategory::where('restaurant_id', $restaurantId)
            ->where('is_active', true)
            ->with(['items' => fn ($q) => $q->where('is_available', true)->orderBy('sort_order')])
            ->orderBy('sort_order')
            ->get();

        return response()->json([
            'categories' => $categories->map(fn ($c) => [
                'id'    => $c->id,
                'name'  => $c->name,
                'slug'  => $c->slug,
                'items' => $c->items->map(fn ($i) => $this->formatMenuItem($i)),
            ]),
        ]);
    }

    public function createMenuItem(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'restaurant_id'      => 'required|exists:users,id',
            'category_id'        => 'required|exists:menu_categories,id',
            'name'               => 'required|string|max:200',
            'description'        => 'nullable|string|max:2000',
            'price'              => 'required|numeric|min:0',
            'image_base64'       => 'required|string',
            'ingredients'        => 'nullable|array',
            'allergens'          => 'nullable|array',
            'preparation_time_min' => 'nullable|integer|min:1',
            'calories'           => 'nullable|integer|min:0',
            'is_vegetarian'      => 'nullable|boolean',
            'is_halal'           => 'nullable|boolean',
            'sort_order'         => 'nullable|integer|min:0',
        ]);

        $imagePath = $this->storeBase64Image($validated['image_base64'], 'menu-items');
        if (!$imagePath) {
            return response()->json(['error' => 'Image invalide'], 422);
        }

        $item = MenuItem::create([
            'restaurant_id'      => $validated['restaurant_id'],
            'category_id'        => $validated['category_id'],
            'name'               => $validated['name'],
            'description'        => $validated['description'] ?? null,
            'price'              => $validated['price'],
            'image_path'         => $imagePath,
            'ingredients'        => $validated['ingredients'] ?? null,
            'allergens'          => $validated['allergens'] ?? null,
            'preparation_time_min' => $validated['preparation_time_min'] ?? 15,
            'calories'           => $validated['calories'] ?? null,
            'is_vegetarian'      => $validated['is_vegetarian'] ?? false,
            'is_halal'           => $validated['is_halal'] ?? false,
            'is_available'       => true,
            'sort_order'         => $validated['sort_order'] ?? 0,
        ]);

        return response()->json(['success' => true, 'item_id' => $item->id]);
    }

    public function updateMenuItem(Request $request, int $itemId): JsonResponse
    {
        $item = MenuItem::findOrFail($itemId);

        $validated = $request->validate([
            'name'               => 'sometimes|string|max:200',
            'description'        => 'sometimes|nullable|string|max:2000',
            'price'              => 'sometimes|numeric|min:0',
            'image_base64'       => 'sometimes|string',
            'ingredients'        => 'sometimes|nullable|array',
            'allergens'          => 'sometimes|nullable|array',
            'preparation_time_min' => 'sometimes|integer|min:1',
            'calories'           => 'sometimes|nullable|integer|min:0',
            'is_vegetarian'      => 'sometimes|boolean',
            'is_halal'           => 'sometimes|boolean',
            'is_available'       => 'sometimes|boolean',
            'sort_order'         => 'sometimes|integer|min:0',
        ]);

        if (!empty($validated['image_base64'])) {
            $imagePath = $this->storeBase64Image($validated['image_base64'], 'menu-items');
            if ($imagePath) {
                $validated['image_path'] = $imagePath;
            }
            unset($validated['image_base64']);
        }

        $item->update($validated);

        return response()->json(['success' => true]);
    }

    public function toggleAvailability(Request $request, int $itemId): JsonResponse
    {
        $item = MenuItem::findOrFail($itemId);
        $item->update(['is_available' => !$item->is_available]);

        return response()->json([
            'success'      => true,
            'is_available' => $item->is_available,
        ]);
    }

    // ── Opening Hours ──

    public function setHours(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'restaurant_id' => 'required|exists:users,id',
            'hours'         => 'required|array',
            'hours.*.day_of_week' => 'required|integer|min:0|max:6',
            'hours.*.open_time'   => 'required|date_format:H:i',
            'hours.*.close_time'  => 'required|date_format:H:i',
            'hours.*.is_closed'   => 'nullable|boolean',
        ]);

        foreach ($validated['hours'] as $hour) {
            RestaurantHour::updateOrCreate(
                [
                    'restaurant_id' => $validated['restaurant_id'],
                    'day_of_week'   => $hour['day_of_week'],
                ],
                [
                    'open_time'  => $hour['open_time'],
                    'close_time' => $hour['close_time'],
                    'is_closed'  => $hour['is_closed'] ?? false,
                ]
            );
        }

        return response()->json(['success' => true]);
    }

    public function getHours(int $restaurantId): JsonResponse
    {
        $hours = RestaurantHour::where('restaurant_id', $restaurantId)
            ->orderBy('day_of_week')
            ->get();

        $isOpen = RestaurantHour::isOpenNow($restaurantId);

        return response()->json([
            'is_open_now' => $isOpen,
            'hours'       => $hours->map(fn ($h) => [
                'day_of_week' => $h->day_of_week,
                'open_time'   => $h->open_time,
                'close_time'  => $h->close_time,
                'is_closed'   => $h->is_closed,
            ]),
        ]);
    }

    // ── Orders ──

    public function createOrder(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'restaurant_id'      => 'required|exists:users,id',
            'customer_id'        => 'required|exists:users,id',
            'order_type'         => 'required|in:delivery,pickup',
            'items'              => 'required|array|min:1',
            'items.*.menu_item_id' => 'required|exists:menu_items,id',
            'items.*.quantity'     => 'required|integer|min:1',
            'items.*.selected_options' => 'nullable|array',
            'items.*.special_instructions' => 'nullable|string|max:500',
            'delivery_address'   => 'required_if:order_type,delivery|nullable|string',
            'delivery_latitude'  => 'nullable|numeric',
            'delivery_longitude' => 'nullable|numeric',
            'customer_phone'     => 'required|string|max:20',
            'notes'              => 'nullable|string|max:1000',
        ]);

        $restaurant = User::find($validated['restaurant_id']);
        if (!$this->isRestaurant($restaurant)) {
            return response()->json(['error' => 'Cet utilisateur n\'est pas un restaurant'], 422);
        }

        if (!RestaurantHour::isOpenNow($validated['restaurant_id'])) {
            return response()->json(['error' => 'Le restaurant est actuellement fermé'], 422);
        }

        $subtotal = 0;
        $orderItems = [];

        foreach ($validated['items'] as $itemData) {
            $menuItem = MenuItem::with('options.values')->find($itemData['menu_item_id']);
            if (!$menuItem || !$menuItem->is_available) {
                return response()->json([
                    'error' => "Le plat \"{$menuItem?->name}\" n'est plus disponible",
                ], 422);
            }

            $unitPrice = (float) $menuItem->price;
            $selectedOptions = $itemData['selected_options'] ?? [];

            foreach ($selectedOptions as $opt) {
                if (isset($opt['value_id'])) {
                    $value = $menuItem->options
                        ->flatMap->values
                        ->firstWhere('id', $opt['value_id']);
                    if ($value) {
                        $unitPrice += (float) $value->price_modifier;
                    }
                }
            }

            $totalPrice = $unitPrice * $itemData['quantity'];
            $subtotal += $totalPrice;

            $orderItems[] = [
                'menu_item_id'         => $menuItem->id,
                'menu_item_name'       => $menuItem->name,
                'unit_price'           => $unitPrice,
                'quantity'             => $itemData['quantity'],
                'total_price'          => $totalPrice,
                'selected_options'     => $selectedOptions,
                'special_instructions' => $itemData['special_instructions'] ?? null,
            ];
        }

        $deliveryFee = $validated['order_type'] === 'delivery' ? 1000 : 0;
        $total = $subtotal + $deliveryFee;

        $order = RestaurantOrder::create([
            'restaurant_id'      => $validated['restaurant_id'],
            'customer_id'        => $validated['customer_id'],
            'order_type'         => $validated['order_type'],
            'status'             => 'pending',
            'subtotal'           => $subtotal,
            'delivery_fee'       => $deliveryFee,
            'total'              => $total,
            'delivery_address'   => $validated['delivery_address'] ?? null,
            'delivery_latitude'  => $validated['delivery_latitude'] ?? null,
            'delivery_longitude' => $validated['delivery_longitude'] ?? null,
            'customer_phone'     => $validated['customer_phone'],
            'notes'              => $validated['notes'] ?? null,
            'estimated_delivery_at' => now()->addMinutes(45),
        ]);

        foreach ($orderItems as $oi) {
            $order->items()->create($oi);
        }

        return response()->json([
            'success'     => true,
            'order_id'    => $order->id,
            'order_number' => $order->order_number,
            'total'       => $total,
            'estimated_delivery_at' => $order->estimated_delivery_at?->toIso8601String(),
        ]);
    }

    public function updateOrderStatus(Request $request, int $orderId): JsonResponse
    {
        $validated = $request->validate([
            'status' => 'required|in:pending,preparing,ready,on_delivery,delivered,picked_up,cancelled',
        ]);

        $order = RestaurantOrder::findOrFail($orderId);
        $order->update([
            'status'       => $validated['status'],
            'delivered_at' => in_array($validated['status'], ['delivered', 'picked_up']) ? now() : $order->delivered_at,
        ]);

        return response()->json(['success' => true, 'status' => $order->status]);
    }

    public function getOrders(Request $request, int $restaurantId): JsonResponse
    {
        $orders = RestaurantOrder::where('restaurant_id', $restaurantId)
            ->with('items')
            ->orderByDesc('created_at')
            ->limit(50)
            ->get();

        return response()->json([
            'orders' => $orders->map(fn ($o) => [
                'id'              => $o->id,
                'order_number'    => $o->order_number,
                'order_type'      => $o->order_type,
                'status'          => $o->status,
                'subtotal'        => (float) $o->subtotal,
                'delivery_fee'    => (float) $o->delivery_fee,
                'total'           => (float) $o->total,
                'customer_phone'  => $o->customer_phone,
                'delivery_address' => $o->delivery_address,
                'notes'           => $o->notes,
                'estimated_delivery_at' => $o->estimated_delivery_at?->toIso8601String(),
                'items'           => $o->items->map(fn ($i) => [
                    'name'            => $i->menu_item_name,
                    'quantity'        => $i->quantity,
                    'unit_price'      => (float) $i->unit_price,
                    'total_price'     => (float) $i->total_price,
                    'selected_options' => $i->selected_options,
                    'special_instructions' => $i->special_instructions,
                ]),
                'created_at'      => $o->created_at?->toIso8601String(),
            ]),
        ]);
    }

    // ── Search & Menu (for Tracy Core) ──

    public function searchRestaurants(Request $request): JsonResponse
    {
        $query = User::where('role', 'vendor')
            ->whereIn('shop_type', ['restaurant_online', 'restaurant_physical'])
            ->where('bot_status', 'active');

        if ($request->has('lat') && $request->has('lng')) {
            $lat = (float) $request->get('lat');
            $lng = (float) $request->get('lng');
            $query->selectRaw('*, (
                6371 * acos(cos(radians(?)) * cos(radians(shop_latitude)) * cos(radians(shop_longitude) - radians(?)) + sin(radians(?)) * sin(radians(shop_latitude)))
            ) AS distance', [$lat, $lng, $lat])
            ->orderBy('distance');
        }

        $restaurants = $query->limit(30)->get();

        return response()->json([
            'restaurants' => $restaurants->map(fn ($r) => [
                'id'           => (string) $r->id,
                'shop_name'    => $r->shop_name ?? $r->name,
                'shop_logo'    => $r->shop_logo_path ? asset('storage/' . $r->shop_logo_path) : null,
                'shop_type'    => $r->shop_type,
                'address'      => $r->shop_address,
                'latitude'     => (float) $r->shop_latitude,
                'longitude'    => (float) $r->shop_longitude,
                'is_open_now'  => RestaurantHour::isOpenNow($r->id),
                'rating'       => 4.5,
            ]),
        ]);
    }

    public function getMenu(int $restaurantId): JsonResponse
    {
        $restaurant = User::find($restaurantId);
        if (!$restaurant || !in_array($restaurant->shop_type, ['restaurant_online', 'restaurant_physical'])) {
            return response()->json(['error' => 'Restaurant introuvable'], 404);
        }

        $categories = MenuCategory::where('restaurant_id', $restaurantId)
            ->where('is_active', true)
            ->with(['items' => fn ($q) => $q->where('is_available', true)->with('options.values')->orderBy('sort_order')])
            ->orderBy('sort_order')
            ->get();

        $hours = RestaurantHour::where('restaurant_id', $restaurantId)->orderBy('day_of_week')->get();

        return response()->json([
            'restaurant' => [
                'id'         => (string) $restaurant->id,
                'shop_name'  => $restaurant->shop_name ?? $restaurant->name,
                'shop_logo'  => $restaurant->shop_logo_path ? asset('storage/' . $restaurant->shop_logo_path) : null,
                'shop_type'  => $restaurant->shop_type,
                'address'    => $restaurant->shop_address,
                'phone'      => $restaurant->phone,
                'is_open_now' => RestaurantHour::isOpenNow($restaurantId),
            ],
            'categories' => $categories->map(fn ($c) => [
                'id'    => (string) $c->id,
                'name'  => $c->name,
                'items' => $c->items->map(fn ($i) => $this->formatMenuItem($i)),
            ]),
            'hours' => $hours->map(fn ($h) => [
                'day_of_week' => $h->day_of_week,
                'open_time'   => $h->open_time,
                'close_time'  => $h->close_time,
                'is_closed'   => $h->is_closed,
            ]),
        ]);
    }

    public function getOrderStatus(int $orderId): JsonResponse
    {
        $order = RestaurantOrder::with('items')->findOrFail($orderId);

        return response()->json([
            'id'              => (string) $order->id,
            'order_number'    => $order->order_number,
            'status'          => $order->status,
            'order_type'      => $order->order_type,
            'total'           => (float) $order->total,
            'estimated_delivery_at' => $order->estimated_delivery_at?->toIso8601String(),
            'delivered_at'    => $order->delivered_at?->toIso8601String(),
            'items'           => $order->items->map(fn ($i) => [
                'name'       => $i->menu_item_name,
                'quantity'   => $i->quantity,
                'total_price' => (float) $i->total_price,
            ]),
        ]);
    }

    // ── Helpers ──

    private function isRestaurant(User $user): bool
    {
        return in_array($user->shop_type, ['restaurant_online', 'restaurant_physical']);
    }

    private function formatMenuItem(MenuItem $item): array
    {
        return [
            'id'                  => $item->id,
            'name'                => $item->name,
            'description'         => $item->description,
            'price'               => (float) $item->price,
            'image_url'           => $item->imageUrl(),
            'preparation_time_min' => $item->preparation_time_min,
            'calories'            => $item->calories,
            'is_vegetarian'       => $item->is_vegetarian,
            'is_halal'            => $item->is_halal,
            'is_available'        => $item->is_available,
            'options'             => $item->options->map(fn ($opt) => [
                'id'             => $opt->id,
                'name'           => $opt->name,
                'type'           => $opt->type,
                'is_required'    => $opt->is_required,
                'max_selections' => $opt->max_selections,
                'values'         => $opt->values->map(fn ($v) => [
                    'id'             => $v->id,
                    'name'           => $v->name,
                    'price_modifier' => (float) $v->price_modifier,
                    'is_default'     => $v->is_default,
                ]),
            ]),
        ];
    }

    private function storeBase64Image(string $base64, string $folder): ?string
    {
        try {
            if (str_contains($base64, ';base64,')) {
                $base64 = explode(';base64,', $base64)[1];
            }
            $decoded = base64_decode($base64);
            if (!$decoded) {
                return null;
            }
            $filename = $folder . '/' . Str::uuid() . '.jpg';
            Storage::disk('public')->put($filename, $decoded);
            return $filename;
        } catch (\Throwable $e) {
            return null;
        }
    }
}
