import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/models/user.dart';
import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran 15e — Onboarding Choix des modes.
///
/// L'utilisateur choisit quels modes activer : Buyer (toujours actif),
/// Vendeur, Partenaire. Les modes sont sauvegardés dans [currentUserProvider].
class ModeSelectionScreen extends ConsumerStatefulWidget {
  const ModeSelectionScreen({super.key});

  @override
  ConsumerState<ModeSelectionScreen> createState() => _ModeSelectionScreenState();
}

class _ModeSelectionScreenState extends ConsumerState<ModeSelectionScreen> {
  bool _isVendor = false;
  bool _isPartner = false;
  bool _saving = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Spacer(flex: 1),
              const Text('Choisissez vos modes',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              const Text(
                'Vous pouvez changer à tout moment dans votre profil.',
                style: TextStyle(fontSize: 13, color: MantotaColors.grey2),
              ),
              const SizedBox(height: 32),
              _ModeCard(
                icon: Icons.shopping_bag_outlined,
                title: 'Acheteur',
                subtitle: 'Discuter avec Tracy, découvrir des produits, commander',
                isActive: true,
                canToggle: false,
                onChanged: (_) {},
              ),
              const SizedBox(height: 12),
              _ModeCard(
                icon: Icons.store_outlined,
                title: 'Vendeur',
                subtitle: 'Créer ma boutique, vendre avec Tracy, gérer mes commandes',
                isActive: _isVendor,
                canToggle: true,
                onChanged: (v) => setState(() => _isVendor = v),
              ),
              const SizedBox(height: 12),
              _ModeCard(
                icon: Icons.campaign_outlined,
                title: 'Partenaire',
                subtitle: 'Promouvoir des produits, gagner des commissions',
                isActive: _isPartner,
                canToggle: true,
                onChanged: (v) => setState(() => _isPartner = v),
              ),
              const Spacer(flex: 2),
              ElevatedButton(
                onPressed: _saving ? null : _saveModes,
                child: _saving
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Text('Continuer'),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  void _saveModes() {
    setState(() => _saving = true);

    final user = ref.read(currentUserProvider);
    if (user != null) {
      final modes = [
        UserMode(mode: 'buyer', isActive: true, canDeactivate: false),
        UserMode(mode: 'vendor', isActive: _isVendor, canDeactivate: true),
        UserMode(mode: 'partner', isActive: _isPartner, canDeactivate: true),
      ];
      ref.read(currentUserProvider.notifier).state = User(
        id: user.id,
        name: user.name,
        displayName: user.displayName,
        phone: user.phone,
        avatarUrl: user.avatarUrl,
        modes: modes,
      );
    }

    setState(() => _saving = false);
    context.go('/chats');
  }
}

class _ModeCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final bool isActive;
  final bool canToggle;
  final ValueChanged<bool> onChanged;

  const _ModeCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.isActive,
    required this.canToggle,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isActive ? MantotaColors.tealPale : MantotaColors.surface1,
        borderRadius: BorderRadius.circular(14),
        border: isActive
            ? Border.all(color: MantotaColors.teal.withValues(alpha: 0.3), width: 1.5)
            : null,
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: isActive ? MantotaColors.teal : MantotaColors.surface3,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: Colors.white, size: 22),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                const SizedBox(height: 2),
                Text(subtitle,
                    style: const TextStyle(fontSize: 11, color: MantotaColors.grey2, height: 1.3)),
              ],
            ),
          ),
          if (canToggle)
            Switch.adaptive(
              value: isActive,
              onChanged: onChanged,
              activeTrackColor: MantotaColors.teal,
            )
          else
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: MantotaColors.teal,
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Text('Actif',
                  style: TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.w600)),
            ),
        ],
      ),
    );
  }
}
