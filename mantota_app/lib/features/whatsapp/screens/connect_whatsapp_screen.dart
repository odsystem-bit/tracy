import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/tracy_avatar.dart';
import '../../../core/widgets/adinkra_background.dart';

/// Écran 10g — Connecter WhatsApp.
///
/// Configuration de WhatsApp Business Cloud API pour le vendeur :
/// - Toggle Tracy sur WhatsApp
/// - Mode hybride (Tracy répond si vendeur ne répond pas dans X secondes)
/// - Statut de connexion
/// - Compteur de conversations (limite plan Free)
class ConnectWhatsappScreen extends ConsumerStatefulWidget {
  const ConnectWhatsappScreen({super.key});

  @override
  ConsumerState<ConnectWhatsappScreen> createState() => _ConnectWhatsappScreenState();
}

class _ConnectWhatsappScreenState extends ConsumerState<ConnectWhatsappScreen> {
  bool _tracyOnWhatsapp = true;
  bool _hybridMode = true;
  String _hybridDelay = '30s';
  bool _loading = true;
  bool _saving = false;
  String? _whatsappNumber;
  int _conversationCount = 0;
  int _conversationLimit = 50;
  String _plan = 'free';
  int _productCount = 0;

  @override
  void initState() {
    super.initState();
    _loadConfig();
  }

