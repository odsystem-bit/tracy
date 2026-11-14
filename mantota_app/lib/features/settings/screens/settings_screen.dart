import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/adinkra_background.dart';

/// Écran 15d — Paramètres.
///
/// Paramètres de l'app : notifications, langue, confidentialité, à propos.
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final name = user?.bestName ?? 'Utilisateur';
    final phone = user?.phone ?? 'Non renseigné';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Paramètres'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: Stack(
        children: [
          const AdinkraBackground(opacity: 0.04),
          ListView(
        children: [
          const _SectionHeader('Compte'),
          _SettingTile(
            icon: Icons.person_outline,
            title: 'Informations personnelles',
            onTap: () => _showInfoDialog(context, name, phone),
          ),
          _SettingTile(
            icon: Icons.lock_outline,
            title: 'Confidentialité',
            onTap: () => _showSimpleDialog(context, 'Confidentialité', 'Gérez qui peut voir vos infos, votre photo et votre statut.'),
          ),
          _SettingTile(
            icon: Icons.shield_outlined,
            title: 'Sécurité',
            onTap: () => _showSimpleDialog(context, 'Sécurité', 'Vérification en 2 étapes et verrouillage biométrique seront disponibles prochainement.'),
          ),
          const _SectionHeader('Préférences'),
          _SettingTile(
            icon: Icons.notifications_outlined,
            title: 'Notifications',
            trailing: const Icon(Icons.chevron_right, color: MantotaColors.grey4, size: 20),
            onTap: () => context.push('/notifications'),
          ),
          _SettingTile(
            icon: Icons.language_outlined,
            title: 'Langue',
            trailing: const Text('Français', style: TextStyle(fontSize: 13, color: MantotaColors.grey2)),
            onTap: () => _showLanguageDialog(context),
          ),
          _SettingTile(
            icon: Icons.dark_mode_outlined,
            title: 'Thème sombre',
            trailing: Switch.adaptive(
              value: false,
              onChanged: null,
              activeTrackColor: MantotaColors.teal,
            ),
            onTap: () {},
          ),
          const _SectionHeader('Application'),
          _SettingTile(
            icon: Icons.info_outline,
            title: 'À propos de MANTOTA',
            trailing: const Text('v1.0.0', style: TextStyle(fontSize: 13, color: MantotaColors.grey2)),
            onTap: () => _showAboutDialog(context),
          ),
          _SettingTile(
            icon: Icons.description_outlined,
            title: 'Conditions générales de vente',
            onTap: () => _showSimpleDialog(context, 'Conditions générales de vente', "En utilisant MANTOTA, vous acceptez nos conditions générales de vente. L'utilisation de Tracy IA est soumise à nos politiques d'IA responsable. Paiement par séquestre (escrow), commission de transaction 2-5% sur chaque vente."),
          ),
          _SettingTile(
            icon: Icons.privacy_tip_outlined,
            title: 'Politique de confidentialité',
            onTap: () => _showSimpleDialog(context, 'Politique de confidentialité', 'Vos données sont protégées. Nous ne vendons jamais vos informations. Les conversations avec Tracy IA sont chiffrées. Données collectées : identification, connexion, conversations avec Tracy, transactions financières. Vous disposez d\'un droit d\'accès, rectification et suppression.'),
          ),
          _SettingTile(
            icon: Icons.headphones_outlined,
            title: 'Support & aide',
            onTap: () => _showSimpleDialog(context, 'Support & aide', 'Besoin d\'aide ?\n\nEmail : support@mantota.com\nWhatsApp : +229 01 97 12 34 56\n\nOu parlez à Tracy directement dans l\'app !'),
          ),
          const SizedBox(height: 20),
        ],
      ),
        ],
      ),
    );
  }

  void _showInfoDialog(BuildContext context, String name, String phone) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Informations personnelles', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
              const SizedBox(height: 16),
              ListTile(
                leading: const Icon(Icons.person, color: MantotaColors.teal),
                title: const Text('Nom affiché'),
                subtitle: Text(name),
              ),
              ListTile(
                leading: const Icon(Icons.phone, color: MantotaColors.teal),
                title: const Text('Téléphone'),
                subtitle: Text(phone),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Fermer'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showLanguageDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => SimpleDialog(
        title: const Text('Choisir la langue'),
        children: ['Français', 'English', 'Fon', 'Yoruba'].map((lang) =>
          SimpleDialogOption(
            onPressed: () => Navigator.pop(ctx),
            child: Row(
              children: [
                Text(lang, style: const TextStyle(fontSize: 15)),
                if (lang == 'Français') ...[
                  const Spacer(),
                  const Icon(Icons.check, color: MantotaColors.teal, size: 18),
                ],
              ],
            ),
          ),
        ).toList(),
      ),
    );
  }

  void _showAboutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Row(
          children: [
            Image.asset('assets/icons/mantota_logo.png', width: 32, height: 32),
            const SizedBox(width: 10),
            const Text('MANTOTA'),
          ],
        ),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text('App v1.0.0', style: TextStyle(fontWeight: FontWeight.w600)),
                SizedBox(width: 12),
                Text('Web v2.0', style: TextStyle(fontWeight: FontWeight.w600, color: MantotaColors.teal)),
              ],
            ),
            SizedBox(height: 12),
            Text('MANTOTA — Plateforme de e-commerce intelligente propulsée par Tracy IA.', style: TextStyle(color: MantotaColors.grey2)),
            SizedBox(height: 8),
            Text('Tracy IA : votre assistante commerciale qui discute, vend et négocie pour vous 24/7 sur l\'app et WhatsApp.', style: TextStyle(color: MantotaColors.grey2)),
            SizedBox(height: 8),
            Text('Acheteur gratuit, vendeur freemium (Free, Starter, Standard, Pro).', style: TextStyle(color: MantotaColors.grey2)),
            SizedBox(height: 12),
            Text('© 2025 MANTOTA. Tous droits réservés.', style: TextStyle(fontSize: 12, color: MantotaColors.grey4)),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Fermer')),
        ],
      ),
    );
  }

  void _showSimpleDialog(BuildContext context, String title, String content) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(content, style: const TextStyle(color: MantotaColors.grey2, height: 1.5)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Fermer')),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;

  const _SectionHeader(this.title);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 16, 14, 6),
      child: Text(title, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: MantotaColors.teal, letterSpacing: 0.5)),
    );
  }
}

class _SettingTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final Widget? trailing;
  final VoidCallback onTap;

  const _SettingTile({required this.icon, required this.title, this.trailing, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: MantotaColors.grey3, size: 22),
      title: Text(title, style: const TextStyle(fontSize: 15)),
      trailing: trailing ?? const Icon(Icons.chevron_right, color: MantotaColors.grey4, size: 20),
      onTap: onTap,
    );
  }
}
