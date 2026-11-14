import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/models/order_track.dart';
import '../../../core/widgets/adinkra_background.dart';

/// Écran 07 — Suivi livraison.
///
/// Timeline temps réel, info livreur, code PIN client.
/// Données récupérées via GET /orders/{id}/track.
class DeliveryTrackingScreen extends ConsumerStatefulWidget {
  final String orderId;

  const DeliveryTrackingScreen({super.key, required this.orderId});

  @override
  ConsumerState<DeliveryTrackingScreen> createState() => _DeliveryTrackingScreenState();
}

class _DeliveryTrackingScreenState extends ConsumerState<DeliveryTrackingScreen> {
  bool _confirming = false;

  @override
  Widget build(BuildContext context) {
    final trackAsync = ref.watch(orderTrackProvider(widget.orderId));

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Commande #${widget.orderId}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
            const Text('Suivi temps réel', style: TextStyle(fontSize: 12, color: MantotaColors.grey2)),
          ],
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: Stack(
        children: [
          const AdinkraBackground(opacity: 0.04),
          trackAsync.when(
            data: (data) => _buildContent(context, data),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (_, __) => _buildFallback(context),
          ),
        ],
      ),
    );
  }

  Widget _buildContent(BuildContext context, OrderTrackData data) {
    final order = data.order;
    final timeline = data.timeline;
    final status = order.status;

    return ListView(
      padding: const EdgeInsets.all(14),
      children: [
        // Statut
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: MantotaColors.tealPale,
            border: Border.all(color: MantotaColors.teal.withValues(alpha: 0.3)),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            children: [
              Text(_statusEmoji(status), style: const TextStyle(fontSize: 30)),
              const SizedBox(height: 6),
              Text(_statusLabel(status), style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: MantotaColors.teal)),
              const SizedBox(height: 4),
              if (order.deliveryDeadline != null)
                Text('Arrivée estimée · ${_formatDate(order.deliveryDeadline!)}', style: const TextStyle(fontSize: 13, color: MantotaColors.grey1)),
              if (order.deliveryGuyName != null) ...[
                const SizedBox(height: 2),
                Text('Livreur : ${order.deliveryGuyName}${order.deliveryGuyPhone != null ? ' · ${order.deliveryGuyPhone}' : ''}', style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
              ],
              const SizedBox(height: 10),
              // Escrow badge
              _buildEscrowBadge(status),
            ],
          ),
        ),
        const SizedBox(height: 16),
        // Barre de progression 3 étapes (comme web Track.vue)
        _buildProgressBar(status),
        const SizedBox(height: 16),
        // Timeline
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: MantotaColors.surface1,
            border: Border.all(color: MantotaColors.surface3),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('ÉTAPES', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.5, color: MantotaColors.grey2)),
              const SizedBox(height: 14),
              ...timeline.asMap().entries.map((entry) {
                final i = entry.key;
                final step = entry.value;
                final isLast = i == timeline.length - 1;
                return _TimelineStep(
                  label: step.label,
                  detail: step.detail,
                  time: _formatTime(step.date),
                  status: _mapStepStatus(step.status),
                  isLast: isLast,
                );
              }),
            ],
          ),
        ),
        if (order.deliveryGuyName != null) ...[
          const SizedBox(height: 16),
          // Livreur
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: MantotaColors.surface1,
              border: Border.all(color: MantotaColors.surface3),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Row(
              children: [
                Container(
                  width: 42, height: 42,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(colors: [MantotaColors.tealPale, MantotaColors.surface2]),
                    borderRadius: BorderRadius.circular(21),
                  ),
                  child: Center(child: Text(_initials(order.deliveryGuyName!), style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: MantotaColors.grey3))),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(order.deliveryGuyName!, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                      if (order.deliveryCompany != null)
                        Text(order.deliveryCompany!, style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
                    ],
                  ),
                ),
                if (order.deliveryGuyPhone != null)
                  Container(
                    width: 36, height: 36,
                    decoration: BoxDecoration(
                      color: MantotaColors.teal.withValues(alpha: 0.1),
                      border: Border.all(color: MantotaColors.teal.withValues(alpha: 0.25)),
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: const Icon(Icons.phone, color: MantotaColors.teal, size: 16),
                  ),
              ],
            ),
          ),
        ],
        const SizedBox(height: 16),
        // Code PIN (visible uniquement pour l'acheteur)
        if (order.deliveryPin != null && order.deliveryPin!.isNotEmpty)
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [MantotaColors.tealDark, Color(0xFF12121F)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Column(
              children: [
                const Text('CODE DE CONFIRMATION',
                    style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.5,
                        color: Colors.white70)),
                const SizedBox(height: 4),
                const Text('À donner au livreur à la réception',
                    style: TextStyle(fontSize: 12, color: Colors.white54)),
                const SizedBox(height: 14),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: order.deliveryPin!.split('').map((d) => Container(
                        width: 44,
                        height: 50,
                        margin: const EdgeInsets.only(right: 10),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Center(
                            child: Text(d,
                                style: const TextStyle(
                                    fontSize: 24,
                                    fontWeight: FontWeight.w900,
                                    color: Colors.white))),
                      )).toList(),
                ),
              ],
            ),
          ),
        if (order.deliveryPin != null && order.deliveryPin!.isNotEmpty)
          const SizedBox(height: 16),
        // Bouton confirmer réception (si shipped, comme web Track.vue)
        if (status == 'shipped') ...[
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _confirming ? null : () => _showConfirmModal(data),
              icon: const Icon(Icons.check_circle, size: 20),
              label: const Text('Confirmer la réception'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size(double.infinity, 50),
              ),
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'En confirmant, vous attestez avoir reçu votre colis en bon état. Les fonds seront libérés au vendeur.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 11, color: MantotaColors.grey3),
          ),
          const SizedBox(height: 16),
        ],
        // Message si pending
        if (status == 'pending')
          Container(
            padding: const EdgeInsets.all(14),
            margin: const EdgeInsets.only(bottom: 16),
            decoration: BoxDecoration(
              color: Colors.amber.withValues(alpha: 0.08),
              border: Border.all(color: Colors.amber.withValues(alpha: 0.3)),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                const Icon(Icons.hourglass_top, size: 18, color: Colors.amber),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Le vendeur prépare votre commande. Vous pourrez confirmer la réception une fois le colis expédié.',
                    style: TextStyle(fontSize: 12, color: Colors.amber[800]),
                  ),
                ),
              ],
            ),
          ),
        // Message si delivered
        if (status == 'delivered')
          Container(
            padding: const EdgeInsets.all(14),
            margin: const EdgeInsets.only(bottom: 16),
            decoration: BoxDecoration(
              color: MantotaColors.tealPale,
              border: Border.all(color: MantotaColors.teal.withValues(alpha: 0.2)),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                const Icon(Icons.check_circle, size: 18, color: MantotaColors.teal),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Livraison confirmée. Les fonds ont été libérés au vendeur.',
                    style: const TextStyle(fontSize: 12, color: MantotaColors.tealDark),
                  ),
                ),
              ],
            ),
          ),
        // Bouton litige si commande en cours
        if (status == 'pending' || status == 'shipped')
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => context.push('/orders/${widget.orderId}/dispute'),
              icon: const Icon(Icons.gavel, size: 16, color: Colors.red),
              label: const Text('Ouvrir un litige', style: TextStyle(color: Colors.red)),
              style: OutlinedButton.styleFrom(
                side: BorderSide(color: Colors.red.withValues(alpha: 0.3)),
                minimumSize: const Size(double.infinity, 46),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildEscrowBadge(String status) {
    final isDelivered = status == 'delivered';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: isDelivered ? MantotaColors.tealPale : Colors.amber.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isDelivered ? Icons.lock_open : Icons.lock,
            size: 12,
            color: isDelivered ? MantotaColors.tealDark : Colors.amber[700],
          ),
          const SizedBox(width: 5),
          Text(
            isDelivered ? 'Fonds libérés au vendeur' : 'Fonds en escrow — sécurisés',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: isDelivered ? MantotaColors.tealDark : Colors.amber[700],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressBar(String status) {
    final steps = ['pending', 'shipped', 'delivered'];
    final currentIdx = steps.indexOf(status);
    if (currentIdx < 0) return const SizedBox.shrink();

    final labels = ['Commandée', 'Expédiée', 'Livrée'];
    final icons = [Icons.receipt_long, Icons.local_shipping, Icons.check_circle];

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: MantotaColors.surface3),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: List.generate(3, (i) {
          final isDone = i <= currentIdx;
          final isCurrent = i == currentIdx;
          return Row(
            children: [
              Column(
                children: [
                  Container(
                    width: 36, height: 36,
                    decoration: BoxDecoration(
                      color: isDone ? MantotaColors.teal : MantotaColors.surface3,
                      shape: BoxShape.circle,
                      border: isCurrent ? Border.all(color: MantotaColors.teal.withValues(alpha: 0.3), width: 3) : null,
                    ),
                    child: Icon(icons[i], size: 18, color: isDone ? Colors.white : MantotaColors.grey4),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    labels[i],
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: isDone ? MantotaColors.grey1 : MantotaColors.grey4,
                    ),
                  ),
                ],
              ),
              if (i < 2)
                Container(
                  width: 40,
                  height: 2,
                  margin: const EdgeInsets.only(bottom: 20),
                  color: i < currentIdx ? MantotaColors.teal.withValues(alpha: 0.6) : MantotaColors.surface3,
                ),
            ],
          );
        }),
      ),
    );
  }

  void _showConfirmModal(OrderTrackData data) {
    final pinCtrl = TextEditingController();
    bool processing = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) => SafeArea(
          child: Padding(
            padding: EdgeInsets.fromLTRB(20, 20, 20, MediaQuery.of(ctx).viewInsets.bottom + 20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 56, height: 56,
                  decoration: BoxDecoration(
                    color: Colors.amber.withValues(alpha: 0.15),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.warning_amber, color: Colors.amber, size: 28),
                ),
                const SizedBox(height: 16),
                const Text('Confirmer la réception', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                const SizedBox(height: 8),
                const Text(
                  'En confirmant, vous attestez avoir reçu votre commande en bon état. Cette action libérera le paiement au vendeur et est irréversible.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 13, color: MantotaColors.grey2),
                ),
                const SizedBox(height: 20),
                const Text('Code Secret de Livraison', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: MantotaColors.grey2)),
                const SizedBox(height: 8),
                TextField(
                  controller: pinCtrl,
                  keyboardType: TextInputType.number,
                  maxLength: 4,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: 8),
                  decoration: const InputDecoration(
                    hintText: '_ _ _ _',
                    counterText: '',
                    border: OutlineInputBorder(),
                    focusedBorder: OutlineInputBorder(
                      borderSide: BorderSide(color: MantotaColors.teal, width: 2),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                const Text('Entrez le code à 4 chiffres reçu lors de votre commande.', style: TextStyle(fontSize: 11, color: MantotaColors.grey4)),
                const SizedBox(height: 20),
                Row(
                  children: [
                    TextButton(
                      onPressed: processing ? null : () => Navigator.pop(ctx),
                      child: const Text('Annuler'),
                    ),
                    const Spacer(),
                    ElevatedButton(
                      onPressed: processing ? null : () async {
                        final pin = pinCtrl.text.trim();
                        if (pin.length != 4) {
                          ScaffoldMessenger.of(ctx).showSnackBar(
                            const SnackBar(content: Text('Le code doit avoir 4 chiffres.')),
                          );
                          return;
                        }
                        setState(() => processing = true);
                        try {
                          final svc = await ref.read(orderServiceProvider.future);
                          await svc.confirmDelivery(widget.orderId, pin);
                          if (ctx.mounted) {
                            Navigator.pop(ctx);
                            ref.invalidate(orderTrackProvider(widget.orderId));
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Réception confirmée. Fonds libérés au vendeur.'),
                                backgroundColor: MantotaColors.teal,
                              ),
                            );
                          }
                        } catch (e) {
                          if (ctx.mounted) {
                            ScaffoldMessenger.of(ctx).showSnackBar(
                              SnackBar(content: Text('Erreur: $e'), backgroundColor: MantotaColors.coral),
                            );
                          }
                        } finally {
                          if (ctx.mounted) setState(() => processing = false);
                        }
                      },
                      child: processing
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Text('Je confirme'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFallback(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.cloud_off, size: 48, color: MantotaColors.grey3),
          const SizedBox(height: 12),
          const Text('Suivi indisponible', style: TextStyle(fontSize: 16, color: MantotaColors.grey2)),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () => ref.refresh(orderTrackProvider(widget.orderId)),
            child: const Text('Réessayer'),
          ),
        ],
      ),
    );
  }

  String _statusEmoji(String status) {
    return switch (status) {
      'pending' => '⏳',
      'shipped' => '🚚',
      'delivered' => '✅',
      'disputed' => '⚠️',
      'cancelled' => '❌',
      _ => '📦',
    };
  }

  String _statusLabel(String status) {
    return switch (status) {
      'pending' => 'En attente',
      'shipped' => 'En cours de livraison',
      'delivered' => 'Livré',
      'disputed' => 'Litige en cours',
      'cancelled' => 'Annulée',
      _ => 'En cours',
    };
  }

  _StepStatus _mapStepStatus(String status) {
    return switch (status) {
      'done' => _StepStatus.done,
      'active' => _StepStatus.active,
      'disputed' => _StepStatus.active,
      'cancelled' => _StepStatus.pending,
      _ => _StepStatus.pending,
    };
  }

  String _formatTime(String? isoDate) {
    if (isoDate == null) return '--:--';
    try {
      final dt = DateTime.parse(isoDate);
      return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return '--:--';
    }
  }

  String _formatDate(String isoDate) {
    try {
      final dt = DateTime.parse(isoDate);
      return '${dt.day}/${dt.month} avant ${dt.hour}h';
    } catch (_) {
      return 'à venir';
    }
  }

  String _initials(String name) {
    final parts = name.split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  }
}

