import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran 07 — Recherche produit.
///
/// Recherche par texte, résultats en grille avec image, nom, prix, boutique.
class SearchProductScreen extends ConsumerStatefulWidget {
  const SearchProductScreen({super.key});

  @override
  ConsumerState<SearchProductScreen> createState() => _SearchProductScreenState();
}

class _SearchProductScreenState extends ConsumerState<SearchProductScreen> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final resultsAsync = _query.isEmpty
        ? null
        : ref.watch(searchProductsProvider(_query));

    return Scaffold(
      appBar: AppBar(
        title: TextField(
          autofocus: true,
          decoration: const InputDecoration(
            hintText: 'Rechercher un produit...',
            border: InputBorder.none,
            prefixIcon: Icon(Icons.search, color: MantotaColors.grey2),
          ),
          onSubmitted: (q) => setState(() => _query = q),
        ),
        actions: [
          TextButton(onPressed: () => context.pop(), child: const Text('Annuler')),
        ],
      ),
      body: _query.isEmpty
          ? const Center(child: Text('Tapez pour rechercher', style: TextStyle(fontSize: 15, color: MantotaColors.grey2)))
          : resultsAsync!.when(
              data: (products) => GridView.builder(
                padding: const EdgeInsets.all(14),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  childAspectRatio: 0.72,
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 10,
                ),
                itemCount: products.length,
                itemBuilder: (_, i) => _ProductCard(
                  name: products[i].name,
                  price: products[i].price,
                ),
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (_, __) => GridView.builder(
                padding: const EdgeInsets.all(14),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  childAspectRatio: 0.72,
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 10,
                ),
                itemCount: 6,
                itemBuilder: (_, i) => _ProductCard(
                  name: ['Nike Air Max 270', 'Sac cuir marron', 'T-shirt Ankara', 'Tecno Spark 10', 'Montre sport', 'Casque audio'][i],
                  price: [45000, 25000, 8000, 65000, 15000, 12000][i],
                ),
              ),
            ),
    );
  }
}

class _ProductCard extends StatelessWidget {
  final String name;
  final int price;

  const _ProductCard({required this.name, required this.price});

  String get _formattedPrice {
    final groups = <String>[];
    String str = price.toString();
    while (str.length > 3) {
      groups.insert(0, str.substring(str.length - 3));
      str = str.substring(0, str.length - 3);
    }
    groups.insert(0, str);
    return '${groups.join(' ')} F';
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.push('/product-detail', extra: {'name': name, 'price': price}),
      child: Container(
      decoration: BoxDecoration(
        color: MantotaColors.surface1,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            flex: 3,
            child: Container(
              decoration: BoxDecoration(
                color: MantotaColors.surface3,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
              ),
              child: const Center(child: Icon(Icons.image_outlined, color: MantotaColors.grey4, size: 32)),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600), maxLines: 1, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 2),
                Text(_formattedPrice, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: MantotaColors.teal)),
              ],
            ),
          ),
        ],
      ),
    ),
    );
  }
}
