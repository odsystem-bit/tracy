import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/services/conversation_service.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/adinkra_background.dart';

/// Écran — Nouvelle conversation.
///
/// Recherche un utilisateur par nom, numéro de téléphone ou nom de boutique.
/// Comme WhatsApp : on saisit une requête, on cherche si la personne
/// est enregistrée sur Mantota, et on démarre une conversation.
class NewChatScreen extends ConsumerStatefulWidget {
  const NewChatScreen({super.key});

  @override
  ConsumerState<NewChatScreen> createState() => _NewChatScreenState();
}

class _NewChatScreenState extends ConsumerState<NewChatScreen> {
  final _controller = TextEditingController();
  bool _searching = false;
  List<UserSearchResult> _results = [];
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _search() async {
    final query = _controller.text.trim();
    if (query.isEmpty) return;

    setState(() {
      _searching = true;
      _results = [];
      _error = null;
    });

    try {
      final svc = await ref.read(conversationServiceProvider.future);
      final users = await svc.searchByQuery(query);
      setState(() {
        _results = users;
        if (users.isEmpty) {
          _error = 'Aucun utilisateur trouvé pour "$query".';
        }
      });
    } catch (e) {
      setState(() {
        _error = 'Erreur de recherche. Vérifiez votre connexion.';
      });
    } finally {
      setState(() => _searching = false);
    }
  }

  void _startConversation(UserSearchResult user) async {
    try {
      final svc = await ref.read(conversationServiceProvider.future);
      final conv = await svc.startConversation(user.id.toString());
      if (mounted) context.go('/chat/${conv.id}');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e'), backgroundColor: MantotaColors.error),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
        title: const Text('Nouvelle conversation'),
      ),
      body: Stack(
        children: [
          const AdinkraBackground(opacity: 0.04),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Rechercher un contact',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Saisissez un nom, un numéro de téléphone ou un nom de boutique.',
                  style: TextStyle(fontSize: 13, color: MantotaColors.grey2),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _controller,
                  keyboardType: TextInputType.text,
                  textInputAction: TextInputAction.search,
                  decoration: const InputDecoration(
                    hintText: 'Nom, numéro ou boutique...',
                    labelText: 'Recherche',
                    prefixIcon: Icon(Icons.search, size: 20),
                  ),
                  onSubmitted: (_) => _search(),
                ),
                const SizedBox(height: 14),
                ElevatedButton.icon(
                  onPressed: _searching ? null : _search,
                  icon: _searching
                      ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Icon(Icons.search, size: 20),
                  label: const Text('Rechercher'),
                ),
                const SizedBox(height: 20),
                // Résultats
                if (_error != null) ...[
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: MantotaColors.error.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.person_search_outlined, color: MantotaColors.error, size: 22),
                        const SizedBox(width: 10),
                        Expanded(child: Text(_error!, style: TextStyle(fontSize: 14, color: MantotaColors.error))),
                      ],
                    ),
                  ),
                ],
                if (_results.isNotEmpty) ...[
                  Text('${_results.length} utilisateur(s) trouvé(s)', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: MantotaColors.teal)),
                  const SizedBox(height: 10),
                  Expanded(
                    child: ListView.builder(
                      itemCount: _results.length,
                      itemBuilder: (context, index) {
                        final user = _results[index];
                        return _UserResultTile(
                          user: user,
                          onTap: () => _startConversation(user),
                        );
                      },
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _UserResultTile extends StatelessWidget {
  final UserSearchResult user;
  final VoidCallback onTap;

  const _UserResultTile({required this.user, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: MantotaColors.tealPale,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: MantotaColors.teal.withValues(alpha: 0.2)),
        ),
        child: Row(
          children: [
            CircleAvatar(
              radius: 24,
              backgroundColor: MantotaColors.teal,
              backgroundImage: user.avatarUrl != null ? NetworkImage(user.avatarUrl!) : null,
              child: user.avatarUrl == null
                  ? Text(user.bestName.substring(0, 2).toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700))
                  : null,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(user.bestName, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                  Text(user.phone, style: const TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                  if (user.shopName != null && user.shopName!.isNotEmpty)
                    Text(user.shopName!, style: const TextStyle(fontSize: 12, color: MantotaColors.teal, fontWeight: FontWeight.w600)),
                ],
              ),
            ),
            if (user.isVendor)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(color: MantotaColors.teal, borderRadius: BorderRadius.circular(6)),
                child: const Text('Vendeur', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w600)),
              ),
            const SizedBox(width: 8),
            const Icon(Icons.chat_outlined, color: MantotaColors.teal, size: 22),
          ],
        ),
      ),
    );
  }
}
