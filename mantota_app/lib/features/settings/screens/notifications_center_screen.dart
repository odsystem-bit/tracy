import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran 15c — Centre de notifications (global).
///
/// Notifications de l'app : messages, commandes, promotions, système.
class NotificationsCenterScreen extends ConsumerWidget {
  const NotificationsCenterScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifsAsync = ref.watch(notificationListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: notifsAsync.when(
        data: (notifs) => ListView(
          padding: const EdgeInsets.all(14),
          children: notifs.map((n) => _NotifItem(
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
      case 'message':
        return Icons.chat_bubble_outline;
      case 'order':
        return Icons.shopping_bag_outlined;
      case 'promotion':
        return Icons.local_offer_outlined;
      case 'delivery':
        return Icons.check_circle_outline;
      default:
        return Icons.notifications_outlined;
    }
  }

  List<Widget> _staticNotifs() {
    return [
      _NotifItem(
        icon: Icons.chat_bubble_outline,
        iconColor: MantotaColors.teal,
        title: 'Nouveau message de Tracy',
        body: 'Promotion Nike activée pour votre boutique.',
        time: 'Il y a 5 min',
        unread: true,
      ),
      _NotifItem(
        icon: Icons.shopping_bag_outlined,
        iconColor: MantotaColors.coral,
        title: 'Votre commande CMD-0843 est en livraison',
        body: 'Le livreur est en route. Arrivée estimée: 15 min.',
        time: 'Il y a 20 min',
        unread: true,
      ),
      _NotifItem(
        icon: Icons.local_offer_outlined,
        iconColor: MantotaColors.teal,
        title: 'Promotion chez TechStore',
        body: '-20% sur tous les Air Max ce weekend.',
        time: 'Il y a 1h',
        unread: false,
      ),
      _NotifItem(
        icon: Icons.check_circle_outline,
        iconColor: MantotaColors.teal,
        title: 'Commande livrée',
        body: 'Votre commande CMD-0831 a été livrée avec succès.',
        time: 'Hier',
        unread: false,
      ),
    ];
  }
}

class _NotifItem extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String title;
  final String body;
  final String time;
  final bool unread;

  const _NotifItem({
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
                Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
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