enum _StepStatus { done, active, pending }

class _TimelineStep extends StatelessWidget {
  final String label;
  final String detail;
  final String time;
  final _StepStatus status;
  final bool isLast;

  const _TimelineStep({
    required this.label,
    this.detail = '',
    required this.time,
    required this.status,
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    final isDone = status == _StepStatus.done;
    final isActive = status == _StepStatus.active;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Column(
          children: [
            Container(
              width: 20, height: 20,
              decoration: BoxDecoration(
                color: isDone ? MantotaColors.teal : (isActive ? MantotaColors.teal : MantotaColors.surface3),
                shape: BoxShape.circle,
                border: isActive ? Border.all(color: MantotaColors.teal.withValues(alpha: 0.3), width: 3) : null,
              ),
              child: isDone ? const Icon(Icons.check, color: Colors.white, size: 12) : null,
            ),
            if (!isLast)
              Container(
                width: 2, height: 28,
                color: isDone ? MantotaColors.teal.withValues(alpha: 0.4) : MantotaColors.surface3,
              ),
          ],
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Padding(
            padding: EdgeInsets.only(bottom: isLast ? 0 : 28),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      label,
                      style: TextStyle(
                        fontSize: 14, fontWeight: FontWeight.w600,
                        color: isDone || isActive ? MantotaColors.grey1 : MantotaColors.grey4,
                      ),
                    ),
                    Text(
                      time,
                      style: TextStyle(
                        fontSize: 12,
                        color: isActive ? MantotaColors.teal : MantotaColors.grey2,
                      ),
                    ),
                  ],
                ),
                if (detail.isNotEmpty) ...[
                  const SizedBox(height: 2),
                  Text(detail, style: const TextStyle(fontSize: 11, color: MantotaColors.grey2)),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}
