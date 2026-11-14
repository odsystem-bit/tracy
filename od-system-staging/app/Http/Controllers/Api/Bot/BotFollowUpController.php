<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\TracyFollowUp;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

/**
 * Endpoint bot : Tracy Core planifie ici les relances client post-négociation.
 * La commande planifiée `mantota:send-tracy-follow-ups` les envoie à l'heure prévue
 * (WhatsApp via le numéro lié du vendeur, ou notification in-app).
 */
class BotFollowUpController extends Controller
{
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'vendor_id' => 'required|integer|exists:users,id',
            'customer_id' => 'required|string|max:40',
            'channel' => 'required|string|in:whatsapp,app',
            'message' => 'required|string|max:1500',
            'context_key' => 'nullable|string|max:80',
            'send_at_minutes' => 'nullable|integer|min:5|max:4320',
        ]);

        // Dédup : si une relance identique est déjà en attente, on ne reprogramme pas.
        $existing = TracyFollowUp::where('vendor_id', $validated['vendor_id'])
            ->where('customer_id', $validated['customer_id'])
            ->where('context_key', $validated['context_key'] ?? '')
            ->where('status', 'pending')
            ->first();

        if ($existing) {
            return response()->json([
                'success' => true,
                'follow_up_id' => $existing->id,
                'send_at' => $existing->send_at?->toIso8601String(),
                'deduplicated' => true,
            ]);
        }

        $followUp = TracyFollowUp::create([
            'vendor_id' => $validated['vendor_id'],
            'customer_id' => $validated['customer_id'],
            'channel' => $validated['channel'],
            'context_key' => $validated['context_key'] ?? '',
            'message' => $validated['message'],
            'send_at' => now()->addMinutes((int) ($validated['send_at_minutes'] ?? 120)),
            'status' => 'pending',
        ]);

        return response()->json([
            'success' => true,
            'follow_up_id' => $followUp->id,
            'send_at' => $followUp->send_at->toIso8601String(),
        ]);
    }
}
