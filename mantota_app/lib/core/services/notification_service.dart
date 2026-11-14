import '../api/api_client.dart';

/// Service pour les notifications.
class NotificationService {
  NotificationService(this._api);

  final ApiClient _api;

  /// Récupère les notifications de l'utilisateur.
  Future<List<AppNotification>> getNotifications() async {
    final json = await _api.get('/notifications');
    final list = json['data'] as List? ?? json as List;
    return list.map((e) => AppNotification.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Notifications vendeur.
  Future<List<AppNotification>> getVendorNotifications() async {
    final json = await _api.get('/vendor/notifications');
    final list = json['data'] as List? ?? json as List;
    return list.map((e) => AppNotification.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Marque toutes les notifications comme lues.
  Future<void> markAllRead() async {
    await _api.post('/notifications/read-all');
  }

  /// Marque une notification comme lue.
  Future<void> markRead(String id) async {
    await _api.post('/notifications/$id/read');
  }
}

/// Modèle de notification.
class AppNotification {
  final String id;
  final String type;
  final String title;
  final String body;
  final bool isRead;
  final DateTime createdAt;

  const AppNotification({
    required this.id,
    required this.type,
    required this.title,
    required this.body,
    required this.isRead,
    required this.createdAt,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) => AppNotification(
        id: json['id'].toString(),
        type: json['type'] as String? ?? 'general',
        title: json['title'] as String,
        body: json['body'] as String? ?? '',
        isRead: json['is_read'] as bool? ?? false,
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}
