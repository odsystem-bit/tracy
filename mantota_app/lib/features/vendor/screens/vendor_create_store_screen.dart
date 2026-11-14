import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran 10d — Création de boutique guidée.
///
/// Wizard en étapes : type de boutique (physique/en ligne), nom,
/// localisation (si physique), logo.
class VendorCreateStoreScreen extends ConsumerStatefulWidget {
  const VendorCreateStoreScreen({super.key});

  @override
  ConsumerState<VendorCreateStoreScreen> createState() =>
      _VendorCreateStoreScreenState();
}

class _VendorCreateStoreScreenState extends ConsumerState<VendorCreateStoreScreen> {
  int _step = 0;
  final _nameController = TextEditingController();
  String _shopType = 'physique';

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  void _next() async {
    if (_step < 2) {
      setState(() => _step++);
    } else {
      try {
        final svc = await ref.read(storeServiceProvider.future);
        await svc.create({
          'name': _nameController.text,
          'type': _shopType,
        });
      } catch (_) {}
      if (mounted) context.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Créer ma boutique'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 20),
          onPressed: () => _step > 0 ? setState(() => _step--) : context.pop(),
        ),
      ),
      body: Column(
        children: [
          // Indicateur de progression
          LinearProgressIndicator(
            value: (_step + 1) / 3,
            backgroundColor: MantotaColors.surface3,
            color: MantotaColors.teal,
            minHeight: 3,
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: switch (_step) {
                0 => _StepType(
                  shopType: _shopType,
                  onChanged: (v) => setState(() => _shopType = v),
                ),
                1 => _StepName(controller: _nameController),
                2 => _StepConfirm(
                  name: _nameController.text,
                  shopType: _shopType,
                ),
                _ => const SizedBox(),
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: ElevatedButton(
              onPressed: _next,
              child: Text(_step < 2 ? 'Continuer' : 'Créer ma boutique'),
            ),
          ),
        ],
      ),
    );
  }
}

class _StepType extends StatelessWidget {
  final String shopType;
  final ValueChanged<String> onChanged;

  const _StepType({required this.shopType, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Type de boutique',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
        const SizedBox(height: 8),
        const Text('Choisissez le type de boutique que vous voulez créer.',
            style: TextStyle(fontSize: 13, color: MantotaColors.grey2)),
        const SizedBox(height: 24),
        _TypeCard(
          icon: Icons.store_outlined,
          title: 'Boutique physique',
          subtitle: 'Vous avez un magasin. Les clients peuvent venir sur place.',
          selected: shopType == 'physique',
          onTap: () => onChanged('physique'),
        ),
        const SizedBox(height: 12),
        _TypeCard(
          icon: Icons.laptop_outlined,
          title: 'Boutique en ligne',
          subtitle: 'Vous vendez uniquement en ligne. Pas de magasin physique.',
          selected: shopType == 'en_ligne',
          onTap: () => onChanged('en_ligne'),
        ),
      ],
    );
  }
}

class _TypeCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final bool selected;
  final VoidCallback onTap;

  const _TypeCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: selected ? MantotaColors.tealPale : MantotaColors.surface1,
          borderRadius: BorderRadius.circular(14),
          border: selected
              ? Border.all(color: MantotaColors.teal.withValues(alpha: 0.3), width: 1.5)
              : null,
        ),
        child: Row(
          children: [
            Container(
              width: 44, height: 44,
              decoration: BoxDecoration(
                color: selected ? MantotaColors.teal : MantotaColors.surface3,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: Colors.white, size: 22),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 2),
                  Text(subtitle, style: const TextStyle(fontSize: 13, color: MantotaColors.grey2, height: 1.3)),
                ],
              ),
            ),
            Icon(selected ? Icons.radio_button_checked : Icons.radio_button_unchecked,
                color: selected ? MantotaColors.teal : MantotaColors.grey4, size: 20),
          ],
        ),
      ),
    );
  }
}

class _StepName extends StatelessWidget {
  final TextEditingController controller;

  const _StepName({required this.controller});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Nom de la boutique',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
        const SizedBox(height: 8),
        const Text('Choisissez un nom clair que vos clients reconnaîtront.',
            style: TextStyle(fontSize: 13, color: MantotaColors.grey2)),
        const SizedBox(height: 24),
        TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'Nom de la boutique',
            hintText: 'Ex: TechStore Cotonou',
          ),
        ),
        const SizedBox(height: 20),
        // TODO: si physique → ajouter champs adresse, GPS, photo devanture
      ],
    );
  }
}

class _StepConfirm extends StatelessWidget {
  final String name;
  final String shopType;

  const _StepConfirm({required this.name, required this.shopType});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Confirmation',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(14)),
          child: Column(
            children: [
              _ConfirmRow(label: 'Nom', value: name.isEmpty ? 'Ma boutique' : name),
              const Divider(),
              _ConfirmRow(label: 'Type', value: shopType == 'physique' ? 'Boutique physique' : 'Boutique en ligne'),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: MantotaColors.teal.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(12),
          ),
          child: const Row(
            children: [
              Icon(Icons.info_outline, color: MantotaColors.teal, size: 18),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Tracy sera automatiquement activée pour votre boutique.',
                  style: TextStyle(fontSize: 13, color: MantotaColors.grey1),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ConfirmRow extends StatelessWidget {
  final String label;
  final String value;

  const _ConfirmRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 14, color: MantotaColors.grey2)),
          Text(value, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
