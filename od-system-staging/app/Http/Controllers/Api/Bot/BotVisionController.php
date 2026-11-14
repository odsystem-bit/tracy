<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\Product;
use App\Models\ProductAuthenticityCheck;
use App\Models\ProductImageEmbedding;
use App\Models\ShopQualitySignal;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

/**
 * BotVisionController — Endpoints pour les modules vision de Tracy Core.
 *
 * Ces endpoints permettent à Tracy Core de:
 * 1. Stocker/récupérer les embeddings CLIP des produits
 * 2. Enregistrer les vérifications d'authenticité
 * 3. Gérer les signaux de qualité boutique
 * 4. Calculer les scores de qualité
 *
 * Tracy Core appelle ces endpoints après traitement d'images par CLIP/YOLOv8.
 */
class BotVisionController extends Controller
{
    /**
     * POST /bot/vision/embeddings
     * Stocke les embeddings CLIP d'un produit (original + augmentés).
     */
    public function storeEmbeddings(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'product_id' => 'required|integer|exists:products,id',
            'vendor_id' => 'required|integer|exists:users,id',
            'image_url' => 'nullable|string|max:500',
            'embeddings' => 'required|array|min:1',
            'embeddings.*.embedding' => 'required|string', // JSON array of floats
            'embeddings.*.is_augmented' => 'boolean',
            'embeddings.*.augmentation_type' => 'nullable|string|max:50',
            'perceptual_hash' => 'nullable|string|max:256',
        ]);

        // Supprimer les anciens embeddings pour ce produit
        ProductImageEmbedding::where('product_id', $validated['product_id'])->delete();

        $created = [];
        foreach ($validated['embeddings'] as $emb) {
            $created[] = ProductImageEmbedding::create([
                'product_id' => $validated['product_id'],
                'vendor_id' => $validated['vendor_id'],
                'image_url' => $validated['image_url'] ?? null,
                'embedding' => $emb['embedding'],
                'is_augmented' => $emb['is_augmented'] ?? false,
                'augmentation_type' => $emb['augmentation_type'] ?? null,
                'perceptual_hash' => $validated['perceptual_hash'] ?? null,
            ])->id;
        }

        return response()->json([
            'success' => true,
            'product_id' => $validated['product_id'],
            'embeddings_stored' => count($created),
            'embedding_ids' => $created,
        ], 201);
    }

    /**
     * GET /bot/vision/embeddings/{vendorId}
     * Récupère tous les embeddings d'un vendeur (pour identification produit).
     */
    public function getEmbeddings(string $vendorId): JsonResponse
    {
        $embeddings = ProductImageEmbedding::where('vendor_id', $vendorId)
            ->with('product:id,name,price,image_path')
            ->get();

        return response()->json([
            'vendor_id' => $vendorId,
            'embeddings' => $embeddings->map(fn (ProductImageEmbedding $e) => [
                'id' => (string) $e->id,
                'product_id' => (string) $e->product_id,
                'product_name' => $e->product?->name,
                'product_price' => (float) ($e->product?->price ?? 0),
                'product_image_url' => $e->product?->image_path
                    ? asset('storage/' . $e->product->image_path)
                    : $e->image_url,
                'store_id' => (string) $e->vendor_id,
                'embedding' => $e->embedding,
                'is_augmented' => $e->is_augmented,
                'augmentation_type' => $e->augmentation_type,
            ]),
            'total' => $embeddings->count(),
        ]);
    }

    /**
     * GET /bot/vision/perceptual-hashes/{vendorId}
     * Récupère les hashes perceptuels d'un vendeur (pour détection duplication).
     */
    public function getPerceptualHashes(string $vendorId): JsonResponse
    {
        $embeddings = ProductImageEmbedding::where('vendor_id', $vendorId)
            ->whereNotNull('perceptual_hash')
            ->where('is_augmented', false) // Only original photos
            ->get(['product_id', 'perceptual_hash']);

        $hashes = [];
        foreach ($embeddings as $e) {
            $hashes[(string) $e->product_id] = $e->perceptual_hash;
        }

        return response()->json([
            'vendor_id' => $vendorId,
            'hashes' => $hashes,
        ]);
    }

    /**
     * POST /bot/vision/authenticity
     * Stocke le résultat d'une vérification d'authenticité.
     */
    public function storeAuthenticityCheck(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'product_id' => 'required|integer|exists:products,id',
            'vendor_id' => 'required|integer|exists:users,id',
            'trust_score' => 'required|numeric|min:0|max:100',
            'flags' => 'nullable|array',
            'has_watermark' => 'boolean',
            'is_duplicate' => 'boolean',
            'duplicate_of' => 'nullable|string',
            'is_too_professional' => 'boolean',
            'resolution_suspicious' => 'boolean',
            'is_upscaled' => 'boolean',
            'recommendation' => 'nullable|string|max:500',
        ]);

        $check = ProductAuthenticityCheck::updateOrCreate(
            ['product_id' => $validated['product_id']],
            $validated
        );

        // Générer des signaux de qualité automatiquement
        $this->createSignalsFromAuthenticity($validated);

        return response()->json([
            'success' => true,
            'check_id' => $check->id,
            'trust_score' => (float) $check->trust_score,
        ], 201);
    }

    /**
     * GET /bot/vision/authenticity/{vendorId}
     * Récupère les vérifications d'authenticité d'un vendeur.
     */
    public function getAuthenticityChecks(string $vendorId): JsonResponse
    {
        $checks = ProductAuthenticityCheck::where('vendor_id', $vendorId)
            ->with('product:id,name,price,image_path')
            ->orderByDesc('created_at')
            ->limit(50)
            ->get();

        return response()->json([
            'vendor_id' => $vendorId,
            'checks' => $checks->map(fn (ProductAuthenticityCheck $c) => [
                'id' => (string) $c->id,
                'product_id' => (string) $c->product_id,
                'product_name' => $c->product?->name,
                'trust_score' => (float) $c->trust_score,
                'flags' => $c->flags ?? [],
                'has_watermark' => $c->has_watermark,
                'is_duplicate' => $c->is_duplicate,
                'is_too_professional' => $c->is_too_professional,
                'resolution_suspicious' => $c->resolution_suspicious,
                'is_upscaled' => $c->is_upscaled,
                'recommendation' => $c->recommendation,
                'created_at' => $c->created_at?->toIso8601String(),
            ]),
            'total' => $checks->count(),
        ]);
    }

    /**
     * POST /bot/vision/quality-signals
     * Enregistre un signal de qualité pour une boutique.
     */
    public function storeQualitySignal(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'store_id' => 'required|integer|exists:users,id',
            'signal_type' => 'required|string|max:50',
            'product_id' => 'nullable|integer|exists:products,id',
            'order_id' => 'nullable|integer|exists:orders,id',
            'description' => 'nullable|string|max:500',
        ]);

        $weight = ShopQualitySignal::getWeight($validated['signal_type']);

        $signal = ShopQualitySignal::create([
            'store_id' => $validated['store_id'],
            'signal_type' => $validated['signal_type'],
            'weight' => $weight,
            'description' => $validated['description'] ?? null,
            'product_id' => $validated['product_id'] ?? null,
            'order_id' => $validated['order_id'] ?? null,
        ]);

        // Vérifier si des actions automatiques sont nécessaires
        $score = $this->computeQualityScore($validated['store_id']);
        $autoActions = $this->getAutoActions($score);

        return response()->json([
            'success' => true,
            'signal_id' => $signal->id,
            'weight' => $weight,
            'current_score' => $score,
            'auto_actions' => $autoActions,
        ], 201);
    }

    /**
     * GET /bot/vision/quality-score/{storeId}
     * Calcule et retourne le score de qualité d'une boutique.
     */
    public function getQualityScore(string $storeId): JsonResponse
    {
        $signals = ShopQualitySignal::where('store_id', $storeId)
            ->where('created_at', '>=', now()->subDays(30))
            ->orderByDesc('created_at')
            ->get();

        $score = $this->computeQualityScore($storeId, $signals);
        $level = $this->getQualityLevel($score);
        $autoActions = $this->getAutoActions($score);

        $positiveCount = $signals->where('weight', '>', 0)->count();
        $negativeCount = $signals->where('weight', '<', 0)->count();

        return response()->json([
            'store_id' => $storeId,
            'score' => $score,
            'level' => $level,
            'total_signals' => $signals->count(),
            'positive_signals' => $positiveCount,
            'negative_signals' => $negativeCount,
            'last_updated' => now()->toIso8601String(),
            'signals' => $signals->take(20)->map(fn (ShopQualitySignal $s) => [
                'id' => (string) $s->id,
                'signal_type' => $s->signal_type,
                'weight' => $s->weight,
                'description' => $s->description,
                'product_id' => $s->product_id ? (string) $s->product_id : null,
                'order_id' => $s->order_id ? (string) $s->order_id : null,
                'created_at' => $s->created_at?->toIso8601String(),
            ]),
            'auto_actions' => $autoActions,
        ]);
    }

    /**
     * GET /bot/vision/quality-score/{storeId}/signals
     * Récupère tous les signaux de qualité d'une boutique (30 derniers jours).
     */
    public function getQualitySignals(string $storeId): JsonResponse
    {
        $signals = ShopQualitySignal::where('store_id', $storeId)
            ->where('created_at', '>=', now()->subDays(30))
            ->orderByDesc('created_at')
            ->get();

        return response()->json([
            'store_id' => $storeId,
            'signals' => $signals->map(fn (ShopQualitySignal $s) => [
                'id' => (string) $s->id,
                'signal_type' => $s->signal_type,
                'weight' => $s->weight,
                'description' => $s->description,
                'product_id' => $s->product_id ? (string) $s->product_id : null,
                'order_id' => $s->order_id ? (string) $s->order_id : null,
                'created_at' => $s->created_at?->toIso8601String(),
            ]),
            'total' => $signals->count(),
        ]);
    }

    // ── Méthodes internes ──────────────────────────────────────────

    private function computeQualityScore(string $storeId, $signals = null): int
    {
        $signals = $signals ?? ShopQualitySignal::where('store_id', $storeId)
            ->where('created_at', '>=', now()->subDays(30))
            ->get();

        $score = 100 + $signals->sum('weight');
        return max(0, min(100, $score));
    }

    private function getQualityLevel(int $score): string
    {
        return match (true) {
            $score >= 80 => 'excellent',
            $score >= 60 => 'good',
            $score >= 40 => 'warning',
            $score >= 20 => 'risk',
            default => 'suspended',
        };
    }

    private function getAutoActions(int $score): array
    {
        return match (true) {
            $score < 20 => ['notify_vendor', 'suspend_store', 'admin_review_required'],
            $score < 40 => ['notify_vendor', 'display_risk_badge', 'limit_visibility'],
            $score < 60 => ['notify_vendor', 'mark_photos_unverified'],
            default => [],
        };
    }

    private function createSignalsFromAuthenticity(array $check): void
    {
        $signalMap = [
            'has_watermark' => 'watermark_detected',
            'is_duplicate' => 'duplicate_photo',
            'is_too_professional' => 'too_professional',
            'resolution_suspicious' => 'low_resolution',
            'is_upscaled' => 'upscaled_image',
        ];

        foreach ($signalMap as $field => $signalType) {
            if (!empty($check[$field])) {
                ShopQualitySignal::create([
                    'store_id' => $check['vendor_id'],
                    'signal_type' => $signalType,
                    'weight' => ShopQualitySignal::getWeight($signalType),
                    'product_id' => $check['product_id'],
                    'description' => "Auto-detected via authenticity check",
                ]);
            }
        }
    }
}
