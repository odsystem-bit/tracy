import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/providers/providers.dart';
import '../../../core/widgets/tracy_avatar.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/adinkra_background.dart';

/// Écran 07e — Confirmation paiement.
///
/// Succès de paiement. N° commande affiché. Fonds en séquestre.
/// Tracy notifie le vendeur automatiquement.
class PaymentConfirmationScreen extends ConsumerWidget {
  const PaymentConfirmationScreen({super.key, required this.orderId});

  final String orderId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final orderAsync = ref.watch(orderDetailProvider(orderId));

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.go('/chats'),
        ),
        title: Row(
          children: [
            TracyAvatar(size: 32, borderRadius: 16),
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Tracy', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
                Text('Paiement validé', style: TextStyle(fontSize: 11, color: MantotaColors.teal)),
              ],
            ),
          ],
        ),
      ),
      body: Stack(
        children: [
          const AdinkraBackground(opacity: 0.04),
          orderAsync.when(
        data: (order) => _buildContent(context, order.formattedTotal, order.reference),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(30),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 40, color: MantotaColors.grey4),
                const SizedBox(height: 12),
                const Text('Commande introuvable', style: TextStyle(fontSize: 14, color: MantotaColors.grey3)),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => context.go('/orders'),
                  child: const Text('Voir mes commandes'),
                ),
              ],
            ),
          ),
        ),
      ),
        ],
      ),
    );
  }

  Widget _buildContent(BuildContext context, String total, String reference) {
    return ListView(
      padding: const EdgeInsets.all(12),
      children: [
        // Success card
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 6, height: 6,
                  decoration: const BoxDecoration(color: MantotaColors.teal, shape: BoxShape.circle),
                ),
                const SizedBox(width: 4),
                const Text('Tracy', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: MantotaColors.teal)),
              ],
            ),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: MantotaColors.tealPale,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(16),
                  topRight: Radius.circular(16),
                  bottomRight: Radius.circular(16),
                ),
              ),
              child: Column(
                children: [
                  const Text('✅', style: TextStyle(fontSize: 36)),
                  const SizedBox(height: 8),
                  const Text('Paiement confirmé !', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: MantotaColors.teal)),
                  const SizedBox(height: 6),
                  Text('$total débités · MTN MoMo ****47', style: const TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                  const SizedBox(height: 10),
                  Text('N° commande : #$reference', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: MantotaColors.grey1)),
                  const SizedBox(height: 4),
                  const Text('Fonds en séquestre jusqu\'à réception', style: TextStyle(fontSize: 12, color: MantotaColors.grey2)),
                ],
              ),
            ),
            const SizedBox(height: 2),
            const Text('10:10', style: TextStyle(fontSize: 10, color: MantotaColors.grey4)),
          ],
        ),
        const SizedBox(height: 8),
        // Tracy follow-up
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 6, height: 6,
                  decoration: const BoxDecoration(color: MantotaColors.teal, shape: BoxShape.circle),
                ),
                const SizedBox(width: 4),
                const Text('Tracy', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: MantotaColors.teal)),
              ],
            ),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: MantotaColors.surface1,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(16),
                  topRight: Radius.circular(16),
                  bottomRight: Radius.circular(16),
                ),
              ),
              child: const Text(
                'Le vendeur est notifié. Je vous tiendrai au courant de l\'expédition 📦',
                style: TextStyle(fontSize: 14, color: MantotaColors.grey1),
              ),
            ),
            const SizedBox(height: 2),
            const Text('10:10', style: TextStyle(fontSize: 10, color: MantotaColors.grey4)),
          ],
        ),
        const SizedBox(height: 24),
        // Escrow badge
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.amber.withValues(alpha: 0.08),
            border: Border.all(color: Colors.amber.withValues(alpha: 0.3)),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            children: [
              const Icon(Icons.lock, size: 18, color: Colors.amber),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Fonds en escrow — sécurisés',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Colors.amber[700]),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        // WhatsApp vendor contact
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () async {
              final uri = Uri.parse('https://wa.me/22900000000');
              if (await canLaunchUrl(uri)) {
                await launchUrl(uri, mode: LaunchMode.externalApplication);
              }
            },
            icon: const Icon(Icons.chat, size: 18, color: MantotaColors.whatsapp),
            label: const Text('Contacter le vendeur sur WhatsApp', style: TextStyle(color: MantotaColors.whatsapp)),
            style: OutlinedButton.styleFrom(
              side: BorderSide(color: MantotaColors.whatsapp.withValues(alpha: 0.3)),
              minimumSize: const Size(double.infinity, 48),
            ),
          ),
        ),
        const SizedBox(height: 24),
        // Actions
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () => context.go('/delivery/$orderId'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: MantotaColors.teal,
                  side: BorderSide(color: MantotaColors.teal.withValues(alpha: 0.3)),
                  minimumSize: const Size(double.infinity, 48),
                ),
                child: const Text('Suivre la livraison'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: ElevatedButton(
                onPressed: () => context.go('/chats'),
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 48),
                ),
                child: const Text('Retour aux chats'),
              ),
            ),
          ],
        ),
      ],
    );
  }
}
