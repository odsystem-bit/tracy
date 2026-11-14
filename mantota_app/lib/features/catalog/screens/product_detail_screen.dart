import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/tracy_avatar.dart';

/// Écran — Fiche produit détaillée.
///
/// Affiche image, nom, prix, description, boutique, et bouton acheter.
class ProductDetailScreen extends StatelessWidget {
  final String productName;
  final int productPrice;
  final String? storeName;
  final String? productImage;
  final String? description;

  const ProductDetailScreen({
    super.key,
    required this.productName,
    required this.productPrice,
    this.storeName,
    this.productImage,
    this.description,
  });

  String get _formattedPrice {
    final groups = <String>[];
    String str = productPrice.toString();
    while (str.length > 3) {
      groups.insert(0, str.substring(str.length - 3));
      str = str.substring(0, str.length - 3);
    }
    groups.insert(0, str);
    return '${groups.join(' ')} F';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
        title: const Text('Fiche produit'),
        actions: [
          IconButton(icon: const Icon(Icons.share_outlined, size: 22), onPressed: () {}),
          IconButton(icon: const Icon(Icons.favorite_border, size: 22), onPressed: () {}),
        ],
      ),
      body: ListView(
        children: [
          // Image produit
          Container(
            height: 280,
            color: MantotaColors.surface2,
            child: productImage != null
                ? Image.network(productImage!, fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => const Center(child: Icon(Icons.image_outlined, color: MantotaColors.grey4, size: 64)))
                : const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.image_outlined, color: MantotaColors.grey4, size: 64),
                        SizedBox(height: 8),
                        Text('Photo du produit', style: TextStyle(fontSize: 13, color: MantotaColors.grey4)),
                      ],
                    ),
                  ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Nom et prix
                Text(productName, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
                const SizedBox(height: 6),
                Text(_formattedPrice, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: MantotaColors.teal)),
                const SizedBox(height: 16),
                // Boutique
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: MantotaColors.surface1,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 40, height: 40,
                        decoration: BoxDecoration(
                          color: MantotaColors.tealPale,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(Icons.store_outlined, color: MantotaColors.teal, size: 20),
                      ),
                      const SizedBox(width: 10),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Boutique', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
                            Text('Vendeur vérifié · 4.8 ★', style: TextStyle(fontSize: 12, color: MantotaColors.grey2)),
                          ],
                        ),
                      ),
                      const Icon(Icons.chevron_right, color: MantotaColors.grey4, size: 20),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                // Description
                const Text('Description', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                Text(
                  description ?? 'Produit de qualité disponible chez nos vendeurs vérifiés. Livraison rapide dans tout le Bénin. Paiement sécurisé via séquestre Mantota.',
                  style: TextStyle(fontSize: 14, color: MantotaColors.grey2, height: 1.5),
                ),
                const SizedBox(height: 16),
                // Infos
                const _InfoRow(label: 'État', value: 'Neuf'),
                const _InfoRow(label: 'Livraison', value: 'Gratuite (Cotonou)'),
                const _InfoRow(label: 'Stock', value: 'En stock'),
                const _InfoRow(label: 'Retour', value: '7 jours'),
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => context.go('/tracy'),
                  icon: const TracyAvatar(size: 18, borderRadius: 4),
                  label: const Text('Demander à Tracy'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: MantotaColors.teal,
                    side: const BorderSide(color: MantotaColors.teal),
                    minimumSize: const Size(0, 50),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton(
                  onPressed: () => context.go('/tracy'),
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(0, 50),
                  ),
                  child: const Text('Acheter'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Text(label, style: const TextStyle(fontSize: 14, color: MantotaColors.grey2)),
          const Spacer(),
          Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