  void _loadConfig() async {
    try {
      final api = await ref.read(apiClientProvider.future);
      final json = await api.get('/tracy/config');
      final config = json['config'] as Map<String, dynamic>?;
      if (config != null && mounted) {
        setState(() {
          _tracyOnWhatsapp = config['whatsapp_enabled'] as bool? ?? true;
          _hybridMode = config['hybrid_mode'] as bool? ?? true;
          _hybridDelay = config['hybrid_delay'] as String? ?? '30s';
          _whatsappNumber = config['whatsapp_number'] as String?;
          _conversationCount = config['conversation_count'] as int? ?? 0;
          _conversationLimit = config['conversation_limit'] as int? ?? 50;
          _plan = config['plan'] as String? ?? 'free';
          _productCount = config['product_count'] as int? ?? 0;
          _loading = false;
        });
      } else if (mounted) {
        setState(() => _loading = false);
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _save() async {
    setState(() => _saving = true);
    try {
      final api = await ref.read(apiClientProvider.future);
      await api.post('/tracy/config', data: {
        'mode': 'active',
        'whatsapp_enabled': _tracyOnWhatsapp,
        'hybrid_mode': _hybridMode,
        'hybrid_delay': _hybridDelay,
      });
      if (mounted) {
        setState(() => _saving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Configuration WhatsApp enregistrée'), backgroundColor: MantotaColors.teal),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _saving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e'), backgroundColor: MantotaColors.error),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Connecter WhatsApp'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => context.pop(),
        ),
        actions: [
          TextButton(
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: MantotaColors.teal))
                : const Text('Enregistrer', style: TextStyle(color: MantotaColors.teal, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Stack(
            children: [
              const AdinkraBackground(opacity: 0.04),
              ListView(
        padding: const EdgeInsets.all(14),
        children: [
          // Statut de connexion
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF25D366).withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Row(
              children: [
                Container(
                  width: 44, height: 44,
                  decoration: BoxDecoration(
                    color: const Color(0xFF25D366),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.chat, color: Colors.white, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_whatsappNumber != null ? 'WhatsApp connecté' : 'WhatsApp non connecté', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: const Color(0xFF25D366))),
                      Text(_whatsappNumber ?? 'Aucun numéro lié', style: const TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(color: _whatsappNumber != null ? const Color(0xFF25D366) : MantotaColors.grey4, borderRadius: BorderRadius.circular(6)),
                  child: Text(_whatsappNumber != null ? 'Actif' : 'Inactif', style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: Colors.white)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Tracy sur WhatsApp
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(14)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const TracyAvatar(size: 20, borderRadius: 6),
                    const SizedBox(width: 8),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Tracy sur WhatsApp', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                          Text('Tracy répond automatiquement à vos clients WhatsApp', style: TextStyle(fontSize: 12, color: MantotaColors.grey2)),
                        ],
                      ),
                    ),
                    Switch.adaptive(value: _tracyOnWhatsapp, onChanged: (v) => setState(() => _tracyOnWhatsapp = v), activeTrackColor: MantotaColors.teal),
                  ],
                ),
                if (_tracyOnWhatsapp) ...[
                  const Divider(height: 24),
                  // Mode hybride
                  Row(
                    children: [
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Mode hybride', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                            Text('Tracy répond si vous ne répondez pas dans le délai', style: TextStyle(fontSize: 12, color: MantotaColors.grey2)),
                          ],
                        ),
                      ),
                      Switch.adaptive(value: _hybridMode, onChanged: (v) => setState(() => _hybridMode = v), activeTrackColor: MantotaColors.teal),
                    ],
                  ),
                  if (_hybridMode) ...[
                    const SizedBox(height: 12),
                    const Text('Délai avant intervention de Tracy', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: MantotaColors.grey2)),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        _DelayChip(label: 'Immédiat', value: '0s', selected: _hybridDelay == '0s', onTap: () => setState(() => _hybridDelay = '0s')),
                        _DelayChip(label: '30 sec', value: '30s', selected: _hybridDelay == '30s', onTap: () => setState(() => _hybridDelay = '30s')),
                        _DelayChip(label: '1 min', value: '1min', selected: _hybridDelay == '1min', onTap: () => setState(() => _hybridDelay = '1min')),
                        _DelayChip(label: '5 min', value: '5min', selected: _hybridDelay == '5min', onTap: () => setState(() => _hybridDelay = '5min')),
                      ],
                    ),
                  ],
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Usage
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(14)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.data_usage_outlined, color: MantotaColors.teal, size: 18),
                    SizedBox(width: 8),
                    Text('Utilisation ce mois', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                  ],
                ),
                const SizedBox(height: 12),
                // Barre de progression
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: _conversationCount / _conversationLimit,
                    backgroundColor: MantotaColors.surface3,
                    color: MantotaColors.teal,
                    minHeight: 8,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('$_conversationCount / $_conversationLimit conversations', style: const TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                    Text('Plan ${_plan[0].toUpperCase()}${_plan.substring(1)}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: MantotaColors.teal)),
                  ],
                ),
                const SizedBox(height: 12),
                const Text(
                  'Passez au plan Starter pour des conversations illimitées.',
                  style: TextStyle(fontSize: 13, color: MantotaColors.grey2),
                ),
                const SizedBox(height: 8),
                ElevatedButton(
                  onPressed: () {},
                  style: ElevatedButton.styleFrom(
                    backgroundColor: MantotaColors.coral,
                    foregroundColor: Colors.white,
                  ),
                  child: const Text('Améliorer mon plan'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Aperçu catalogue
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(14)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.inventory_2_outlined, color: MantotaColors.teal, size: 18),
                    SizedBox(width: 8),
                    Text('Catalogue WhatsApp', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                  ],
                ),
                const SizedBox(height: 8),
                const Text(
                  'Vos produits sont automatiquement synchronisés avec WhatsApp Commerce. Les clients peuvent voir votre catalogue directement dans WhatsApp.',
                  style: TextStyle(fontSize: 13, color: MantotaColors.grey2, height: 1.4),
                ),
                const SizedBox(height: 8),
                Text('$_productCount produits synchronisés', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: MantotaColors.teal)),
              ],
            ),
          ),
        ],
      ),
            ],
          ),
    );
  }
}

class _DelayChip extends StatelessWidget {
  final String label;
  final String value;
  final bool selected;
  final VoidCallback onTap;

  const _DelayChip({required this.label, required this.value, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          margin: const EdgeInsets.only(right: 6),
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            color: selected ? MantotaColors.teal : MantotaColors.surface2,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(label, textAlign: TextAlign.center, style: TextStyle(
            fontSize: 12, fontWeight: FontWeight.w600,
            color: selected ? Colors.white : MantotaColors.grey2,
          )),
        ),
      ),
    );
  }
}
