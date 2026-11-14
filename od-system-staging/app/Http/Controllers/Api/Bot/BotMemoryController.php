<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\MemoryEntry;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class BotMemoryController extends Controller
{
    /**
     * POST /bot/memory
     * Sauvegarde une entrée en mémoire longue.
     */
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'scope' => 'required|string|in:client,customer,vendor,store,conversation',
            'entity_id' => 'required|string|max:100',
            'key' => 'required|string|max:255',
            'value' => 'required|string|max:5000',
            'source' => 'nullable|string|in:inferred,explicit,observed,user_provided',
        ]);

        $entry = MemoryEntry::create([
            'scope' => $validated['scope'],
            'entity_id' => $validated['entity_id'],
            'key' => $validated['key'],
            'value' => $validated['value'],
            'source' => $validated['source'] ?? 'inferred',
        ]);

        return response()->json([
            'id' => (string) $entry->id,
            'scope' => $entry->scope,
            'entity_id' => $entry->entity_id,
            'key' => $entry->key,
            'value' => $entry->value,
            'source' => $entry->source,
            'created_at' => $entry->created_at?->toIso8601String(),
            'updated_at' => $entry->updated_at?->toIso8601String(),
        ], 201);
    }

    /**
     * GET /bot/memory/search
     * Recherche d'entrées en mémoire par scope et entity_id.
     */
    public function search(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'scope' => 'required|string',
            'entity_id' => 'required|string|max:100',
            'query' => 'nullable|string',
        ]);

        $query = MemoryEntry::where('scope', $validated['scope'])
            ->where('entity_id', $validated['entity_id'])
            ->where(function ($q) {
                $q->whereNull('expires_at')->orWhere('expires_at', '>', now());
            });

        if (! empty($validated['query'])) {
            $query->where(function ($q) use ($validated) {
                $q->where('key', 'ILIKE', '%' . $validated['query'] . '%')
                  ->orWhere('value', 'ILIKE', '%' . $validated['query'] . '%');
            });
        }

        $entries = $query->orderByDesc('updated_at')->limit(50)->get();

        return response()->json([
            'entries' => $entries->map(fn (MemoryEntry $e) => [
                'id' => (string) $e->id,
                'scope' => $e->scope,
                'entity_id' => $e->entity_id,
                'key' => $e->key,
                'value' => $e->value,
                'source' => $e->source,
                'created_at' => $e->created_at?->toIso8601String(),
                'updated_at' => $e->updated_at?->toIso8601String(),
                'expires_at' => $e->expires_at?->toIso8601String(),
            ]),
            'total' => $entries->count(),
        ]);
    }

    /**
     * PATCH /bot/memory/{id}
     * Met à jour la valeur d'une entrée en mémoire.
     */
    public function update(Request $request, string $id): JsonResponse
    {
        $validated = $request->validate([
            'value' => 'required|string|max:5000',
        ]);

        $entry = MemoryEntry::findOrFail($id);
        $entry->update(['value' => $validated['value']]);

        return response()->json([
            'id' => (string) $entry->id,
            'scope' => $entry->scope,
            'entity_id' => $entry->entity_id,
            'key' => $entry->key,
            'value' => $entry->value,
            'source' => $entry->source,
            'updated_at' => $entry->updated_at?->toIso8601String(),
        ]);
    }

    /**
     * DELETE /bot/memory/{id}
     * Supprime une entrée de la mémoire longue.
     */
    public function destroy(Request $request, string $id): JsonResponse
    {
        $validated = $request->validate([
            'reason' => 'nullable|string|max:500',
        ]);

        $entry = MemoryEntry::findOrFail($id);
        $entry->delete();

        return response()->json([
            'success' => true,
            'reason' => $validated['reason'] ?? null,
        ]);
    }
}
