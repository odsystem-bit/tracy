<?php

declare(strict_types=1);

use App\Http\Controllers\Api\Admin\AdminApiController;
use App\Http\Controllers\Api\Admin\KnowledgeAdminController;
use App\Http\Controllers\Api\Bot\BotCampaignController;
use App\Http\Controllers\Api\Bot\BotCurrencyController;
use App\Http\Controllers\Api\Bot\BotMemoryController;
use App\Http\Controllers\Api\Bot\BotOrderController;
use App\Http\Controllers\Api\Bot\BotOrderTrackingController;
use App\Http\Controllers\Api\Bot\BotPartnerController;
use App\Http\Controllers\Api\Bot\BotPaymentController;
use App\Http\Controllers\Api\Bot\BotProductController;
use App\Http\Controllers\Api\Bot\BotStoreController;
use App\Http\Controllers\Api\Bot\BotSubscriptionController;
use App\Http\Controllers\Api\Bot\BotRestaurantController;
use App\Http\Controllers\Api\Bot\BotFollowUpController;
use App\Http\Controllers\Api\Bot\BotVendorReportController;
use App\Http\Controllers\Api\Bot\BotVisionController;
use App\Http\Controllers\Api\Bot\BotWalletController;
use App\Http\Controllers\Api\Bot\ProductController;
use App\Http\Controllers\Api\Bot\VendorController;
use App\Http\Controllers\Api\Mobile\MobileConversationController;
use App\Http\Controllers\Api\Mobile\MobileRestaurantController;
use App\Http\Controllers\Api\Mobile\MobileDisputeController;
use App\Http\Controllers\Api\Mobile\MobileOrderController;
use App\Http\Controllers\Api\Mobile\MobileStoreController;
use App\Http\Controllers\Api\Mobile\MobileSubscriptionController;
use App\Http\Controllers\Api\Mobile\MobileTracyController;
use App\Http\Controllers\Api\Mobile\MobileWalletController;
use App\Http\Controllers\Api\OtpAuthController;
use App\Http\Controllers\Api\UserModeController;
use App\Http\Controllers\Api\UserProfileController;
use App\Http\Controllers\Webhook\MonerooWebhookController;
use App\Http\Controllers\Webhook\WhatsAppWebhookController;
use Illuminate\Support\Facades\Route;

// ── Auth OTP (téléphone) ──
Route::post('/auth/otp/request', [OtpAuthController::class, 'requestOtp']);
Route::post('/auth/otp/verify', [OtpAuthController::class, 'verifyOtp']);

// ── Devises (public) ──
Route::get('/currencies', [\App\Http\Controllers\Api\CurrencyController::class, 'index']);

// ── Référentiel géographique (public) ──
Route::get('/geo/resolve', [\App\Http\Controllers\Api\GeoController::class, 'resolve']);
Route::get('/villes/{id}/quartiers', [\App\Http\Controllers\Api\GeoController::class, 'villeQuartiers'])->whereNumber('id');

