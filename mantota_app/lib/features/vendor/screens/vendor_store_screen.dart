import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran 10b — Ma boutique.
///
/// Informations de la boutique, catalogue produits, lien config Tracy.
class VendorStoreScreen extends ConsumerWidget {
  const VendorStoreScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final storeAsync = ref.watch(storeDetailProvider);
    final productsAsync = ref.watch(storeProductsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ma boutique'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
        actions: [
          IconButton(icon: const Icon(Icons.share_outlined, size: 20), onPressed: () => _shareStore(context, ref)),
          IconButton(icon: const Icon(Icons.settings_outlined, size: 20), onPressed: () => context.push('/vendor/tracy')),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(14),
        children: [
          // Boutique header
          storeAsync.when(
            data: (store) => Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(14)),
              child: Row(
                children: [
                  Container(
                    width: 56, height: 56,
                    decoration: BoxDecoration(color: MantotaColors.teal, borderRadius: BorderRadius.circular(14)),
                    child: const Icon(Icons.store, color: Colors.white, size: 28),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(store?.name ?? 'Ma Boutique', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                        Text(store?.type ?? 'Boutique physique · Cotonou', style: const TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                        Text('⭐ ${store?.rating.toStringAsFixed(1) ?? '4.8'} · ${store?.productCount ?? 0} produits', style: const TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (_, __) => Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(14)),
              child: Row(
                children: [
                  Container(
                    width: 56, height: 56,
                    decoration: BoxDecoration(color: MantotaColors.teal, borderRadius: BorderRadius.circular(14)),
                    child: const Icon(Icons.store, color: Colors.white, size: 28),
                  ),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Ma Boutique', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                        Text('Boutique physique · Cotonou', style: TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                        Text('⭐ 4.8 · 23 produits', style: TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Lien boutique partageable
          _StoreShareCard(ref: ref),
          const SizedBox(height: 16),
          // Actions rapides
          Row(
            children: [
              Expanded(child: _QuickAction(icon: Icons.add_circle_outline, label: 'Ajouter produit', onTap: () => context.push('/vendor/add-product'))),
              const SizedBox(width: 10),
              Expanded(child: _QuickAction(icon: Icons.tune_outlined, label: 'Config Tracy', onTap: () => context.push('/vendor/tracy'))),
              const SizedBox(width: 10),
              Expanded(child: _QuickAction(icon: Icons.bar_chart_outlined, label: 'Statistiques', onTap: () => context.push('/vendor/stats'))),
            ],
          ),
          const SizedBox(height: 16),
          // Catalogue
          const Text('Catalogue', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          productsAsync.when(
            data: (products) => GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, childAspectRatio: 0.72, crossAxisSpacing: 10, mainAxisSpacing: 10),
              itemCount: products.length,
              itemBuilder: (_, i) => _ProductMiniCard(name: products[i].name, price: products[i].price),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (_, __) => GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, childAspectRatio: 0.72, crossAxisSpacing: 10, mainAxisSpacing: 10),
              itemCount: 4,
              itemBuilder: (_, i) => _ProductMiniCard(name: ['Nike Air Max', 'Sac cuir', 'T-shirt', 'Montre'][i], price: [45000, 25000, 8000, 15000][i]),
            ),
          ),
        ],
      ),
    );
  }

  void _shareStore(BuildContext context, WidgetRef ref) async {
    try {
      final api = await ref.read(apiClientProvider.future);
      final json = await api.get('/vendor/store/share');
      final storeUrl = json['store_url'] as String? ?? '';
      final shareText = json['share_text'] as String? ?? 'Découvrez ma boutique sur MANTOTA !';

      if (storeUrl.isNotEmpty) {
        Share.share(shareText);
      } else {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Impossible de récupérer le lien de la boutique.')),
          );
        }
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e')),
        );
      }
    }
  }
}

class _StoreShareCard extends ConsumerWidget {
  const _StoreShareCard({required this.ref});

  final WidgetRef ref;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FutureBuilder(
      future: _fetchShareInfo(ref),
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const SizedBox.shrink();
        }

        final data = snapshot.data as Map<String, dynamic>?;
        if (data == null) return const SizedBox.shrink();

        final storeUrl = data['store_url'] as String? ?? '';
        final slug = data['store_slug'] as String? ?? '';

        if (storeUrl.isEmpty) return const SizedBox.shrink();

        return Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [MantotaColors.tealDark, Color(0xFF12121F)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                children: [
                  Icon(Icons.link, color: Colors.white70, size: 16),
                  SizedBox(width: 6),
                  Text('LIEN DE MA BOUTIQUE', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.5, color: Colors.white54)),
                ],
              ),
              const SizedBox(height: 8),
              Text(storeUrl, style: const TextStyle(fontSize: 13, color: Colors.white, fontWeight: FontWeight.w600), maxLines: 2, overflow: TextOverflow.ellipsis),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () => Share.share(data['share_text'] as String? ?? storeUrl),
                      icon: const Icon(Icons.share, size: 16),
                      label: const Text('Partager'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: MantotaColors.teal,
                        foregroundColor: Colors.white,
                        minimumSize: const Size(double.infinity, 38),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: () async {
                      final uri = Uri.parse(storeUrl);
                      if (await canLaunchUrl(uri)) {
                        await launchUrl(uri, mode: LaunchMode.externalApplication);
                      }
                    },
                    icon: const Icon(Icons.open_in_new, color: Colors.white70, size: 18),
                    style: IconButton.styleFrom(
                      backgroundColor: Colors.white.withValues(alpha: 0.1),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: () {
                      Clipboard.setData(ClipboardData(text: storeUrl));
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Lien copié !'), duration: Duration(seconds: 2)),
                      );
                    },
                    icon: const Icon(Icons.copy, color: Colors.white70, size: 18),
                    style: IconButton.styleFrom(
                      backgroundColor: Colors.white.withValues(alpha: 0.1),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Future<Map<String, dynamic>?> _fetchShareInfo(WidgetRef ref) async {
    try {
      final api = await ref.read(apiClientProvider.future);
      return api.get('/vendor/store/share');
    } catch (_) {
      return null;
    }
  }
}

class _QuickAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _QuickAction({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: MantotaColors.tealPale, borderRadius: BorderRadius.circular(12)),
        child: Column(
          children: [
            Icon(icon, color: MantotaColors.teal, size: 24),
            const SizedBox(height: 6),
            Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: MantotaColors.teal), textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}

class _ProductMiniCard extends StatelessWidget {
  final String name;
  final int price;

  const _ProductMiniCard({required this.name, required this.price});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(child: Container(decoration: BoxDecoration(color: MantotaColors.surface3, borderRadius: const BorderRadius.vertical(top: Radius.circular(12))))),
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
    );
  }
}
