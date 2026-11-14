import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/adinkra_background.dart';

/// Écran 07g — Découvrir.
///
/// Feed de produits et boutiques recommandés par Tracy.
class DiscoverScreen extends ConsumerWidget {
  const DiscoverScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final productsAsync = ref.watch(trendingProductsProvider);
    final storesAsync = ref.watch(popularStoresProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Découvrir')),
      body: Stack(
        children: [
          const AdinkraBackground(opacity: 0.04),
          ListView(
        padding: const EdgeInsets.all(14),
        children: [
          _CategoryChips(),
          const SizedBox(height: 14),
          const Text('Recommandé par Tracy', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          SizedBox(
            height: 200,
            child: productsAsync.when(
              data: (products) => ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: products.length,
                separatorBuilder: (_, __) => const SizedBox(width: 10),
                itemBuilder: (_, i) => _RecommendCard(
                  name: products[i].name,
                  price: products[i].price,
                ),
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (_, __) => const Center(
                child: Padding(
                  padding: EdgeInsets.all(20),
                  child: Text('Impossible de charger les produits', style: TextStyle(color: MantotaColors.grey3)),
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),
          const Text('Boutiques populaires', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          storesAsync.when(
            data: (stores) => Column(
              children: stores.map((s) => _StoreTile(
                name: s.name,
                rating: s.rating.toStringAsFixed(1),
              )).toList(),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (_, __) => const Center(
              child: Padding(
                padding: EdgeInsets.all(20),
                child: Text('Impossible de charger les boutiques', style: TextStyle(color: MantotaColors.grey3)),
              ),
            ),
          ),
        ],
      ),
        ],
      ),
    );
  }
}

class _CategoryChips extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final cats = ['Tout', 'Mode', 'Tech', 'Maison', 'Beauté', 'Sport'];
    return SizedBox(
      height: 32,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: cats.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (_, i) => Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
          decoration: BoxDecoration(
            color: i == 0 ? MantotaColors.teal : MantotaColors.surface1,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Text(cats[i], style: TextStyle(
            fontSize: 13, fontWeight: FontWeight.w600,
            color: i == 0 ? Colors.white : MantotaColors.grey2,
          )),
        ),
      ),
    );
  }
}

class _RecommendCard extends StatelessWidget {
  final String name;
  final int price;

  const _RecommendCard({required this.name, required this.price});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
    onTap: () => context.push('/product-detail', extra: {'name': name, 'price': price}),
    child: Container(
      width: 140,
      decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: MantotaColors.surface3,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
              ),
              child: const Center(child: Icon(Icons.image_outlined, color: MantotaColors.grey4, size: 28)),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600), maxLines: 1, overflow: TextOverflow.ellipsis),
                Text('$price F', style: const TextStyle(fontSize: 12, color: MantotaColors.teal, fontWeight: FontWeight.w700)),
              ],
            ),
          ),
        ],
      ),
    ),
    );
  }
}

class _StoreTile extends StatelessWidget {
  final String name;
  final String rating;

  const _StoreTile({required this.name, required this.rating});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
      child: Row(
        children: [
          Container(
            width: 40, height: 40,
            decoration: BoxDecoration(color: MantotaColors.surface3, borderRadius: BorderRadius.circular(10)),
            child: const Icon(Icons.store_outlined, color: MantotaColors.grey2, size: 20),
          ),
          const SizedBox(width: 10),
          Expanded(child: Text(name, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600))),
          Text('⭐ $rating', style: const TextStyle(fontSize: 13, color: MantotaColors.grey2)),
        ],
      ),
    );
  }
}
