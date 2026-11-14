<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\Partner;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class BotPartnerController extends Controller
{
    /**
     * GET /bot/partners/search
     * Recherche d'un partenaire/créateur de contenu par nom.
     */
    public function search(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'query' => 'required|string|min:1',
        ]);

        $user = User::where('role', 'influencer')
            ->where(function ($q) use ($validated) {
                $q->where('name', 'ILIKE', '%' . $validated['query'] . '%')
                  ->orWhere('referral_code', 'ILIKE', '%' . $validated['query'] . '%');
            })
            ->first();

        if (! $user) {
            return response()->json(['error' => 'Partenaire non trouvé'], 404);
        }

        $commissions = \App\Models\Transaction::where('user_id', $user->id)
            ->where('type', 'earning')
            ->sum('amount_total');

        return response()->json([
            'id' => (string) $user->id,
            'nom' => $user->name,
            'commissions_cumulees' => (float) $commissions,
            'code_parrainage' => $user->referral_code,
        ]);
    }
}
