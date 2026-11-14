import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/models/user.dart';
import '../../../core/providers/providers.dart';
import '../../../core/router/app_router.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/adinkra_background.dart';

/// Écran 15 — Profil & Modes (style WhatsApp Business).
///
/// En-tête avec photo, nom, téléphone, statut en ligne.
/// Stats rapides (commandes, wallet, note boutique).
/// Modes activés dynamiquement depuis [currentUserProvider].
/// Menu raccourcis vers Wallet, Commandes, Espace vendeur, etc.
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);

    final name = user?.bestName ?? 'Utilisateur';
    final phone = user?.phone ?? '+229 01 97 12 34 56';
    final avatarUrl = user?.avatarUrl;
    final modes = user?.modes ?? [
      UserMode(mode: 'buyer', isActive: true, canDeactivate: false),
      UserMode(mode: 'vendor', isActive: true, canDeactivate: true),
    ];
    final isVendor = modes.any((m) => m.mode == 'vendor' && m.isActive);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profil'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_outlined, size: 20),
            onPressed: () => _showEditDialog(context, ref, name),
          ),
        ],
      ),
      body: Stack(
        children: [
          const AdinkraBackground(opacity: 0.04),
          ListView(
        children: [
          // ── En-tête profil (style WhatsApp Business) ──
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
            child: Column(
              children: [
                Stack(
                  children: [
                    CircleAvatar(
                      radius: 48,
                      backgroundColor: MantotaColors.tealPale,
                      backgroundImage: avatarUrl != null ? NetworkImage(avatarUrl) : null,
                      child: avatarUrl == null
                          ? const Icon(Icons.person, color: MantotaColors.teal, size: 48)
                          : null,
                    ),
                    Positioned(
                      bottom: 0,
                      right: 0,
                      child: GestureDetector(
                        onTap: () => _showPhotoOptions(context),
                        child: Container(
                          width: 28, height: 28,
                          decoration: BoxDecoration(
                            color: MantotaColors.teal,
                            shape: BoxShape.circle,
                            border: Border.all(color: Colors.white, width: 2),
                          ),
                          child: const Icon(Icons.camera_alt, color: Colors.white, size: 14),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                Text(name, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
                const SizedBox(height: 4),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.phone, size: 14, color: MantotaColors.grey2),
                    const SizedBox(width: 6),
                    Text(phone, style: const TextStyle(fontSize: 14, color: MantotaColors.grey2)),
                  ],
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: MantotaColors.teal.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 8, height: 8,
                        decoration: const BoxDecoration(color: MantotaColors.teal, shape: BoxShape.circle),
                      ),
                      const SizedBox(width: 6),
                      const Text('En ligne', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: MantotaColors.teal)),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // ── Stats rapides ──
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14),
            child: Row(
              children: [
                _StatCard(
                  icon: Icons.receipt_long_outlined,
                  label: 'Commandes',
                  value: '—',
                  onTap: () => context.push('/orders'),
                ),
                const SizedBox(width: 10),
                _StatCard(
                  icon: Icons.account_balance_wallet_outlined,
                  label: 'Wallet',
                  value: '—',
                  onTap: () => context.push('/wallet'),
                ),
                const SizedBox(width: 10),
                if (isVendor)
                  _StatCard(
                    icon: Icons.star_outline,
                    label: 'Note',
                    value: '—',
                    onTap: () => context.push('/vendor/store'),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // ── Modes ──
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 14),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(14)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Mes modes', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                    Text('Actifs: ${modes.where((m) => m.isActive).length}', style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
                  ],
                ),
                const SizedBox(height: 10),
                ...modes.map((m) => _ModeChip(
                  icon: _iconForMode(m.mode),
                  label: _labelForMode(m.mode),
                  active: m.isActive,
                  canToggle: m.canDeactivate,
                  onToggle: m.canDeactivate
                      ? (v) => _toggleMode(context, ref, modes, m.mode, v)
                      : null,
                )),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // ── Menu ──
          _SectionLabel('Compte'),
          _MenuTile(icon: Icons.account_balance_wallet_outlined, title: 'Wallet', subtitle: 'Solde & transactions', onTap: () => context.push('/wallet')),
          _MenuTile(icon: Icons.receipt_long_outlined, title: 'Mes commandes', subtitle: 'Suivi & historique', onTap: () => context.push('/orders')),

          if (isVendor) ...[
            _SectionLabel('Vendeur'),
            _MenuTile(icon: Icons.store_outlined, title: 'Espace vendeur', subtitle: 'Dashboard & commandes', onTap: () => context.push('/vendor')),
            _MenuTile(icon: Icons.add_circle_outline, title: 'Ajouter produit', subtitle: 'Via Tracy ou manuel', onTap: () => context.push('/vendor/add-product')),
            _MenuTile(icon: Icons.workspace_premium_outlined, title: 'Abonnements', subtitle: 'Free, Starter, Standard, Pro', onTap: () => context.push('/vendor/subscriptions')),
            _MenuTile(icon: Icons.tune_outlined, title: 'Configurer Tracy', subtitle: 'Mode & personnalité', onTap: () => context.push('/vendor/tracy')),
            _MenuTile(icon: Icons.chat_outlined, title: 'Connecter WhatsApp', subtitle: 'Tracy sur WhatsApp', onTap: () => context.push('/vendor/whatsapp')),
          ],

          _SectionLabel('App'),
          _MenuTile(icon: Icons.notifications_outlined, title: 'Notifications', subtitle: 'Messages & alertes', onTap: () => context.push('/notifications')),
          _MenuTile(icon: Icons.settings_outlined, title: 'Paramètres', subtitle: 'Préférences & sécurité', onTap: () => context.push('/settings')),
          _MenuTile(icon: Icons.info_outline, title: 'À propos', subtitle: 'MANTOTA v1.0.0 • Web v2.0', onTap: () => _showAboutDialog(context)),
          _MenuTile(icon: Icons.privacy_tip_outlined, title: 'CGV & Confidentialité', subtitle: 'Conditions & politique', onTap: () => _showLegalInfo(context)),

          const SizedBox(height: 20),

          // ── Déconnexion ──
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14),
            child: OutlinedButton.icon(
              onPressed: () async {
                final auth = await ref.read(authServiceProvider.future);
                await auth.logout();
                ref.read(currentUserProvider.notifier).state = null;
                ref.read(authStateProvider.notifier).state = AuthState.unauthenticated;
                if (context.mounted) context.go('/login');
              },
              style: OutlinedButton.styleFrom(
                foregroundColor: MantotaColors.error,
                side: BorderSide(color: MantotaColors.error.withValues(alpha: 0.3)),
                minimumSize: const Size(double.infinity, 48),
              ),
              icon: const Icon(Icons.logout, size: 18),
              label: const Text('Déconnexion'),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
        ],
      ),
    );
  }

  IconData _iconForMode(String mode) {
    switch (mode) {
      case 'buyer': return Icons.shopping_bag_outlined;
      case 'vendor': return Icons.store_outlined;
      case 'partner': return Icons.campaign_outlined;
      default: return Icons.circle_outlined;
    }
  }

  String _labelForMode(String mode) {
    switch (mode) {
      case 'buyer': return 'Acheteur';
      case 'vendor': return 'Vendeur';
      case 'partner': return 'Partenaire';
      default: return mode;
    }
  }

  void _toggleMode(BuildContext context, WidgetRef ref, List<UserMode> modes, String mode, bool value) async {
    final updated = modes.map((m) {
      if (m.mode == mode) return UserMode(mode: m.mode, isActive: value, canDeactivate: m.canDeactivate);
      return m;
    }).toList();
    final user = ref.read(currentUserProvider);
    if (user != null) {
      ref.read(currentUserProvider.notifier).state = User(
        id: user.id,
        name: user.name,
        displayName: user.displayName,
        phone: user.phone,
        avatarUrl: user.avatarUrl,
        modes: updated,
      );
    }
    try {
      final svc = await ref.read(authServiceProvider.future);
      await svc.updateModes(mode: mode, active: value);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(value ? 'Mode ${_labelForMode(mode)} activé' : 'Mode ${_labelForMode(mode)} désactivé'),
          backgroundColor: MantotaColors.teal,
          duration: const Duration(seconds: 2),
        ),
      );
    } catch (e) {
      // Revert on error
      final reverted = modes.map((m) {
        if (m.mode == mode) return UserMode(mode: m.mode, isActive: !value, canDeactivate: m.canDeactivate);
        return m;
      }).toList();
      if (user != null) {
        ref.read(currentUserProvider.notifier).state = User(
          id: user.id,
          name: user.name,
          displayName: user.displayName,
          phone: user.phone,
          avatarUrl: user.avatarUrl,
          modes: reverted,
        );
      }
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erreur lors du changement de mode: $e'),
            backgroundColor: MantotaColors.error,
          ),
        );
      }
    }
  }

  void _showEditDialog(BuildContext context, WidgetRef ref, String currentName) {
    final controller = TextEditingController(text: currentName);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Modifier le nom'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(labelText: 'Nom affiché'),
          autofocus: true,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
          ElevatedButton(
            onPressed: () async {
              final newName = controller.text.trim();
              if (newName.isEmpty) return;
              Navigator.pop(ctx);
              try {
                final api = await ref.read(apiClientProvider.future);
                await api.patch('/user/profile', data: {'display_name': newName});
                final user = ref.read(currentUserProvider);
                if (user != null) {
                  ref.read(currentUserProvider.notifier).state = User(
                    id: user.id,
                    name: user.name,
                    displayName: newName,
                    phone: user.phone,
                    avatarUrl: user.avatarUrl,
                    modes: user.modes,
                  );
                }
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Profil mis à jour'),
                      backgroundColor: MantotaColors.teal,
                      duration: Duration(seconds: 2),
                    ),
                  );
                }
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Erreur: $e'),
                      backgroundColor: MantotaColors.error,
                    ),
                  );
                }
              }
            },
            child: const Text('Enregistrer'),
          ),
        ],
      ),
    );
  }

  void _showPhotoOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.photo_camera, color: MantotaColors.teal),
              title: const Text('Prendre une photo'),
              onTap: () { Navigator.pop(ctx); },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library, color: MantotaColors.teal),
              title: const Text('Choisir depuis la galerie'),
              onTap: () { Navigator.pop(ctx); },
            ),
          ],
        ),
      ),
    );
  }

  void _showAboutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('À propos'),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('MANTOTA', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            SizedBox(height: 8),
            Text('Version: 1.0.0'),
            Text('Plateforme e-commerce africaine'),
            SizedBox(height: 8),
            Text('Tracy IA — Assistante shopping'),
            Text('Web v2.0 • Mobile v1.0'),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Fermer')),
        ],
      ),
    );
  }

  void _showLegalInfo(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('CGV & Confidentialité'),
        content: const SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Conditions Générales de Vente', style: TextStyle(fontWeight: FontWeight.w700)),
              SizedBox(height: 8),
              Text('MANTOTA est une plateforme de mise en relation entre acheteurs et vendeurs. Les paiements sont sécurisés via Moneroo. Les fonds sont conservés en escrow jusqu\'à confirmation de réception.'),
              SizedBox(height: 12),
              Text('Politique de Confidentialité', style: TextStyle(fontWeight: FontWeight.w700)),
              SizedBox(height: 8),
              Text('Vos données personnelles (téléphone, nom) sont utilisées uniquement pour le fonctionnement de la plateforme. Elles ne sont jamais vendues à des tiers.'),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Fermer')),
        ],
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final VoidCallback onTap;

  const _StatCard({required this.icon, required this.label, required this.value, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            color: MantotaColors.surface1,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            children: [
              Icon(icon, color: MantotaColors.teal, size: 22),
              const SizedBox(height: 6),
              Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
              const SizedBox(height: 2),
              Text(label, style: const TextStyle(fontSize: 11, color: MantotaColors.grey2)),
            ],
          ),
        ),
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 14, 6),
      child: Text(text, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: MantotaColors.teal, letterSpacing: 0.5)),
    );
  }
}

class _ModeChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool active;
  final bool canToggle;
  final ValueChanged<bool>? onToggle;

  const _ModeChip({required this.icon, required this.label, required this.active, required this.canToggle, this.onToggle});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(icon, size: 20, color: active ? MantotaColors.teal : MantotaColors.grey4),
          const SizedBox(width: 10),
          Text(label, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500)),
          const Spacer(),
          if (canToggle && onToggle != null)
            Switch.adaptive(
              value: active,
              onChanged: onToggle,
              activeTrackColor: MantotaColors.teal,
            )
          else
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: MantotaColors.teal,
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Text('Actif', style: TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.w600)),
            ),
        ],
      ),
    );
  }
}

class _MenuTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _MenuTile({required this.icon, required this.title, required this.subtitle, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Container(
        width: 36, height: 36,
        decoration: BoxDecoration(
          color: MantotaColors.surface1,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, color: MantotaColors.teal, size: 18),
      ),
      title: Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
      trailing: const Icon(Icons.chevron_right, color: MantotaColors.grey4, size: 20),
      onTap: onTap,
    );
  }
}