// ── Modes utilisateur (authentifié) ──
Route::middleware('auth:sanctum')->group(function () {
    Route::get('/user/modes', [UserModeController::class, 'index']);
    Route::post('/user/modes/toggle', [UserModeController::class, 'toggle']);
    Route::patch('/user/profile', [UserProfileController::class, 'update']);
    Route::patch('/user/currency', [\App\Http\Controllers\Api\CurrencyController::class, 'update']);

    // ── Mobile App API (APK MANTOTA) ──

    // Orders
    Route::get('/orders', [MobileOrderController::class, 'index']);
    Route::get('/vendor/orders', [MobileOrderController::class, 'vendorOrders']);
    Route::post('/orders', [MobileOrderController::class, 'store']);
    Route::get('/orders/{id}', [MobileOrderController::class, 'show'])->where('id', '[0-9]+|CMD-[A-Za-z0-9]+');
    Route::patch('/orders/{id}/status', [MobileOrderController::class, 'updateStatus'])->where('id', '[0-9]+|CMD-[A-Za-z0-9]+');
    Route::post('/orders/{id}/confirm-delivery', [MobileOrderController::class, 'confirmDelivery'])->where('id', '[0-9]+|CMD-[A-Za-z0-9]+');
    Route::post('/orders/{id}/dispute', [MobileOrderController::class, 'openDispute'])->where('id', '[0-9]+|CMD-[A-Za-z0-9]+');
    Route::post('/orders/{id}/pay', [MobileOrderController::class, 'initPayment'])->where('id', '[0-9]+|CMD-[A-Za-z0-9]+');
    Route::get('/orders/{id}/track', [MobileOrderController::class, 'track'])->where('id', '[0-9]+|CMD-[A-Za-z0-9]+');

    // Wallet
    Route::get('/wallet/balance', [MobileWalletController::class, 'balance']);
    Route::get('/wallet/transactions', [MobileWalletController::class, 'transactions']);
    Route::post('/wallet/withdraw', [MobileWalletController::class, 'withdraw']);
    Route::post('/wallet/deposit', [MobileWalletController::class, 'deposit']);

    // Vendor Store
    Route::get('/vendor/store', [MobileStoreController::class, 'show']);
    Route::put('/vendor/store', [MobileStoreController::class, 'update']);
    Route::get('/vendor/store/share', [MobileStoreController::class, 'shareLink']);
    Route::get('/vendor/store/stats', [MobileStoreController::class, 'stats']);

    // Subscriptions
    Route::get('/subscriptions/plans', [MobileSubscriptionController::class, 'plans']);
    Route::get('/subscriptions/current', [MobileSubscriptionController::class, 'current']);
    Route::post('/subscriptions/activate', [MobileSubscriptionController::class, 'activate']);
    Route::post('/subscriptions/activate-free', [MobileSubscriptionController::class, 'activateFree']);
    Route::post('/subscriptions/confirm', [MobileSubscriptionController::class, 'confirm']);

    // Disputes
    Route::get('/disputes', [MobileDisputeController::class, 'index']);
    Route::get('/disputes/{orderId}', [MobileDisputeController::class, 'show'])->where('orderId', '[0-9]+|CMD-[A-Za-z0-9]+');
    Route::post('/disputes/{orderId}/messages', [MobileDisputeController::class, 'sendMessage'])->where('orderId', '[0-9]+|CMD-[A-Za-z0-9]+');
    Route::post('/disputes/{orderId}/resolve', [MobileDisputeController::class, 'resolve'])->where('orderId', '[0-9]+|CMD-[A-Za-z0-9]+');

    // Tracy Core proxy
    Route::post('/tracy/chat', [MobileTracyController::class, 'chat']);
    Route::post('/tracy/search', [MobileTracyController::class, 'search']);
    Route::post('/tracy/negotiate', [MobileTracyController::class, 'negotiate']);
    Route::get('/tracy/config', [MobileTracyController::class, 'getConfig']);
    Route::post('/tracy/config', [MobileTracyController::class, 'saveConfig']);

    // Vision (Product identification, Conformity, Shop Quality)
    Route::post('/tracy/identify-product', [MobileTracyController::class, 'identifyProduct']);
    Route::post('/tracy/check-conformity', [MobileTracyController::class, 'checkConformity']);
    Route::get('/tracy/shop-quality', [MobileTracyController::class, 'getShopQuality']);

    // Restaurant proxy (Tracy Core)
    Route::get('/tracy/restaurants', [MobileTracyController::class, 'listRestaurants']);
    Route::get('/tracy/restaurants/{restaurantId}/menu', [MobileTracyController::class, 'getRestaurantMenu'])->where('restaurantId', '[0-9]+');
    Route::post('/tracy/restaurants/order', [MobileTracyController::class, 'createRestaurantOrder']);
    Route::get('/tracy/restaurants/order/{orderId}', [MobileTracyController::class, 'getRestaurantOrderStatus']);

    // Shop config (address_form, negotiation rules)
    Route::get('/tracy/shop-config', [MobileTracyController::class, 'getShopConfig']);
    Route::post('/tracy/shop-config', [MobileTracyController::class, 'updateShopConfig']);

    // Restaurant
    Route::get('/restaurants', [MobileRestaurantController::class, 'listRestaurants']);
    Route::get('/restaurants/{restaurantId}/menu', [MobileRestaurantController::class, 'getMenu']);
    Route::post('/restaurants/orders', [MobileRestaurantController::class, 'createOrder']);
    Route::get('/restaurants/orders', [MobileRestaurantController::class, 'getMyOrders']);
    Route::get('/restaurants/orders/{orderId}', [MobileRestaurantController::class, 'getOrderStatus']);

    // User search & Conversations
    Route::get('/users/search', [MobileConversationController::class, 'searchUser']);
    Route::get('/conversations', [MobileConversationController::class, 'index']);
    Route::post('/conversations', [MobileConversationController::class, 'store']);
    Route::get('/conversations/{id}/messages', [MobileConversationController::class, 'messages'])->where('id', '[0-9]+');
    Route::post('/conversations/{id}/messages', [MobileConversationController::class, 'sendMessage'])->where('id', '[0-9]+');
    Route::post('/conversations/{id}/read', [MobileConversationController::class, 'markAsRead'])->where('id', '[0-9]+');
});

