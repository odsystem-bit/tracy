<?php

declare(strict_types=1);

namespace App\Http\Controllers\Public;

use App\Enums\OrderStatus;
use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\Product;
use App\Models\User;
use App\Services\Payment\MonerooService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Str;

class GuestCheckoutController extends Controller
{
    public function store(Request $request): JsonResponse
    {
        $validated = Validator::make($request->all(), [
            'product_id'        => ['required', 'integer', 'exists:products,id'],
            'customer_name'     => ['required', 'string', 'max:255'],
            'customer_phone'    => ['required', 'string', 'max:30'],
            'customer_email'    => ['nullable', 'email', 'max:255'],
            'country'           => ['required', 'string', 'max:5'],
            'city'              => ['required', 'string', 'max:100'],
            'landmark_indication' => ['nullable', 'string', 'max:500'],
        ])->validate();

        return DB::transaction(function () use ($validated) {
            $product = Product::findOrFail($validated['product_id']);

            if ($product->status !== 'actif') {
                return response()->json(['error' => 'Produit non disponible'], 422);
            }

            if ($product->type === 'physical' && $product->stock <= 0) {
                return response()->json(['error' => 'Produit en rupture de stock'], 422);
            }

            if (! $product->vendor_id) {
                return response()->json(['error' => 'Ce produit n\'a pas de vendeur associé'], 422);
            }

            $vendor = User::find($product->vendor_id);
            $commissionPercent = $product->commission_percent ?? ($vendor?->commission_percent ?? 10);
            $commissionAmount = $product->price * ($commissionPercent / 100);

            $order = Order::create([
                'reference'         => Order::generateReference(),
                'vendor_id'         => $product->vendor_id,
                'product_id'        => $product->id,
                'customer_name'     => $validated['customer_name'],
                'customer_phone'    => $validated['customer_phone'],
                'customer_email'    => $validated['customer_email'] ?? null,
                'customer_whatsapp' => $validated['customer_phone'],
                'country'           => $validated['country'],
                'city'              => $validated['city'],
                'landmark_indication' => $validated['landmark_indication'] ?? null,
                'amount_paid'       => $product->price,
                'commission_amount' => $commissionAmount,
                'vendor_earnings'   => $product->price - $commissionAmount,
                'delivery_fee_paid' => 0,
                'status'            => OrderStatus::PENDING,
                'payment_status'    => 'awaiting',
                'payment_gateway'   => 'moneroo',
                'tracking_token'    => Str::random(40),
                'delivery_pin'      => str_pad((string) rand(1000, 9999), 4, '0', STR_PAD_LEFT),
            ]);

            if ($product->type === 'physical') {
                $product->decrement('stock');
            }

            $paymentUrl = null;
            try {
                $result = MonerooService::createPaymentLink([
                    'amount'        => $product->price,
                    'reference'     => $order->reference,
                    'customer_name' => $validated['customer_name'],
                    'customer_phone'=> $validated['customer_phone'],
                    'return_url'    => config('app.url') . '/track/' . $order->id . '?token=' . $order->tracking_token,
                    'description'   => 'Commande ' . $order->reference . ' — ' . $product->name,
                ]);
                $paymentUrl = $result['url'];
            } catch (\Exception $e) {
                $paymentUrl = null;
            }

            return response()->json([
                'success'        => true,
                'order_id'       => $order->id,
                'reference'      => $order->reference,
                'product'        => [
                    'id'    => $product->id,
                    'name'  => $product->name,
                    'price' => (float) $product->price,
                ],
                'amount'         => (float) $product->price,
                'payment_url'    => $paymentUrl,
                'tracking_url'   => config('app.url') . '/track/' . $order->id . '?token=' . $order->tracking_token,
                'tracking_token' => $order->tracking_token,
            ]);
        });
    }
}
