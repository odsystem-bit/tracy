<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Admin;

use App\Enums\UserRole;
use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\Product;
use App\Models\Transaction;
use App\Models\User;
use App\Models\OrderDisputeMessage;
use App\Models\RestaurantOrder;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class AdminApiController extends Controller
{
    /**
     * POST /api/admin/login — Authentifie un admin et retourne un token.
     */
    public function login(Request $request): JsonResponse
    {
        $request->validate([
            'email'    => 'required|string|email',
            'password' => 'required|string',
        ]);

        $user = User::where('email', $request->email)->first();

        if (!$user || !password_verify($request->password, $user->password)) {
            return response()->json([
                'message' => 'Identifiants incorrects.',
            ], 401);
        }

        if ($user->role !== UserRole::ADMIN) {
            return response()->json([
                'message' => 'Accès refusé. Ce portail est réservé aux administrateurs.',
            ], 403);
        }

        $token = $user->createToken('admin-panel', ['admin'])->plainTextToken;

        return response()->json([
            'token' => $token,
            'user'  => [
                'id'    => $user->id,
                'name'  => $user->name,
                'email' => $user->email,
                'role'  => $user->role->value,
            ],
        ]);
    }

    /**
     * POST /api/admin/logout — Révoque le token courant.
     */
    public function logout(Request $request): JsonResponse
    {
        $request->user()->currentAccessToken()->delete();

        return response()->json(['message' => 'Déconnecté.']);
    }

    /**
     * GET /api/admin/me — Retourne l'admin connecté.
     */
    public function me(Request $request): JsonResponse
    {
        $user = $request->user();

        return response()->json([
            'id'    => $user->id,
            'name'  => $user->name,
            'email' => $user->email,
            'role'  => $user->role->value,
        ]);
    }

    /**
     * GET /api/admin/dashboard — KPI globaux.
     */
    public function dashboard(): JsonResponse
    {
        $totalUsers    = User::count();
        $totalVendors  = User::where('role', UserRole::VENDOR)->count();
        $totalBuyers   = User::where('role', UserRole::BUYER)->count();
        $totalCreators = User::where('role', UserRole::INFLUENCER)->count();
        $totalProducts = Product::count();
        $totalOrders   = Order::count();
        $pendingOrders = Order::whereNotIn('status', ['delivered', 'cancelled'])->count();
        $openDisputes  = OrderDisputeMessage::count();
        $totalRevenue  = (float) Transaction::where('type', 'deposit')->where('status', 'completed')->sum('amount_total');
        $totalWithdrawals = (float) Transaction::where('type', 'withdrawal')->where('status', 'completed')->sum('amount_target');

        $newUsersThisWeek = User::where('created_at', '>=', now()->subDays(7))->count();
        $ordersThisWeek   = Order::where('created_at', '>=', now()->subDays(7))->count();

        $recentUsers = User::orderByDesc('created_at')
            ->limit(10)
            ->get(['id', 'name', 'email', 'role', 'created_at']);

        $recentOrders = Order::with('vendor:id,name,shop_name')
            ->orderByDesc('created_at')
            ->limit(10)
            ->get(['id', 'reference', 'status', 'amount_paid', 'vendor_id', 'created_at']);

        return response()->json([
            'kpis' => [
                'total_users'        => $totalUsers,
                'total_vendors'      => $totalVendors,
                'total_buyers'       => $totalBuyers,
                'total_creators'     => $totalCreators,
                'total_products'     => $totalProducts,
                'total_orders'       => $totalOrders,
                'pending_orders'     => $pendingOrders,
                'open_disputes'      => $openDisputes,
                'total_revenue'      => $totalRevenue,
                'total_withdrawals'  => $totalWithdrawals,
                'new_users_week'     => $newUsersThisWeek,
                'orders_week'        => $ordersThisWeek,
            ],
            'recent_users'  => $recentUsers,
            'recent_orders' => $recentOrders->map(fn ($o) => [
                'id'           => $o->id,
                'order_number' => $o->reference,
                'status'       => $o->status,
                'total'        => (float) $o->amount_paid,
                'vendor'       => $o->vendor?->shop_name ?? $o->vendor?->name ?? 'N/A',
                'created_at'   => $o->created_at?->toIso8601String(),
            ]),
        ]);
    }

    /**
     * GET /api/admin/users — Liste paginée des utilisateurs.
     */
    public function users(Request $request): JsonResponse
    {
        $query = User::query()
            ->when($request->input('search'), function ($q, $search) {
                $q->where(function ($sub) use ($search) {
                    $sub->where('name', 'ILIKE', "%{$search}%")
                        ->orWhere('email', 'ILIKE', "%{$search}%")
                        ->orWhere('phone', 'ILIKE', "%{$search}%");
                });
            })
            ->when($request->input('role'), function ($q, $role) {
                $q->where('role', $role);
            })
            ->when($request->input('status') === 'banned', function ($q) {
                $q->onlyTrashed();
            })
            ->orderByDesc('created_at');

        $perPage = min((int) $request->input('per_page', 20), 100);
        $users = $query->paginate($perPage);

        return response()->json([
            'data' => $users->items()->map(fn ($u) => [
                'id'            => $u->id,
                'name'          => $u->name,
                'email'         => $u->email,
                'phone'         => $u->phone,
                'role'          => $u->role->value,
                'country'       => $u->country,
                'kyc_status'    => $u->kyc_status ?? 'none',
                'shop_name'     => $u->shop_name,
                'shop_type'     => $u->shop_type,
                'bot_plan'      => $u->bot_plan,
                'bot_status'    => $u->bot_status,
                'is_banned'     => $u->trashed(),
                'is_vip'        => $u->is_vip ?? false,
                'wallet_balance'=> (float) ($u->wallet?->balance ?? 0),
                'product_count' => $u->products()->count(),
                'order_count'   => $u->ordersAsVendor()->count(),
                'revenue'       => (float) $u->ordersAsVendor()->where('status', 'delivered')->sum('amount_paid'),
                'modes'         => $u->activeModes()->pluck('mode')->toArray(),
                'created_at'    => $u->created_at?->toIso8601String(),
            ]),
            'meta' => [
                'current_page' => $users->currentPage(),
                'last_page'    => $users->lastPage(),
                'total'        => $users->total(),
                'per_page'     => $users->perPage(),
            ],
        ]);
    }

    /**
     * GET /api/admin/users/{id} — Détail d'un utilisateur.
     */
    public function userShow(int $id): JsonResponse
    {
        $user = User::withTrashed()->with(['wallet', 'activeModes'])->findOrFail($id);

        $recentTransactions = $user->transactions()->orderByDesc('created_at')->limit(10)->get();
        $recentOrders = $user->ordersAsVendor()->with('product:id,name')->orderByDesc('created_at')->limit(5)->get();

        return response()->json([
            'id'             => $user->id,
            'name'           => $user->name,
            'email'          => $user->email,
            'phone'          => $user->phone,
            'role'           => $user->role->value,
            'country'        => $user->country,
            'kyc_status'     => $user->kyc_status ?? 'none',
            'shop_name'      => $user->shop_name,
            'shop_type'      => $user->shop_type,
            'shop_address'   => $user->shop_address,
            'shop_latitude'  => $user->shop_latitude,
            'shop_longitude' => $user->shop_longitude,
            'bot_plan'       => $user->bot_plan,
            'bot_status'     => $user->bot_status,
            'is_banned'      => $user->trashed(),
            'is_vip'         => $user->is_vip ?? false,
            'wallet_balance' => (float) ($user->wallet?->balance ?? 0),
            'product_count'  => $user->products()->count(),
            'order_count'    => $user->ordersAsVendor()->count(),
            'revenue'        => (float) $user->ordersAsVendor()->where('status', 'delivered')->sum('amount_paid'),
            'modes'          => $user->activeModes->pluck('mode')->toArray(),
            'recent_transactions' => $recentTransactions->map(fn ($t) => [
                'id'       => $t->id,
                'type'     => $t->type,
                'amount'   => (float) $t->amount_total,
                'status'   => $t->status,
                'reference'=> $t->reference,
                'created_at' => $t->created_at?->toIso8601String(),
            ]),
            'recent_orders' => $recentOrders->map(fn ($o) => [
                'id'           => $o->id,
                'reference'    => $o->reference,
                'status'       => $o->status instanceof \App\Enums\OrderStatus ? $o->status->value : (string) $o->status,
                'total'        => (float) $o->amount_paid,
                'product'      => $o->product?->name ?? 'N/A',
                'created_at'   => $o->created_at?->toIso8601String(),
            ]),
            'created_at' => $user->created_at?->toIso8601String(),
        ]);
    }

    /**
     * PATCH /api/admin/users/{id}/ban — Bannir/débannir.
     */
    public function toggleBan(int $id): JsonResponse
    {
        $user = User::withTrashed()->findOrFail($id);

        if ($user->trashed()) {
            $user->restore();
            $message = 'Utilisateur réactivé.';
        } else {
            $user->delete();
            $message = 'Utilisateur banni.';
        }

        return response()->json([
            'success'  => true,
            'is_banned' => $user->trashed(),
            'message'  => $message,
        ]);
    }

    /**
     * GET /api/admin/orders — Liste paginée des commandes.
     */
    public function orders(Request $request): JsonResponse
    {
        $query = Order::with(['vendor:id,name,shop_name', 'product:id,name'])
            ->when($request->input('status'), function ($q, $status) {
                $q->where('status', $status);
            })
            ->when($request->input('search'), function ($q, $search) {
                $q->where('reference', 'ILIKE', "%{$search}%");
            })
            ->orderByDesc('created_at');

        $perPage = min((int) $request->input('per_page', 20), 100);
        $orders = $query->paginate($perPage);

        return response()->json([
            'data' => $orders->items()->map(fn ($o) => [
                'id'              => $o->id,
                'order_number'    => $o->reference,
                'status'          => $o->status instanceof \App\Enums\OrderStatus ? $o->status->value : (string) $o->status,
                'total'           => (float) $o->amount_paid,
                'commission'      => (float) $o->commission_amount,
                'vendor_earnings' => (float) $o->vendor_earnings,
                'delivery_fee'    => (float) $o->delivery_fee_paid,
                'delivery_company'=> $o->delivery_company,
                'customer'        => $o->customer_name,
                'customer_phone'  => $o->customer_phone,
                'product'         => $o->product?->name ?? 'N/A',
                'vendor'          => $o->vendor?->shop_name ?? $o->vendor?->name ?? 'N/A',
                'country'         => $o->country,
                'city'            => $o->city,
                'tracking_token'  => $o->tracking_token,
                'dispute_reason'  => $o->dispute_reason,
                'is_overdue'      => $o->isOverdue(),
                'created_at'      => $o->created_at?->toIso8601String(),
            ]),
            'meta' => [
                'current_page' => $orders->currentPage(),
                'last_page'    => $orders->lastPage(),
                'total'        => $orders->total(),
                'per_page'     => $orders->perPage(),
            ],
        ]);
    }

    /**
     * GET /api/admin/restaurants — Liste des restaurants.
     */
    public function restaurants(Request $request): JsonResponse
    {
        $query = User::whereIn('shop_type', ['restaurant_online', 'restaurant_physical'])
            ->when($request->input('search'), function ($q, $search) {
                $q->where('shop_name', 'ILIKE', "%{$search}%");
            })
            ->orderByDesc('created_at');

        $perPage = min((int) $request->input('per_page', 20), 100);
        $restaurants = $query->paginate($perPage);

        $restaurantOrders = RestaurantOrder::select('restaurant_id',
            DB::raw('COUNT(*) as total_orders'),
            DB::raw('SUM(CASE WHEN status = \'delivered\' THEN 1 ELSE 0 END) as delivered_orders')
        )->groupBy('restaurant_id')->get()->keyBy('restaurant_id');

        return response()->json([
            'data' => $restaurants->items()->map(fn ($r) => [
                'id'              => $r->id,
                'shop_name'       => $r->shop_name ?? $r->name,
                'shop_type'       => $r->shop_type,
                'address'         => $r->shop_address,
                'phone'           => $r->phone,
                'bot_status'      => $r->bot_status,
                'total_orders'    => $restaurantOrders->get($r->id)?->total_orders ?? 0,
                'delivered_orders'=> $restaurantOrders->get($r->id)?->delivered_orders ?? 0,
                'created_at'      => $r->created_at?->toIso8601String(),
            ]),
            'meta' => [
                'current_page' => $restaurants->currentPage(),
                'last_page'    => $restaurants->lastPage(),
                'total'        => $restaurants->total(),
                'per_page'     => $restaurants->perPage(),
            ],
        ]);
    }

    /**
     * GET /api/admin/finance — Données financières.
     */
    public function finance(): JsonResponse
    {
        $deposits    = (float) Transaction::where('type', 'deposit')->where('status', 'completed')->sum('amount_total');
        $withdrawals = (float) Transaction::where('type', 'withdrawal')->where('status', 'completed')->sum('amount_target');
        $pendingWithdrawals = Transaction::where('type', 'withdrawal')->where('status', 'pending')->count();
        $escrowBalance = (float) Order::whereNotIn('status', ['delivered', 'cancelled'])->sum('amount_paid');

        $recentTransactions = Transaction::orderByDesc('created_at')
            ->limit(20)
            ->get(['id', 'type', 'status', 'amount_total', 'amount_target', 'created_at']);

        $pendingWithdrawals = Transaction::with('user:id,name,email,phone,country,kyc_status')
            ->where('type', 'withdrawal')
            ->where('status', 'pending')
            ->orderByDesc('created_at')
            ->limit(50)
            ->get();

        $completedWithdrawals = Transaction::with('user:id,name,email,phone,country,kyc_status')
            ->where('type', 'withdrawal')
            ->where('status', 'completed')
            ->orderByDesc('created_at')
            ->limit(50)
            ->get();

        $allWithdrawals = $pendingWithdrawals->concat($completedWithdrawals);

        return response()->json([
            'summary' => [
                'total_deposits'         => $deposits,
                'total_withdrawals'      => $withdrawals,
                'pending_withdrawals'    => $pendingWithdrawals->count(),
                'pending_withdrawals_amount' => (float) $pendingWithdrawals->sum('amount_target'),
                'escrow_balance'         => $escrowBalance,
                'net_revenue'            => $deposits - $withdrawals,
            ],
            'recent_transactions' => $recentTransactions->map(fn ($t) => [
                'id'            => $t->id,
                'type'          => $t->type,
                'status'        => $t->status,
                'amount_total'  => (float) $t->amount_total,
                'amount_target' => (float) $t->amount_target,
                'created_at'    => $t->created_at?->toIso8601String(),
            ]),
            'withdrawals' => $allWithdrawals->map(fn ($t) => [
                'id'            => $t->id,
                'user'          => $t->user?->name ?? 'N/A',
                'email'         => $t->user?->email ?? 'N/A',
                'amount'        => (float) $t->amount_target,
                'method'        => $t->payment_gateway ?? 'N/A',
                'country'       => $t->user?->country ?? 'N/A',
                'kyc'           => $t->user?->kyc_status ?? 'unknown',
                'status'        => $t->status,
                'created_at'    => $t->created_at?->toIso8601String(),
            ]),
        ]);
    }

    /**
     * GET /api/admin/tracy/status — Status Tracy Core.
     */
    public function tracyStatus(): JsonResponse
    {
        $tracyUrl = config('services.tracy_core.url', 'http://127.0.0.1:8001');

        try {
            $response = \Illuminate\Support\Facades\Http::withHeaders([
                'X-Api-Key' => config('services.tracy_core.api_key', ''),
            ])->timeout(5)->get($tracyUrl . '/health');

            if ($response->successful()) {
                return response()->json([
                    'online'  => true,
                    'service' => $response->json('service', 'tracy-core'),
                    'url'     => $tracyUrl,
                ]);
            }

            return response()->json([
                'online'  => false,
                'url'     => $tracyUrl,
                'error'   => 'HTTP ' . $response->status(),
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'online'  => false,
                'url'     => $tracyUrl,
                'error'   => $e->getMessage(),
            ]);
        }
    }

    /**
     * GET /api/admin/tracy/config — Config Tracy Core (read-only).
     */
    public function tracyConfig(): JsonResponse
    {
        $tracyUrl = config('services.tracy_core.url', 'http://127.0.0.1:8001');

        try {
            $response = \Illuminate\Support\Facades\Http::withHeaders([
                'X-Api-Key' => config('services.tracy_core.api_key', ''),
            ])->timeout(5)->get($tracyUrl . '/config');

            if ($response->successful()) {
                return response()->json($response->json());
            }

            return response()->json([
                'error'  => 'HTTP ' . $response->status(),
                'online' => false,
            ], 502);
        } catch (\Exception $e) {
            return response()->json([
                'error'  => $e->getMessage(),
                'online' => false,
            ], 502);
        }
    }

    /**
     * GET /api/admin/live-feed — Feed temps réel (activités récentes).
     */
    public function liveFeed(Request $request): JsonResponse
    {
        $page = (int) $request->input('page', 1);
        $perPage = 20;

        $items = collect();

        // Recent users
        User::orderByDesc('created_at')->limit(5)->get()
            ->each(fn ($u) => $items->push([
                'type'    => 'user_registered',
                'message' => "Nouvel utilisateur : {$u->name} ({$u->role->value})",
                'time'    => $u->created_at?->toIso8601String(),
            ]));

        // Recent orders
        Order::orderByDesc('created_at')->limit(5)->get()
            ->each(fn ($o) => $items->push([
                'type'    => 'order_created',
                'message' => "Commande {$o->reference} — " . ($o->status instanceof \App\Enums\OrderStatus ? $o->status->value : (string) $o->status),
                'time'    => $o->created_at?->toIso8601String(),
            ]));

        // Recent transactions
        Transaction::orderByDesc('created_at')->limit(5)->get()
            ->each(fn ($t) => $items->push([
                'type'    => 'transaction',
                'message' => "Transaction {$t->type} — {$t->status}",
                'time'    => $t->created_at?->toIso8601String(),
            ]));

        $sorted = $items->sortByDesc('time')->values();

        return response()->json([
            'data' => $sorted->forPage($page, $perPage),
            'meta' => [
                'current_page' => $page,
                'total'        => $sorted->count(),
            ],
        ]);
    }

    /**
     * GET /api/admin/growth — Croissance users & commandes (30 derniers jours).
     */
    public function growth(): JsonResponse
    {
        $days = 30;
        $startDate = now()->subDays($days)->startOfDay();

        $usersPerDay = User::selectRaw("DATE(created_at) as date, COUNT(*) as count")
            ->where('created_at', '>=', $startDate)
            ->groupByRaw("DATE(created_at)")
            ->orderByRaw("DATE(created_at)")
            ->get()
            ->keyBy('date');

        $ordersPerDay = Order::selectRaw("DATE(created_at) as date, COUNT(*) as count, COALESCE(SUM(amount_paid), 0) as revenue")
            ->where('created_at', '>=', $startDate)
            ->groupByRaw("DATE(created_at)")
            ->orderByRaw("DATE(created_at)")
            ->get()
            ->keyBy('date');

        $series = [];
        for ($i = $days; $i >= 0; $i--) {
            $date = now()->subDays($i)->format('Y-m-d');
            $series[] = [
                'date'    => $date,
                'users'   => $usersPerDay->get($date)?->count ?? 0,
                'orders'  => $ordersPerDay->get($date)?->count ?? 0,
                'revenue' => (float) ($ordersPerDay->get($date)?->revenue ?? 0),
            ];
        }

        $totalUsers = User::count();
        $totalOrders = Order::count();
        $newUsers30 = User::where('created_at', '>=', $startDate)->count();
        $newOrders30 = Order::where('created_at', '>=', $startDate)->count();

        return response()->json([
            'series' => $series,
            'summary' => [
                'total_users'    => $totalUsers,
                'total_orders'   => $totalOrders,
                'new_users_30d'  => $newUsers30,
                'new_orders_30d' => $newOrders30,
                'avg_users_day'  => round($newUsers30 / $days, 1),
                'avg_orders_day' => round($newOrders30 / $days, 1),
            ],
        ]);
    }

    /**
     * GET /api/admin/revenue — Revenus & commissions.
     */
    public function revenue(): JsonResponse
    {
        $totalCommission = (float) Order::where('status', 'delivered')->sum('commission_amount');
        $totalVendorEarnings = (float) Order::where('status', 'delivered')->sum('vendor_earnings');
        $totalDeliveryFees = (float) Order::where('status', 'delivered')->sum('delivery_fee_paid');
        $totalOrderValue = (float) Order::where('status', 'delivered')->sum('amount_paid');

        $deposits = (float) Transaction::where('type', 'deposit')->where('status', 'completed')->sum('amount_total');
        $withdrawals = (float) Transaction::where('type', 'withdrawal')->where('status', 'completed')->sum('amount_target');
        $gatewayFees = (float) Transaction::where('status', 'completed')->sum('gateway_fee');
        $mantotaMarkup = (float) Transaction::where('status', 'completed')->sum('mantota_markup');

        // Revenue by plan
        $planRevenue = User::selectRaw("bot_plan, COUNT(*) as vendors, COALESCE(SUM(0), 0) as estimate")
            ->where('role', UserRole::VENDOR)
            ->groupBy('bot_plan')
            ->get();

        // Last 30 days revenue
        $startDate = now()->subDays(30)->startOfDay();
        $dailyRevenue = Order::selectRaw("DATE(created_at) as date, COALESCE(SUM(commission_amount), 0) as commission, COALESCE(SUM(amount_paid), 0) as gross")
            ->where('created_at', '>=', $startDate)
            ->where('status', 'delivered')
            ->groupByRaw("DATE(created_at)")
            ->orderByRaw("DATE(created_at)")
            ->get()
            ->keyBy('date');

        $series = [];
        for ($i = 30; $i >= 0; $i--) {
            $date = now()->subDays($i)->format('Y-m-d');
            $series[] = [
                'date'       => $date,
                'commission' => (float) ($dailyRevenue->get($date)?->commission ?? 0),
                'gross'      => (float) ($dailyRevenue->get($date)?->gross ?? 0),
            ];
        }

        return response()->json([
            'summary' => [
                'total_commission'      => $totalCommission,
                'total_vendor_earnings' => $totalVendorEarnings,
                'total_delivery_fees'   => $totalDeliveryFees,
                'total_order_value'     => $totalOrderValue,
                'total_deposits'        => $deposits,
                'total_withdrawals'     => $withdrawals,
                'gateway_fees'          => $gatewayFees,
                'mantota_markup'        => $mantotaMarkup,
                'net_revenue'           => $totalCommission + $mantotaMarkup + $totalDeliveryFees,
            ],
            'plan_breakdown' => $planRevenue,
            'series' => $series,
        ]);
    }

    /**
     * GET /api/admin/countries — Stats par pays.
     */
    public function countries(): JsonResponse
    {
        $usersByCountry = User::selectRaw("country, COUNT(*) as users")
            ->whereNotNull('country')
            ->where('country', '!=', '')
            ->groupBy('country')
            ->orderByDesc('users')
            ->get();

        $ordersByCountry = Order::selectRaw("country, COUNT(*) as orders, COALESCE(SUM(amount_paid), 0) as revenue")
            ->whereNotNull('country')
            ->where('country', '!=', '')
            ->groupBy('country')
            ->orderByDesc('orders')
            ->get()
            ->keyBy('country');

        $data = $usersByCountry->map(function ($u) use ($ordersByCountry) {
            $orders = $ordersByCountry->get($u->country);
            return [
                'country'   => $u->country,
                'users'     => $u->users,
                'orders'    => $orders?->orders ?? 0,
                'revenue'   => (float) ($orders?->revenue ?? 0),
            ];
        });

        // Add countries with orders but no users
        $ordersByCountry->each(function ($o, $country) use ($data, $usersByCountry) {
            if (!$usersByCountry->contains('country', $country)) {
                $data->push([
                    'country' => $country,
                    'users'   => 0,
                    'orders'  => $o->orders,
                    'revenue' => (float) $o->revenue,
                ]);
            }
        });

        return response()->json([
            'data' => $data->sortByDesc('orders')->values(),
            'summary' => [
                'total_countries' => $data->count(),
                'total_users'     => $usersByCountry->sum('users'),
                'total_orders'    => $ordersByCountry->sum('orders'),
            ],
        ]);
    }

    /**
     * GET /api/admin/shops-map — Boutiques avec coordonnées géo.
     */
    public function shopsMap(Request $request): JsonResponse
    {
        $query = User::where('role', UserRole::VENDOR)
            ->whereNotNull('shop_latitude')
            ->whereNotNull('shop_longitude')
            ->where('shop_latitude', '!=', 0)
            ->where('shop_longitude', '!=', 0)
            ->when($request->input('search'), function ($q, $search) {
                $q->where('shop_name', 'ILIKE', "%{$search}%")
                  ->orWhere('name', 'ILIKE', "%{$search}%");
            });

        $perPage = min((int) $request->input('per_page', 200), 500);
        $shops = $query->paginate($perPage);

        return response()->json([
            'data' => collect($shops->items())->map(fn ($s) => [
                'id'          => $s->id,
                'shop_name'   => $s->shop_name ?? $s->name,
                'shop_type'   => $s->shop_type,
                'bot_status'  => $s->bot_status,
                'bot_plan'    => $s->bot_plan,
                'country'     => $s->country,
                'address'     => $s->shop_address,
                'latitude'    => (float) $s->shop_latitude,
                'longitude'   => (float) $s->shop_longitude,
                'phone'       => $s->phone,
                'slug'        => $s->slug,
                'created_at'  => $s->created_at?->toIso8601String(),
            ]),
            'meta' => [
                'total'        => $shops->total(),
                'current_page' => $shops->currentPage(),
            ],
        ]);
    }

    /**
     * GET /api/admin/shop-quality — Qualité des boutiques.
     */
    public function shopQuality(): JsonResponse
    {
        $vendors = User::where('role', UserRole::VENDOR)
            ->withCount(['products as total_products' => function ($q) {
                $q->where('status', 'active');
            }])
            ->limit(100)
            ->orderByDesc('created_at')
            ->get(['id', 'name', 'shop_name', 'shop_type', 'bot_status', 'bot_plan', 'country', 'created_at']);

        $vendorIds = $vendors->pluck('id');
        $orderStats = Order::selectRaw('vendor_id, COUNT(*) as total, SUM(CASE WHEN status = \'delivered\' THEN 1 ELSE 0 END) as delivered, SUM(CASE WHEN status = \'disputed\' THEN 1 ELSE 0 END) as disputed')
            ->whereIn('vendor_id', $vendorIds)
            ->groupBy('vendor_id')
            ->get()
            ->keyBy('vendor_id');

        $data = $vendors->map(function ($v) use ($orderStats) {
            $stats = $orderStats->get($v->id);
            $total = $stats?->total ?? 0;
            $delivered = $stats?->delivered ?? 0;
            $disputed = $stats?->disputed ?? 0;
            $deliveryRate = $total > 0 ? round(($delivered / $total) * 100, 1) : 0;
            $disputeRate = $total > 0 ? round(($disputed / $total) * 100, 1) : 0;

            // Quality score: delivery rate - dispute rate + product bonus
            $qualityScore = max(0, min(100, $deliveryRate - $disputeRate + min($v->total_products * 2, 20)));

            return [
                'id'             => $v->id,
                'shop_name'      => $v->shop_name ?? $v->name,
                'shop_type'      => $v->shop_type,
                'bot_status'     => $v->bot_status,
                'bot_plan'       => $v->bot_plan,
                'country'        => $v->country,
                'total_products' => $v->total_products,
                'total_orders'   => $total,
                'delivered'      => $delivered,
                'disputed'       => $disputed,
                'delivery_rate'  => $deliveryRate,
                'dispute_rate'   => $disputeRate,
                'quality_score'  => $qualityScore,
                'created_at'     => $v->created_at?->toIso8601String(),
            ];
        })->sortByDesc('quality_score')->values();

        return response()->json([
            'data' => $data,
            'summary' => [
                'total_shops'    => $data->count(),
                'avg_quality'    => round($data->avg('quality_score'), 1),
                'active_shops'   => $data->where('bot_status', 'active')->count(),
                'avg_products'   => round($data->avg('total_products'), 1),
            ],
        ]);
    }

    /**
     * GET /api/admin/security — Sécurité (users bannis, activité suspecte).
     */
    public function security(): JsonResponse
    {
        $bannedUsers = User::onlyTrashed()->count();
        $vipUsers = User::where('is_vip', true)->count();
        $unverifiedEmails = User::whereNull('email_verified_at')->count();
        $unverifiedPhones = User::whereNull('phone_verified_at')->whereNotNull('phone')->count();

        $recentBanned = User::onlyTrashed()
            ->orderByDesc('deleted_at')
            ->limit(10)
            ->get(['id', 'name', 'email', 'role', 'deleted_at']);

        $disputedOrders = Order::where('status', 'disputed')
            ->orderByDesc('created_at')
            ->limit(10)
            ->get(['id', 'reference', 'customer_name', 'vendor_id', 'dispute_reason', 'created_at']);

        return response()->json([
            'summary' => [
                'banned_users'      => $bannedUsers,
                'vip_users'         => $vipUsers,
                'unverified_emails' => $unverifiedEmails,
                'unverified_phones' => $unverifiedPhones,
                'disputed_orders'   => Order::where('status', 'disputed')->count(),
            ],
            'recent_banned' => $recentBanned,
            'recent_disputes' => $disputedOrders->map(fn ($o) => [
                'id'            => $o->id,
                'reference'     => $o->reference,
                'customer'      => $o->customer_name,
                'dispute_reason'=> $o->dispute_reason,
                'created_at'    => $o->created_at?->toIso8601String(),
            ]),
        ]);
    }

    /**
     * GET /api/admin/system-health — Santé système.
     */
    public function systemHealth(): JsonResponse
    {
        $dbSize = DB::selectOne("SELECT pg_database_size(current_database()) as size")->size ?? 0;

        $tableCounts = [
            'users'        => User::count(),
            'products'     => Product::count(),
            'orders'       => Order::count(),
            'transactions' => Transaction::count(),
        ];

        $tracyUrl = config('services.tracy_core.url', 'http://127.0.0.1:8001');
        $tracyOnline = false;
        $tracyError = null;
        try {
            $resp = \Illuminate\Support\Facades\Http::withHeaders([
                'X-Api-Key' => config('services.tracy_core.api_key', ''),
            ])->timeout(3)->get($tracyUrl . '/health');
            $tracyOnline = $resp->successful();
            if (!$tracyOnline) $tracyError = 'HTTP ' . $resp->status();
        } catch (\Exception $e) {
            $tracyError = $e->getMessage();
        }

        return response()->json([
            'php_version'    => PHP_VERSION,
            'laravel_version'=> app()->version(),
            'db_size_mb'     => round($dbSize / 1024 / 1024, 2),
            'table_counts'   => $tableCounts,
            'tracy_core'     => [
                'online' => $tracyOnline,
                'url'    => $tracyUrl,
                'error'  => $tracyError,
            ],
            'server_time'    => now()->toIso8601String(),
        ]);
    }

    /**
     * GET /api/admin/notifications — Notifications agrégées pour l'admin.
     */
    public function notifications(): JsonResponse
    {
        $notifications = [];

        // 1. Nouveaux litiges (orders disputed — dernières 48h)
        $disputedOrders = Order::where('status', 'disputed')
            ->where('created_at', '>=', now()->subDays(2))
            ->orderByDesc('created_at')
            ->limit(20)
            ->get();

        foreach ($disputedOrders as $order) {
            $notifications[] = [
                'id'          => 'dispute_' . $order->id,
                'type'        => 'dispute',
                'severity'    => 'danger',
                'title'       => 'Nouveau litige',
                'message'     => "Commande {$order->reference} — {$order->customer_name} : {$order->dispute_reason}",
                'link'        => '/orders?tab=disputes',
                'created_at'  => $order->created_at?->toIso8601String(),
                'read'        => false,
            ];
        }

        // 2. Nouvelles inscriptions (dernières 24h)
        $newUsers = User::where('created_at', '>=', now()->subDay())
            ->orderByDesc('created_at')
            ->limit(20)
            ->get();

        foreach ($newUsers as $user) {
            $notifications[] = [
                'id'          => 'user_' . $user->id,
                'type'        => 'new_user',
                'severity'    => 'info',
                'title'       => 'Nouvelle inscription',
                'message'     => "{$user->name} ({$user->email}) — Rôle: {$user->role->value}",
                'link'        => '/users',
                'created_at'  => $user->created_at?->toIso8601String(),
                'read'        => false,
            ];
        }

        // 3. Utilisateurs bannis récemment
        $bannedUsers = User::onlyTrashed()
            ->where('deleted_at', '>=', now()->subDays(7))
            ->orderByDesc('deleted_at')
            ->limit(10)
            ->get();

        foreach ($bannedUsers as $user) {
            $notifications[] = [
                'id'          => 'banned_' . $user->id,
                'type'        => 'banned',
                'severity'    => 'warning',
                'title'       => 'Utilisateur banni',
                'message'     => "{$user->name} ({$user->email}) a été banni",
                'link'        => '/users?status=banned',
                'created_at'  => $user->deleted_at?->toIso8601String(),
                'read'        => false,
            ];
        }

        // 4. KYC en attente
        $pendingKyc = User::where('kyc_status', 'pending')
            ->orderByDesc('created_at')
            ->limit(10)
            ->get();

        foreach ($pendingKyc as $user) {
            $notifications[] = [
                'id'          => 'kyc_' . $user->id,
                'type'        => 'kyc',
                'severity'    => 'warning',
                'title'       => 'KYC en attente',
                'message'     => "{$user->name} ({$user->email}) — vérification KYC en attente",
                'link'        => '/users',
                'created_at'  => $user->created_at?->toIso8601String(),
                'read'        => false,
            ];
        }

        // 5. Retraits en attente
        $pendingWithdrawals = Transaction::with('user:id,name,email')
            ->where('type', 'withdrawal')
            ->where('status', 'pending')
            ->orderByDesc('created_at')
            ->limit(10)
            ->get();

        foreach ($pendingWithdrawals as $tx) {
            $notifications[] = [
                'id'          => 'withdrawal_' . $tx->id,
                'type'        => 'withdrawal',
                'severity'    => 'warning',
                'title'       => 'Retrait en attente',
                'message'     => "{$tx->user?->name} — " . number_format((float) $tx->amount_target, 0, ',', ' ') . " FCFA",
                'link'        => '/finance?tab=payouts',
                'created_at'  => $tx->created_at?->toIso8601String(),
                'read'        => false,
            ];
        }

        // 6. Alertes sécurité — emails non vérifiés avec rôle vendor
        $unverifiedVendors = User::whereNull('email_verified_at')
            ->whereIn('role', [UserRole::VENDOR, UserRole::INFLUENCER])
            ->where('created_at', '>=', now()->subDays(7))
            ->orderByDesc('created_at')
            ->limit(5)
            ->get();

        foreach ($unverifiedVendors as $user) {
            $notifications[] = [
                'id'          => 'unverified_' . $user->id,
                'type'        => 'security',
                'severity'    => 'warning',
                'title'       => 'Email non vérifié',
                'message'     => "{$user->name} ({$user->email}) — {$user->role->value} sans email vérifié",
                'link'        => '/users',
                'created_at'  => $user->created_at?->toIso8601String(),
                'read'        => false,
            ];
        }

        // Sort by created_at descending
        usort($notifications, fn ($a, $b) => strcmp($b['created_at'] ?? '', $a['created_at'] ?? ''));

        $unreadCount = count(array_filter($notifications, fn ($n) => !$n['read']));

        return response()->json([
            'data'        => array_slice($notifications, 0, 50),
            'unread_count'=> $unreadCount,
            'total'       => count($notifications),
        ]);
    }
}
