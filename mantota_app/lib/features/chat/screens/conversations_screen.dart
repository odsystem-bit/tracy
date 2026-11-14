import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/models/conversation.dart';
import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/adinkra_background.dart';

/// Écran 03 — Liste des conversations.
///
/// Affiche toutes les conversations avec badges canal (App / WhatsApp).
/// Le bottom nav est géré par MainScaffold (StatefulShellRoute).
class ConversationsScreen extends ConsumerStatefulWidget {
  const ConversationsScreen({super.key});

  @override
  ConsumerState<ConversationsScreen> createState() => _ConversationsScreenState();
}

class _ConversationsScreenState extends ConsumerState<ConversationsScreen> {
  String _searchQuery = '';
  bool _showSearch = false;

  @override
  Widget build(BuildContext context) {
    final conversationsAsync = ref.watch(conversationListProvider);

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop) {
          if (_showSearch) {
            setState(() { _showSearch = false; _searchQuery = ''; });
          } else {
            SystemNavigator.pop();
          }
        }
      },
      child: Scaffold(
      appBar: AppBar(
        title: _showSearch
            ? TextField(
                autofocus: true,
                decoration: const InputDecoration(
                  hintText: 'Rechercher un contact...',
                  border: InputBorder.none,
                  hintStyle: TextStyle(fontSize: 15, color: MantotaColors.grey2),
                ),
                onChanged: (q) => setState(() => _searchQuery = q.toLowerCase()),
              )
            : const Text('Messages'),
        actions: [
          IconButton(
            icon: Icon(_showSearch ? Icons.close : Icons.search, size: 22),
            onPressed: () => setState(() {
              _showSearch = !_showSearch;
              if (!_showSearch) _searchQuery = '';
            }),
          ),
        ],
      ),
      body: Stack(
        children: [
          const AdinkraBackground(opacity: 0.03),
          conversationsAsync.when(
        data: (conversations) {
          final filtered = _searchQuery.isEmpty
              ? conversations
              : conversations.where((c) => c.name.toLowerCase().contains(_searchQuery)).toList();
          return ListView(
            children: [
              // ── Section Statuts (bientôt disponible) ──
              if (_searchQuery.isEmpty) ...[
                _StatusComingSoon(),
                const Divider(height: 1),
              ],
              if (_searchQuery.isEmpty || 'tracy'.contains(_searchQuery))
                _ConversationTile(
                  name: 'Tracy',
                  lastMessage: 'Promotion Nike activée ✓',
                  time: 'Maintenant',
                  isTracy: true,
                  isOnline: true,
                  channel: null,
                  onTap: () => context.go('/tracy'),
                ),
              ...filtered.map((c) => _ConversationTile(
                name: c.name,
                lastMessage: c.lastMessage ?? '',
                time: c.timeLabel,
                unreadCount: c.unreadCount,
                channel: c.channel == MessageChannel.whatsapp ? Channel.whatsapp : Channel.app,
                onTap: () => context.go('/chat/${c.id}'),
              )),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, __) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.cloud_off, size: 48, color: MantotaColors.grey3),
                const SizedBox(height: 12),
                const Text('Impossible de charger les conversations', style: TextStyle(fontSize: 14, color: MantotaColors.grey2)),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => ref.refresh(conversationListProvider),
                  child: const Text('Réessayer'),
                ),
              ],
            ),
          );
        },
      ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/new-chat'),
        backgroundColor: MantotaColors.teal,
        child: const Icon(Icons.edit_outlined, color: Colors.white),
      ),
      ),
    );
  }
}

enum Channel { app, whatsapp }

class _ConversationTile extends StatelessWidget {
  final String name;
  final String lastMessage;
  final String time;
  final int unreadCount;
  final bool isTracy;
  final bool isOnline;
  final Channel? channel;
  final VoidCallback onTap;

  const _ConversationTile({
    required this.name,
    required this.lastMessage,
    required this.time,
    this.unreadCount = 0,
    this.isTracy = false,
    this.isOnline = false,
    this.channel,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      onTap: onTap,
      leading: CircleAvatar(
        radius: 26,
        backgroundColor: isTracy ? MantotaColors.tealPale : MantotaColors.surface2,
        child: isTracy
            ? ClipOval(
                child: Image.asset(
                  'assets/icons/tracy_avatar.jpeg',
                  fit: BoxFit.cover,
                  width: 52,
                  height: 52,
                ),
              )
            : Text(name.substring(0, 2).toUpperCase(),
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
      ),
      title: Row(
        children: [
          Flexible(
            child: Text(name,
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                overflow: TextOverflow.ellipsis),
          ),
          if (channel != null) ...[
            const SizedBox(width: 6),
            _ChannelBadge(channel: channel!),
          ],
        ],
      ),
      subtitle: Text(lastMessage,
          style: TextStyle(
            fontSize: 13,
            color: isTracy ? MantotaColors.teal : MantotaColors.grey2,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis),
      trailing: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Text(time, style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
          if (unreadCount > 0) ...[
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
              decoration: BoxDecoration(
                color: MantotaColors.teal,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text('$unreadCount',
                  style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700)),
            ),
          ],
        ],
      ),
    );
  }
}

class _ChannelBadge extends StatelessWidget {
  final Channel channel;

  const _ChannelBadge({required this.channel});

  @override
  Widget build(BuildContext context) {
    final isWa = channel == Channel.whatsapp;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
      decoration: BoxDecoration(
        color: isWa ? const Color(0xFF25D36620) : MantotaColors.tealPale,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        isWa ? 'WhatsApp' : 'App',
        style: TextStyle(
          fontSize: 9,
          fontWeight: FontWeight.w600,
          color: isWa ? const Color(0xFF25D366) : MantotaColors.teal,
        ),
      ),
    );
  }
}

/// Section statuts — Bientôt disponible.
class _StatusComingSoon extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Les statuts seront bientôt disponibles !'),
            backgroundColor: MantotaColors.teal,
            duration: Duration(seconds: 2),
          ),
        );
      },
      child: Container(
        height: 80,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            Stack(
              children: [
                Container(
                  width: 52, height: 52,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: MantotaColors.grey4, width: 2),
                  ),
                  child: const CircleAvatar(
                    radius: 26,
                    backgroundColor: MantotaColors.surface2,
                    child: Icon(Icons.photo_camera_outlined, color: MantotaColors.grey3, size: 24),
                  ),
                ),
                Positioned(
                  bottom: 0, right: 0,
                  child: Container(
                    width: 18, height: 18,
                    decoration: BoxDecoration(
                      color: MantotaColors.grey3,
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 2),
                    ),
                    child: const Icon(Icons.add, color: Colors.white, size: 10),
                  ),
                ),
              ],
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('Statuts', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: MantotaColors.tealPale,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: const Text(
                          'Bientôt disponible',
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: MantotaColors.teal),
                        ),
                      ),
                      const SizedBox(width: 8),
                      const Text(
                        'Partagez avec vos contacts',
                        style: TextStyle(fontSize: 12, color: MantotaColors.grey2),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
