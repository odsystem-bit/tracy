<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\OtpCode;
use App\Models\User;
use App\Models\UserMode;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

class OtpAuthController extends Controller
{
    private const OTP_EXPIRY_MINUTES = 5;
    private const OTP_MAX_ATTEMPTS = 5;

    public function requestOtp(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'phone' => 'required|string|min:8|max:15',
        ]);

        $phone = $this->normalizePhone($validated['phone']);

        $recentCount = OtpCode::where('phone', $phone)
            ->where('created_at', '>=', now()->subMinutes(10))
            ->count();

        if ($recentCount >= 3) {
            return response()->json([
                'message' => 'Trop de demandes. Réessayez dans 10 minutes.',
            ], 429);
        }

        $code = str_pad((string) random_int(0, 999999), 6, '0', STR_PAD_LEFT);

        OtpCode::create([
            'phone' => $phone,
            'code' => $code,
            'expires_at' => now()->addMinutes(self::OTP_EXPIRY_MINUTES),
            'used' => false,
        ]);

        // TODO: Envoyer le code via SMS (Moneroo SMS, Twilio, ou autre provider)
        // Pour le dev, on retourne le code dans la réponse
        $isDev = app()->environment('local', 'testing');

        return response()->json([
            'message' => 'Code OTP envoyé par SMS.',
            'phone' => $phone,
            ...($isDev ? ['dev_code' => $code] : []),
        ]);
    }

    public function verifyOtp(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'phone' => 'required|string|min:8|max:15',
            'code' => 'required|string|size:6',
            'display_name' => 'nullable|string|max:255',
        ]);

        $phone = $this->normalizePhone($validated['phone']);

        $otp = OtpCode::where('phone', $phone)
            ->where('code', $validated['code'])
            ->where('used', false)
            ->latest()
            ->first();

        if (!$otp || !$otp->isValid()) {
            return response()->json([
                'message' => 'Code OTP invalide ou expiré.',
            ], 422);
        }

        $otp->update(['used' => true]);

        $user = User::where('phone', $phone)->first();

        $isNewUser = false;

        if (!$user) {
            $isNewUser = true;
            $user = User::create([
                'name' => $validated['display_name'] ?? 'Utilisateur',
                'display_name' => $validated['display_name'] ?? null,
                'phone' => $phone,
                'phone_verified_at' => now(),
                'role' => 'buyer',
                'password' => Hash::make(Str::random(32)),
                'email' => $phone . '@mantota.app',
            ]);

            UserMode::create([
                'user_id' => $user->id,
                'mode' => 'buyer',
                'is_active' => true,
            ]);
        } else {
            if (!$user->phone_verified_at) {
                $user->update(['phone_verified_at' => now()]);
            }
        }

        $token = $user->createToken('mobile-app')->plainTextToken;

        $modes = $user->modes()->get();
        $modesData = [];
        foreach (['buyer', 'vendor', 'partner'] as $mode) {
            $userMode = $modes->firstWhere('mode', $mode);
            $modesData[] = [
                'mode' => $mode,
                'is_active' => $userMode?->is_active ?? ($mode === 'buyer'),
                'can_deactivate' => $mode !== 'buyer',
            ];
        }

        return response()->json([
            'message' => $isNewUser ? 'Compte créé avec succès.' : 'Connexion réussie.',
            'is_new_user' => $isNewUser,
            'user' => [
                'id' => $user->id,
                'name' => $user->name,
                'display_name' => $user->display_name,
                'phone' => $user->phone,
                'avatar_url' => $user->avatar_url,
            ],
            'modes' => $modesData,
            'token' => $token,
        ]);
    }

    private function normalizePhone(string $phone): string
    {
        // Retirer tout sauf les chiffres
        $phone = preg_replace('/[^0-9]/', '', $phone);

        // L'app mobile envoie le numéro en format international (ex: 22951000000, 2250700000000)
        // Aucun préfixe n'est ajouté côté serveur — comme WhatsApp.
        return $phone;
    }
}
