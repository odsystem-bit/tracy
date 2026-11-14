import 'dart:convert';
import 'dart:io';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/providers/providers.dart';
import '../../../core/services/tracy_chat_service.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/adinkra_background.dart';

/// Écran de conformité post-livraison.
///
/// Après livraison, Tracy demande au client si le produit correspond à la photo.
/// Le client peut : confirmer (conform), signaler partiel, ou signaler non conforme.
/// Si non conforme, le client envoie une photo du produit reçu pour comparaison CLIP.
class ConformityScreen extends ConsumerStatefulWidget {
  final String orderId;
  final int productId;
  final int storeId;
  final String productName;
  final String? catalogImageUrl;

  const ConformityScreen({
    super.key,
    required this.orderId,
    required this.productId,
    required this.storeId,
    required this.productName,
    this.catalogImageUrl,
  });

  @override
  ConsumerState<ConformityScreen> createState() => _ConformityScreenState();
}

class _ConformityScreenState extends ConsumerState<ConformityScreen> {
  final _imagePicker = ImagePicker();
  String? _selectedVerdict;
  String? _receivedPhotoPath;
  String? _receivedPhotoBase64;
  bool _submitting = false;
  ConformityResult? _result;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 22),
          onPressed: () => context.pop(),
        ),
        title: const Text('Conformité produit', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
      ),
      body: Stack(
        children: [
          const AdinkraBackground(opacity: 0.03),
          SafeArea(
            child: _result != null ? _buildResult(context) : _buildForm(context),
          ),
        ],
      ),
    );
  }

  Widget _buildForm(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: MantotaColors.tealPale,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              children: [
                const Icon(Icons.inventory_2_outlined, color: MantotaColors.teal, size: 28),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(widget.productName, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: MantotaColors.grey1)),
                      Text('Commande #${widget.orderId}', style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
                    ],
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 24),

          // Catalog image
          if (widget.catalogImageUrl != null) ...[
            const Text('Photo du catalogue', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: MantotaColors.grey1)),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: CachedNetworkImage(
                imageUrl: widget.catalogImageUrl!,
                height: 200,
                width: double.infinity,
                fit: BoxFit.cover,
                placeholder: (_, __) => Container(height: 200, color: MantotaColors.surface1),
                errorWidget: (_, __, ___) => Container(height: 200, color: MantotaColors.surface1, child: const Icon(Icons.image, size: 40, color: MantotaColors.grey3)),
              ),
            ),
            const SizedBox(height: 24),
          ],

          // Question
          const Text(
            'Le produit reçu correspond-il à la photo ?',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: MantotaColors.grey1),
          ),
          const SizedBox(height: 16),

          // Verdict options
          _VerdictOption(
            label: 'Conforme',
            description: 'Le produit correspond à la photo',
            icon: Icons.check_circle_outline,
            color: MantotaColors.teal,
            isSelected: _selectedVerdict == 'conform',
            onTap: () => setState(() => _selectedVerdict = 'conform'),
          ),
          const SizedBox(height: 10),
          _VerdictOption(
            label: 'Partiellement conforme',
            description: 'Quelques différences mineures',
            icon: Icons.error_outline,
            color: Colors.amber.shade600,
            isSelected: _selectedVerdict == 'partial',
            onTap: () => setState(() => _selectedVerdict = 'partial'),
          ),
          const SizedBox(height: 10),
          _VerdictOption(
            label: 'Non conforme',
            description: 'Le produit ne correspond pas à la photo',
            icon: Icons.cancel_outlined,
            color: Colors.red.shade400,
            isSelected: _selectedVerdict == 'non_conform',
            onTap: () => setState(() => _selectedVerdict = 'non_conform'),
          ),

          // Photo upload for non-conform
          if (_selectedVerdict == 'non_conform' || _selectedVerdict == 'partial') ...[
            const SizedBox(height: 24),
            const Text(
              'Photo du produit reçu',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: MantotaColors.grey1),
            ),
            const SizedBox(height: 4),
            const Text(
              'Tracy va comparer cette photo avec le catalogue',
              style: TextStyle(fontSize: 12, color: MantotaColors.grey2),
            ),
            const SizedBox(height: 12),
            GestureDetector(
              onTap: _pickReceivedPhoto,
              child: Container(
                height: 160,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: MantotaColors.surface1,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: MantotaColors.surface3, width: 1),
                ),
                child: _receivedPhotoPath != null
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.file(File(_receivedPhotoPath!), fit: BoxFit.cover),
                      )
                    : Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.camera_alt_outlined, size: 36, color: MantotaColors.grey3),
                          const SizedBox(height: 8),
                          Text('Prendre / choisir une photo', style: TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                        ],
                      ),
              ),
            ),
          ],

          const SizedBox(height: 32),

          // Submit button
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton(
              onPressed: _selectedVerdict == null || _submitting
                  ? null
                  : _submitConformity,
              style: ElevatedButton.styleFrom(
                backgroundColor: MantotaColors.teal,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                disabledBackgroundColor: MantotaColors.surface3,
              ),
              child: _submitting
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Envoyer mon retour', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResult(BuildContext context) {
    final isPositive = _result!.success && _selectedVerdict == 'conform';
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80, height: 80,
            decoration: BoxDecoration(
              color: isPositive ? MantotaColors.teal.withValues(alpha: 0.1) : Colors.red.withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: Icon(
              isPositive ? Icons.check_circle : Icons.info_outline,
              size: 40,
              color: isPositive ? MantotaColors.teal : Colors.red.shade400,
            ),
          ),
          const SizedBox(height: 20),
          Text(
            isPositive ? 'Merci pour votre retour !' : 'Retour enregistré',
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: MantotaColors.grey1),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          Text(
            _result!.messageToClient.isNotEmpty
                ? _result!.messageToClient
                : isPositive
                    ? 'Votre confirmation aide la boutique à maintenir la qualité.'
                    : 'Tracy a notifié le vendeur. Si nécessaire, un administrateur examinera le cas.',
            style: const TextStyle(fontSize: 14, color: MantotaColors.grey2, height: 1.5),
            textAlign: TextAlign.center,
          ),
          if (_result!.photoSimilarity != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: MantotaColors.surface1,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                'Similarité photo: ${(_result!.photoSimilarity! * 100).round()}%',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: _result!.photoSimilarity! >= 0.75 ? MantotaColors.teal : Colors.red.shade400,
                ),
              ),
            ),
          ],
          const SizedBox(height: 32),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton(
              onPressed: () => context.go('/orders'),
              style: ElevatedButton.styleFrom(
                backgroundColor: MantotaColors.teal,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text('Mes commandes', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _pickReceivedPhoto() async {
    final picked = await _imagePicker.pickImage(source: ImageSource.camera, maxWidth: 1024, imageQuality: 85);
    if (picked == null) return;

    final bytes = await File(picked.path).readAsBytes();
    setState(() {
      _receivedPhotoPath = picked.path;
      _receivedPhotoBase64 = base64Encode(bytes);
    });
  }

  Future<void> _submitConformity() async {
    if (_selectedVerdict == null) return;

    setState(() => _submitting = true);

    try {
      final svc = await ref.read(tracyChatServiceProvider.future);
      final result = await svc.checkConformity(
        orderId: widget.orderId,
        productId: widget.productId,
        storeId: widget.storeId,
        verdict: _selectedVerdict!,
        receivedPhotoBase64: _receivedPhotoBase64,
        catalogPhotoBase64: null,
      );

      if (mounted) {
        setState(() {
          _result = result;
          _submitting = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _submitting = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Erreur. Réessayez plus tard.'), backgroundColor: Colors.red),
        );
      }
    }
  }
}

class _VerdictOption extends StatelessWidget {
  final String label;
  final String description;
  final IconData icon;
  final Color color;
  final bool isSelected;
  final VoidCallback onTap;

  const _VerdictOption({
    required this.label,
    required this.description,
    required this.icon,
    required this.color,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? color.withValues(alpha: 0.08) : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected ? color : MantotaColors.surface3,
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: isSelected ? color : MantotaColors.grey1)),
                  Text(description, style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
                ],
              ),
            ),
            if (isSelected)
              Icon(Icons.check_circle, color: color, size: 22),
          ],
        ),
      ),
    );
  }
}
