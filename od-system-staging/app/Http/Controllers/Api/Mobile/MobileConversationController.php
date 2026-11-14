<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Mobile;

use App\Http\Controllers\Controller;
use App\Models\Conversation;
use App\Models\ConversationMessage;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class MobileConversationController extends Controller
{
    /**
     * Recherche un utilisateur par nom, numéro de téléphone ou nom de boutique.
     * GET /users/search?q=...
     */
    public function searchUser(Request $request): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'q'      => 'nullable|string|min:1',
            'phone'  => 'nullable|string|min:4',
        ]);

        if ($validator->fails()) {
            return response()->json(['message' => 'Recherche invalide.'], 422);
        }

        $query = $request->input('q', $request->input('phone', ''));
        if (empty($query)) {
            return response()->json(['message' => 'Recherche invalide.'], 422);
        }

        $currentUser = $request->user();

        // Recherche par nom, téléphone, nom de boutique, display_name
        $users = User::where('id', '!=', $currentUser->id)
            ->where(function ($q) use ($query) {
                $q->where('name', 'ILIKE', "%{$query}%")
                  ->orWhere('display_name', 'ILIKE', "%{$query}%")
                  ->orWhere('phone', 'ILIKE', "%{$query}%")
                  ->orWhere('shop_name', 'ILIKE', "%{$query}%")
                  ->orWhere('business_name', 'ILIKE', "%{$query}%");
            })
            ->limit(20)
            ->get();

        if ($users->isEmpty()) {
            return response()->json(['users' => [], 'user' => null], 200);
        }

        $results = $users->map(function ($user) {
            $isVendor = $user->hasMode('vendor');
            return [
                'id' => $user->id,
                'name' => $user->name ?? '',
                'display_name' => $user->display_name ?? $user->name,
                'phone' => $user->phone,
                'avatar_url' => $user->profile_photo_url ?? null,
                'is_online' => false,
                'is_vendor' => $isVendor,
                'shop_name' => $user->shop_name ?? null,
            ];
        });

        // Garder la compatibilité avec l'ancien format (user unique) + nouveau format (users list)
        return response()->json([
            'users' => $results,
            'user' => $results->first(),
        ]);
    }

    /**
     * Liste les conversations de l'utilisateur connecté.
     * GET /conversations
     */
    public function index(Request $request): JsonResponse
    {
        $userId = $request->user()->id;

        $conversations = Conversation::where('user1_id', $userId)
            ->orWhere('user2_id', $userId)
            ->with(['user1', 'user2'])
            ->orderByDesc('last_message_time')
            ->get();

        $result = $conversations->map(function ($conv) use ($userId) {
            $other = $conv->otherUser($userId);
            $isTracy = false; // Tracy channel handled separately

            return [
                'id' => (string) $conv->id,
                'name' => $other->display_name ?? $other->name ?? 'Utilisateur',
                'avatar_url' => $other->profile_photo_url ?? null,
                'last_message' => $conv->last_message,
                'last_message_time' => $conv->last_message_time?->toIso8601String(),
                'unread_count' => $conv->unreadCountFor($userId),
                'channel' => 'app',
                'is_online' => false,
                'is_tracy' => $isTracy,
            ];
        });

        return response()->json(['data' => $result]);
    }

    /**
     * Démarre ou récupère une conversation avec un utilisateur.
     * POST /conversations { user_id: ... }
     */
    public function store(Request $request): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'user_id' => 'required|integer|exists:users,id',
        ]);

        if ($validator->fails()) {
            return response()->json(['message' => 'Utilisateur invalide.'], 422);
        }

        $currentUserId = $request->user()->id;
        $otherUserId = (int) $request->input('user_id');

        if ($currentUserId === $otherUserId) {
            return response()->json(['message' => 'Impossible de démarrer une conversation avec soi-même.'], 422);
        }

        // Assurer user1_id < user2_id pour l'unicité
        $user1Id = min($currentUserId, $otherUserId);
        $user2Id = max($currentUserId, $otherUserId);

        $conv = Conversation::firstOrCreate(
            ['user1_id' => $user1Id, 'user2_id' => $user2Id],
        );

        $other = $conv->otherUser($currentUserId);

        return response()->json([
            'id' => (string) $conv->id,
            'name' => $other->display_name ?? $other->name ?? 'Utilisateur',
            'avatar_url' => $other->profile_photo_url ?? null,
            'last_message' => $conv->last_message,
            'last_message_time' => $conv->last_message_time?->toIso8601String(),
            'unread_count' => $conv->unreadCountFor($currentUserId),
            'channel' => 'app',
            'is_online' => false,
            'is_tracy' => false,
        ]);
    }

    /**
     * Récupère les messages d'une conversation.
     * GET /conversations/{id}/messages
     */
    public function messages(Request $request, string $id): JsonResponse
    {
        $userId = $request->user()->id;

        $conv = Conversation::find($id);
        if (!$conv) {
            return response()->json(['message' => 'Conversation introuvable.'], 404);
        }

        if ($conv->user1_id !== $userId && $conv->user2_id !== $userId) {
            return response()->json(['message' => 'Non autorisé.'], 403);
        }

        $messages = $conv->messages()->orderBy('created_at')->limit(100)->get();

        $result = $messages->map(fn ($msg) => [
            'id' => (string) $msg->id,
            'text' => $msg->content,
            'is_from_me' => $msg->sender_id === $userId,
            'is_from_tracy' => $msg->is_from_tracy,
            'type' => $msg->type,
            'created_at' => $msg->created_at?->toIso8601String(),
            'channel' => $msg->channel,
        ]);

        return response()->json(['data' => $result]);
    }

    /**
     * Envoie un message dans une conversation.
     * POST /conversations/{id}/messages { type, content }
     */
    public function sendMessage(Request $request, string $id): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'type' => 'sometimes|string|in:text,image,audio,product,order,system',
            'content' => 'required|string',
        ]);

        if ($validator->fails()) {
            return response()->json(['message' => 'Message invalide.'], 422);
        }

        $userId = $request->user()->id;

        $conv = Conversation::find($id);
        if (!$conv) {
            return response()->json(['message' => 'Conversation introuvable.'], 404);
        }

        if ($conv->user1_id !== $userId && $conv->user2_id !== $userId) {
            return response()->json(['message' => 'Non autorisé.'], 403);
        }

        $msg = ConversationMessage::create([
            'conversation_id' => $conv->id,
            'sender_id' => $userId,
            'type' => $request->input('type', 'text'),
            'content' => $request->input('content'),
            'channel' => 'app',
            'is_from_tracy' => false,
        ]);

        // Update conversation's last message
        $conv->update([
            'last_message' => mb_substr($request->input('content'), 0, 100),
            'last_message_time' => now(),
        ]);

        return response()->json([
            'id' => (string) $msg->id,
            'text' => $msg->content,
            'is_from_me' => true,
            'is_from_tracy' => false,
            'type' => $msg->type,
            'created_at' => $msg->created_at?->toIso8601String(),
            'channel' => $msg->channel,
        ]);
    }

    /**
     * Marque une conversation comme lue.
     * POST /conversations/{id}/read
     */
    public function markAsRead(Request $request, string $id): JsonResponse
    {
        $userId = $request->user()->id;

        $conv = Conversation::find($id);
        if (!$conv) {
            return response()->json(['message' => 'Conversation introuvable.'], 404);
        }

        if ($conv->user1_id !== $userId && $conv->user2_id !== $userId) {
            return response()->json(['message' => 'Non autorisé.'], 403);
        }

        if ($conv->user1_id === $userId) {
            $conv->update(['user1_last_read' => now()]);
        } else {
            $conv->update(['user2_last_read' => now()]);
        }

        return response()->json(['ok' => true]);
    }
}
