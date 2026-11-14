<?php

declare(strict_types=1);

namespace App\Http\Controllers\Public;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Cache;

class PublicChatController extends Controller
{
    /**
     * POST /api/public/chat — Proxy public vers Tracy Core.
     * Rate-limité par IP pour éviter l'abus.
     */
    public function chat(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'text'            => ['required', 'string', 'max:500'],
            'store_id'        => ['nullable', 'string'],
            'customer_id'     => ['nullable', 'string'],
            'conversation_id' => ['nullable', 'string'],
            'country_code'    => ['nullable', 'string', 'size:2'],
            'city'            => ['nullable', 'string', 'max:100'],
            'latitude'        => ['nullable', 'numeric', 'between:-90,90'],
            'longitude'       => ['nullable', 'numeric', 'between:-180,180'],
            'image'           => ['nullable', 'string', 'max:4194304'], // data URL base64 (~3 Mo)
        ]);

        $ip = $request->ip();

        // Détection du pays via IP (geolocation)
        $countryCode = isset($validated['country_code'])
            ? strtoupper($validated['country_code'])
            : ($this->countryFromHeaders($request) ?? $this->detectCountryFromIp($ip));

        $cacheKey = "public_chat:{$ip}";
        $count = (int) Cache::get($cacheKey, 0);

        if ($count >= 20) {
            return response()->json([
                'error' => 'Trop de messages. Réessayez dans quelques minutes.',
            ], 429);
        }

        Cache::put($cacheKey, $count + 1, now()->addMinutes(5));

        $tracyUrl = config('services.tracy_core.url', 'http://127.0.0.1:8001');
        $apiKey   = config('services.tracy_core.api_key', '');

        try {
            $response = Http::withHeaders([
                'X-Api-Key' => $apiKey,
            ])->timeout(60)->post($tracyUrl . '/chat', array_filter([
                'store_id'        => $validated['store_id'] ?? 'public',
                'customer_id'     => $validated['customer_id'] ?? $ip,
                'text'            => $validated['text'],
                'conversation_id' => $validated['conversation_id'] ?? null,
                'country_code'    => $countryCode,
                'city'            => $validated['city'] ?? null,
                'latitude'        => isset($validated['latitude']) ? (float) $validated['latitude'] : null,
                'image'           => $validated['image'] ?? null,
                'longitude'       => isset($validated['longitude']) ? (float) $validated['longitude'] : null,
            ], fn ($v) => $v !== null));

            if ($response->successful()) {
                return response()->json($response->json());
            }

            Log::error('public_chat_tracy_error', [
                'status' => $response->status(),
                'body'   => $response->body(),
            ]);

            return response()->json([
                'text' => 'Désolée, je rencontre un problème technique. Réessayez dans un instant.',
                'correlation_id' => null,
                'agent' => null,
                'tools_used' => [],
            ], 200);
        } catch (\Exception $e) {
            Log::error('public_chat_tracy_exception', [
                'error' => $e->getMessage(),
            ]);

            return response()->json([
                'text' => 'Désolée, je ne suis pas disponible pour le moment. Téléchargez l\'app Mantota pour continuer !',
                'correlation_id' => null,
                'agent' => null,
                'tools_used' => [],
            ], 200);
        }
    }

    /**
     * Pays fourni par le reverse-proxy / CDN (fiable, sans appel externe).
     */
    private function countryFromHeaders(Request $request): ?string
    {
        foreach (['CF-IPCountry', 'X-Country-Code', 'CloudFront-Viewer-Country'] as $h) {
            $v = $request->header($h);
            if (is_string($v) && preg_match('/^[A-Za-z]{2}$/', $v) && strtoupper($v) !== 'XX') {
                return strtoupper($v);
            }
        }

        return null;
    }

    /**
     * Détecte le pays d'une adresse IP via un service de géolocalisation.
     * Retourne le code ISO 2 lettres (ex: BJ, CI, NG, GH, TG, SN).
     */
    private function detectCountryFromIp(string $ip): ?string
    {
        // IPs locales → pas de géolocalisation
        if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) === false) {
            return null;
        }

        try {
            $response = Http::timeout(1)->get("http://ip-api.com/json/{$ip}?fields=countryCode");
            if ($response->successful()) {
                $code = $response->json('countryCode');
                if ($code && strlen($code) === 2) {
                    return strtoupper($code);
                }
            }
        } catch (\Exception $e) {
            Log::warning('ip_geolocation_failed', ['ip' => $ip, 'error' => $e->getMessage()]);
        }

        return null;
    }
}
