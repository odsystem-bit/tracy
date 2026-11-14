import '../api/api_client.dart';
import '../models/order.dart';

/// Service pour les commandes (acheteur et vendeur).
class OrderService {
  OrderService(this._api);

  final ApiClient _api;

  /// Commandes de l'utilisateur connecté (acheteur).
  Future<List<Order>> myOrders() async {
    final json = await _api.get('/orders');
    final list = json['data'] as List? ?? json as List;
    return list.map((e) => Order.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Commandes reçues par le vendeur.
  Future<List<Order>> vendorOrders() async {
    final json = await _api.get('/vendor/orders');
    final list = json['data'] as List? ?? json as List;
    return list.map((e) => Order.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Détail d'une commande.
  Future<Order> getById(String id) async {
    final json = await _api.get('/orders/$id');
    return Order.fromJson(json);
  }

  /// Crée une commande (après négociation Tracy).
  Future<Order> create(Map<String, dynamic> data) async {
    final json = await _api.post('/orders', data: data);
    return Order.fromJson(json);
  }

  /// Met à jour le statut d'une commande (vendeur).
  Future<Order> updateStatus(String id, String status) async {
    final json = await _api.patch('/orders/$id/status', data: {'status': status});
    return Order.fromJson(json);
  }

  /// Confirme la réception (code PIN client).
  Future<void> confirmDelivery(String id, String pinCode) async {
    await _api.post('/orders/$id/confirm-delivery', data: {'pin_code': pinCode});
  }
}
