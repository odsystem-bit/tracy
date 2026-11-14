import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/adinkra_background.dart';

/// Écran 15b — Wallet détaillé.
///
/// Solde, historique des transactions, bouton retrait.
class WalletScreen extends ConsumerWidget {
  const WalletScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final balanceAsync = ref.watch(walletBalanceProvider);
    final transactionsAsync = ref.watch(walletTransactionsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Wallet'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: Stack(
        children: [
          const AdinkraBackground(opacity: 0.04),
          ListView(
        padding: const EdgeInsets.all(14),
        children: [
          // Carte solde
          balanceAsync.when(
            data: (b) => Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [MantotaColors.teal, MantotaColors.tealDark],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Solde disponible', style: TextStyle(fontSize: 14, color: Colors.white70)),
                  const SizedBox(height: 6),
                  Text('${b.balance.toInt()} F', style: const TextStyle(fontSize: 34, fontWeight: FontWeight.w900, color: Colors.white)),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Text('En attente: ${b.pending.toInt()} F', style: const TextStyle(fontSize: 13, color: Colors.white70)),
                      const SizedBox(width: 16),
                      Text('Retirable: ${b.withdrawable.toInt()} F', style: const TextStyle(fontSize: 13, color: Colors.white)),
                    ],
                  ),
                ],
              ),
            ),
            loading: () => const Center(child: Padding(padding: EdgeInsets.all(20), child: CircularProgressIndicator())),
            error: (e, _) => Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: MantotaColors.surface1,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Solde disponible', style: TextStyle(fontSize: 14, color: MantotaColors.grey2)),
                  const SizedBox(height: 6),
                  Text('Erreur de chargement', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: MantotaColors.error)),
                  const SizedBox(height: 8),
                  Text(e.toString(), style: const TextStyle(fontSize: 12, color: MantotaColors.grey4)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Actions
          Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: () => _showWithdrawDialog(context, ref),
                  child: const Text('Retirer'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton(
                  onPressed: () => _showDepositDialog(context, ref),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: MantotaColors.surface1,
                    foregroundColor: MantotaColors.grey1,
                  ),
                  child: const Text('Déposer'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          // Transactions récentes
          const Text('Transactions récentes', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          transactionsAsync.when(
            data: (txs) => txs.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(30),
                      child: Column(
                        children: [
                          Icon(Icons.receipt_long_outlined, size: 40, color: MantotaColors.grey4),
                          const SizedBox(height: 10),
                          const Text('Aucune transaction', style: TextStyle(fontSize: 14, color: MantotaColors.grey3)),
                        ],
                      ),
                    ),
                  )
                : Column(
              children: txs.map((t) => _TransactionTile(
                type: t.type,
                description: t.description,
                amount: '${t.isPositive ? '+' : ''}${t.amount.toInt()} F',
                isPositive: t.isPositive,
                time: t.createdAt.toString(),
              )).toList(),
            ),
            loading: () => const Center(child: Padding(padding: EdgeInsets.all(20), child: CircularProgressIndicator())),
            error: (e, _) => Center(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Text('Erreur: $e', style: const TextStyle(fontSize: 13, color: MantotaColors.grey3)),
              ),
            ),
          ),
        ],
      ),
        ],
      ),
    );
  }

  void _showWithdrawDialog(BuildContext context, WidgetRef ref) {
    final amountCtrl = TextEditingController();
    final methodCtrl = TextEditingController(text: 'mtn_benin');
    final accountCtrl = TextEditingController();
    bool isSubmitting = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) => SafeArea(
          child: Padding(
            padding: EdgeInsets.fromLTRB(20, 20, 20, MediaQuery.of(ctx).viewInsets.bottom + 20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Retrait', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                const SizedBox(height: 16),
                TextField(
                  controller: amountCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Montant (F)',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: methodCtrl.text,
                  decoration: const InputDecoration(
                    labelText: 'Méthode',
                    border: OutlineInputBorder(),
                  ),
                  items: const [
                    DropdownMenuItem(value: 'mtn_benin', child: Text('MTN Mobile Money')),
                    DropdownMenuItem(value: 'moov_benin', child: Text('Moov Money')),
                    DropdownMenuItem(value: 'celtiis_benin', child: Text('Celtiis Cash')),
                  ],
                  onChanged: (v) => methodCtrl.text = v ?? 'mtn_benin',
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: accountCtrl,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Numéro de téléphone',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: isSubmitting
                        ? null
                        : () async {
                            final amount = double.tryParse(amountCtrl.text);
                            if (amount == null || amount <= 0) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('Montant invalide.')));
                              return;
                            }
                            setState(() => isSubmitting = true);
                            try {
                              final svc = await ref.read(walletServiceProvider.future);
                              await svc.requestWithdrawal(amount, methodCtrl.text, accountCtrl.text);
                              if (context.mounted) {
                                Navigator.pop(ctx);
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text('Demande de retrait envoyée.')));
                                ref.invalidate(walletBalanceProvider);
                                ref.invalidate(walletTransactionsProvider);
                              }
                            } catch (e) {
                              setState(() => isSubmitting = false);
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text('Erreur: $e')));
                              }
                            }
                          },
                    child: isSubmitting
                        ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Text('Confirmer le retrait'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showDepositDialog(BuildContext context, WidgetRef ref) {
    final amountCtrl = TextEditingController();
    bool isSubmitting = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) => SafeArea(
          child: Padding(
            padding: EdgeInsets.fromLTRB(20, 20, 20, MediaQuery.of(ctx).viewInsets.bottom + 20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Dépôt', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                const SizedBox(height: 16),
                TextField(
                  controller: amountCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Montant (F)',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: isSubmitting
                        ? null
                        : () async {
                            final amount = double.tryParse(amountCtrl.text);
                            if (amount == null || amount <= 0) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('Montant invalide.')));
                              return;
                            }
                            setState(() => isSubmitting = true);
                            try {
                              final api = await ref.read(apiClientProvider.future);
                              final result = await api.post('/wallet/deposit', data: {'amount': amount});
                              final checkoutUrl = result['checkout_url'] as String?;
                              if (checkoutUrl != null && checkoutUrl.isNotEmpty) {
                                if (context.mounted) {
                                  Navigator.pop(ctx);
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Redirection vers Moneroo...')));
                                }
                              } else {
                                if (context.mounted) {
                                  Navigator.pop(ctx);
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Dépôt initialisé.')));
                                  ref.invalidate(walletBalanceProvider);
                                  ref.invalidate(walletTransactionsProvider);
                                }
                              }
                            } catch (e) {
                              setState(() => isSubmitting = false);
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text('Erreur: $e')));
                              }
                            }
                          },
                    child: isSubmitting
                        ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Text('Déposer via Moneroo'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _TransactionTile extends StatelessWidget {
  final String type;
  final String description;
  final String amount;
  final bool isPositive;
  final String time;

  const _TransactionTile({
    required this.type,
    required this.description,
    required this.amount,
    required this.isPositive,
    required this.time,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
      child: Row(
        children: [
          Container(
            width: 36, height: 36,
            decoration: BoxDecoration(
              color: isPositive ? MantotaColors.teal.withValues(alpha: 0.15) : MantotaColors.error.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              isPositive ? Icons.arrow_downward : Icons.arrow_upward,
              color: isPositive ? MantotaColors.teal : MantotaColors.error,
              size: 18,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(type, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                Text(description, style: const TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                Text(time, style: const TextStyle(fontSize: 11, color: MantotaColors.grey4)),
              ],
            ),
          ),
          Text(
            amount,
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w800,
              color: isPositive ? MantotaColors.teal : MantotaColors.error,
            ),
          ),
        ],
      ),
    );
  }
}
