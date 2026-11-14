import 'dart:convert';
import 'dart:io';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/providers/providers.dart';
import '../../../core/services/tracy_chat_service.dart';
import '../../../core/theme/mantota_theme.dart';
import '../widgets/chat_image_gallery.dart';

/// Écran 05 — Canal privé @Tracy.
///
/// Conversation directe avec Tracy (l'assistante IA).
/// Tracy propose des produits, gère les commandes, donne des conseils.
class TracyChannelScreen extends ConsumerStatefulWidget {
  const TracyChannelScreen({super.key});

  @override
  ConsumerState<TracyChannelScreen> createState() => _TracyChannelScreenState();
}

class _TracyChannelScreenState extends ConsumerState<TracyChannelScreen> {
  final _inputController = TextEditingController();
  final _scrollController = ScrollController();
  final List<_ChatMessage> _messages = [];
  bool _isTyping = false;
  final _imagePicker = ImagePicker();
  int? _selectedVendorId;

  @override
  void initState() {
    super.initState();
    _messages.add(_ChatMessage(
      text: "Bonjour ! Je suis Tracy, votre assistante commerciale. Je peux vous aider à trouver des produits, négocier des prix et passer commande. Que recherchez-vous ?",
      isTracy: true,
    ));
  }

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage() async {
    final text = _inputController.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add(_ChatMessage(text: text, isTracy: false));
      _inputController.clear();
      _isTyping = true;
    });

    _scrollToBottom();

    try {
      final svc = await ref.read(tracyChatServiceProvider.future);
      final response = await svc.chat(conversationId: 'tracy', message: text);
      if (mounted) {
        setState(() {
          _messages.add(_ChatMessage(
            text: response.text,
            isTracy: true,
            productMatches: response.products?.map((p) => p.toMatch()).toList(),
            vendorConversationId: response.vendorConversationId,
            paymentUrl: response.paymentUrl,
            trackingUrl: response.trackingUrl,
          ));
          _isTyping = false;
        });
        _scrollToBottom();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _messages.add(_ChatMessage(text: _tracyFallback(text), isTracy: true));
          _isTyping = false;
        });
        _scrollToBottom();
      }
    }
  }

  Future<void> _pickAndIdentifyProduct(ImageSource source) async {
    try {
      final picked = await _imagePicker.pickImage(source: source, maxWidth: 1024, imageQuality: 85);
      if (picked == null) return;

      final bytes = await File(picked.path).readAsBytes();
      final base64Image = base64Encode(bytes);

      setState(() {
        _messages.add(_ChatMessage(
          text: 'Photo envoyée pour identification',
          isTracy: false,
          imagePath: picked.path,
        ));
        _isTyping = true;
      });
      _scrollToBottom();

      final svc = await ref.read(tracyChatServiceProvider.future);
      final result = await svc.identifyProduct(
        imageBase64: base64Image,
        vendorId: _selectedVendorId ?? 1,
      );

      if (mounted) {
        setState(() {
          _isTyping = false;
          if (result.notFound) {
            _messages.add(_ChatMessage(
              text: result.message.isNotEmpty
                  ? result.message
                  : "Je n'ai pas trouvé ce produit dans la boutique. Voulez-vous que je demande au vendeur ? Ou décrivez-moi ce que vous cherchez.",
              isTracy: true,
            ));
          } else if (result.matched || result.needsConfirmation) {
            _messages.add(_ChatMessage(
              text: result.message,
              isTracy: true,
              productMatches: result.topMatches,
            ));
          } else {
            _messages.add(_ChatMessage(
              text: result.message.isNotEmpty
                  ? result.message
                  : "Je n'ai pas pu analyser la photo. Pouvez-vous la renvoyer ou décrire le produit ?",
              isTracy: true,
            ));
          }
        });
        _scrollToBottom();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isTyping = false;
          _messages.add(_ChatMessage(
            text: "Je n'ai pas pu analyser la photo pour le moment. Pouvez-vous décrire le produit que vous cherchez ?",
            isTracy: true,
          ));
        });
        _scrollToBottom();
      }
    }
  }

  void _showPhotoOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: MantotaColors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.camera_alt, color: MantotaColors.teal),
                title: const Text('Prendre une photo'),
                subtitle: const Text('Capture du produit en direct'),
                onTap: () {
                  Navigator.pop(ctx);
                  _pickAndIdentifyProduct(ImageSource.camera);
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_library, color: MantotaColors.teal),
                title: const Text('Choisir depuis la galerie'),
                subtitle: const Text('Screenshot de live, photo existante...'),
                onTap: () {
                  Navigator.pop(ctx);
                  _pickAndIdentifyProduct(ImageSource.gallery);
                },
              ),
              const SizedBox(height: 8),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Text(
                  'Tracy va scanner votre photo et trouver le produit dans la boutique',
                  style: TextStyle(fontSize: 12, color: MantotaColors.grey2),
                  textAlign: TextAlign.center,
                ),
              ),
              const SizedBox(height: 12),
            ],
          ),
        ),
      ),
    );
  }

  String _tracyFallback(String userMessage) {
    final msg = userMessage.toLowerCase();
    if (msg.contains('prix') || msg.contains('combien')) {
      return "Les prix varient selon les boutiques. Donnez-moi le nom du produit qui vous intéresse et je chercherai le meilleur prix pour vous !";
    }
    if (msg.contains('livrer') || msg.contains('livraison')) {
      return "La livraison est disponible à Cotonou, Porto-Novo et les environs. Frais à partir de 1000 F. Délai : 24-48h.";
    }
    if (msg.contains('bonjour') || msg.contains('salut') || msg.contains('hello')) {
      return "Salut ! Ravi de vous revoir. Comment puis-je vous aider aujourd'hui ?";
    }
    if (msg.contains('commande') || msg.contains('acheter')) {
      return "Parfait ! Pour passer commande, cherchez un produit dans l'onglet Rechercher, puis cliquez sur 'Acheter'. Je peux aussi vous recommander des produits populaires.";
    }
    return "Je note votre demande. Voulez-vous que je cherche des produits correspondants dans le catalogue ?";
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 22),
          onPressed: () => context.go('/chats'),
        ),
        title: Row(
          children: [
            Container(
              width: 38, height: 38,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(10),
                boxShadow: [
                  BoxShadow(
                    color: MantotaColors.teal.withValues(alpha: 0.2),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: Image.asset(
                  'assets/icons/tracy_avatar.jpeg',
                  fit: BoxFit.cover,
                ),
              ),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Tracy', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                Row(
                  children: [
                    Container(width: 6, height: 6, decoration: const BoxDecoration(color: MantotaColors.teal, shape: BoxShape.circle)),
                    const SizedBox(width: 5),
                    const Text('En ligne · MANTOTA', style: TextStyle(fontSize: 11, color: MantotaColors.teal)),
                  ],
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
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              itemCount: _messages.length + (_isTyping ? 1 : 0),
              itemBuilder: (context, index) {
                if (_isTyping && index == _messages.length) {
                  return const Padding(
                    padding: EdgeInsets.only(top: 8),
                    child: Row(
                      children: [
                        SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: MantotaColors.teal)),
                        SizedBox(width: 8),
                        Text('Tracy écrit...', style: TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                      ],
                    ),
                  );
                }
                final msg = _messages[index];
                return _MessageBubble(message: msg);
              },
            ),
          ),
          _ChatInputBar(
            controller: _inputController,
            onSend: _sendMessage,
            onPhoto: _showPhotoOptions,
          ),
        ],
      ),
    );
  }
}

