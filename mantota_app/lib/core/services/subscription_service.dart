import '../api/api_client.dart';

/// Service d'abonnements vendeur pour l'application mobile MANTOTA.
///
/// Gère les plans Free, Starter, Standard, Pro et TPF.
class SubscriptionService {
  SubscriptionService(this._api);

  final ApiClient _api;

  /// Récupère tous les plans disponibles.
  Future<List<SubscriptionPlan>> getPlans() async {
    final json = await _api.get('/subscriptions/plans');
    final list = json['plans'] as List? ?? [];
    return list
        .map((e) => SubscriptionPlan.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Récupère le plan actuel du vendeur.
  Future<CurrentSubscription> getCurrent() async {
    final json = await _api.get('/subscriptions/current');
    return CurrentSubscription.fromJson(json);
  }

  /// Active un plan payant (initie le paiement Moneroo).
  Future<PaymentInitResult> activate(String plan) async {
    final json = await _api.post('/subscriptions/activate', data: {
      'plan': plan,
    });
    return PaymentInitResult.fromJson(json);
  }

  /// Active le plan gratuit.
  Future<void> activateFree() async {
    await _api.post('/subscriptions/activate-free', data: {});
  }

  /// Confirme un abonnement après paiement.
  Future<Map<String, dynamic>> confirm(String reference) async {
    return _api.post('/subscriptions/confirm', data: {
      'reference': reference,
    });
  }
}

/// Plan d'abonnement.
class SubscriptionPlan {
  final String id;
  final String name;
  final double price;
  final int durationDays;
  final double commissionRate;
  final List<String> features;
  final int? productLimit;
  final bool isFree;

  const SubscriptionPlan({
    required this.id,
    required this.name,
    required this.price,
    required this.durationDays,
    required this.commissionRate,
    required this.features,
    this.productLimit,
    required this.isFree,
  });

  factory SubscriptionPlan.fromJson(Map<String, dynamic> json) =>
      SubscriptionPlan(
        id: json['id'] as String,
        name: json['name'] as String,
        price: (json['price'] as num).toDouble(),
        durationDays: json['duration_days'] as int? ?? 0,
        commissionRate: (json['commission_rate'] as num).toDouble(),
        features: (json['features'] as List? ?? [])
            .map((e) => e as String)
            .toList(),
        productLimit: json['product_limit'] as int?,
        isFree: json['is_free'] as bool? ?? false,
      );
}

/// Abonnement actuel du vendeur.
class CurrentSubscription {
  final String plan;
  final String planName;
  final bool isActive;
  final DateTime? expiresAt;
  final double commissionRate;
  final int? productLimit;
  final List<String> features;

  const CurrentSubscription({
    required this.plan,
    required this.planName,
    required this.isActive,
    this.expiresAt,
    required this.commissionRate,
    this.productLimit,
    required this.features,
  });

  factory CurrentSubscription.fromJson(Map<String, dynamic> json) =>
      CurrentSubscription(
        plan: json['plan'] as String? ?? 'free',
        planName: json['plan_name'] as String? ?? 'Free',
        isActive: json['is_active'] as bool? ?? false,
        expiresAt: json['expires_at'] != null
            ? DateTime.parse(json['expires_at'] as String)
            : null,
        commissionRate: (json['commission_rate'] as num).toDouble(),
        productLimit: json['product_limit'] as int?,
        features: (json['features'] as List? ?? [])
            .map((e) => e as String)
            .toList(),
      );
}

/// Résultat d'initialisation de paiement (réutilisé depuis payment_service).
class PaymentInitResult {
  final String? paymentId;
  final String? checkoutUrl;
  final String reference;
  final double? amount;

  const PaymentInitResult({
    this.paymentId,
    this.checkoutUrl,
    required this.reference,
    this.amount,
  });

  factory PaymentInitResult.fromJson(Map<String, dynamic> json) =>
      PaymentInitResult(
        paymentId: json['payment_id'] as String?,
        checkoutUrl: json['checkout_url'] as String?,
        reference: json['reference'] as String? ?? '',
        amount: (json['amount'] as num?)?.toDouble(),
      );
}
