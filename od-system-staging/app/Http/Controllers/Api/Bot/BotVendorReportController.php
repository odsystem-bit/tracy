<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\Conversation;
use App\Models\ConversationMessage;
use App\Models\User;
use App\Notifications\TracyVendorReportNotification;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class BotVendorReportController extends Controller
{
    /**
     * POST /bot/vendors/{vendorId}/reports
     * Tracy envoie un compte-rendu (résumé) ou une demande de contact au vendeur.
     */
    public function store(Request $request, int $vendorId): JsonResponse
    {
        $validated = $request->validate([
            'kind' => 'required|in:negotiation,sale,contact_request,summary',
            'summary' => 'required|string|max:1500',
            'customer_name' => 'nullable|string|max:255',
            'customer_phone' => 'nullable|string|max:30',
            'product_name' => 'nullable|string|max:255',
            'conversation_id' => 'nullable|string|max:255',
        ]);

        $vendor = User::findOrFail($vendorId);

        $vendor->notify(new TracyVendorReportNotification(
            $validated['kind'],
            $validated['summary'],
            collect($validated)->except(['kind', 'summary'])->all(),
        ));

        return response()->json(['success' => true]);
    }

    /**
     * POST /bot/vendors/{vendorId}/connect
     * Met un client (utilisateur de l'app) en relation directe avec le vendeur :
     * crée la vraie conversation in-app + un message d'introduction de Tracy.
     * Réservé à l'APK — sur le web public il n'y a pas d'utilisateur connecté.
     */
    public function connect(Request $request, int $vendorId): JsonResponse
    {
        $validated = $request->validate([
            'client_user_id' => 'required|integer|exists:users,id',
            'summary' => 'nullable|string|max:1500',
            'product_name' => 'nullable|string|max:255',
        ]);

        $vendor = User::findOrFail($vendorId);
        $client = User::findOrFail((int) $validated['client_user_id']);

        if ($vendor->id === $client->id) {
            return response()->json(['success' => false, 'message' => 'Même utilisateur'], 422);
        }

        $conv = Conversation::firstOrCreate([
            'user1_id' => min($vendor->id, $client->id),
            'user2_id' => max($vendor->id, $client->id),
        ]);

        $intro = 'Tracy vous a mis en relation. ' . ($validated['summary'] ?? 'Le client souhaite discuter.');
        ConversationMessage::create([
            'conversation_id' => $conv->id,
            'sender_id' => $vendor->id,
            'type' => 'system',
            'content' => mb_substr($intro, 0, 1500),
            'channel' => 'app',
            'is_from_tracy' => true,
        ]);
        $conv->update(['last_message' => mb_substr($intro, 0, 100), 'last_message_time' => now()]);

        $vendor->notify(new TracyVendorReportNotification(
            TracyVendorReportNotification::KIND_CONTACT_REQUEST,
            $intro,
            [
                'customer_name' => $client->display_name ?? $client->name,
                'customer_phone' => $client->phone ?? null,
                'product_name' => $validated['product_name'] ?? null,
                'conversation_id' => (string) $conv->id,
            ],
        ));

        return response()->json(['success' => true, 'conversation_id' => (string) $conv->id]);
    }

    /**
     * GET /bot/vendors/{vendorId}/reports
     * Derniers comptes-rendus de Tracy pour ce vendeur (utilisé par VendorCopilot).
     */
    public function index(Request $request, int $vendorId): JsonResponse
    {
        $limit = min(max((int) $request->query('limit', 10), 1), 30);
        $vendor = User::findOrFail($vendorId);

        $reports = $vendor->notifications()
            ->latest()
            ->limit(100)
            ->get()
            ->filter(fn ($n) => ($n->data['type'] ?? null) === 'tracy_report')
            ->take($limit)
            ->map(fn ($n) => [
                'id' => $n->id,
                'kind' => $n->data['kind'] ?? 'summary',
                'summary' => $n->data['message'] ?? '',
                'customer_name' => $n->data['customer_name'] ?? null,
                'customer_phone' => $n->data['customer_phone'] ?? null,
                'product_name' => $n->data['product_name'] ?? null,
                'read' => $n->read_at !== null,
                'created_at' => $n->created_at?->toIso8601String(),
            ])
            ->values();

        return response()->json(['reports' => $reports]);
    }
}
