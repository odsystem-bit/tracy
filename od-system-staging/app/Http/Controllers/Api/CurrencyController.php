<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Currency;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class CurrencyController extends Controller
{
    /**
     * GET /api/currencies
     * Liste publique des devises actives.
     */
    public function index(): JsonResponse
    {
        $currencies = Currency::where('is_active', true)->get();

        return response()->json([
            'currencies' => $currencies->map(fn (Currency $c) => [
                'code' => $c->code,
                'name' => $c->name,
                'symbol' => $c->symbol,
                'rate_to_xof' => $c->rate_to_xof,
                'country_codes' => $c->country_codes ?? [],
            ]),
        ]);
    }

    /**
     * PATCH /api/user/currency
     * Met à jour la devise préférée de l'utilisateur connecté.
     */
    public function update(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'currency' => 'required|string|size:3',
        ]);

        $currency = Currency::where('code', $validated['currency'])
            ->where('is_active', true)
            ->first();

        if (!$currency) {
            return response()->json(['message' => 'Devise non supportée.'], 422);
        }

        $user = $request->user();
        $user->preferred_currency = $currency->code;
        $user->save();

        return response()->json([
            'message' => 'Devise mise à jour.',
            'currency' => [
                'code' => $currency->code,
                'name' => $currency->name,
                'symbol' => $currency->symbol,
            ],
        ]);
    }
}
