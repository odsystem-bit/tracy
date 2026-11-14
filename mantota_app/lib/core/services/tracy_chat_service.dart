import '../api/api_client.dart';
import 'location_service.dart';

/// Service pour l'intégration Tracy Core (FastAPI).
///
/// Gère les conversations avec Tracy : recherche produit,
/// négociation, création de commande, réponses automatiques.
class TracyChatService {
  TracyChatService(this._api, [LocationService? location])
      : _location = location ?? LocationService();

  final ApiClient _api;
  final LocationService _location;

  /// Envoie un message à Tracy Core et récupère sa réponse.
  ///
  /// Tracy Core peut retourner :
  /// - Du texte simple
  /// - Des fiches produit (search)
  /// - Une contre-offre (négociation)
  /// - Un récapitulatif de commande
  ///
  /// [vendorMode] : true pour parler à Tracy en tant que vendeur (gestion de
  /// sa propre boutique), false pour le parcours acheteur.
  /// [storeId] : boutique ciblée quand le client discute avec un vendeur précis.
  /// La position est ajoutée si l'utilisateur l'a autorisée.
  ///
  /// Passe toujours par Laravel (authentifié) : aucune clé Tracy Core n'est
  /// embarquée dans l'APK. Les erreurs sont propagées à l'appelant.
  Future<TracyResponse> chat({
    required String conversationId,
    required String message,
    bool vendorMode = false,
    String? storeId,
    Map<String, dynamic>? context,
  }) async {
    final loc = vendorMode ? null : await _location.current();
    final json = await _api.post('/tracy/chat', data: {
      'conversation_id': conversationId,
      'message': message,
      'context': {
        ...?context,
        'mode': vendorMode ? 'vendor' : 'buyer',
        if (storeId != null) 'store_id': storeId,
        if (loc != null) 'latitude': loc.latitude,
        if (loc != null) 'longitude': loc.longitude,
      },
    });
    return TracyResponse.fromJson(json);
  }

  /// Recherche de produits via Tracy.
  Future<TracySearchResult> searchProducts(String query) async {
    final json = await _api.post('/tracy/search', data: {'query': query});
    return TracySearchResult.fromJson(json);
  }

  /// Lance une négociation pour un produit.
  Future<TracyNegotiationResult> negotiate({
    required String productId,
    required int offeredPrice,
  }) async {
    final json = await _api.post('/tracy/negotiate', data: {
      'product_id': productId,
      'offered_price': offeredPrice,
    });
    return TracyNegotiationResult.fromJson(json);
  }

  /// Identifie un produit à partir d'une photo envoyée par le client.
  ///
  /// Le client envoie une photo (ex: screenshot de live TikTok),
  /// Tracy Core la compare avec le catalogue du vendeur via CLIP + YOLOv8.
  Future<ProductIdentifyResult> identifyProduct({
    required String imageBase64,
    required int vendorId,
  }) async {
    try {
      final json = await _api.post('/tracy/identify-product', data: {
        'image_base64': imageBase64,
        'vendor_id': vendorId,
      });
      return ProductIdentifyResult.fromJson(json);
    } on ApiClientError catch (e) {
      return ProductIdentifyResult(
        matched: false,
        notFound: true,
        message: 'Service d\'identification indisponible. ${e.message}',
      );
    } on ApiNetworkError {
      return ProductIdentifyResult(
        matched: false,
        notFound: true,
        message: 'Connexion impossible. Vérifiez votre réseau.',
      );
    }
  }

  /// Vérifie la conformité d'un produit après livraison.
  ///
  /// Tracy demande au client si le produit correspond à la photo.
  /// Si non, le client envoie une photo du produit reçu pour comparaison.
  Future<ConformityResult> checkConformity({
    required String orderId,
    required int productId,
    required int storeId,
    required String verdict, // conform, partial, non_conform
    String? receivedPhotoBase64,
    String? catalogPhotoBase64,
  }) async {
    try {
      final json = await _api.post('/tracy/check-conformity', data: {
        'order_id': orderId,
        'product_id': productId,
        'store_id': storeId,
        'verdict': verdict,
        if (receivedPhotoBase64 != null) 'received_photo_base64': receivedPhotoBase64,
        if (catalogPhotoBase64 != null) 'catalog_photo_base64': catalogPhotoBase64,
      });
      return ConformityResult.fromJson(json);
    } on ApiClientError catch (e) {
      return ConformityResult(
        success: false,
        messageToClient: 'Service indisponible. ${e.message}',
      );
    } on ApiNetworkError {
      return ConformityResult(
        success: false,
        messageToClient: 'Connexion impossible. Votre retour sera enregistré plus tard.',
      );
    }
  }

  /// Récupère le score de qualité de la boutique du vendeur connecté.
  Future<ShopQualityResult> getShopQuality() async {
    try {
      final json = await _api.get('/tracy/shop-quality');
      return ShopQualityResult.fromJson(json);
    } catch (_) {
      return ShopQualityResult(score: 100, level: 'excellent', positiveSignals: 0, negativeSignals: 0);
    }
  }
}

