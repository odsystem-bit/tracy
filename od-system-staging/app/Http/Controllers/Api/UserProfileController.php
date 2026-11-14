<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class UserProfileController extends Controller
{
    /**
     * PATCH /user/profile — Met à jour le profil de l'utilisateur connecté.
     */
    public function update(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'display_name' => 'nullable|string|max:255',
            'avatar_url'   => 'nullable|string|max:500',
        ]);

        $user = $request->user();
        $user->update($validated);

        return response()->json([
            'message' => 'Profil mis à jour.',
            'user' => [
                'id'           => $user->id,
                'name'         => $user->name,
                'display_name' => $user->display_name,
                'phone'        => $user->phone,
                'avatar_url'   => $user->avatar_url,
            ],
        ]);
    }
}
