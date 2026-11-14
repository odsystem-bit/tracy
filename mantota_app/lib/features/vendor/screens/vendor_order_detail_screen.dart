import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/models/order_track.dart';

/// Écran — Détail commande vendeur.
///
/// Informations complètes : client, produit, montant, statut, actions.
class VendorOrderDetailScreen extends ConsumerWidget {
  final String orderId;

  const VendorOrderDetailScreen({super.key, required this.orderId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final orderAsync = ref.watch(orderDetailProvider(orderId));
    final trackAsync = ref.watch(orderTrackProvider(orderId));

    return Scaffold(
      appBar: AppBar(
        title: Text(orderId),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: orderAsync.when(
        data: (order) => _buildContent(
          context,
          ref,
          trackAsync: trackAsync,
          customerName: order.customerName ?? 'Client',
          productName: order.productName,
          total: order.formattedTotal,
          statusLabel: order.statusLabel,
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
                const Text('Commande introuvable', style: TextStyle(fontSize: 14, color: MantotaColors.grey3)),
                const SizedBox(height: 8),
                Text(e.toString(), style: const TextStyle(fontSize: 11, color: MantotaColors.grey4), textAlign: TextAlign.center),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildContent(
    BuildContext context,
    WidgetRef ref, {
    required AsyncValue<OrderTrackData> trackAsync,
    required String customerName,
    required String productName,
    required String total,
    required String statusLabel,
  }) {
    return ListView(
        padding: const EdgeInsets.all(14),
        children: [
          // Statut principal
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: MantotaColors.coral.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Row(
              children: [
                const Icon(Icons.local_shipping_outlined, color: MantotaColors.coral, size: 28),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(statusLabel, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: MantotaColors.coral)),
                      const Text('Livreur en route', style: TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Client
          const Text('Client', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
            child: Row(
              children: [
                CircleAvatar(radius: 18, backgroundColor: MantotaColors.surface3, child: Text(customerName.isNotEmpty ? customerName.substring(0, 2).toUpperCase() : '??', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700))),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(customerName, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                      const Text('+229 01 97 12 34 56', style: TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                    ],
                  ),
                ),
                const Icon(Icons.chat_bubble_outline, color: MantotaColors.teal, size: 20),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Produit
          const Text('Produit', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
            child: Row(
              children: [
                Container(
                  width: 48, height: 48,
                  decoration: BoxDecoration(color: MantotaColors.surface3, borderRadius: BorderRadius.circular(10)),
                  child: const Icon(Icons.inventory_2_outlined, color: MantotaColors.grey2, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(productName, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                      const Text('Qté: 1', style: TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                    ],
                  ),
                ),
                Text(total, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: MantotaColors.teal)),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Timeline
          const Text('Suivi', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          trackAsync.when(
            data: (track) => Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
              child: track.timeline.isEmpty
                  ? const Text('Aucun suivi disponible', style: TextStyle(fontSize: 13, color: MantotaColors.grey3))
                  : Column(
                      children: track.timeline.asMap().entries.map((e) => _TimelineStep(
                        label: e.value.label,
                        time: e.value.date,
                        done: e.value.status == 'done' || e.value.status == 'current',
                        isLast: e.key == track.timeline.length - 1,
                      )).toList(),
                    ),
            ),
            loading: () => const Center(child: Padding(padding: EdgeInsets.all(20), child: CircularProgressIndicator())),
            error: (_, __) => Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
              child: const Text('Suivi non disponible', style: TextStyle(fontSize: 13, color: MantotaColors.grey3)),
            ),
          ),
          const SizedBox(height: 20),
          // Actions
          Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: () => context.push('/chat/$orderId'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: MantotaColors.surface1,
                    foregroundColor: MantotaColors.grey1,
                  ),
                  child: const Text('Contacter le client'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton(
                  onPressed: () async {
                    try {
                      final svc = await ref.read(orderServiceProvider.future);
                      await svc.updateStatus(orderId, 'shipped');
                      ref.invalidate(orderDetailProvider(orderId));
                      ref.invalidate(orderTrackProvider(orderId));
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Statut mis à jour : Expédié')));
                      }
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('Erreur: $e')));
                      }
                    }
                  },
                  child: const Text('Marquer expédié'),
                ),
              ),
            ],
          ),
        ],
      );
  }
}

class _TimelineStep extends StatelessWidget {
  final String label;
  final String time;
  final bool done;
  final bool isLast;

  const _TimelineStep({
    required this.label,
    required this.time,
    required this.done,
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Column(
          children: [
            Container(
              width: 20, height: 20,
              decoration: BoxDecoration(
                color: done ? MantotaColors.teal : MantotaColors.surface3,
                shape: BoxShape.circle,
              ),
              child: done ? const Icon(Icons.check, color: Colors.white, size: 12) : null,
            ),
            if (!isLast) Container(width: 2, height: 24, color: MantotaColors.teal.withValues(alpha: 0.3)),
          ],
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Padding(
            padding: EdgeInsets.only(bottom: isLast ? 0 : 24),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(label, style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: done ? MantotaColors.grey1 : MantotaColors.grey4)),
                Text(time, style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
