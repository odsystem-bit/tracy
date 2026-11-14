import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/onboarding/screens/splash_screen.dart';
import '../../features/onboarding/screens/login_screen.dart';
import '../../features/onboarding/screens/otp_screen.dart';
import '../../features/onboarding/screens/mode_selection_screen.dart';
import '../../features/chat/screens/conversations_screen.dart';
import '../../features/chat/screens/chat_screen.dart';
import '../../features/chat/screens/tracy_channel_screen.dart';
import '../../features/chat/screens/contact_profile_screen.dart';
import '../../features/chat/screens/new_chat_screen.dart';
import '../../features/chat/screens/status_screen.dart';
import '../../features/catalog/screens/search_product_screen.dart';
import '../../features/catalog/screens/product_detail_screen.dart';
import '../../features/orders/screens/order_history_screen.dart';
import '../../features/orders/screens/payment_screen.dart';
import '../../features/orders/screens/delivery_tracking_screen.dart';
import '../../features/orders/screens/product_search_screen.dart';
import '../../features/orders/screens/negotiation_screen.dart';
import '../../features/orders/screens/order_recap_screen.dart';
import '../../features/orders/screens/payment_confirmation_screen.dart';
import '../../features/orders/screens/dispute_screen.dart';
import '../../features/orders/screens/conformity_screen.dart';
import '../../features/subscriptions/screens/subscription_screen.dart';
import '../../features/discover/screens/discover_screen.dart';
import '../../features/profile/screens/profile_screen.dart';
import '../../features/vendor/screens/vendor_dashboard_screen.dart';
import '../../features/vendor/screens/vendor_store_screen.dart';
import '../../features/vendor/screens/vendor_tracy_config_screen.dart';
import '../../features/vendor/screens/vendor_create_store_screen.dart';
import '../../features/vendor/screens/vendor_add_product_screen.dart';
import '../../features/vendor/screens/vendor_orders_screen.dart';
import '../../features/vendor/screens/vendor_order_detail_screen.dart';
import '../../features/vendor/screens/vendor_notifications_screen.dart';
import '../../features/whatsapp/screens/connect_whatsapp_screen.dart';
import '../../features/wallet/screens/wallet_screen.dart';
import '../../features/settings/screens/settings_screen.dart';
import '../../features/settings/screens/notifications_center_screen.dart';
import '../../features/restaurant/screens/restaurants_screen.dart';
import '../../features/restaurant/screens/restaurant_menu_screen.dart';
import '../widgets/main_scaffold.dart';

/// État d'authentification observé par le router.
enum AuthState { initial, authenticated, unauthenticated }

/// Provider qui observe l'état d'auth en temps réel.
final authStateProvider = StateProvider<AuthState>((ref) => AuthState.initial);

/// Routes publiques (accessibles sans auth).
const _publicRoutes = ['/splash', '/login', '/otp'];

