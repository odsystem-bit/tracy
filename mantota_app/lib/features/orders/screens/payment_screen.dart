import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran 06 — Paiement.
///
/// Mobile Money + Wallet Mantota. Séquestre automatique.
class PaymentScreen extends ConsumerStatefulWidget {
  final String orderId;

  const PaymentScreen({super.key, required this.orderId});

  @override
  ConsumerState<PaymentScreen> createState() => _PaymentScreenState();
}

class _PaymentScreenState extends ConsumerState<PaymentScreen> {
  int _selectedMethod = 0;
  bool _isPaying = false;
  String? _errorMessage;

  final _methods = [
    _PaymentMethod(icon: '🟡', name: 'MTN Mobile Money', color: const Color(0xFF1A1800)),
    _PaymentMethod(icon: '🟠', name: 'Moov Money', color: const Color(0xFF1A0800)),
    _PaymentMethod(icon: '💳', name: 'Wallet Mantota', color: MantotaColors.tealPale),
  ];

  @override
  Widget build(BuildContext context) {
    final orderAsync = ref.watch(orderDetailProvider(widget.orderId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Paiement'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 12, top: 8, bottom: 8),
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: MantotaColors.tealPale,
              border: Border.all(color: MantotaColors.teal.withValues(alpha: 0.3)),
              borderRadius: BorderRadius.circular(6),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.lock, size: 12, color: MantotaColors.teal),
                SizedBox(width: 4),
                Text('SÉCURISÉ', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: MantotaColors.teal)),
              ],
            ),
          ),
        ],
      ),
      body: orderAsync.when(
        data: (order) => _buildBody(context, order.productName, order.formattedTotal, order.storeName ?? 'Boutique'),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, __) => _buildBody(context, 'Nike Air Max 270 — T.42', '40 500 FCFA', 'Boutique Stan'),
      ),
    );
  }

  Widget _buildBody(BuildContext context, String productName, String total, String storeName) {
    return Column(
        children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(14),
              children: [
                // Récap commande
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
                      Text('Commande #${widget.orderId}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: MantotaColors.grey2, letterSpacing: 1)),
                      const SizedBox(height: 6),
                      Text(productName, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                      const SizedBox(height: 2),
                      Text(storeName, style: const TextStyle(fontSize: 13, color: MantotaColors.teal)),
                      const SizedBox(height: 10),
                      Text(total, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w900, letterSpacing: -0.5)),
                      const SizedBox(height: 10),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                        decoration: BoxDecoration(
                          color: MantotaColors.tealPale,
                          border: Border.all(color: MantotaColors.teal.withValues(alpha: 0.2)),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Row(
                          children: [
                            Icon(Icons.lock_outline, size: 14, color: MantotaColors.teal),
                            SizedBox(width: 6),
                            Expanded(
              child: Text(
                                'Fonds bloqués jusqu\'à confirmation de réception',
                                style: TextStyle(fontSize: 12, color: MantotaColors.teal),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                // Mode de paiement
                const Text('MODE DE PAIEMENT', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.5, color: MantotaColors.grey2)),
                const SizedBox(height: 10),
                ...List.generate(_methods.length, (i) {
                  final m = _methods[i];
                  final selected = _selectedMethod == i;
                  return GestureDetector(
                    onTap: () => setState(() => _selectedMethod = i),
                    child: Container(
                      margin: const EdgeInsets.only(bottom: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 12),
                      decoration: BoxDecoration(
                        color: selected ? MantotaColors.tealPale : MantotaColors.surface1,
                        border: Border.all(
                          color: selected ? MantotaColors.teal.withValues(alpha: 0.4) : MantotaColors.surface3,
                        ),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 32, height: 32,
                            decoration: BoxDecoration(color: m.color, borderRadius: BorderRadius.circular(8)),
                            child: Center(child: Text(m.icon, style: const TextStyle(fontSize: 16))),
                          ),
                          const SizedBox(width: 10),
                          Expanded(child: Text(m.name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600))),
                          if (selected)
                            const Icon(Icons.check_circle, color: MantotaColors.teal, size: 18)
                          else
                            const Icon(Icons.radio_button_unchecked, color: MantotaColors.grey4, size: 18),
                        ],
                      ),
                    ),
                  );
                }),
                const SizedBox(height: 16),
                // Info Moneroo
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: MantotaColors.surface1,
                    border: Border.all(color: MantotaColors.surface3),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.shield_outlined, size: 16, color: MantotaColors.grey2),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Paiement sécurisé via Moneroo. Tous les moyens Mobile Money sont supportés.',
                          style: TextStyle(fontSize: 12, color: MantotaColors.grey2),
                        ),
                      ),
                    ],
                  ),
                ),
                if (_errorMessage != null) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.red.withValues(alpha: 0.1),
                      border: Border.all(color: Colors.red.withValues(alpha: 0.3)),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.error_outline, color: Colors.red, size: 18),
                        const SizedBox(width: 8),
                        Expanded(child: Text(_errorMessage!, style: const TextStyle(fontSize: 13, color: Colors.red))),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
          // CTA
          Container(
            padding: const EdgeInsets.fromLTRB(14, 8, 14, 16),
            decoration: const BoxDecoration(
              border: Border(top: BorderSide(color: MantotaColors.border)),
            ),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isPaying ? null : _pay,
                style: ElevatedButton.styleFrom(
                  backgroundColor: MantotaColors.coral,
                  foregroundColor: Colors.white,
                  minimumSize: const Size(double.infinity, 50),
                ),
                child: _isPaying
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.lock, size: 16),
                          const SizedBox(width: 6),
                          Text('Payer $total'),
                        ],
                      ),
              ),
            ),
          ),
        ],
      );
  }

  void _pay() async {
    setState(() {
      _isPaying = true;
      _errorMessage = null;
    });

    try {
      final paymentSvc = await ref.read(paymentServiceProvider.future);
      final result = await paymentSvc.initOrderPayment(widget.orderId);

      if (result.checkoutUrl != null && result.checkoutUrl!.isNotEmpty) {
        final uri = Uri.parse(result.checkoutUrl!);
        if (await canLaunchUrl(uri)) {
          await launchUrl(uri, mode: LaunchMode.inAppBrowserView);
          setState(() => _isPaying = false);
          if (mounted) {
            _showPaymentWaitingDialog(result.reference);
          }
        } else {
          setState(() {
            _isPaying = false;
            _errorMessage = 'Impossible d\'ouvrir la page de paiement.';
          });
        }
      } else {
        setState(() => _isPaying = false);
        if (mounted) {
          context.go('/payment/confirm/${widget.orderId}');
        }
      }
    } catch (e) {
      setState(() {
        _isPaying = false;
        _errorMessage = 'Erreur de paiement: $e';
      });
    }
  }

  void _showPaymentWaitingDialog(String reference) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.hourglass_top, color: MantotaColors.teal),
            SizedBox(width: 8),
            Text('Paiement en cours', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Une page de paiement s\'est ouverte dans votre navigateur.', style: TextStyle(fontSize: 14)),
            const SizedBox(height: 8),
            Text('Référence: $reference', style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
            const SizedBox(height: 12),
            const Text('Cliquez sur « J\'ai payé » une fois le paiement effectué.', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              context.go('/payment/confirm/${widget.orderId}');
            },
            child: const Text('J\'ai payé', style: TextStyle(color: MantotaColors.teal)),
          ),
        ],
      ),
    );
  }
}

class _PaymentMethod {
  final String icon;
  final String name;
  final Color color;

  const _PaymentMethod({required this.icon, required this.name, required this.color});
}
