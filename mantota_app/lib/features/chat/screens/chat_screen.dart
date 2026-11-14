import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran 04 — Conversation active.
///
/// Affiche les messages d'une conversation avec input texte.
/// Badge canal visible (App / WhatsApp).
class ChatScreen extends ConsumerStatefulWidget {
  final String conversationId;

  const ChatScreen({super.key, required this.conversationId});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _inputController = TextEditingController();
  final _scrollController = ScrollController();
  final List<_Msg> _messages = [];
  bool _loaded = false;

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadMessages() async {
    if (_loaded) return;
    _loaded = true;
    try {
      final svc = await ref.read(conversationServiceProvider.future);
      final msgs = await svc.getMessages(widget.conversationId);
      if (mounted) {
        setState(() {
          _messages.addAll(msgs.map((m) => _Msg(
            text: m.text,
            isFromMe: m.isFromMe,
          )));
        });
        _scrollToBottom();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _messages.addAll([
            _Msg(text: "Bonjour, vous avez encore le Nike Air Max 270 ?", isFromMe: true),
            _Msg(text: "Oui ! Taille 42 disponible. 45 000 F.", isFromMe: false),
            _Msg(text: "Parfait, je prends.", isFromMe: true),
            _Msg(text: "C'est livré quand ?", isFromMe: true),
          ]);
        });
      }
    }
  }

  String _nameFromId(String id) {
    switch (id) {
      case 'kolade': return 'Kolade Mensah';
      case 'fatoumata': return 'Fatoumata D.';
      case 'amis': return 'Amis Cotonou';
      default: return id;
    }
  }

  void _send() async {
    final text = _inputController.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add(_Msg(text: text, isFromMe: true));
      _inputController.clear();
    });
    _scrollToBottom();

    try {
      final svc = await ref.read(conversationServiceProvider.future);
      await svc.sendMessage(conversationId: widget.conversationId, text: text);
    } catch (_) {}

    Future.delayed(const Duration(milliseconds: 1200), () {
      if (mounted) {
        setState(() {
          _messages.add(_Msg(text: _autoReply(text), isFromMe: false));
        });
        _scrollToBottom();
      }
    });
  }

  String _autoReply(String msg) {
    final m = msg.toLowerCase();
    if (m.contains('prix') || m.contains('combien')) return "Le prix est de 45 000 F, négociable si vous prenez 2 paires.";
    if (m.contains('livrer') || m.contains('livraison')) return "Livraison demain matin avant 10h. C'est 1000 F en plus.";
    if (m.contains('ok') || m.contains('parfait') || m.contains('bien')) return "Super ! Je vous envoie le lien de paiement.";
    return "D'accord, je reviens vers vous dans quelques minutes.";
  }

  void _showCallDialog(BuildContext context, String name) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Appeler $name'),
        content: const Text('Les appels audio seront disponibles dans une prochaine mise à jour.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('OK')),
        ],
      ),
    );
  }

  void _showChatOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.person_outline, color: MantotaColors.teal),
              title: const Text('Voir le profil'),
              onTap: () { Navigator.pop(ctx); context.push('/contact/${widget.conversationId}'); },
            ),
            ListTile(
              leading: const Icon(Icons.search, color: MantotaColors.teal),
              title: const Text('Rechercher dans la conversation'),
              onTap: () { Navigator.pop(ctx); },
            ),
            ListTile(
              leading: const Icon(Icons.notifications_off_outlined, color: MantotaColors.grey3),
              title: const Text('Couper les notifications'),
              onTap: () { Navigator.pop(ctx); },
            ),
            ListTile(
              leading: const Icon(Icons.block, color: MantotaColors.error),
              title: const Text('Bloquer', style: TextStyle(color: MantotaColors.error)),
              onTap: () { Navigator.pop(ctx); },
            ),
          ],
        ),
      ),
    );
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
    _loadMessages();
    final name = _nameFromId(widget.conversationId);
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 22),
          onPressed: () => context.go('/chats'),
        ),
        title: GestureDetector(
          onTap: () => context.push('/contact/${widget.conversationId}'),
          child: Row(
            children: [
              CircleAvatar(
                radius: 19,
                backgroundColor: MantotaColors.surface2,
                child: Text(name.substring(0, 2).toUpperCase(),
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
              ),
              const SizedBox(width: 10),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(name, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                  Row(
                    children: [
                      Container(
                        width: 6, height: 6,
                        decoration: const BoxDecoration(color: MantotaColors.teal, shape: BoxShape.circle),
                      ),
                      const SizedBox(width: 5),
                      const Text('En ligne', style: TextStyle(fontSize: 11, color: MantotaColors.teal)),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
        actions: [
          IconButton(icon: const Icon(Icons.phone_outlined, size: 22), onPressed: () => _showCallDialog(context, name)),
          IconButton(icon: const Icon(Icons.more_vert, size: 22), onPressed: () => _showChatOptions(context)),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              itemCount: _messages.length,
              itemBuilder: (context, index) => _MessageBubble(msg: _messages[index]),
            ),
          ),
          _ChatInput(controller: _inputController, onSend: _send),
        ],
      ),
    );
  }
}

class _Msg {
  final String text;
  final bool isFromMe;
  _Msg({required this.text, required this.isFromMe});
}

class _MessageBubble extends StatelessWidget {
  final _Msg msg;

  const _MessageBubble({required this.msg});

  @override
  Widget build(BuildContext context) {
    final isFromMe = msg.isFromMe;
    return Align(
      alignment: isFromMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
        decoration: BoxDecoration(
          color: isFromMe ? MantotaColors.teal : MantotaColors.surface1,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isFromMe ? 16 : 4),
            bottomRight: Radius.circular(isFromMe ? 4 : 16),
          ),
        ),
        child: Text(
          msg.text,
          style: TextStyle(
            fontSize: 14,
            color: isFromMe ? Colors.white : MantotaColors.grey1,
            height: 1.4,
          ),
        ),
      ),
    );
  }
}

