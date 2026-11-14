import '../api/api_client.dart';
import '../models/product.dart';

/// Service pour les produits (catalogue, recherche, CRUD vendeur).
class ProductService {
  ProductService(this._api);

  final ApiClient _api;

  /// Recherche de produits par mot-clé.
  Future<List<Product>> search(String query) async {
    final json = await _api.get('/products/search', queryParameters: {'q': query});
    final list = json['data'] as List? ?? json as List;
    return list.map((e) => Product.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Produits tendance (page Découvrir).
  Future<List<Product>> trending() async {
    final json = await _api.get('/products/trending');
    final list = json['data'] as List? ?? json as List;
    return list.map((e) => Product.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Produits d'une boutique.
  Future<List<Product>> byStore(String storeId) async {
    final json = await _api.get('/stores/$storeId/products');
    final list = json['data'] as List? ?? json as List;
    return list.map((e) => Product.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Crée un produit (vendeur).
  Future<Product> create(Map<String, dynamic> data) async {
    final json = await _api.post('/products', data: data);
    return Product.fromJson(json);
  }

  /// Met à jour un produit.
  Future<Product> update(String id, Map<String, dynamic> data) async {
    final json = await _api.put('/products/$id', data: data);
    return Product.fromJson(json);
  }

  /// Supprime un produit.
  Future<void> delete(String id) async {
    await _api.delete('/products/$id');
  }
}
