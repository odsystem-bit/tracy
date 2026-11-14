import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/widgets/tracy_avatar.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran 07c — Négociation.
///
/// Tracy négocie avec le vendeur. L'acheteur voit la contre-offre
/// et choisit : accepter, refuser ou relancer.
class NegotiationScreen extends ConsumerStatefulWidget {
  const NegotiationScreen({super.key});

  @override
  ConsumerState<NegotiationScreen> createState() => _NegotiationScreenState();
}

class _NegotiationScreenState extends ConsumerState<NegotiationScreen> {
  bool _negotiating = false;
  bool _showOffer = false;
  String _offerText = '';

  @override
  void initState() {
    super.initState();
    _startNegotiation();
  }

  void _startNegotiation() async {
    setState(() => _negotiating = true);
    try {
      final svc = await ref.read(tracyChatServiceProvider.future);
      final result = await svc.negotiate(productId: 'air-max-270', offeredPrice: 35000);
      if (mounted) {
        setState(() {
          _negotiating = false;
          _showOffer = true;
          _offerText = result.message;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _negotiating = false;
          _showOffer = true;
          _offerText = 'Le vendeur propose 38 000 F (−6%). C\'est son meilleur prix. Ça vous va ?';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
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
                Text(
                  _negotiating ? 'Négociation active' : 'Contre-offre reçue',
                  style: TextStyle(fontSize: 11, color: MantotaColors.teal),
                ),
              ],
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(12),
              children: [
                // User message
                _UserBubble(text: 'Je veux la Air Max 270, mais 40 500 c\'est cher. Tu peux faire 35 000 ?', time: '10:05'),
                const SizedBox(height: 8),
                // Tracy consulting
                _TracyBubble(text: 'Je consulte le vendeur… ⏳', time: '10:05'),
                const SizedBox(height: 8),
                if (_negotiating)
                  _TracyBubble(text: '⏳ En attente de la réponse du vendeur…', time: '10:06'),
                if (_showOffer) ...[
                  _TracyOfferBubble(
                    text: _offerText,
                    time: '10:06',
                  ),
                  const SizedBox(height: 12),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Wrap(
                      spacing: 8, runSpacing: 8,
                      alignment: WrapAlignment.center,
                      children: [
                        _ActionButton(
                          label: '✓ J\'accepte',
                          color: MantotaColors.teal,
                          textColor: Colors.white,
                          onTap: () => context.go('/order-recap'),
                        ),
                        _ActionButton(
                          label: '✗ Non merci',
                          color: MantotaColors.surface2,
                          textColor: MantotaColors.grey3,
                          onTap: () => context.pop(),
                        ),
                        _ActionButton(
                          label: '↩ Contre-offre',
                          color: MantotaColors.surface2,
                          textColor: MantotaColors.grey3,
                          onTap: () => setState(() { _showOffer = false; _startNegotiation(); }),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _UserBubble extends StatelessWidget {
  final String text;
  final String time;

  const _UserBubble({required this.text, required this.time});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        Flexible(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: MantotaColors.teal,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(16),
                bottomLeft: Radius.circular(16),
              ),
            ),
            child: Text(text, style: const TextStyle(fontSize: 14, color: Colors.white)),
          ),
        ),
      ],
    );
  }
}

class _TracyBubble extends StatelessWidget {
  final String text;
  final String time;

  const _TracyBubble({required this.text, required this.time});

  @override
  Widget build(BuildContext context) {
    return Column(
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
          child: Text(text, style: const TextStyle(fontSize: 14, color: MantotaColors.grey1)),
        ),
        const SizedBox(height: 2),
        Text(time, style: const TextStyle(fontSize: 10, color: MantotaColors.grey4)),
      ],
    );
  }
}

class _TracyOfferBubble extends StatelessWidget {
  final String text;
  final String time;

  const _TracyOfferBubble({required this.text, required this.time});

  @override
  Widget build(BuildContext context) {
    return Column(
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
            color: MantotaColors.tealPale,
            border: Border.all(color: MantotaColors.teal.withValues(alpha: 0.2)),
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(16),
              topRight: Radius.circular(16),
              bottomRight: Radius.circular(16),
            ),
          ),
          child: RichText(
            text: TextSpan(
              style: const TextStyle(fontSize: 14, color: MantotaColors.grey1),
              children: [
                const TextSpan(text: 'Le vendeur propose '),
                TextSpan(text: '38 000 F', style: const TextStyle(fontWeight: FontWeight.w800, color: MantotaColors.teal)),
                const TextSpan(text: ' (−6%). C\'est son meilleur prix. Ça vous va ?'),
              ],
            ),
          ),
        ),
        const SizedBox(height: 2),
        Text(time, style: const TextStyle(fontSize: 10, color: MantotaColors.grey4)),
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
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(20)),
        child: Text(label, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: textColor)),
      ),
    );
  }
}