/// Provider du GoRouter.
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/splash',
    redirect: (context, state) {
      final location = state.matchedLocation;
      final isPublicRoute = _publicRoutes.contains(location);

      if (authState == AuthState.initial) {
        return isPublicRoute ? null : '/splash';
      }

      if (authState == AuthState.unauthenticated) {
        return isPublicRoute ? null : '/login';
      }

      if (authState == AuthState.authenticated && isPublicRoute) {
        return '/chats';
      }

      return null;
    },
    routes: [
      // ── Onboarding ──
      GoRoute(path: '/splash', builder: (_, __) => const SplashScreen()),
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/otp', builder: (_, __) => const OtpScreen()),
      GoRoute(path: '/modes', builder: (_, __) => const ModeSelectionScreen()),

      // ── Onglets principaux avec bottom nav persistant ──
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) =>
            MainScaffold(navigationShell: navigationShell),
        branches: [
          // Onglet 0 : Chats
          StatefulShellBranch(
            routes: [
              GoRoute(path: '/chats', builder: (_, __) => const ConversationsScreen()),
              GoRoute(path: '/chat/:id', builder: (_, state) => ChatScreen(conversationId: state.pathParameters['id']!)),
              GoRoute(path: '/tracy', builder: (_, __) => const TracyChannelScreen()),
              GoRoute(path: '/contact/:id', builder: (_, state) => ContactProfileScreen(contactId: state.pathParameters['id']!)),
            ],
          ),
          // Onglet 1 : Rechercher
          StatefulShellBranch(
            routes: [
              GoRoute(path: '/search', builder: (_, __) => const SearchProductScreen()),
            ],
          ),
          // Onglet 2 : Découvrir
          StatefulShellBranch(
            routes: [
              GoRoute(path: '/discover', builder: (_, __) => const DiscoverScreen()),
            ],
          ),
          // Onglet 3 : Commandes
          StatefulShellBranch(
            routes: [
              GoRoute(path: '/orders', builder: (_, __) => const OrderHistoryScreen()),
            ],
          ),
          // Onglet 4 : Profil
          StatefulShellBranch(
            routes: [
              GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
            ],
          ),
        ],
      ),

      // ── Chat ──
      GoRoute(path: '/new-chat', builder: (_, __) => const NewChatScreen()),
      GoRoute(path: '/statuses', builder: (_, __) => const StatusScreen()),

      // ── Vendor ──
      GoRoute(path: '/vendor', builder: (_, __) => const VendorDashboardScreen()),
      GoRoute(path: '/vendor/store', builder: (_, __) => const VendorStoreScreen()),
      GoRoute(path: '/vendor/tracy', builder: (_, __) => const VendorTracyConfigScreen()),
      GoRoute(path: '/vendor/create-store', builder: (_, __) => const VendorCreateStoreScreen()),
      GoRoute(path: '/vendor/add-product', builder: (_, __) => const VendorAddProductScreen()),
      GoRoute(path: '/vendor/orders', builder: (_, __) => const VendorOrdersScreen()),
      GoRoute(path: '/vendor/orders/:id', builder: (_, state) => VendorOrderDetailScreen(orderId: state.pathParameters['id']!)),
      GoRoute(path: '/vendor/notifications', builder: (_, __) => const VendorNotificationsScreen()),
      GoRoute(path: '/vendor/whatsapp', builder: (_, __) => const ConnectWhatsappScreen()),
      GoRoute(path: '/vendor/stats', builder: (_, __) => const VendorDashboardScreen()),
      GoRoute(path: '/vendor/subscriptions', builder: (_, __) => const SubscriptionScreen()),

      // ── Commun ──
      GoRoute(path: '/wallet', builder: (_, __) => const WalletScreen()),
      GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
      GoRoute(path: '/notifications', builder: (_, __) => const NotificationsCenterScreen()),

      // ── Restaurants ──
      GoRoute(path: '/restaurants', builder: (_, __) => const RestaurantsScreen()),
      GoRoute(path: '/restaurants/:id', builder: (_, state) => RestaurantMenuScreen(restaurantId: int.tryParse(state.pathParameters['id'] ?? '0') ?? 0)),

      // ── Acheteur (flow commande via Tracy) ──
      GoRoute(path: '/product-search', builder: (_, __) => const ProductSearchScreen()),
      GoRoute(path: '/product-detail', builder: (_, state) {
        final extra = state.extra as Map<String, dynamic>? ?? {};
        return ProductDetailScreen(
          productName: extra['name'] as String? ?? 'Produit',
          productPrice: extra['price'] as int? ?? 0,
          storeName: extra['storeName'] as String?,
          productImage: extra['image'] as String?,
          description: extra['description'] as String?,
        );
      }),
      GoRoute(path: '/negotiation', builder: (_, __) => const NegotiationScreen()),
      GoRoute(path: '/order-recap/:orderId', builder: (_, state) => OrderRecapScreen(orderId: state.pathParameters['orderId']!)),
      GoRoute(path: '/payment/confirm/:orderId', builder: (_, state) => PaymentConfirmationScreen(orderId: state.pathParameters['orderId']!)),
      GoRoute(path: '/payment/:orderId', builder: (_, state) => PaymentScreen(orderId: state.pathParameters['orderId']!)),
      GoRoute(path: '/delivery/:orderId', builder: (_, state) => DeliveryTrackingScreen(orderId: state.pathParameters['orderId']!)),
      GoRoute(path: '/orders/:orderId/dispute', builder: (_, state) => DisputeScreen(orderId: state.pathParameters['orderId']!)),
      GoRoute(path: '/orders/:orderId/conformity', builder: (_, state) {
        final extra = state.extra as Map<String, dynamic>? ?? {};
        return ConformityScreen(
          orderId: state.pathParameters['orderId']!,
          productId: extra['productId'] as int? ?? 0,
          storeId: extra['storeId'] as int? ?? 0,
          productName: extra['productName'] as String? ?? 'Produit',
          catalogImageUrl: extra['catalogImageUrl'] as String?,
        );
      }),
      GoRoute(path: '/orders/:orderId', builder: (_, state) => DeliveryTrackingScreen(orderId: state.pathParameters['orderId']!)),
    ],
  );
});