class _ChatInput extends StatefulWidget {
  final TextEditingController controller;
  final VoidCallback onSend;

  const _ChatInput({required this.controller, required this.onSend});

  @override
  State<_ChatInput> createState() => _ChatInputState();
}

class _ChatInputState extends State<_ChatInput> {
  bool _isRecording = false;

  void _startRecording() {
    setState(() => _isRecording = true);
  }

  void _stopRecording() {
    if (_isRecording) {
      setState(() => _isRecording = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Message vocal enregistré (fonctionnalité à venir)'),
          duration: Duration(seconds: 2),
          backgroundColor: MantotaColors.teal,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: const BoxDecoration(
          color: MantotaColors.white,
          border: Border(top: BorderSide(color: MantotaColors.surface3, width: 1)),
        ),
        child: _isRecording
            ? Row(
                children: [
                  const Icon(Icons.mic, color: MantotaColors.error, size: 28),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Text('Enregistrement en cours...', style: TextStyle(fontSize: 14, color: MantotaColors.error, fontWeight: FontWeight.w600)),
                  ),
                  GestureDetector(
                    onTap: _stopRecording,
                    child: Container(
                      width: 40, height: 40,
                      decoration: const BoxDecoration(color: MantotaColors.teal, shape: BoxShape.circle),
                      child: const Icon(Icons.send, color: Colors.white, size: 20),
                    ),
                  ),
                ],
              )
            : Row(
                children: [
                  GestureDetector(
                    onLongPress: _startRecording,
                    child: const Padding(
                      padding: EdgeInsets.all(8),
                      child: Icon(Icons.mic_outlined, color: MantotaColors.grey2, size: 24),
                    ),
                  ),
                  Expanded(
                    child: TextField(
                      controller: widget.controller,
                      style: const TextStyle(fontSize: 14),
                      decoration: InputDecoration(
                        hintText: 'Message...',
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
                      onSubmitted: (_) => widget.onSend(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  GestureDetector(
                    onTap: widget.onSend,
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
