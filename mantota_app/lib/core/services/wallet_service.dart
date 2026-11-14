import '../api/api_client.dart';

/// Service pour le wallet Mantota (solde, transactions, retraits).
class WalletService {
  WalletService(this._api);

  final ApiClient _api;

  /// Récupère le solde du wallet.
  Future<WalletBalance> getBalance() async {
    final json = await _api.get('/wallet/balance');
    return WalletBalance.fromJson(json);
  }

  /// Récupère l'historique des transactions.
  Future<List<WalletTransaction>> getTransactions() async {
    final json = await _api.get('/wallet/transactions');
    final list = json['data'] as List? ?? json as List;
    return list.map((e) => WalletTransaction.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Demande un retrait.
  Future<void> requestWithdrawal(double amount, String method, String account) async {
    await _api.post('/wallet/withdraw', data: {
      'amount': amount,
      'method': method,
      'account': account,
    });
  }
}

/// Solde du wallet.
class WalletBalance {
  final double balance;
  final double pending;
  final double withdrawable;

  const WalletBalance({
    required this.balance,
    required this.pending,
    required this.withdrawable,
  });

  factory WalletBalance.fromJson(Map<String, dynamic> json) => WalletBalance(
        balance: (json['balance'] as num).toDouble(),
        pending: (json['pending'] as num?)?.toDouble() ?? 0,
        withdrawable: (json['withdrawable'] as num?)?.toDouble() ?? 0,
      );
}

/// Transaction du wallet.
class WalletTransaction {
  final String id;
  final String type;
  final String description;
  final double amount;
  final bool isPositive;
  final DateTime createdAt;

  const WalletTransaction({
    required this.id,
    required this.type,
    required this.description,
    required this.amount,
    required this.isPositive,
    required this.createdAt,
  });

  factory WalletTransaction.fromJson(Map<String, dynamic> json) => WalletTransaction(
        id: json['id'].toString(),
        type: json['type'] as String,
        description: json['description'] as String? ?? '',
        amount: (json['amount'] as num).toDouble(),
        isPositive: (json['amount'] as num).toDouble() >= 0,
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}
