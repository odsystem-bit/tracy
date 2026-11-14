import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran — Notifications vendeur.
///
/// Alertes : nouvelles commandes, paiements, messages Tracy, etc.
class VendorNotificationsScreen extends ConsumerWidget {
  const VendorNotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifsAsync = ref.watch(vendorNotificationListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
        actions: [
          TextButton(
            onPressed: () async {
              final svc = await ref.read(notificationServiceProvider.future);
              await svc.markAllRead();
              ref.invalidate(vendorNotificationListProvider);
            },
            child: const Text('Tout marquer lu', style: TextStyle(fontSize: 13)),
          ),
        ],
      ),
      body: notifsAsync.when(
        data: (notifs) => ListView(
          padding: const EdgeInsets.all(14),
          children: notifs.map((n) => _NotifTile(
            icon: _iconForType(n.type),
            iconColor: MantotaColors.teal,
            title: n.title,
            body: n.body,
            time: n.createdAt.toString(),
            unread: !n.isRead,
          )).toList(),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, __) => ListView(
          padding: const EdgeInsets.all(14),
          children: _staticNotifs(),
        ),
      ),
    );
  }

  IconData _iconForType(String type) {
    switch (type) {
      case 'order':
        return Icons.shopping_bag_outlined;
      case 'payment':
        return Icons.payments_outlined;
      case 'tracy':
        return Icons.auto_awesome;
      case 'review':
        return Icons.star_outline;
      case 'goal':
        return Icons.trending_up;
      default:
        return Icons.notifications_outlined;
    }
  }

  List<Widget> _staticNotifs() {
    return [
      _NotifTile(
        icon: Icons.shopping_bag_outlined,
        iconColor: MantotaColors.teal,
        title: 'Nouvelle commande',
        body: 'Kolade Mensah a commandé Nike Air Max 270 pour 40 500 F.',
        time: 'Il y a 5 min',
        unread: true,
      ),
      _NotifTile(
        icon: Icons.payments_outlined,
        iconColor: MantotaColors.teal,
        title: 'Paiement reçu',
        body: 'Fatoumata D. a payé 28 000 F pour le sac cuir marron.',
        time: 'Il y a 1h',
        unread: true,
      ),
      _NotifTile(
        icon: Icons.auto_awesome,
        iconColor: MantotaColors.teal,
        title: 'Tracy a négocié',
        body: 'Tracy a conclu une vente à 38 000 F avec Amina S. (prix initial: 45 000 F).',
        time: 'Il y a 2h',
        unread: false,
      ),
      _NotifTile(
        icon: Icons.star_outline,
        iconColor: MantotaColors.coral,
        title: 'Nouvel avis',
        body: 'Brice K. a laissé un avis 5★ sur votre boutique.',
        time: 'Hier',
        unread: false,
      ),
      _NotifTile(
        icon: Icons.trending_up,
        iconColor: MantotaColors.teal,
        title: 'Objectif atteint',
        body: 'Vous avez dépassé 100 000 F de ventes cette semaine !',
        time: 'Il y a 2 jours',
        unread: false,
      ),
    ];
  }
}

class _NotifTile extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String title;
  final String body;
  final String time;
  final bool unread;

  const _NotifTile({
    required this.icon,
    required this.iconColor,
    required this.title,
    required this.body,
    required this.time,
    required this.unread,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: unread ? iconColor.withValues(alpha: 0.06) : MantotaColors.surface1,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36, height: 36,
            decoration: BoxDecoration(color: iconColor.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(10)),
            child: Icon(icon, color: iconColor, size: 18),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(child: Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700))),
                    if (unread) Container(width: 8, height: 8, decoration: const BoxDecoration(color: MantotaColors.teal, shape: BoxShape.circle)),
                  ],
                ),
                const SizedBox(height: 3),
                Text(body, style: const TextStyle(fontSize: 13, color: MantotaColors.grey2, height: 1.3)),
                const SizedBox(height: 4),
                Text(time, style: const TextStyle(fontSize: 11, color: MantotaColors.grey4)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