// ── Public store (accessible sans auth) ──
Route::get('/stores/{slug}', [MobileStoreController::class, 'publicStore']);

// ── Public chat (proxy vers Tracy Core, rate-limité) ──
Route::post('/public/chat', [\App\Http\Controllers\Public\PublicChatController::class, 'chat'])
    ->middleware('throttle:20,5');

// ── Public guest checkout ──
Route::post('/public/checkout', [\App\Http\Controllers\Public\GuestCheckoutController::class, 'store'])
    ->middleware('throttle:10,5');

Route::prefix('bot')->middleware('bot.apikey')->group(function () {
    // ── Vendors ──
    Route::post('/vendors', [VendorController::class, 'store']);
    Route::get('/vendors/{vendorId}/stats', [BotOrderController::class, 'vendorStats']);
    Route::get('/vendors/{vendorId}/reports', [BotVendorReportController::class, 'index'])->whereNumber('vendorId');
    Route::post('/vendors/{vendorId}/reports', [BotVendorReportController::class, 'store'])->whereNumber('vendorId');
    Route::post('/vendors/{vendorId}/connect', [BotVendorReportController::class, 'connect'])->whereNumber('vendorId');
    Route::get('/vendors/{phone}', [VendorController::class, 'findByPhone']);

    // ── Relances client post-négociation (Tracy) ──
    Route::post('/follow-ups', [BotFollowUpController::class, 'store']);

    // ── Products ──
    Route::post('/products', [ProductController::class, 'store']);
    Route::get('/products/search', [BotProductController::class, 'search']);

    // ── Catalog ──
    Route::get('/catalog/search', [BotProductController::class, 'catalogSearch']);
    Route::post('/catalog/send', [BotProductController::class, 'sendCatalog']);

    // ── Stores ──
    Route::post('/stores', [BotStoreController::class, 'store']);
    Route::get('/stores/search', [BotStoreController::class, 'search']);
    Route::get('/stores/{storeId}/info', [BotStoreController::class, 'getInfo']);
    Route::get('/stores/{storeId}/config', [BotStoreController::class, 'getConfig']);
    Route::post('/stores/{storeId}/config', [BotStoreController::class, 'updateConfig']);
    Route::get('/stores/{storeId}/delivery-quartiers', [BotStoreController::class, 'getDeliveryQuartiers']);
    Route::post('/stores/{storeId}/delivery-quartiers', [BotStoreController::class, 'setDeliveryQuartiers']);
    Route::delete('/stores/{storeId}/delivery-quartiers/{quartierId}', [BotStoreController::class, 'removeDeliveryQuartier'])->whereNumber('quartierId');

    // ── Currencies ──
    Route::get('/currencies', [BotCurrencyController::class, 'index']);

    // ── Orders ──
    Route::post('/orders', [BotOrderController::class, 'store']);
    Route::get('/orders/{id}/track', [BotOrderTrackingController::class, 'track']);
    Route::post('/orders/{id}/cancel', [BotOrderTrackingController::class, 'cancel']);
    Route::get('/orders/{reference}', [BotOrderController::class, 'show'])->where('reference', 'CMD-[A-Za-z0-9]+');

    // ── Payments ──
    Route::post('/payments', [BotPaymentController::class, 'create']);
    Route::post('/payments/send-link', [BotPaymentController::class, 'sendLink']);

    // ── Wallet ──
    Route::get('/wallet/{userId}', [BotWalletController::class, 'show']);
    Route::post('/wallet/withdraw', [BotWalletController::class, 'withdraw']);

    // ── Campaigns ──
    Route::get('/campaigns/{id}', [BotCampaignController::class, 'show']);

    // ── Partners ──
    Route::get('/partners/search', [BotPartnerController::class, 'search']);

    // ── Memory ──
    Route::post('/memory', [BotMemoryController::class, 'store']);
    Route::get('/memory/search', [BotMemoryController::class, 'search']);
    Route::patch('/memory/{id}', [BotMemoryController::class, 'update']);
    Route::delete('/memory/{id}', [BotMemoryController::class, 'destroy']);

    // ── Subscriptions Tracy ──
    Route::post('/subscriptions/tracy', [BotSubscriptionController::class, 'activate']);

    // ── Vision (Product Vision, Authenticity, Shop Quality) ──
    Route::prefix('vision')->group(function () {
        // Embeddings CLIP
        Route::post('/embeddings', [BotVisionController::class, 'storeEmbeddings']);
        Route::get('/embeddings/{vendorId}', [BotVisionController::class, 'getEmbeddings']);
        Route::get('/perceptual-hashes/{vendorId}', [BotVisionController::class, 'getPerceptualHashes']);

        // Authenticity checks
        Route::post('/authenticity', [BotVisionController::class, 'storeAuthenticityCheck']);
        Route::get('/authenticity/{vendorId}', [BotVisionController::class, 'getAuthenticityChecks']);

        // Shop quality signals & scores
        Route::post('/quality-signals', [BotVisionController::class, 'storeQualitySignal']);
        Route::get('/quality-score/{storeId}', [BotVisionController::class, 'getQualityScore']);
        Route::get('/quality-score/{storeId}/signals', [BotVisionController::class, 'getQualitySignals']);
    });

    // ── Support / Litiges ──
    Route::post('/support/tickets', [\App\Http\Controllers\Api\Bot\BotSupportController::class, 'store']);
    Route::post('/disputes', [\App\Http\Controllers\Api\Bot\BotSupportController::class, 'createDispute']);

    // ── Knowledge RAG ──
    Route::get('/knowledge/search', [\App\Http\Controllers\Api\Bot\BotKnowledgeController::class, 'search']);
    Route::get('/knowledge/documents', [\App\Http\Controllers\Api\Bot\BotKnowledgeController::class, 'documents']);
    Route::get('/knowledge/documents/{id}', [\App\Http\Controllers\Api\Bot\BotKnowledgeController::class, 'showDocument'])->whereNumber('id');
    Route::post('/knowledge/documents/{id}/chunks', [\App\Http\Controllers\Api\Bot\BotKnowledgeController::class, 'upsertChunks'])->whereNumber('id');
    Route::post('/knowledge/gaps/log', [\App\Http\Controllers\Api\Bot\BotKnowledgeController::class, 'logGap']);

    // ── Restaurant ──
    Route::prefix('restaurant')->group(function () {
        Route::get('/search', [BotRestaurantController::class, 'searchRestaurants']);
        Route::get('/menu/{restaurantId}', [BotRestaurantController::class, 'getMenu']);
        Route::post('/categories', [BotRestaurantController::class, 'createCategory']);
        Route::get('/categories/{restaurantId}', [BotRestaurantController::class, 'listCategories']);
        Route::post('/menu-items', [BotRestaurantController::class, 'createMenuItem']);
        Route::put('/menu-items/{itemId}', [BotRestaurantController::class, 'updateMenuItem']);
        Route::patch('/menu-items/{itemId}/availability', [BotRestaurantController::class, 'toggleAvailability']);
        Route::post('/hours', [BotRestaurantController::class, 'setHours']);
        Route::get('/hours/{restaurantId}', [BotRestaurantController::class, 'getHours']);
        Route::post('/orders', [BotRestaurantController::class, 'createOrder']);
        Route::patch('/orders/{orderId}/status', [BotRestaurantController::class, 'updateOrderStatus']);
        Route::get('/orders/{orderId}/status', [BotRestaurantController::class, 'getOrderStatus']);
        Route::get('/orders/{restaurantId}', [BotRestaurantController::class, 'getOrders']);
    });
});

