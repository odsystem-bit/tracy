import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../models/conversation.dart';
import '../models/order.dart';
import '../models/order_track.dart';
import '../models/product.dart';
import '../models/user.dart';
import '../services/auth_service.dart';
import '../services/conversation_service.dart';
import '../services/product_service.dart';
import '../services/order_service.dart';
import '../services/payment_service.dart';
import '../services/subscription_service.dart';
import '../services/wallet_service.dart';
import '../services/notification_service.dart';
import '../services/store_service.dart';
import '../services/tracy_chat_service.dart';
import '../services/restaurant_service.dart';

// ── Status / Stories providers ──

/// Statuts des contacts (visible par ceux avec qui on a échangé).
final statusListProvider = FutureProvider<List<UserStatus>>((ref) async {
  final svc = await ref.watch(conversationServiceProvider.future);
  return svc.getStatuses();
});

/// Statuts de Tracy (promotions, annonces).
final tracyStatusProvider = FutureProvider<List<StatusItem>>((ref) async {
  final svc = await ref.watch(conversationServiceProvider.future);
  return svc.getTracyStatuses();
});

/// Provider du client API (singleton).
final apiClientProvider = FutureProvider<ApiClient>((ref) async {
  return ApiClient.create();
});

/// Provider du service d'authentification.
final authServiceProvider = FutureProvider<AuthService>((ref) async {
  final api = await ref.watch(apiClientProvider.future);
  return AuthService(api);
});

/// Utilisateur courant (stocké en mémoire après login).
final currentUserProvider = StateProvider<User?>((ref) => null);

/// Provider du service de conversations.
final conversationServiceProvider = FutureProvider<ConversationService>((ref) async {
  final api = await ref.watch(apiClientProvider.future);
  return ConversationService(api);
});

/// Provider du service de produits.
final productServiceProvider = FutureProvider<ProductService>((ref) async {
  final api = await ref.watch(apiClientProvider.future);
  return ProductService(api);
});

/// Provider du service de commandes.
final orderServiceProvider = FutureProvider<OrderService>((ref) async {
  final api = await ref.watch(apiClientProvider.future);
  return OrderService(api);
});

/// Provider du service wallet.
final walletServiceProvider = FutureProvider<WalletService>((ref) async {
  final api = await ref.watch(apiClientProvider.future);
  return WalletService(api);
});

/// Provider du service de notifications.
final notificationServiceProvider = FutureProvider<NotificationService>((ref) async {
  final api = await ref.watch(apiClientProvider.future);
  return NotificationService(api);
});

/// Provider du service de boutique.
final storeServiceProvider = FutureProvider<StoreService>((ref) async {
  final api = await ref.watch(apiClientProvider.future);
  return StoreService(api);
});

/// Provider du service Tracy Core.
final tracyChatServiceProvider = FutureProvider<TracyChatService>((ref) async {
  final api = await ref.watch(apiClientProvider.future);
  return TracyChatService(api);
});

/// Provider du service de paiement (Moneroo).
final paymentServiceProvider = FutureProvider<PaymentService>((ref) async {
  final api = await ref.watch(apiClientProvider.future);
  return PaymentService(api);
});

/// Provider du service d'abonnements.
final subscriptionServiceProvider = FutureProvider<SubscriptionService>((ref) async {
  final api = await ref.watch(apiClientProvider.future);
  return SubscriptionService(api);
});

// ── Data providers (fetch from API with fallback) ──

/// Liste des conversations.
final conversationListProvider = FutureProvider<List<Conversation>>((ref) async {
  final svc = await ref.watch(conversationServiceProvider.future);
  return svc.getConversations();
});

/// Commandes de l'utilisateur (acheteur).
final orderListProvider = FutureProvider<List<Order>>((ref) async {
  final svc = await ref.watch(orderServiceProvider.future);
  return svc.myOrders();
});

/// Commandes vendeur.
final vendorOrderListProvider = FutureProvider<List<Order>>((ref) async {
  final svc = await ref.watch(orderServiceProvider.future);
  return svc.vendorOrders();
});

