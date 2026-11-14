import '../api/api_client.dart';

/// Service pour la gestion de boutique (vendeur).
class StoreService {
  StoreService(this._api);

  final ApiClient _api;

  /// Récupère la boutique du vendeur connecté.
  Future<Store?> getMyStore() async {
    try {
      final json = await _api.get('/vendor/store');
      return Store.fromJson(json);
    } on ApiClientError catch (e) {
      if (e.statusCode == 404) return null;
      rethrow;
    }
  }

  /// Crée une boutique.
  Future<Store> create(Map<String, dynamic> data) async {
    final json = await _api.post('/stores', data: data);
    return Store.fromJson(json);
  }

  /// Met à jour la boutique.
  Future<Store> update(String id, Map<String, dynamic> data) async {
    final json = await _api.put('/stores/$id', data: data);
    return Store.fromJson(json);
  }

  /// Récupère les boutiques populaires (page Découvrir).
  Future<List<Store>> popular() async {
    final json = await _api.get('/stores/popular');
    final list = json['data'] as List? ?? json as List;
    return list.map((e) => Store.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Statistiques de la boutique du vendeur.
  Future<Map<String, dynamic>> getStats() async {
    final json = await _api.get('/vendor/store/stats');
    return json;
  }
}

/// Modèle de boutique.
class Store {
  final String id;
  final String name;
  final String? description;
  final String? logoUrl;
  final String? address;
  final double? latitude;
  final double? longitude;
  final String type;
  final double rating;
  final int productCount;
  final String? category;

  const Store({
    required this.id,
    required this.name,
    this.description,
    this.logoUrl,
    this.address,
    this.latitude,
    this.longitude,
    required this.type,
    required this.rating,
    required this.productCount,
    this.category,
  });

  factory Store.fromJson(Map<String, dynamic> json) => Store(
        id: json['id'].toString(),
        name: json['name'] as String,
        description: json['description'] as String?,
        logoUrl: json['logo_url'] as String?,
        address: json['address'] as String?,
        latitude: (json['latitude'] as num?)?.toDouble(),
        longitude: (json['longitude'] as num?)?.toDouble(),
        type: json['type'] as String? ?? 'physique',
        rating: (json['rating'] as num?)?.toDouble() ?? 0,
        productCount: json['product_count'] as int? ?? 0,
        category: json['category'] as String?,
      );
}
