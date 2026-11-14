import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/tracy_avatar.dart';
import '../../../core/widgets/adinkra_background.dart';

/// Écran 10 — Dashboard Vendeur.
///
/// Vue d'ensemble : Tracy active, commandes récentes, stats rapides.
/// Navigation : Dashboard · Boutique · Commandes · Profil
class VendorDashboardScreen extends ConsumerStatefulWidget {
  const VendorDashboardScreen({super.key});

  @override
  ConsumerState<VendorDashboardScreen> createState() => _VendorDashboardScreenState();
}

class _VendorDashboardScreenState extends ConsumerState<VendorDashboardScreen> {
  bool _tracyActive = true;
  bool _tracyLoading = false;

  @override
  void initState() {
    super.initState();
    _loadTracyConfig();
  }

  void _loadTracyConfig() async {
    try {
      final api = await ref.read(apiClientProvider.future);
      final json = await api.get('/tracy/config');
      final config = json['config'] as Map<String, dynamic>?;
      if (config != null && mounted) {
        final mode = config['tracy_mode'] as String? ?? config['mode'] as String? ?? 'active';
        setState(() => _tracyActive = mode != 'discovery');
      }
    } catch (_) {}
  }

  void _toggleTracy(bool value) async {
    setState(() {
      _tracyActive = value;
      _tracyLoading = true;
    });
    try {
      final api = await ref.read(apiClientProvider.future);
      await api.post('/tracy/config', data: {
        'mode': value ? 'active' : 'discovery',
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(value ? 'Tracy activée' : 'Tracy en mode découverte'),
            backgroundColor: MantotaColors.teal,
            duration: const Duration(seconds: 2),
          ),
        );
      }
    } catch (_) {
      if (mounted) {
        setState(() => _tracyActive = !value);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Erreur lors du changement de mode Tracy'),
            backgroundColor: MantotaColors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _tracyLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ordersAsync = ref.watch(vendorOrderListProvider);
    final storeStatsAsync = ref.watch(storeStatsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
        actions: [
          IconButton(icon: const Icon(Icons.notifications_outlined, size: 22), onPressed: () => context.push('/vendor/notifications')),
        ],
      ),
      body: Stack(
        children: [
          const AdinkraBackground(opacity: 0.04),
          ListView(
        padding: const EdgeInsets.all(14),
        children: [
          // Tracy status card
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: MantotaColors.tealPale,
              border: Border.all(color: MantotaColors.teal.withValues(alpha: 0.2)),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Row(
              children: [
                Container(
                  width: 40, height: 40,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(colors: [MantotaColors.teal, MantotaColors.tealDark]),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const TracyAvatar(size: 40, borderRadius: 10),
                ),
                const SizedBox(width: 10),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Tracy', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: MantotaColors.teal)),
                      Text('Mode 3 · Répond, vend, négocie', style: TextStyle(fontSize: 12, color: MantotaColors.grey2)),
                    ],
                  ),
                ),
                Switch.adaptive(
                  value: _tracyActive,
                  onChanged: _tracyLoading ? null : _toggleTracy,
                  activeTrackColor: MantotaColors.teal,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Stats row
          storeStatsAsync.when(
            data: (stats) => Column(
              children: [
                Row(
                  children: [
                    Expanded(child: _StatCard(label: 'Ventes', value: _formatRevenue(stats['revenue'] ?? 0.0), icon: Icons.trending_up)),
                    const SizedBox(width: 10),
                    Expanded(child: _StatCard(label: 'Commandes', value: '${stats['total_orders'] ?? 0}', icon: Icons.shopping_bag_outlined)),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(child: _StatCard(label: 'Produits', value: '${stats['total_products'] ?? 0}', icon: Icons.inventory_2_outlined)),
                    const SizedBox(width: 10),
                    Expanded(child: _StatCard(label: 'Note', value: '${stats['rating'] ?? 5.0}★', icon: Icons.star_outline)),
                  ],
                ),
              ],
            ),
            loading: () => const Center(child: Padding(padding: EdgeInsets.all(20), child: CircularProgressIndicator())),
            error: (_, __) => Row(
              children: [
                Expanded(child: _StatCard(label: 'Ventes', value: '—', icon: Icons.trending_up)),
                const SizedBox(width: 10),
                Expanded(child: _StatCard(label: 'Commandes', value: '—', icon: Icons.shopping_bag_outlined)),
              ],
            ),
          ),
          const SizedBox(height: 20),
          // Commandes récentes
          const Text('Commandes récentes', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          ordersAsync.when(
            data: (orders) => orders.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(30),
                      child: Column(
                        children: [
                          const Icon(Icons.inbox_outlined, size: 48, color: MantotaColors.grey4),
                          const SizedBox(height: 14),
                          const Text('Aucune commande', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: MantotaColors.grey3)),
                          const SizedBox(height: 6),
                          const Text('Les commandes de vos clients apparaîtront ici', style: TextStyle(fontSize: 13, color: MantotaColors.grey4)),
                        ],
                      ),
                    ),
                  )
                : Column(
              children: orders.take(3).map((o) => _RecentOrder(
                name: o.customerName ?? 'Client',
                product: o.productName,
                amount: o.formattedTotal,
                status: o.statusLabel,
              )).toList(),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (_, __) => Center(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    const Icon(Icons.cloud_off, size: 40, color: MantotaColors.grey4),
                    const SizedBox(height: 12),
                    const Text('Impossible de charger les commandes', style: TextStyle(fontSize: 14, color: MantotaColors.grey3)),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
        ],
      ),
    );
  }

  String _formatRevenue(double amount) {
    if (amount >= 1000000) return '${(amount / 1000000).toStringAsFixed(1)}M F';
    if (amount >= 1000) return '${(amount / 1000).toStringAsFixed(0)}k F';
    return '${amount.toStringAsFixed(0)} F';
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;

  const _StatCard({required this.label, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: MantotaColors.teal, size: 18),
          const SizedBox(height: 6),
          Text(value, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
          Text(label, style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
        ],
      ),
    );
  }
}

class _RecentOrder extends StatelessWidget {
  final String name;
  final String product;
  final String amount;
  final String status;

  const _RecentOrder({required this.name, required this.product, required this.amount, required this.status});

  @override
  Widget build(BuildContext context) {
    final statusColor = status == 'Livraison' ? MantotaColors.coral : MantotaColors.teal;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(11)),
      child: Row(
        children: [
          Container(
            width: 34, height: 34,
            decoration: BoxDecoration(color: MantotaColors.surface3, borderRadius: BorderRadius.circular(10)),
            child: const Icon(Icons.shopping_bag_outlined, color: MantotaColors.grey2, size: 16),
          ),
          const SizedBox(width: 9),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
                Text(product, style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(amount, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(color: statusColor, borderRadius: BorderRadius.circular(4)),
                child: Text(status, style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: Colors.white)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
