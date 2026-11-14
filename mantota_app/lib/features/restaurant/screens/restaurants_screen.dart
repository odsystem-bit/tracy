import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/services/restaurant_service.dart';
import '../../../core/theme/mantota_theme.dart';

class RestaurantsScreen extends ConsumerWidget {
  const RestaurantsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final restaurantsAsync = ref.watch(restaurantsListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Restaurants', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 22),
          onPressed: () => context.pop(),
        ),
      ),
      body: restaurantsAsync.when(
        data: (restaurants) {
          if (restaurants.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.restaurant_outlined, size: 48, color: MantotaColors.grey3),
                  const SizedBox(height: 12),
                  const Text('Aucun restaurant disponible', style: TextStyle(fontSize: 15, color: MantotaColors.grey2)),
                  const SizedBox(height: 4),
                  Text('Revenez plus tard !', style: TextStyle(fontSize: 13, color: MantotaColors.grey3)),
                ],
              ),
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            itemCount: restaurants.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final r = restaurants[index];
              return _RestaurantCard(restaurant: r);
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, __) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.wifi_off, size: 40, color: MantotaColors.grey3),
              const SizedBox(height: 12),
              const Text('Connexion impossible', style: TextStyle(fontSize: 14, color: MantotaColors.grey2)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.refresh(restaurantsListProvider),
                child: const Text('Réessayer'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RestaurantCard extends StatelessWidget {
  final RestaurantSummary restaurant;

  const _RestaurantCard({required this.restaurant});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.push('/restaurants/${restaurant.id}'),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          boxShadow: [
            BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 8, offset: const Offset(0, 2)),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(14)),
              child: restaurant.shopLogo != null
                  ? CachedNetworkImage(
                      imageUrl: restaurant.shopLogo!,
                      height: 140,
                      width: double.infinity,
                      fit: BoxFit.cover,
                      placeholder: (_, __) => Container(height: 140, color: MantotaColors.surface1),
                      errorWidget: (_, __, ___) => Container(
                        height: 140,
                        color: MantotaColors.surface1,
                        child: const Icon(Icons.restaurant, size: 40, color: MantotaColors.grey3),
                      ),
                    )
                  : Container(
                      height: 140,
                      color: MantotaColors.surface1,
                      child: const Icon(Icons.restaurant, size: 40, color: MantotaColors.grey3),
                    ),
            ),
            Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          restaurant.shopName,
                          style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: MantotaColors.grey1),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (restaurant.address != null) ...[
                          const SizedBox(height: 2),
                          Row(
                            children: [
                              const Icon(Icons.location_on, size: 12, color: MantotaColors.grey3),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Text(
                                  restaurant.address!,
                                  style: const TextStyle(fontSize: 12, color: MantotaColors.grey2),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: restaurant.isOpenNow
                          ? MantotaColors.teal.withValues(alpha: 0.1)
                          : Colors.red.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      restaurant.isOpenNow ? 'Ouvert' : 'Fermé',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: restaurant.isOpenNow ? MantotaColors.teal : Colors.red,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