class _ChatMessage {
  final String text;
  final bool isTracy;
  final DateTime timestamp;
  final String? imagePath;
  final List<ProductMatch>? productMatches;
  final String? vendorConversationId;
  final String? paymentUrl;
  final String? trackingUrl;

  _ChatMessage({
    required this.text,
    required this.isTracy,
    DateTime? timestamp,
    this.imagePath,
    this.productMatches,
    this.vendorConversationId,
    this.paymentUrl,
    this.trackingUrl,
  }) : timestamp = timestamp ?? DateTime.now();
}

/// Ouvre une URL dans le navigateur in-app (le client ne quitte pas Mantota).
Future<void> _openUrl(BuildContext context, String url) async {
  final uri = Uri.tryParse(url);
  if (uri == null) return;
  await launchUrl(uri, mode: LaunchMode.inAppBrowserView);
}

class _MessageBubble extends StatelessWidget {
  final _ChatMessage message;

  const _MessageBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final isTracy = message.isTracy;
    return Align(
      alignment: isTracy ? Alignment.centerLeft : Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.78,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: isTracy ? MantotaColors.tealPale : MantotaColors.teal,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: isTracy ? Radius.zero : const Radius.circular(16),
            bottomRight: isTracy ? const Radius.circular(16) : Radius.zero,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (message.imagePath != null) ...[
              GestureDetector(
                onTap: () => ChatImageGallery.open(
                  context,
                  images: [FileImage(File(message.imagePath!))],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: Image.file(
                    File(message.imagePath!),
                    width: double.infinity,
                    height: 180,
                    fit: BoxFit.cover,
                  ),
                ),
              ),
              const SizedBox(height: 8),
            ],
            Text(
              message.text,
              style: TextStyle(
                fontSize: 14,
                color: isTracy ? MantotaColors.grey1 : Colors.white,
                height: 1.4,
              ),
            ),
            if (message.productMatches != null && message.productMatches!.isNotEmpty) ...[
              const SizedBox(height: 10),
              ...message.productMatches!.map(
                (m) => _ProductMatchCard(
                  match: m,
                  galleryUrls: message.productMatches!
                      .where((p) => p.imageUrl != null)
                      .map((p) => p.imageUrl!)
                      .toList(),
                ),
              ),
            ],
            if (message.paymentUrl != null) ...[
              const SizedBox(height: 10),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () =>
                      _openUrl(context, message.paymentUrl!),
                  icon: const Icon(Icons.lock_outline, size: 16),
                  label: const Text('Payer maintenant'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green.shade700,
                    foregroundColor: Colors.white,
                    minimumSize: const Size(double.infinity, 36),
                    textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
            ],
            if (message.trackingUrl != null) ...[
              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () =>
                      _openUrl(context, message.trackingUrl!),
                  icon: const Icon(Icons.local_shipping_outlined, size: 16),
                  label: const Text('Suivre ma commande'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: MantotaColors.teal,
                    minimumSize: const Size(double.infinity, 36),
                    textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
            ],
            if (message.vendorConversationId != null) ...[
              const SizedBox(height: 10),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => context.push('/chat/${message.vendorConversationId}'),
                  icon: const Icon(Icons.chat_bubble_outline, size: 16),
                  label: const Text('Ouvrir la discussion'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: MantotaColors.teal,
                    foregroundColor: Colors.white,
                    minimumSize: const Size(double.infinity, 36),
                    textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ProductMatchCard extends StatelessWidget {
  final ProductMatch match;
  final List<String>? galleryUrls;

  const _ProductMatchCard({required this.match, this.galleryUrls});

  @override
  Widget build(BuildContext context) {
    final confidencePercent = (match.confidence * 100).round();
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: MantotaColors.surface3, width: 1),
      ),
      child: Row(
        children: [
          if (match.imageUrl != null)
            GestureDetector(
              onTap: () {
                final urls = galleryUrls ?? [match.imageUrl!];
                ChatImageGallery.open(
                  context,
                  images: urls
                      .map((u) => CachedNetworkImageProvider(u) as ImageProvider)
                      .toList(),
                  initialIndex: urls.indexOf(match.imageUrl!),
                );
              },
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: CachedNetworkImage(
                  imageUrl: match.imageUrl!,
                  width: 56, height: 56,
                  fit: BoxFit.cover,
                  placeholder: (_, __) => Container(width: 56, height: 56, color: MantotaColors.surface1),
                  errorWidget: (_, __, ___) => Container(width: 56, height: 56, color: MantotaColors.surface1, child: const Icon(Icons.image, size: 20, color: MantotaColors.grey3)),
                ),
              ),
            )
          else
            Container(
              width: 56, height: 56,
              decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(8)),
              child: const Icon(Icons.shopping_bag, size: 24, color: MantotaColors.grey3),
            ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  match.productName,
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: MantotaColors.grey1),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text(
                      '${match.price.toStringAsFixed(0)} F',
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: MantotaColors.teal),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: confidencePercent >= 75
                            ? MantotaColors.teal.withValues(alpha: 0.1)
                            : (confidencePercent >= 50 ? Colors.amber.withValues(alpha: 0.1) : Colors.red.withValues(alpha: 0.1)),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        '$confidencePercent% match',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w600,
                          color: confidencePercent >= 75
                              ? MantotaColors.teal
                              : (confidencePercent >= 50 ? Colors.amber.shade700 : Colors.red),
                        ),
                      ),
                    ),
                  ],
                ),
                if (match.stock != null && match.stock! > 0)
                  Text('${match.stock} en stock', style: const TextStyle(fontSize: 11, color: MantotaColors.grey2)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ChatInputBar extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onSend;
  final VoidCallback onPhoto;

  const _ChatInputBar({required this.controller, required this.onSend, required this.onPhoto});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: const BoxDecoration(
          color: MantotaColors.white,
          border: Border(top: BorderSide(color: MantotaColors.surface3, width: 1)),
        ),
        child: Row(
          children: [
            IconButton(icon: const Icon(Icons.camera_alt_outlined, color: MantotaColors.teal, size: 24), onPressed: onPhoto),
            IconButton(icon: const Icon(Icons.mic_outlined, color: MantotaColors.grey2, size: 24), onPressed: () {}),
            Expanded(
              child: TextField(
                controller: controller,
                style: const TextStyle(fontSize: 14),
                decoration: InputDecoration(
                  hintText: 'Parlez à Tracy...',
                  hintStyle: const TextStyle(fontSize: 14),
                  isDense: true,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  filled: true,
                  fillColor: MantotaColors.surface1,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide.none,
                  ),
                ),
                onSubmitted: (_) => onSend(),
              ),
            ),
            const SizedBox(width: 8),
            GestureDetector(
              onTap: onSend,
              child: Container(
                width: 40, height: 40,
                decoration: const BoxDecoration(color: MantotaColors.teal, shape: BoxShape.circle),
                child: const Icon(Icons.send, color: Colors.white, size: 20),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
