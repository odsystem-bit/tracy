import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran Abonnements — Plans Free, Starter, Standard, Pro, TPF.
///
/// Affiche les plans disponibles, le plan actuel, et permet
/// d'activer un plan payant via Moneroo.
class SubscriptionScreen extends ConsumerStatefulWidget {
  const SubscriptionScreen({super.key});

  @override
  ConsumerState<SubscriptionScreen> createState() =>
      _SubscriptionScreenState();
}

class _SubscriptionScreenState extends ConsumerState<SubscriptionScreen> {
  String? _activatingPlan;
  String? _errorMessage;

  @override
  Widget build(BuildContext context) {
    final plansAsync = ref.watch(subscriptionPlansProvider);
    final currentAsync = ref.watch(currentSubscriptionProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Abonnements'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: plansAsync.when(
        data: (plans) => currentAsync.when(
          data: (current) => _buildContent(context, plans, current),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (_, __) => _buildContent(context, plans, null),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.cloud_off, size: 48, color: MantotaColors.grey3),
              const SizedBox(height: 12),
              Text('Erreur: $e', style: const TextStyle(color: MantotaColors.grey2)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.refresh(subscriptionPlansProvider),
                child: const Text('Réessayer'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildContent(
      BuildContext context, List<dynamic> plans, dynamic current) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Plan actuel
        if (current != null) ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [MantotaColors.tealDark, Color(0xFF12121F)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('PLAN ACTUEL',
                    style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.5,
                        color: Colors.white54)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Text(current.planName,
                        style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.w900,
                            color: Colors.white)),
                    const Spacer(),
                    if (current.isActive)
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: MantotaColors.teal,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: const Text('ACTIF',
                            style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                color: Colors.white)),
                      ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Commission: ${(current.commissionRate * 100).toStringAsFixed(0)}% par vente',
                  style: const TextStyle(fontSize: 13, color: Colors.white70),
                ),
                if (current.expiresAt != null)
                  Text(
                    'Expire le ${current.expiresAt!.day}/${current.expiresAt!.month}/${current.expiresAt!.year}',
                    style: const TextStyle(fontSize: 12, color: Colors.white54),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 24),
        ],
        // Titre
        const Text('CHOISIR UN PLAN',
            style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.5,
                color: MantotaColors.grey2)),
        const SizedBox(height: 14),
        // Plans
        ...plans.map<Widget>((plan) => _buildPlanCard(plan, current)),
      ],
    );
  }

  Widget _buildPlanCard(dynamic plan, dynamic current) {
    final isCurrent = current != null && current.plan == plan.id;
    final isFree = plan.isFree;
    final isActivating = _activatingPlan == plan.id;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isCurrent ? MantotaColors.tealPale : MantotaColors.surface1,
        border: Border.all(
          color: isCurrent
              ? MantotaColors.teal.withValues(alpha: 0.4)
              : MantotaColors.surface3,
        ),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(plan.name,
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.w800)),
              ),
              if (isCurrent)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: MantotaColors.teal,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Text('ACTUEL',
                      style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: Colors.white)),
                ),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                isFree
                    ? 'Gratuit'
                    : '${plan.price.toStringAsFixed(0)} FCFA',
                style: const TextStyle(
                    fontSize: 22, fontWeight: FontWeight.w900),
              ),
              if (!isFree && plan.durationDays > 0) ...[
                const SizedBox(width: 4),
                Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Text(
                    '/ ${plan.durationDays == 365 ? 'an' : 'mois'}',
                    style: const TextStyle(
                        fontSize: 13, color: MantotaColors.grey2),
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Commission: ${(plan.commissionRate * 100).toStringAsFixed(0)}% par vente',
            style: const TextStyle(fontSize: 13, color: MantotaColors.teal),
          ),
          const SizedBox(height: 12),
          // Features
          ...plan.features.map<Widget>((f) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.check_circle,
                        size: 16, color: MantotaColors.teal),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(f,
                          style: const TextStyle(
                              fontSize: 13, color: MantotaColors.grey1)),
                    ),
                  ],
                ),
              )),
          const SizedBox(height: 14),
          // CTA
          if (!isCurrent)
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: isActivating ? null : () => _activatePlan(plan.id),
                style: ElevatedButton.styleFrom(
                  backgroundColor:
                      isFree ? MantotaColors.surface2 : MantotaColors.coral,
                  foregroundColor:
                      isFree ? MantotaColors.grey1 : Colors.white,
                  minimumSize: const Size(double.infinity, 44),
                ),
                child: isActivating
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white))
                    : Text(isFree
                        ? 'Activer le plan gratuit'
                        : 'Souscrire — ${plan.price.toStringAsFixed(0)} FCFA'),
              ),
            ),
        ],
      ),
    );
  }

  void _activatePlan(String planId) async {
    setState(() {
      _activatingPlan = planId;
      _errorMessage = null;
    });

    try {
      final subSvc = await ref.read(subscriptionServiceProvider.future);

      if (planId == 'free') {
        await subSvc.activateFree();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Plan Free activé.'),
              backgroundColor: MantotaColors.teal,
            ),
          );
          ref.refresh(currentSubscriptionProvider);
        }
      } else {
        final result = await subSvc.activate(planId);

        if (result.checkoutUrl != null && result.checkoutUrl!.isNotEmpty) {
          final uri = Uri.parse(result.checkoutUrl!);
          if (await canLaunchUrl(uri)) {
            await launchUrl(uri, mode: LaunchMode.inAppBrowserView);
            if (mounted) {
              _showSubscriptionWaitingDialog(result.reference);
            }
          } else {
            setState(() {
              _errorMessage = 'Impossible d\'ouvrir la page de paiement.';
            });
          }
        }
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Erreur: $e';
      });
    } finally {
      setState(() => _activatingPlan = null);
    }
  }

  void _showSubscriptionWaitingDialog(String reference) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Text('Paiement en cours',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
        content: Text(
          'Une page de paiement s\'est ouverte.\nRéférence: $reference\n\nCliquez sur « J\'ai payé » une fois le paiement effectué.',
          style: const TextStyle(fontSize: 14),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              ref.refresh(currentSubscriptionProvider);
            },
            child: const Text('J\'ai payé',
                style: TextStyle(color: MantotaColors.teal)),
          ),
        ],
      ),
    );
  }
}
