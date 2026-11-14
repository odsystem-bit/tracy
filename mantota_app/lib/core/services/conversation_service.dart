import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../models/conversation.dart';
import '../theme/mantota_theme.dart';

/// Service pour les conversations et messages.
class ConversationService {
  ConversationService(this._api);

  final ApiClient _api;

  /// Récupère la liste des conversations de l'utilisateur connecté.
  Future<List<Conversation>> getConversations() async {
    final json = await _api.get('/conversations');
    final list = json['data'] as List? ?? json as List;
    return list.map((e) => Conversation.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Récupère les messages d'une conversation.
  Future<List<Message>> getMessages(String conversationId) async {
    final json = await _api.get('/conversations/$conversationId/messages');
    final list = json['data'] as List? ?? json as List;
    return list.map((e) => Message.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Envoie un message texte dans une conversation.
  Future<Message> sendMessage({
    required String conversationId,
    required String text,
  }) async {
    final json = await _api.post('/conversations/$conversationId/messages', data: {
      'type': 'text',
      'content': text,
    });
    return Message.fromJson(json);
  }

  /// Marque une conversation comme lue.
  Future<void> markAsRead(String conversationId) async {
    await _api.post('/conversations/$conversationId/read');
  }

  /// Recherche un utilisateur par nom, numéro de téléphone ou nom de boutique.
  /// Retourne une liste (potentiellement vide) des utilisateurs trouvés.
  Future<List<UserSearchResult>> searchByQuery(String query) async {
    try {
      final json = await _api.get('/users/search', queryParameters: {'q': query});
      final users = json['users'] as List? ?? [];
      if (users.isEmpty) {
        // Fallback: ancien format avec user unique
        if (json['user'] != null) {
          return [UserSearchResult.fromJson(json['user'] as Map<String, dynamic>)];
        }
        return [];
      }
      return users.map((e) => UserSearchResult.fromJson(e as Map<String, dynamic>)).toList();
    } on ApiClientError catch (e) {
      if (e.statusCode == 404) return [];
      rethrow;
    }
  }

  /// Démarre ou récupère une conversation avec un utilisateur par son ID.
  Future<Conversation> startConversation(String userId) async {
    final json = await _api.post('/conversations', data: {'user_id': userId});
    return Conversation.fromJson(json);
  }

  /// Récupère les statuts/stories des contacts (visible par ceux avec qui on a échangé).
  Future<List<UserStatus>> getStatuses() async {
    try {
      final json = await _api.get('/statuses');
      final list = json['data'] as List? ?? json as List;
      return list.map((e) => UserStatus.fromJson(e as Map<String, dynamic>)).toList();
    } on ApiClientError {
      return [];
    }
  }

  /// Publie un statut (texte ou image).
  Future<void> postStatus({required String type, required String content}) async {
    await _api.post('/statuses', data: {'type': type, 'content': content});
  }

  /// Récupère les statuts de Tracy (promotions, annonces).
  Future<List<StatusItem>> getTracyStatuses() async {
    return [
      StatusItem(
        id: 'tracy_1',
        type: StatusType.text,
        content: '🔥 Offre spéciale : 20% sur tous les produits électroniques cette semaine !',
        createdAt: DateTime.now().subtract(const Duration(hours: 2)),
        backgroundColor: MantotaColors.teal,
      ),
      StatusItem(
        id: 'tracy_2',
        type: StatusType.text,
        content: '✅ Nouveau vendeur vérifié : TechStore Cotonou — Produits authentiques garantis',
        createdAt: DateTime.now().subtract(const Duration(hours: 5)),
        backgroundColor: const Color(0xFF1B8B6E),
      ),
      StatusItem(
        id: 'tracy_3',
        type: StatusType.text,
        content: '💡 Astuce Tracy : Négociez vos prix avec moi directement dans le chat !',
        createdAt: DateTime.now().subtract(const Duration(hours: 8)),
        backgroundColor: MantotaColors.coral,
      ),
    ];
  }
}

/// Résultat de recherche d'utilisateur par téléphone.
class UserSearchResult {
  final int id;
  final String name;
  final String? displayName;
  final String phone;
  final String? avatarUrl;
  final bool isOnline;
  final bool isVendor;
  final String? shopName;

  const UserSearchResult({
    required this.id,
    required this.name,
    this.displayName,
    required this.phone,
    this.avatarUrl,
    this.isOnline = false,
    this.isVendor = false,
    this.shopName,
  });

  factory UserSearchResult.fromJson(Map<String, dynamic> json) => UserSearchResult(
        id: json['id'] as int,
        name: json['name'] as String? ?? '',
        displayName: json['display_name'] as String?,
        phone: json['phone'] as String? ?? '',
        avatarUrl: json['avatar_url'] as String?,
        isOnline: json['is_online'] as bool? ?? false,
        isVendor: json['is_vendor'] as bool? ?? false,
        shopName: json['shop_name'] as String?,
      );

  String get bestName => displayName?.isNotEmpty == true ? displayName! : name;
}

enum StatusType { text, image }

/// Un item de statut (une "story").
class StatusItem {
  final String id;
  final StatusType type;
  final String content;
  final DateTime createdAt;
  final Color? backgroundColor;

  const StatusItem({
    required this.id,
    required this.type,
    required this.content,
    required this.createdAt,
    this.backgroundColor,
  });

  factory StatusItem.fromJson(Map<String, dynamic> json) => StatusItem(
        id: json['id'].toString(),
        type: json['type'] == 'image' ? StatusType.image : StatusType.text,
        content: json['content'] as String? ?? '',
        createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ?? DateTime.now(),
        backgroundColor: null,
      );
}

/// Statuts d'un utilisateur (groupés comme WhatsApp).
class UserStatus {
  final int userId;
  final String name;
  final String? avatarUrl;
  final List<StatusItem> items;
  final bool isTracy;

  const UserStatus({
    required this.userId,
    required this.name,
    this.avatarUrl,
    required this.items,
    this.isTracy = false,
  });

  factory UserStatus.fromJson(Map<String, dynamic> json) => UserStatus(
        userId: json['user_id'] as int? ?? 0,
        name: json['name'] as String? ?? '',
        avatarUrl: json['avatar_url'] as String?,
        items: (json['items'] as List? ?? [])
            .map((e) => StatusItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        isTracy: json['is_tracy'] as bool? ?? false,
      );

  bool get hasUnviewed => items.isNotEmpty;
}
