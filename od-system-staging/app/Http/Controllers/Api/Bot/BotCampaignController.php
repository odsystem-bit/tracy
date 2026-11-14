<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\Campaign;
use Illuminate\Http\JsonResponse;

class BotCampaignController extends Controller
{
    /**
     * GET /bot/campaigns/{id}
     * Récupère les détails d'une campagne.
     */
    public function show(string $id): JsonResponse
    {
        $campaign = Campaign::with(['vendor', 'product'])->findOrFail($id);

        $smartLinkIds = $campaign->smartLinks()->pluck('id');
        $clicks = \DB::table('click_logs')->whereIn('smart_link_id', $smartLinkIds)->count();
        $conversions = $campaign->orders()->where('status', '!=', 'cancelled')->count();

        return response()->json([
            'id' => (string) $campaign->id,
            'nom' => $campaign->title,
            'statut' => $campaign->status->value,
            'audience' => $campaign->niche ?? null,
            'vues' => (int) $clicks,
            'clics' => (int) $clicks,
            'conversions' => (int) $conversions,
        ]);
    }
}