/// Réponse générique de Tracy.
class TracyResponse {
  final String text;
  final TracyResponseType type;
  final List<TracyProductCard>? products;
  final TracyOffer? offer;
  final TracyOrderRecap? recap;
  final String? vendorConversationId;
  final String? paymentUrl;
  final String? trackingUrl;

  const TracyResponse({
    required this.text,
    required this.type,
    this.products,
    this.offer,
    this.recap,
    this.vendorConversationId,
    this.paymentUrl,
    this.trackingUrl,
  });

  factory TracyResponse.fromJson(Map<String, dynamic> json) {
    final typeStr = json['type'] as String? ?? 'text';
    final data = json['data'] is Map ? json['data'] as Map<String, dynamic> : null;
    return TracyResponse(
      text: json['text'] as String? ?? '',
      type: TracyResponseType.values.firstWhere(
        (e) => e.name == typeStr,
        orElse: () => TracyResponseType.text,
      ),
      products: (json['products'] as List?)
          ?.map((e) => TracyProductCard.fromJson(e as Map<String, dynamic>))
          .toList(),
      offer: json['offer'] != null
          ? TracyOffer.fromJson(json['offer'] as Map<String, dynamic>)
          : null,
      recap: json['recap'] != null
          ? TracyOrderRecap.fromJson(json['recap'] as Map<String, dynamic>)
          : null,
      vendorConversationId: data?['vendor_conversation_id'] as String?,
      paymentUrl: data?['payment_url'] as String?,
      trackingUrl: data?['tracking_url'] as String?,
    );
  }
}

enum TracyResponseType { text, search, offer, recap, confirmation }

/// Fiche produit retournée par Tracy.
class TracyProductCard {
  final String id;
  final String name;
  final String shop;
  final String price;
  final double rawPrice;
  final String? imageUrl;
  final String storeId;

  const TracyProductCard({
    required this.id,
    required this.name,
    required this.shop,
    required this.price,
    this.rawPrice = 0,
    this.imageUrl,
    this.storeId = '',
  });

  factory TracyProductCard.fromJson(Map<String, dynamic> json) =>
      TracyProductCard(
        id: json['id'].toString(),
        name: json['name'] as String? ?? 'Produit',
        shop: json['shop'] as String? ?? '',
        price: json['price']?.toString() ?? '',
        rawPrice: (json['raw_price'] as num?)?.toDouble() ?? 0,
        imageUrl: json['image_url'] as String?,
        storeId: json['store_id']?.toString() ?? '',
      );

  /// Adaptation pour l'affichage commun des fiches produit.
  ProductMatch toMatch() => ProductMatch(
        productId: id,
        productName: name,
        price: rawPrice,
        imageUrl: imageUrl,
        confidence: 1,
        storeId: storeId,
      );
}

/// Contre-offre de négociation.
class TracyOffer {
  final int price;
  final int discountPercent;
  final bool isBestPrice;

  const TracyOffer({
    required this.price,
    required this.discountPercent,
    required this.isBestPrice,
  });

  factory TracyOffer.fromJson(Map<String, dynamic> json) => TracyOffer(
        price: (json['price'] as num).toInt(),
        discountPercent: (json['discount_percent'] as num?)?.toInt() ?? 0,
        isBestPrice: json['is_best_price'] as bool? ?? true,
      );
}

/// Récapitulatif de commande.
class TracyOrderRecap {
  final String productName;
  final int negotiatedPrice;
  final int deliveryFee;
  final int total;
  final String address;

  const TracyOrderRecap({
    required this.productName,
    required this.negotiatedPrice,
    required this.deliveryFee,
    required this.total,
    required this.address,
  });

  factory TracyOrderRecap.fromJson(Map<String, dynamic> json) => TracyOrderRecap(
        productName: json['product_name'] as String,
        negotiatedPrice: (json['negotiated_price'] as num).toInt(),
        deliveryFee: (json['delivery_fee'] as num?)?.toInt() ?? 0,
        total: (json['total'] as num).toInt(),
        address: json['address'] as String? ?? '',
      );
}

/// Résultat de recherche Tracy.
class TracySearchResult {
  final String message;
  final List<TracyProductCard> products;

  const TracySearchResult({required this.message, required this.products});

