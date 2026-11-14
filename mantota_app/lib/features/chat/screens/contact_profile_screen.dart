import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/mantota_theme.dart';

/// Écran — Profil d'un contact.
///
/// Affiche la photo, le nom, le téléphone, le statut en ligne,
/// et les options (appel, bloquer, signaler).
class ContactProfileScreen extends StatelessWidget {
  final String contactId;

  const ContactProfileScreen({super.key, required this.contactId});

  String _nameFromId(String id) {
    switch (id) {
      case 'kolade': return 'Kolade Mensah';
      case 'fatoumata': return 'Fatoumata D.';
      case 'amis': return 'Amis Cotonou';
      default: return id;
    }
  }

  String _phoneFromId(String id) {
    switch (id) {
      case 'kolade': return '+229 97 45 12 34';
      case 'fatoumata': return '+229 96 78 56 12';
      case 'amis': return 'Groupe · 5 membres';
      default: return '+229 00 00 00 00';
    }
  }

  bool _isStore(String id) {
    return id == 'kolade' || id == 'fatoumata';
  }

  @override
  Widget build(BuildContext context) {
    final name = _nameFromId(contactId);
    final phone = _phoneFromId(contactId);
    final isStore = _isStore(contactId);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
        title: const Text('Profil contact'),
      ),
      body: ListView(
        children: [
          const SizedBox(height: 20),
          // Photo et nom
          Center(
            child: Column(
              children: [
                CircleAvatar(
                  radius: 48,
                  backgroundColor: MantotaColors.surface2,
                  child: Text(
                    name.substring(0, 2).toUpperCase(),
                    style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: MantotaColors.teal),
                  ),
                ),
                const SizedBox(height: 12),
                Text(name, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
                const SizedBox(height: 4),
                Text(phone, style: const TextStyle(fontSize: 14, color: MantotaColors.grey2)),
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
          const SizedBox(height: 20),
          // Actions rapides
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 40),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _ActionIcon(icon: Icons.chat_outlined, label: 'Message', onTap: () => context.go('/chat/$contactId')),
                _ActionIcon(icon: Icons.phone_outlined, label: 'Appeler', onTap: () {}),
                _ActionIcon(icon: Icons.videocam_outlined, label: 'Vidéo', onTap: () {}),
              ],
            ),
          ),
          const SizedBox(height: 24),
          // Infos
          if (isStore) ...[
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 14),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(color: MantotaColors.tealPale, borderRadius: BorderRadius.circular(14)),
              child: Row(
                children: [
                  const Icon(Icons.store_outlined, color: MantotaColors.teal, size: 22),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Boutique de $name', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
                        const Text('Vendeur vérifié · 4.8 ★', style: TextStyle(fontSize: 12, color: MantotaColors.grey2)),
                      ],
                    ),
                  ),
                  const Icon(Icons.chevron_right, color: MantotaColors.grey4, size: 20),
                ],
              ),
            ),
            const SizedBox(height: 14),
          ],
          // Options
          ListTile(
            leading: const Icon(Icons.notifications_outlined, color: MantotaColors.grey3, size: 22),
            title: const Text('Notifications', style: TextStyle(fontSize: 15)),
            trailing: Switch.adaptive(value: true, onChanged: (_) {}, activeTrackColor: MantotaColors.teal),
          ),
          ListTile(
            leading: const Icon(Icons.image_outlined, color: MantotaColors.grey3, size: 22),
            title: const Text('Médias partagés', style: TextStyle(fontSize: 15)),
            trailing: const Text('12', style: TextStyle(fontSize: 13, color: MantotaColors.grey2)),
            onTap: () {},
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.block, color: MantotaColors.error, size: 22),
            title: Text('Bloquer $name', style: const TextStyle(fontSize: 15, color: MantotaColors.error)),
            onTap: () {},
          ),
          ListTile(
            leading: const Icon(Icons.flag_outlined, color: MantotaColors.error, size: 22),
            title: const Text('Signaler', style: TextStyle(fontSize: 15, color: MantotaColors.error)),
            onTap: () {},
          ),
        ],
      ),
    );
  }
}

class _ActionIcon extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _ActionIcon({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            width: 48, height: 48,
            decoration: BoxDecoration(
              color: MantotaColors.surface1,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(icon, color: MantotaColors.teal, size: 22),
          ),
          const SizedBox(height: 6),
          Text(label, style: const TextStyle(fontSize: 11, color: MantotaColors.grey2)),
        ],
      ),
    );
  }
}
