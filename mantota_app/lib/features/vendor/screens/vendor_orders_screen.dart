import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/models/order.dart';
import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran 10f (commandes) — Commandes entrantes vendeur.
///
/// Liste des commandes avec filtres par statut.
class VendorOrdersScreen extends ConsumerWidget {
  const VendorOrdersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ordersAsync = ref.watch(vendorOrderListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Commandes'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: Column(
        children: [
          // Filtres
          SizedBox(
            height: 40,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 14),
              children: [
                _FilterChip(label: 'Toutes', selected: true),
                _FilterChip(label: 'Nouvelles', selected: false),
                _FilterChip(label: 'En cours', selected: false),
                _FilterChip(label: 'Livrées', selected: false),
              ],
            ),
          ),
          const SizedBox(height: 6),
          // Liste
          Expanded(
            child: ordersAsync.when(
              data: (orders) => orders.isEmpty
                  ? Center(
                      child: Padding(
                        padding: const EdgeInsets.all(30),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
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
                  : ListView(
                padding: const EdgeInsets.symmetric(horizontal: 14),
                children: orders.map((o) => _OrderRow(
                  ref_: o.reference,
                  client: o.customerName ?? '',
                  product: o.productName,
                  amount: o.formattedTotal,
                  status: o.statusLabel,
                  statusColor: _statusColor(o.status),
                  onTap: () => context.push('/vendor/orders/${o.id}'),
                )).toList(),
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(30),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.cloud_off, size: 40, color: MantotaColors.grey4),
                      const SizedBox(height: 12),
                      const Text('Impossible de charger les commandes', style: TextStyle(fontSize: 14, color: MantotaColors.grey3)),
                      const SizedBox(height: 8),
                      Text(e.toString(), style: const TextStyle(fontSize: 11, color: MantotaColors.grey4), textAlign: TextAlign.center),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _statusColor(OrderStatus status) {
    switch (status) {
      case OrderStatus.delivered:
      case OrderStatus.paid:
        return MantotaColors.teal;
      case OrderStatus.shipped:
        return MantotaColors.coral;
      case OrderStatus.cancelled:
        return MantotaColors.error;
      default:
        return MantotaColors.grey4;
    }
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final bool selected;

  const _FilterChip({required this.label, required this.selected});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(right: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: selected ? MantotaColors.teal : MantotaColors.surface1,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(label, style: TextStyle(
        fontSize: 13, fontWeight: FontWeight.w600,
        color: selected ? Colors.white : MantotaColors.grey2,
      )),
    );
  }
}

class _OrderRow extends StatelessWidget {
  final String ref_;
  final String client;
  final String product;
  final String amount;
  final String status;
  final Color statusColor;
  final VoidCallback onTap;

  const _OrderRow({
    required this.ref_,
    required this.client,
    required this.product,
    required this.amount,
    required this.status,
    required this.statusColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
        child: Row(
          children: [
            Container(
              width: 40, height: 40,
              decoration: BoxDecoration(color: MantotaColors.surface3, borderRadius: BorderRadius.circular(10)),
              child: const Icon(Icons.shopping_bag_outlined, color: MantotaColors.grey2, size: 20),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(client, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                  Text(product, style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
                  Text(ref_, style: const TextStyle(fontSize: 11, color: MantotaColors.grey4)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(amount, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                const SizedBox(height: 3),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(color: statusColor.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(4)),
                  child: Text(status, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: statusColor)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