// Webhook public Moneroo (pas de clé API)
Route::post('/webhook/moneroo', [MonerooWebhookController::class, 'handle']);

// Webhook WhatsApp Cloud API (public, vérifié par token)
Route::get('/whatsapp/webhook', [WhatsAppWebhookController::class, 'verify']);
Route::post('/whatsapp/webhook', [WhatsAppWebhookController::class, 'handle']);

// ── Admin Panel API (React) ─────────────────────────────────────
Route::prefix('admin')->group(function () {
    // Public (login)
    Route::post('/login', [AdminApiController::class, 'login']);

    // Protected (Sanctum token + role:admin)
    Route::middleware('auth:admin_api')->group(function () {
        Route::post('/logout', [AdminApiController::class, 'logout']);
        Route::get('/me', [AdminApiController::class, 'me']);
        Route::get('/dashboard', [AdminApiController::class, 'dashboard']);
        Route::get('/live-feed', [AdminApiController::class, 'liveFeed']);

        // Users
        Route::get('/users', [AdminApiController::class, 'users']);
        Route::get('/users/{id}', [AdminApiController::class, 'userShow'])->whereNumber('id');
        Route::patch('/users/{id}/ban', [AdminApiController::class, 'toggleBan'])->whereNumber('id');

        // Orders
        Route::get('/orders', [AdminApiController::class, 'orders']);

        // Restaurants
        Route::get('/restaurants', [AdminApiController::class, 'restaurants']);

        // Finance
        Route::get('/finance', [AdminApiController::class, 'finance']);

        // Tracy Core status
        Route::get('/tracy/status', [AdminApiController::class, 'tracyStatus']);
        Route::get('/tracy/config', [AdminApiController::class, 'tracyConfig']);

        // Growth
        Route::get('/growth', [AdminApiController::class, 'growth']);

        // Revenue
        Route::get('/revenue', [AdminApiController::class, 'revenue']);

        // Countries
        Route::get('/countries', [AdminApiController::class, 'countries']);

        // Shops map
        Route::get('/shops-map', [AdminApiController::class, 'shopsMap']);

        // Shop quality
        Route::get('/shop-quality', [AdminApiController::class, 'shopQuality']);

        // Security
        Route::get('/security', [AdminApiController::class, 'security']);

        // System health
        Route::get('/system-health', [AdminApiController::class, 'systemHealth']);

        // Notifications
        Route::get('/notifications', [AdminApiController::class, 'notifications']);

        // Knowledge RAG management
        Route::prefix('knowledge')->group(function () {
            Route::get('/documents', [KnowledgeAdminController::class, 'index']);
            Route::get('/documents/{id}', [KnowledgeAdminController::class, 'show'])->whereNumber('id');
            Route::post('/documents', [KnowledgeAdminController::class, 'store']);
            Route::put('/documents/{id}', [KnowledgeAdminController::class, 'update'])->whereNumber('id');
            Route::patch('/documents/{id}/status', [KnowledgeAdminController::class, 'changeStatus'])->whereNumber('id');
            Route::delete('/documents/{id}', [KnowledgeAdminController::class, 'destroy'])->whereNumber('id');
            Route::post('/documents/{id}/chunks', [KnowledgeAdminController::class, 'upsertChunks'])->whereNumber('id');
            Route::get('/countries', [KnowledgeAdminController::class, 'countries']);
            Route::get('/gaps', [KnowledgeAdminController::class, 'gapsIndex']);
            Route::patch('/gaps/{id}', [KnowledgeAdminController::class, 'gapsUpdate'])->whereNumber('id');
        });
    });
});
