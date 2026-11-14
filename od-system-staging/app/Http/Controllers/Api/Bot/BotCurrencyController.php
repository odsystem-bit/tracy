<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\Currency;
use Illuminate\Http\JsonResponse;

class BotCurrencyController extends Controller
{
    /**
     * GET /bot/currencies
     * Retourne la liste des devises actives avec leurs taux de conversion.
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
}
