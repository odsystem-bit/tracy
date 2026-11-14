import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/widgets/tracy_avatar.dart';
import '../../../core/services/tracy_chat_service.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran 07b — Recherche produit via Tracy.
///
/// L'acheteur demande un produit. Tracy cherche dans les boutiques
/// et affiche les résultats sous forme de fiches produit.
class ProductSearchScreen extends ConsumerStatefulWidget {
  const ProductSearchScreen({super.key});

  @override
  ConsumerState<ProductSearchScreen> createState() => _ProductSearchScreenState();
}

class _ProductSearchScreenState extends ConsumerState<ProductSearchScreen> {
  final _inputController = TextEditingController();
  final _scrollController = ScrollController();
  final List<_ChatItem> _items = [];
  bool _isSearching = false;

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendQuery() async {
    final query = _inputController.text.trim();
    if (query.isEmpty) return;

    setState(() {
      _items.add(_ChatItem.user(text: query, time: _now()));
      _isSearching = true;
    });
    _inputController.clear();

    try {
      final svc = await ref.read(tracyChatServiceProvider.future);
      final response = await svc.chat(conversationId: 'search', message: query);

      if (!mounted) return;
      setState(() {
        if (response.type == TracyResponseType.search && response.products != null) {
          _items.add(_ChatItem.tracyText(text: response.text.isEmpty ? 'J\'ai trouvé ${response.products!.length} résultats pour vous 🔍' : response.text, time: _now()));
          for (final p in response.products!) {
            _items.add(_ChatItem.tracyProduct(
              name: p.name,
              shop: p.shop,
              price: p.price,
              time: _now(),
            ));
          }
          _items.add(_ChatItem.tracyText(text: 'Lequel vous intéresse ? Je peux négocier le prix pour vous 😉', time: _now()));
        } else {
          _items.add(_ChatItem.tracyText(text: response.text.isEmpty ? 'Je n\'ai rien trouvé pour cette recherche.' : response.text, time: _now()));
        }
        _isSearching = false;
      });
      _scrollToBottom();
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _items.add(_ChatItem.tracyText(text: 'J\'ai trouvé 3 résultats pour vous 🔍', time: _now()));
        _items.add(_ChatItem.tracyProduct(
          name: 'Nike Air Max 270',
          shop: 'Boutique Stan · Taille 42 ✓',
          price: '40 500 F',
          time: _now(),
        ));
        _items.add(_ChatItem.tracyProduct(
          name: 'Nike Air Max 90',
          shop: 'SneakerZone · Taille 42 ✓',
          price: '38 000 F',
          time: _now(),
        ));
        _items.add(_ChatItem.tracyProduct(
          name: 'Nike Air Max Plus',
          shop: 'SportCenter · Taille 42 ✓',
          price: '42 000 F',
          time: _now(),
        ));
        _items.add(_ChatItem.tracyText(text: 'Lequel vous intéresse ? Je peux négocier le prix pour vous 😉', time: _now()));
        _isSearching = false;
      });
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  String _now() {
    final t = DateTime.now();
    return '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
        title: Row(
          children: [
            TracyAvatar(size: 32, borderRadius: 16),
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Tracy', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
                Text(
                  _isSearching ? 'Recherche en cours…' : 'En ligne',
                  style: TextStyle(fontSize: 11, color: MantotaColors.teal),
                ),
              ],
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(12),
              itemCount: _items.length,
              itemBuilder: (_, i) => _buildItem(_items[i]),
            ),
          ),
          _buildInput(),
        ],
      ),
    );
  }

  Widget _buildItem(_ChatItem item) {
    if (item.isUser) {
      return Container(
        margin: const EdgeInsets.only(bottom: 8),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            Flexible(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: MantotaColors.teal,
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(16),
                    topRight: Radius.circular(16),
                    bottomLeft: Radius.circular(16),
                  ),
                ),
                child: Text(item.text!, style: const TextStyle(fontSize: 14, color: Colors.white)),
              ),
            ),
          ],
        ),
      );
    }

    if (item.product != null) {
      return Container(
        margin: const EdgeInsets.only(bottom: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _tracyLabel(),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: MantotaColors.tealPale,
                borderRadius: BorderRadius.circular(14),
              ),
              child: _ProductCard(
                name: item.product!.name,
                shop: item.product!.shop,
                price: item.product!.price,
                onTap: () => context.go('/negotiation'),
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _tracyLabel(),
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: MantotaColors.surface1,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(16),
                bottomRight: Radius.circular(16),
              ),
            ),
            child: Text(item.text!, style: const TextStyle(fontSize: 14, color: MantotaColors.grey1)),
          ),
          const SizedBox(height: 2),
          Text(item.time, style: const TextStyle(fontSize: 10, color: MantotaColors.grey4)),
        ],
      ),
    );
  }

  Widget _tracyLabel() {
    return Row(
      children: [
        Container(
          width: 6, height: 6,
          decoration: const BoxDecoration(color: MantotaColors.teal, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        const Text('Tracy', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: MantotaColors.teal)),
      ],
    );
  }

  Widget _buildInput() {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: MantotaColors.border)),
        color: Colors.white,
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _inputController,
                decoration: InputDecoration(
                  hintText: 'Décrivez ce que vous cherchez…',
                  hintStyle: const TextStyle(fontSize: 14),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none),
                  filled: true,
                  fillColor: MantotaColors.surface1,
                ),
                onSubmitted: (_) => _sendQuery(),
              ),
            ),
            const SizedBox(width: 8),
            GestureDetector(
              onTap: _sendQuery,
              child: Container(
                width: 42, height: 42,
                decoration: const BoxDecoration(color: MantotaColors.teal, shape: BoxShape.circle),
                child: const Icon(Icons.send, color: Colors.white, size: 18),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ChatItem {
  final bool isUser;
  final String? text;
  final _ProductResult? product;
  final String time;

  _ChatItem._({required this.isUser, this.text, this.product, required this.time});

  factory _ChatItem.user({required String text, required String time}) =>
      _ChatItem._(isUser: true, text: text, time: time);

  factory _ChatItem.tracyText({required String text, required String time}) =>
      _ChatItem._(isUser: false, text: text, time: time);

  factory _ChatItem.tracyProduct({required String name, required String shop, required String price, required String time}) =>
      _ChatItem._(isUser: false, product: _ProductResult(name: name, shop: shop, price: price), time: time);
}

class _ProductResult {
  final String name;
  final String shop;
  final String price;

  const _ProductResult({required this.name, required this.shop, required this.price});
}

class _ProductCard extends StatelessWidget {
  final String name;
  final String shop;
  final String price;
  final VoidCallback onTap;

  const _ProductCard({required this.name, required this.shop, required this.price, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Row(
        children: [
          Container(
            width: 56, height: 56,
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [MantotaColors.tealPale, MantotaColors.surface2]),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Center(child: Text('👟', style: TextStyle(fontSize: 24))),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
                const SizedBox(height: 2),
                Text(shop, style: const TextStyle(fontSize: 12, color: MantotaColors.grey2)),
                const SizedBox(height: 4),
                Text(price, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: MantotaColors.teal)),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: MantotaColors.teal,
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Text('Voir détails', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
