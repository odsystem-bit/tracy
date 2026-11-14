import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/services/conversation_service.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/tracy_avatar.dart';

/// Écran — Statuts (Stories) à la WhatsApp.
///
/// Affiche:
/// - Mon statut (ajouter)
/// - Statut de Tracy (promotions, annonces)
/// - Statuts des contacts (visibles par ceux avec qui on a échangé au moins une fois)
class StatusScreen extends ConsumerStatefulWidget {
  const StatusScreen({super.key});

  @override
  ConsumerState<StatusScreen> createState() => _StatusScreenState();
}

class _StatusScreenState extends ConsumerState<StatusScreen> {
  @override
  Widget build(BuildContext context) {
    final statusesAsync = ref.watch(statusListProvider);
    final tracyStatusAsync = ref.watch(tracyStatusProvider);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
        title: const Text('Statuts'),
        actions: [
          IconButton(
            icon: const Icon(Icons.camera_alt_outlined, size: 22),
            onPressed: () => _showAddStatusDialog(context),
          ),
        ],
      ),
      body: ListView(
        children: [
          // ── Mon statut ──
          _StatusTile(
            name: 'Mon statut',
            subtitle: 'Appuyez pour ajouter un statut',
            isMe: true,
            avatar: null,
            initials: 'Moi',
            onTap: () => _showAddStatusDialog(context),
          ),
          const Divider(height: 1),

          // ── Tracy ──
          tracyStatusAsync.when(
            data: (tracyItems) => tracyItems.isEmpty
                ? const SizedBox.shrink()
                : Column(
                    children: [
                      _StatusTile(
                        name: 'Tracy',
                        subtitle: '${tracyItems.length} mise(s) à jour',
                        isTracy: true,
                        avatar: null,
                        initials: 'T',
                        onTap: () => context.push('/tracy'),
                      ),
                      const Divider(height: 1),
                    ],
                  ),
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
          ),

          // ── Contacts ──
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Text(
              'Statuts récents',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: MantotaColors.grey2),
            ),
          ),
          statusesAsync.when(
            data: (statuses) {
              if (statuses.isEmpty) {
                return const Padding(
                  padding: EdgeInsets.all(40),
                  child: Center(
                    child: Text(
                      'Aucun statut disponible.\nLes statuts de vos contacts apparaîtront ici.',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 14, color: MantotaColors.grey3),
                    ),
                  ),
                );
              }
              return Column(
                children: statuses.map((s) => _StatusTile(
                  name: s.name,
                  subtitle: _timeAgo(s.items.last.createdAt),
                  avatar: s.avatarUrl,
                  initials: s.name.substring(0, 2).toUpperCase(),
                  onTap: () => _showStatusViewer(context, s),
                )).toList(),
              );
            },
            loading: () => const Center(child: Padding(padding: EdgeInsets.all(20), child: CircularProgressIndicator())),
            error: (_, __) => const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }

  String _timeAgo(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) return "À l'instant";
    if (diff.inMinutes < 60) return 'Il y a ${diff.inMinutes} min';
    if (diff.inHours < 24) return 'Il y a ${diff.inHours}h';
    return 'Il y a ${diff.inDays}j';
  }

  void _showAddStatusDialog(BuildContext context) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Nouveau statut'),
        content: TextField(
          controller: controller,
          maxLines: 3,
          autofocus: true,
          decoration: const InputDecoration(
            hintText: 'Que voulez-vous partager ?',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
          ElevatedButton(
            onPressed: () async {
              if (controller.text.trim().isEmpty) return;
              try {
                final svc = await ref.read(conversationServiceProvider.future);
                await svc.postStatus(type: 'text', content: controller.text.trim());
              } catch (_) {}
              if (ctx.mounted) Navigator.pop(ctx);
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Statut publié'), backgroundColor: MantotaColors.teal),
                );
              }
            },
            child: const Text('Publier'),
          ),
        ],
      ),
    );
  }

  void _showStatusViewer(BuildContext context, UserStatus status) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => _StatusViewer(status: status),
      ),
    );
  }
}

class _StatusTile extends StatelessWidget {
  final String name;
  final String subtitle;
  final bool isMe;
  final bool isTracy;
  final String? avatar;
  final String initials;
  final VoidCallback onTap;

  const _StatusTile({
    required this.name,
    required this.subtitle,
    this.isMe = false,
    this.isTracy = false,
    this.avatar,
    required this.initials,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      onTap: onTap,
      leading: Stack(
        children: [
          CircleAvatar(
            radius: 26,
            backgroundColor: isTracy ? MantotaColors.tealPale : MantotaColors.surface2,
            backgroundImage: avatar != null ? NetworkImage(avatar!) : null,
            child: avatar == null
                ? isTracy
                    ? const TracyAvatar(size: 52, borderRadius: 26)
                    : Text(initials, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700))
                : null,
          ),
          if (isMe)
            Positioned(
              bottom: 0, right: 0,
              child: Container(
                width: 20, height: 20,
                decoration: BoxDecoration(
                  color: MantotaColors.teal,
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white, width: 2),
                ),
                child: const Icon(Icons.add, color: Colors.white, size: 12),
              ),
            ),
        ],
      ),
      title: Text(name, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 13, color: MantotaColors.grey2)),
    );
  }
}

class _StatusViewer extends StatefulWidget {
  final UserStatus status;

  const _StatusViewer({required this.status});

  @override
  State<_StatusViewer> createState() => _StatusViewerState();
}

class _StatusViewerState extends State<_StatusViewer> {
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    _nextAfterDelay();
  }

  void _nextAfterDelay() {
    Future.delayed(const Duration(seconds: 5), () {
      if (!mounted) return;
      if (_currentIndex < widget.status.items.length - 1) {
        setState(() => _currentIndex++);
        _nextAfterDelay();
      } else {
        Navigator.pop(context);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.status.items[_currentIndex];
    return Scaffold(
      backgroundColor: item.backgroundColor ?? MantotaColors.teal,
      body: GestureDetector(
        onTapDown: (details) {
          final width = MediaQuery.of(context).size.width;
          if (details.globalPosition.dx < width / 3) {
            if (_currentIndex > 0) setState(() => _currentIndex--);
          } else {
            if (_currentIndex < widget.status.items.length - 1) {
              setState(() => _currentIndex++);
            } else {
              Navigator.pop(context);
            }
          }
        },
        child: SafeArea(
          child: Column(
            children: [
              // Barre de progression
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                child: Row(
                  children: List.generate(
                    widget.status.items.length,
                    (i) => Expanded(
                      child: Container(
                        margin: const EdgeInsets.symmetric(horizontal: 2),
                        height: 3,
                        decoration: BoxDecoration(
                          color: i <= _currentIndex ? Colors.white : Colors.white.withValues(alpha: 0.3),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              // En-tête
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 18,
                      backgroundColor: Colors.white.withValues(alpha: 0.2),
                      child: Text(widget.status.name.substring(0, 2).toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(widget.status.name, style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600)),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, color: Colors.white, size: 24),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),
              // Contenu
              Expanded(
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32),
                    child: Text(
                      item.content,
                      style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w600, height: 1.4),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
