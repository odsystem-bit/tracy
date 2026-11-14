import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/models/order.dart';
import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran 07e — Historique des commandes (Buyer).
class OrderHistoryScreen extends ConsumerWidget {
  const OrderHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ordersAsync = ref.watch(orderListProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Mes commandes')),
      body: ordersAsync.when(
        data: (orders) => orders.isEmpty
            ? Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.shopping_bag_outlined, size: 48, color: MantotaColors.grey4),
                    const SizedBox(height: 12),
                    const Text('Aucune commande', style: TextStyle(fontSize: 16, color: MantotaColors.grey3)),
                    const SizedBox(height: 4),
                    const Text('Vos commandes apparaîtront ici.', style: TextStyle(fontSize: 13, color: MantotaColors.grey4)),
                  ],
                ),
              )
            : ListView(
          padding: const EdgeInsets.all(14),
          children: orders.map((o) => GestureDetector(
            onTap: () => context.push('/orders/${o.id}'),
            child: _OrderTile(
              reference: o.reference,
              product: o.productName,
              total: o.total,
              status: o.statusLabel,
              statusColor: _statusColor(o.status),
            ),
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
        return MantotaColors.teal;
    }
  }
}

class _OrderTile extends StatelessWidget {
  final String reference;
  final String product;
  final int total;
  final String status;
  final Color statusColor;
  final VoidCallback? onTap;

  const _OrderTile({
    required this.reference,
    required this.product,
    required this.total,
    required this.status,
    required this.statusColor,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
        child: Row(
          children: [
            Container(
              width: 44, height: 44,
              decoration: BoxDecoration(color: MantotaColors.surface3, borderRadius: BorderRadius.circular(10)),
              child: const Icon(Icons.shopping_bag_outlined, color: MantotaColors.grey2, size: 22),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(product, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                  Text(reference, style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text('$total F', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                const SizedBox(height: 2),
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