/// Solde du wallet.
final walletBalanceProvider = FutureProvider<WalletBalance>((ref) async {
  final svc = await ref.watch(walletServiceProvider.future);
  return svc.getBalance();
});

/// Transactions du wallet.
final walletTransactionsProvider = FutureProvider<List<WalletTransaction>>((ref) async {
  final svc = await ref.watch(walletServiceProvider.future);
  return svc.getTransactions();
});

/// Notifications utilisateur.
final notificationListProvider = FutureProvider<List<AppNotification>>((ref) async {
  final svc = await ref.watch(notificationServiceProvider.future);
  return svc.getNotifications();
});

/// Notifications vendeur.
final vendorNotificationListProvider = FutureProvider<List<AppNotification>>((ref) async {
  final svc = await ref.watch(notificationServiceProvider.future);
  return svc.getVendorNotifications();
});

/// Produits tendance.
final trendingProductsProvider = FutureProvider<List<Product>>((ref) async {
  final svc = await ref.watch(productServiceProvider.future);
  return svc.trending();
});

/// Détail d'une commande (family provider par orderId).
final orderDetailProvider = FutureProvider.family<Order, String>((ref, orderId) async {
  final svc = await ref.watch(orderServiceProvider.future);
  return svc.getById(orderId);
});

/// Ma boutique (vendor).
final storeDetailProvider = FutureProvider<Store?>((ref) async {
  final svc = await ref.watch(storeServiceProvider.future);
  return svc.getMyStore();
});

/// Boutiques populaires.
final popularStoresProvider = FutureProvider<List<Store>>((ref) async {
  final svc = await ref.watch(storeServiceProvider.future);
  return svc.popular();
});

/// Produits de ma boutique (vendor).
final storeProductsProvider = FutureProvider<List<Product>>((ref) async {
  final store = await ref.watch(storeDetailProvider.future);
  if (store == null) return [];
  final svc = await ref.watch(productServiceProvider.future);
  return svc.byStore(store.id);
});

/// Recherche de produits (family par query).
final searchProductsProvider = FutureProvider.family<List<Product>, String>((ref, query) async {
  final svc = await ref.watch(productServiceProvider.future);
  return svc.search(query);
});

// ── Subscription providers ──

/// Plans d'abonnement disponibles.
final subscriptionPlansProvider = FutureProvider<List<SubscriptionPlan>>((ref) async {
  final svc = await ref.watch(subscriptionServiceProvider.future);
  return svc.getPlans();
});

/// Abonnement actuel du vendeur.
final currentSubscriptionProvider = FutureProvider<CurrentSubscription>((ref) async {
  final svc = await ref.watch(subscriptionServiceProvider.future);
  return svc.getCurrent();
});

/// Suivi de commande (timeline, livreur, statut).
final orderTrackProvider = FutureProvider.family<OrderTrackData, String>((ref, orderId) async {
  final api = await ref.watch(apiClientProvider.future);
  final json = await api.get('/orders/$orderId/track');
  return OrderTrackData.fromJson(json);
});

/// Statistiques de la boutique vendeur.
final storeStatsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final svc = await ref.watch(storeServiceProvider.future);
  return svc.getStats();
});

// ── Restaurant providers ──

final restaurantServiceProvider = FutureProvider<RestaurantService>((ref) async {
  final api = await ref.watch(apiClientProvider.future);
  return RestaurantService(api);
});

final restaurantsListProvider = FutureProvider<List<RestaurantSummary>>((ref) async {
  final svc = await ref.watch(restaurantServiceProvider.future);
  return svc.listRestaurants();
});

final restaurantMenuProvider = FutureProvider.family<RestaurantMenu, int>((ref, restaurantId) async {
  final svc = await ref.watch(restaurantServiceProvider.future);
  return svc.getMenu(restaurantId);
});

final myRestaurantOrdersProvider = FutureProvider<List<MyRestaurantOrder>>((ref) async {
  final svc = await ref.watch(restaurantServiceProvider.future);
  return svc.getMyOrders();
});
