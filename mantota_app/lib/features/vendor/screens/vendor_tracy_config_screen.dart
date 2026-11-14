import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/tracy_avatar.dart';
import '../../../core/widgets/adinkra_background.dart';

/// Écran 10c — Config Tracy.
///
/// Configuration du mode Tracy (découverte, active, pro), personnalité,
/// messages automatiques. Toutes les sélections sont interactives.
class VendorTracyConfigScreen extends ConsumerStatefulWidget {
  const VendorTracyConfigScreen({super.key});

  @override
  ConsumerState<VendorTracyConfigScreen> createState() => _VendorTracyConfigScreenState();
}

class _VendorTracyConfigScreenState extends ConsumerState<VendorTracyConfigScreen> {
  String _selectedMode = 'active';
  final Map<String, bool> _personalityTags = {
    'Amicale': true,
    'Professionnelle': false,
    'Drôle': false,
    'Directe': true,
  };
  final Map<String, bool> _autoMessages = {
    'Message de bienvenue': true,
    'Relance panier abandonné': true,
    'Confirmation commande': true,
    "Demande d'avis après livraison": false,
  };
  bool _saving = false;
  bool _loading = true;

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
          _selectedMode = config['tracy_mode'] as String? ?? config['mode'] as String? ?? 'active';
          final personality = config['tracy_personality'] as List? ?? config['personality_tags'] as List? ?? [];
          for (final key in _personalityTags.keys) {
            _personalityTags[key] = personality.contains(key);
          }
          final autoMsgs = config['tracy_auto_messages'] as List? ?? config['auto_messages'] as List? ?? [];
          for (final key in _autoMessages.keys) {
            _autoMessages[key] = autoMsgs.contains(key);
          }
          _loading = false;
        });
      } else if (mounted) {
        setState(() => _loading = false);
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Configuration Tracy'),
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
          // Mode Tracy
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: MantotaColors.tealPale, borderRadius: BorderRadius.circular(14)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Mode Tracy', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                const SizedBox(height: 10),
                _ModeOption(
                  title: 'Découverte',
                  desc: 'Tracy répond basique, vous gérez tout',
                  selected: _selectedMode == 'discovery',
                  onTap: () => setState(() => _selectedMode = 'discovery'),
                ),
                _ModeOption(
                  title: 'Active',
                  desc: 'Tracy répond, vend et négocie pour vous',
                  selected: _selectedMode == 'active',
                  onTap: () => setState(() => _selectedMode = 'active'),
                ),
                _ModeOption(
                  title: 'Pro',
                  desc: 'Tracy gère tout 24/7 + campagnes + analytics',
                  selected: _selectedMode == 'pro',
                  onTap: () => setState(() => _selectedMode = 'pro'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Personnalité
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Personnalité', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8, runSpacing: 8,
                  children: _personalityTags.keys.map((label) => _TagChip(
                    label: label,
                    selected: _personalityTags[label]!,
                    onTap: () => setState(() => _personalityTags[label] = !_personalityTags[label]!),
                  )).toList(),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Messages auto
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Messages automatiques', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                const SizedBox(height: 10),
                ..._autoMessages.keys.map((label) => _ToggleRow(
                  label: label,
                  value: _autoMessages[label]!,
                  onChanged: (v) => setState(() => _autoMessages[label] = v),
                )),
              ],
            ),
          ),
          const SizedBox(height: 20),
          // Aperçu
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: MantotaColors.teal.withValues(alpha: 0.06),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                const TracyAvatar(size: 28, borderRadius: 8),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Tracy est active', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: MantotaColors.teal)),
                      Text(
                        'Mode: ${_modeLabel(_selectedMode)} · ${_personalityTags.entries.where((e) => e.value).map((e) => e.key).join(', ')}',
                        style: const TextStyle(fontSize: 12, color: MantotaColors.grey2),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
            ],
          ),
    );
  }

  String _modeLabel(String mode) {
    switch (mode) {
      case 'discovery': return 'Découverte';
      case 'active': return 'Active';
      case 'pro': return 'Pro';
      default: return mode;
    }
  }

  void _save() async {
    setState(() => _saving = true);
    try {
      final api = await ref.read(apiClientProvider.future);
      await api.post('/tracy/config', data: {
        'mode': _selectedMode,
        'personality_tags': _personalityTags.entries.where((e) => e.value).map((e) => e.key).toList(),
        'auto_messages': _autoMessages.entries.where((e) => e.value).map((e) => e.key).toList(),
      });
      if (mounted) {
        setState(() => _saving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Configuration Tracy enregistrée'), backgroundColor: MantotaColors.teal),
        );
        context.pop();
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
}

class _ModeOption extends StatelessWidget {
  final String title;
  final String desc;
  final bool selected;
  final VoidCallback onTap;

  const _ModeOption({required this.title, required this.desc, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: selected ? MantotaColors.teal : Colors.white,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          children: [
            Icon(selected ? Icons.radio_button_checked : Icons.radio_button_unchecked,
                color: selected ? Colors.white : MantotaColors.grey2, size: 18),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: selected ? Colors.white : MantotaColors.grey1)),
                  Text(desc, style: TextStyle(fontSize: 12, color: selected ? Colors.white70 : MantotaColors.grey2)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TagChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _TagChip({required this.label, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: selected ? MantotaColors.teal : MantotaColors.surface2,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Text(label, style: TextStyle(
          fontSize: 13, fontWeight: FontWeight.w600,
          color: selected ? Colors.white : MantotaColors.grey2,
        )),
      ),
    );
  }
}

class _ToggleRow extends StatelessWidget {
  final String label;
  final bool value;
  final ValueChanged<bool> onChanged;

  const _ToggleRow({required this.label, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Expanded(child: Text(label, style: const TextStyle(fontSize: 14))),
          Switch.adaptive(value: value, onChanged: onChanged, activeTrackColor: MantotaColors.teal),
        ],
      ),
    );
  }
}
