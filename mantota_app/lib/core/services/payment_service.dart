import '../api/api_client.dart';

/// Service de paiement pour l'application mobile MANTOTA.
///
/// Gère l'initialisation des paiements via Moneroo (backend Laravel)
/// et la vérification du statut des paiements.
class PaymentService {
  PaymentService(this._api);

  final ApiClient _api;

  /// Initialise un paiement pour une commande via Moneroo.
  ///
  /// Retourne l'URL de checkout Moneroo vers laquelle rediriger l'utilisateur.
  Future<PaymentInitResult> initOrderPayment(String orderId) async {
    final json = await _api.post('/orders/$orderId/pay', data: {});
    return PaymentInitResult.fromJson(json);
  }

  /// Vérifie le statut d'un paiement.
  Future<PaymentStatusResult> checkStatus(String orderId) async {
    final json = await _api.get('/orders/$orderId/track');
    return PaymentStatusResult.fromJson(json);
  }

  /// Initialise un paiement d'abonnement (Starter, Standard, Pro, TPF).
  Future<PaymentInitResult> initSubscriptionPayment(String plan) async {
    final json = await _api.post('/subscriptions/activate', data: {
      'plan': plan,
    });
    return PaymentInitResult.fromJson(json);
  }

  /// Initialise un dépôt sur wallet.
  Future<PaymentInitResult> initWalletDeposit(double amount) async {
    final json = await _api.post('/wallet/deposit', data: {
      'amount': amount,
    });
    return PaymentInitResult.fromJson(json);
  }
}

/// Résultat de l'initialisation d'un paiement.
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

/// Statut d'un paiement vérifié.
class PaymentStatusResult {
  final String orderStatus;
  final String paymentStatus;
  final String reference;

  const PaymentStatusResult({
    required this.orderStatus,
    required this.paymentStatus,
    required this.reference,
  });

  factory PaymentStatusResult.fromJson(Map<String, dynamic> json) =>
      PaymentStatusResult(
        orderStatus: (json['order']?['status'] as String?) ?? 'pending',
        paymentStatus:
            (json['order']?['payment_status'] as String?) ?? 'pending',
        reference:
            (json['order']?['reference'] as String?) ?? '',
      );
}
