import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran Litige — Ouvrir un litige sur une commande.
///
/// L'acheteur décrit le problème, Tracy transmet à l'admin MANTOTA.
class DisputeScreen extends ConsumerStatefulWidget {
  final String orderId;

  const DisputeScreen({super.key, required this.orderId});

  @override
  ConsumerState<DisputeScreen> createState() => _DisputeScreenState();
}

class _DisputeScreenState extends ConsumerState<DisputeScreen> {
  final _reasonController = TextEditingController();
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    _reasonController.dispose();
    super.dispose();
  }

  void _submitDispute() async {
    if (_reasonController.text.trim().length < 10) {
      setState(() => _errorMessage = 'Décrivez le problème (min. 10 caractères).');
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      final api = await ref.read(apiClientProvider.future);
      await api.post('/orders/${widget.orderId}/dispute', data: {
        'reason': _reasonController.text.trim(),
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Litige ouvert. L\'équipe MANTOTA va examiner votre réclamation.'),
            backgroundColor: MantotaColors.teal,
          ),
        );
        context.go('/orders/${widget.orderId}');
      }
    } catch (e) {
      setState(() {
        _isSubmitting = false;
        _errorMessage = 'Erreur: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ouvrir un litige'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Warning banner
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.orange.withValues(alpha: 0.1),
              border: Border.all(color: Colors.orange.withValues(alpha: 0.3)),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Row(
              children: [
                Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 24),
                SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Les fonds restent bloqués en séquestre pendant le litige. '
                    'L\'équipe MANTOTA tranchera sous 48h.',
                    style: TextStyle(fontSize: 13, color: Colors.orange),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          // Order info
          Text('Commande #${widget.orderId}',
              style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: MantotaColors.grey2,
                  letterSpacing: 1)),
          const SizedBox(height: 16),
          // Reason input
          const Text('Décrivez le problème',
              style: TextStyle(
                  fontSize: 14, fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          const Text(
            'Soyez précis : produit non conforme, non livré, endommagé, etc.',
            style: TextStyle(fontSize: 12, color: MantotaColors.grey2),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _reasonController,
            maxLines: 6,
            decoration: InputDecoration(
              hintText: 'Ex: Le produit reçu ne correspond pas à la description. '
                  'J\'ai commandé une paire Nike Air Max taille 42 mais j\'ai reçu une taille 40...',
              hintStyle: const TextStyle(fontSize: 13, color: MantotaColors.grey4),
              filled: true,
              fillColor: MantotaColors.surface1,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: MantotaColors.surface3),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: MantotaColors.teal.withValues(alpha: 0.4)),
              ),
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
                  Expanded(child: Text(_errorMessage!,
                      style: const TextStyle(fontSize: 13, color: Colors.red))),
                ],
              ),
            ),
          ],
          const SizedBox(height: 24),
          // Quick reasons
          const Text('RAISONS FRÉQUENTES',
              style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.5,
                  color: MantotaColors.grey2)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _QuickReason(
                label: 'Produit non reçu',
                onTap: () => _reasonController.text =
                    'Produit non reçu. La commande n\'a pas été livrée dans les délais annoncés.',
              ),
              _QuickReason(
                label: 'Produit non conforme',
                onTap: () => _reasonController.text =
                    'Produit non conforme à la description. Le produit reçu ne correspond pas à ce qui était annoncé.',
              ),
              _QuickReason(
                label: 'Produit endommagé',
                onTap: () => _reasonController.text =
                    'Produit reçu endommagé. L\'emballage ou le produit lui-même présente des dommages.',
              ),
              _QuickReason(
                label: 'Taille incorrecte',
                onTap: () => _reasonController.text =
                    'Taille incorrecte. Le produit reçu ne correspond pas à la taille commandée.',
              ),
            ],
          ),
          const SizedBox(height: 24),
          // Submit
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _isSubmitting ? null : _submitDispute,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
                foregroundColor: Colors.white,
                minimumSize: const Size(double.infinity, 50),
              ),
              child: _isSubmitting
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.gavel, size: 16),
                        SizedBox(width: 6),
                        Text('Ouvrir le litige'),
                      ],
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

class _QuickReason extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const _QuickReason({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: MantotaColors.surface1,
          border: Border.all(color: MantotaColors.surface3),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(label,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: MantotaColors.grey2)),
      ),
    );
  }
}
