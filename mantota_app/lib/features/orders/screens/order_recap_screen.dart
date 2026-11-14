import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/widgets/tracy_avatar.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran 07d — Récap commande.
///
/// Tracy résume : produit, prix négocié, frais livraison, adresse.
/// L'acheteur confirme ou modifie avant paiement.
class OrderRecapScreen extends ConsumerWidget {
  const OrderRecapScreen({super.key, required this.orderId});

  final String orderId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final orderAsync = ref.watch(orderDetailProvider(orderId));

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
        title: Row(
          children: [
            TracyAvatar(size: 32, borderRadius: 16),
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Tracy', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
                Text('Récapitulatif', style: TextStyle(fontSize: 11, color: MantotaColors.teal)),
              ],
            ),
          ],
        ),
      ),
      body: orderAsync.when(
        data: (order) => _buildContent(context, order.productName, order.formattedTotal, order.deliveryAddress ?? 'Cotonou, Fidjrossè'),
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
    );
  }

  Widget _buildContent(BuildContext context, String productName, String total, String address) {
    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(12),
            children: [
              // Tracy recap bubble
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
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('📋 Récapitulatif commande', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
                        const SizedBox(height: 10),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('👟 $productName', style: const TextStyle(fontSize: 14, height: 1.6)),
                              const SizedBox(height: 4),
                              Text.rich(
                                TextSpan(
                                  style: const TextStyle(fontSize: 14, height: 1.6),
                                  children: [
                                    const TextSpan(text: '💰 Prix négocié : '),
                                    TextSpan(text: total, style: const TextStyle(fontWeight: FontWeight.w800, color: MantotaColors.teal)),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 4),
                              const Text.rich(
                                TextSpan(
                                  style: TextStyle(fontSize: 14, height: 1.6),
                                  children: [
                                    TextSpan(text: '🚚 Livraison : '),
                                    TextSpan(text: '2 000 F', style: TextStyle(fontWeight: FontWeight.w700)),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 8),
                              const Divider(),
                              const SizedBox(height: 4),
                              Text.rich(
                                TextSpan(
                                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
                                  children: [
                                    const TextSpan(text: 'Total : '),
                                    TextSpan(text: total, style: const TextStyle(color: MantotaColors.teal)),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text('📍 Livraison à : $address', style: const TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 2),
                  const Text('10:08', style: TextStyle(fontSize: 10, color: MantotaColors.grey4)),
                ],
              ),
              const SizedBox(height: 16),
              // Actions
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Wrap(
                  spacing: 8, runSpacing: 8,
                  alignment: WrapAlignment.center,
                  children: [
                    _ActionButton(
                      label: 'Confirmer & Payer',
                      color: MantotaColors.teal,
                      textColor: Colors.white,
                      onTap: () => context.go('/payment/$orderId'),
                    ),
                    _ActionButton(
                      label: 'Modifier adresse',
                      color: MantotaColors.surface2,
                      textColor: MantotaColors.grey3,
                      onTap: () {},
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ActionButton extends StatelessWidget {
  final String label;
  final Color color;
  final Color textColor;
  final VoidCallback onTap;

  const _ActionButton({required this.label, required this.color, required this.textColor, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
        decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(20)),
        child: Text(label, style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: textColor)),
      ),
    );
  }
}
