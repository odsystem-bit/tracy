<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Mobile;

use App\Http\Controllers\Controller;
use App\Models\MenuCategory;
use App\Models\MenuItem;
use App\Models\RestaurantHour;
use App\Models\RestaurantOrder;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class MobileRestaurantController extends Controller
{
    public function listRestaurants(Request $request): JsonResponse
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
                'id'           => $r->id,
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
                'id'         => $restaurant->id,
                'shop_name'  => $restaurant->shop_name ?? $restaurant->name,
                'shop_logo'  => $restaurant->shop_logo_path ? asset('storage/' . $restaurant->shop_logo_path) : null,
                'shop_type'  => $restaurant->shop_type,
                'address'    => $restaurant->shop_address,
                'phone'      => $restaurant->phone,
                'is_open_now' => RestaurantHour::isOpenNow($restaurantId),
            ],
            'categories' => $categories->map(fn ($c) => [
                'id'    => $c->id,
                'name'  => $c->name,
                'items' => $c->items->map(fn ($i) => [
                    'id'                  => $i->id,
                    'name'                => $i->name,
                    'description'         => $i->description,
                    'price'               => (float) $i->price,
                    'image_url'           => asset('storage/' . $i->image_path),
                    'preparation_time_min' => $i->preparation_time_min,
                    'calories'            => $i->calories,
                    'is_vegetarian'       => $i->is_vegetarian,
                    'is_halal'            => $i->is_halal,
                    'options'             => $i->options->map(fn ($opt) => [
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
                ]),
            ]),
            'hours' => $hours->map(fn ($h) => [
                'day_of_week' => $h->day_of_week,
                'open_time'   => $h->open_time,
                'close_time'  => $h->close_time,
                'is_closed'   => $h->is_closed,
            ]),
        ]);
    }

    public function createOrder(Request $request): JsonResponse
    {
        $user = $request->user();

        $validated = $request->validate([
            'restaurant_id'      => 'required|exists:users,id',
            'order_type'         => 'required|in:delivery,pickup',
            'items'              => 'required|array|min:1',
            'items.*.menu_item_id' => 'required|exists:menu_items,id',
            'items.*.quantity'     => 'required|integer|min:1',
            'items.*.selected_options' => 'nullable|array',
            'items.*.special_instructions' => 'nullable|string|max:500',
            'delivery_address'   => 'required_if:order_type,delivery|nullable|string',
            'delivery_latitude'  => 'nullable|numeric',
            'delivery_longitude' => 'nullable|numeric',
            'notes'              => 'nullable|string|max:1000',
        ]);

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
            'customer_id'        => $user->id,
            'order_type'         => $validated['order_type'],
            'status'             => 'pending',
            'subtotal'           => $subtotal,
            'delivery_fee'       => $deliveryFee,
            'total'              => $total,
            'delivery_address'   => $validated['delivery_address'] ?? null,
            'delivery_latitude'  => $validated['delivery_latitude'] ?? null,
            'delivery_longitude' => $validated['delivery_longitude'] ?? null,
            'customer_phone'     => $user->phone,
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
            'subtotal'    => $subtotal,
            'delivery_fee' => $deliveryFee,
            'total'       => $total,
            'estimated_delivery_at' => $order->estimated_delivery_at?->toIso8601String(),
        ]);
    }

    public function getMyOrders(Request $request): JsonResponse
    {
        $user = $request->user();
        $orders = RestaurantOrder::where('customer_id', $user->id)
            ->with(['items', 'restaurant:id,name,shop_name,shop_logo_path'])
            ->orderByDesc('created_at')
            ->limit(30)
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
                'estimated_delivery_at' => $o->estimated_delivery_at?->toIso8601String(),
                'restaurant_name' => $o->restaurant?->shop_name ?? $o->restaurant?->name,
                'restaurant_logo' => $o->restaurant?->shop_logo_path ? asset('storage/' . $o->restaurant->shop_logo_path) : null,
                'items'           => $o->items->map(fn ($i) => [
                    'name'            => $i->menu_item_name,
                    'quantity'        => $i->quantity,
                    'unit_price'      => (float) $i->unit_price,
                    'total_price'     => (float) $i->total_price,
                    'special_instructions' => $i->special_instructions,
                ]),
                'created_at'      => $o->created_at?->toIso8601String(),
            ]),
        ]);
    }

    public function getOrderStatus(int $orderId): JsonResponse
    {
        $order = RestaurantOrder::with('items')->findOrFail($orderId);

        return response()->json([
            'id'              => $order->id,
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
}
