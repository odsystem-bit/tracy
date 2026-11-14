<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\User;
use App\Models\UserMode;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class UserModeController extends Controller
{
    private const ALLOWED_MODES = ['buyer', 'vendor', 'partner'];
    private const ALWAYS_ACTIVE = ['buyer'];

    public function index(Request $request): JsonResponse
    {
        $user = $request->user();

        $modes = $user->modes()->get();

        $result = [];
        foreach (self::ALLOWED_MODES as $mode) {
            $userMode = $modes->firstWhere('mode', $mode);
            $result[] = [
                'mode' => $mode,
                'is_active' => $userMode?->is_active ?? in_array($mode, self::ALWAYS_ACTIVE),
                'can_deactivate' => !in_array($mode, self::ALWAYS_ACTIVE),
            ];
        }

        return response()->json(['modes' => $result]);
    }

    public function toggle(Request $request): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'mode' => 'required|string|in:buyer,vendor,partner',
            'active' => 'required|boolean',
        ]);

        if ($validator->fails()) {
            return response()->json(['message' => 'Mode invalide.', 'errors' => $validator->errors()], 422);
        }

        $mode = $request->input('mode');
        $active = $request->input('active');

        if (in_array($mode, self::ALWAYS_ACTIVE) && !$active) {
            return response()->json([
                'message' => 'Le mode ' . $mode . ' est toujours actif.',
            ], 422);
        }

        /** @var User $user */
        $user = $request->user();

        if ($active) {
            $user->activateMode($mode);
        } else {
            $user->deactivateMode($mode);
        }

        return response()->json([
            'mode' => $mode,
            'is_active' => $active,
        ]);
    }
}