  factory TracySearchResult.fromJson(Map<String, dynamic> json) =>
      TracySearchResult(
        message: json['message'] as String? ?? '',
        products: (json['products'] as List? ?? [])
            .map((e) => TracyProductCard.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

/// Résultat de négociation.
class TracyNegotiationResult {
  final String message;
  final TracyOffer? offer;

  const TracyNegotiationResult({required this.message, this.offer});

  factory TracyNegotiationResult.fromJson(Map<String, dynamic> json) =>
      TracyNegotiationResult(
        message: json['message'] as String? ?? '',
        offer: json['offer'] != null
            ? TracyOffer.fromJson(json['offer'] as Map<String, dynamic>)
            : null,
      );
}

// ── Vision: Product Identification ──────────────────────────────

/// Résultat de l'identification produit par photo.
class ProductIdentifyResult {
  final bool matched;
  final bool needsConfirmation;
  final bool notFound;
  final List<ProductMatch> topMatches;
  final String message;
  final double processingTimeMs;

  const ProductIdentifyResult({
    required this.matched,
    this.needsConfirmation = false,
    this.notFound = false,
    this.topMatches = const [],
    this.message = '',
    this.processingTimeMs = 0,
  });

  factory ProductIdentifyResult.fromJson(Map<String, dynamic> json) =>
      ProductIdentifyResult(
        matched: json['matched'] as bool? ?? false,
        needsConfirmation: json['needs_confirmation'] as bool? ?? false,
        notFound: json['not_found'] as bool? ?? false,
        message: json['message'] as String? ?? '',
        processingTimeMs: (json['processing_time_ms'] as num?)?.toDouble() ?? 0,
        topMatches: (json['top_matches'] as List? ?? [])
            .map((e) => ProductMatch.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

/// Un produit identifié avec son score de confiance.
class ProductMatch {
  final String productId;
  final String productName;
  final double price;
  final String? imageUrl;
  final double confidence;
  final String storeId;
  final int? stock;

  const ProductMatch({
    required this.productId,
    required this.productName,
    required this.price,
    this.imageUrl,
    required this.confidence,
    required this.storeId,
    this.stock,
  });

  factory ProductMatch.fromJson(Map<String, dynamic> json) => ProductMatch(
        productId: json['product_id'].toString(),
        productName: json['product_name'] as String? ?? 'Produit',
        price: (json['price'] as num?)?.toDouble() ?? 0,
        imageUrl: json['image_url'] as String?,
        confidence: (json['confidence'] as num?)?.toDouble() ?? 0,
        storeId: json['store_id'].toString(),
        stock: json['stock'] as int?,
      );
}

// ── Vision: Conformity Check ────────────────────────────────────

/// Résultat de la vérification de conformité post-livraison.
class ConformityResult {
  final bool success;
  final String orderId;
  final String productId;
  final String storeId;
  final String clientVerdict;
  final double? photoSimilarity;
  final bool photoChecked;
  final String messageToClient;
  final String messageToVendor;
  final String? adminNotification;

  const ConformityResult({
    this.success = true,
    this.orderId = '',
    this.productId = '',
    this.storeId = '',
    this.clientVerdict = '',
    this.photoSimilarity,
    this.photoChecked = false,
    this.messageToClient = '',
    this.messageToVendor = '',
    this.adminNotification,
  });

  factory ConformityResult.fromJson(Map<String, dynamic> json) =>
      ConformityResult(
        success: json['signal_generated'] as bool? ?? true,
        orderId: json['order_id']?.toString() ?? '',
        productId: json['product_id']?.toString() ?? '',
        storeId: json['store_id']?.toString() ?? '',
        clientVerdict: json['client_verdict'] as String? ?? '',
        photoSimilarity: (json['photo_similarity'] as num?)?.toDouble(),
        photoChecked: json['photo_checked'] as bool? ?? false,
        messageToClient: json['message_to_client'] as String? ?? '',
        messageToVendor: json['message_to_vendor'] as String? ?? '',
        adminNotification: json['admin_notification'] as String?,
      );
}

// ── Vision: Shop Quality Score ──────────────────────────────────

/// Score de qualité de la boutique du vendeur.
class ShopQualityResult {
  final int score;
  final String level;
  final int positiveSignals;
  final int negativeSignals;
  final List<QualitySignalItem> recentSignals;

  const ShopQualityResult({
    required this.score,
    required this.level,
    this.positiveSignals = 0,
    this.negativeSignals = 0,
    this.recentSignals = const [],
  });

  factory ShopQualityResult.fromJson(Map<String, dynamic> json) =>
      ShopQualityResult(
        score: (json['score'] as num?)?.toInt() ?? 100,
        level: json['level'] as String? ?? 'excellent',
        positiveSignals: (json['positive_signals'] as num?)?.toInt() ?? 0,
        negativeSignals: (json['negative_signals'] as num?)?.toInt() ?? 0,
        recentSignals: (json['recent_signals'] as List? ?? [])
            .map((e) => QualitySignalItem.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

/// Un signal de qualité récent.
class QualitySignalItem {
  final String type;
  final int weight;
  final String? description;
  final String? date;

  const QualitySignalItem({
    required this.type,
    required this.weight,
    this.description,
    this.date,
  });

  factory QualitySignalItem.fromJson(Map<String, dynamic> json) =>
      QualitySignalItem(
        type: json['type'] as String? ?? '',
        weight: (json['weight'] as num?)?.toInt() ?? 0,
        description: json['description'] as String?,
        date: json['date'] as String?,
      );
}
