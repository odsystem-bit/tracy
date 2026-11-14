import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/tracy_avatar.dart';

/// Écran 10e — Ajout produit via Tracy.
///
/// Le vendeur décrit son produit en langage naturel, Tracy l'ajoute
/// au catalogue automatiquement. Alternative: formulaire manuel.
class VendorAddProductScreen extends ConsumerStatefulWidget {
  const VendorAddProductScreen({super.key});

  @override
  ConsumerState<VendorAddProductScreen> createState() => _VendorAddProductScreenState();
}

class _VendorAddProductScreenState extends ConsumerState<VendorAddProductScreen> {
  final _tracyInputController = TextEditingController();
  bool _useManualForm = false;

  // Formulaires manuels
  final _nameController = TextEditingController();
  final _priceController = TextEditingController();
  final _descController = TextEditingController();
  final _stockController = TextEditingController();
  String _category = 'Autre';
  bool _publishing = false;

  @override
  void dispose() {
    _tracyInputController.dispose();
    _nameController.dispose();
    _priceController.dispose();
    _descController.dispose();
    _stockController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ajouter un produit'),
        actions: [
          TextButton(
            onPressed: () => setState(() => _useManualForm = !_useManualForm),
            child: Text(_useManualForm ? 'Mode Tracy' : 'Mode manuel',
                style: const TextStyle(fontSize: 14, color: MantotaColors.teal)),
          ),
        ],
      ),
      body: _useManualForm ? _buildManualForm() : _buildTracyMode(),
    );
  }

  Widget _buildTracyMode() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: MantotaColors.tealPale,
              border: Border.all(color: MantotaColors.teal.withValues(alpha: 0.2)),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Row(
              children: [
                const TracyAvatar(size: 20, borderRadius: 6),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Décrivez votre produit à Tracy. Elle crée la fiche automatiquement.',
                    style: TextStyle(fontSize: 14, color: MantotaColors.grey1),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _tracyInputController,
            maxLines: 4,
            decoration: const InputDecoration(
              hintText: 'Ex: Nike Air Max 270 taille 42, noir et blanc, 45000 FCFA, neuf dans la boîte',
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () async {
              try {
                final svc = await ref.read(tracyChatServiceProvider.future);
                await svc.chat(conversationId: 'vendor', vendorMode: true, message: 'Ajoute ce produit: ${_tracyInputController.text}');
              } catch (_) {}
              if (context.mounted) context.pop();
            },
            child: const Text('Envoyer à Tracy'),
          ),
          const SizedBox(height: 24),
          const Text('Exemples', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: MantotaColors.grey2)),
          const SizedBox(height: 8),
          _ExampleChip(text: 'Sac cuir marron, fait main, 25000 F, stock 5'),
          _ExampleChip(text: 'T-shirt Ankara motif gold, tailles S/M/L, 8000 F'),
          _ExampleChip(text: 'Tecno Spark 10, 64GB, bleu, 65000 F, garantie 6 mois'),
        ],
      ),
    );
  }

  Widget _buildManualForm() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Info boutique
          FutureBuilder(
            future: ref.read(storeDetailProvider.future),
            builder: (context, snapshot) {
              if (snapshot.hasData && snapshot.data != null) {
                final store = snapshot.data!;
                return Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: MantotaColors.tealPale,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.store_outlined, color: MantotaColors.teal, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(store.name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
                            Text(
                              store.type == 'physique' ? 'Boutique physique' : 'Boutique en ligne',
                              style: const TextStyle(fontSize: 12, color: MantotaColors.grey2),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              }
              return const SizedBox.shrink();
            },
          ),
          // Photo
          GestureDetector(
            onTap: () {},
            child: Container(
              height: 120,
              decoration: BoxDecoration(
                color: MantotaColors.surface1,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: MantotaColors.surface3, width: 1),
              ),
              child: const Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.add_a_photo_outlined, color: MantotaColors.grey4, size: 32),
                  SizedBox(height: 6),
                  Text('Ajouter une photo', style: TextStyle(fontSize: 13, color: MantotaColors.grey2)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _nameController,
            decoration: const InputDecoration(labelText: 'Nom du produit *'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _priceController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Prix (FCFA) *', prefixText: 'F '),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _descController,
            maxLines: 3,
            decoration: const InputDecoration(labelText: 'Description'),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            value: _category,
            decoration: const InputDecoration(labelText: 'Catégorie'),
            items: ['Électronique', 'Mode', 'Beauté', 'Maison', 'Sport', 'Alimentation', 'Autre']
                .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                .toList(),
            onChanged: (v) => setState(() => _category = v ?? 'Autre'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _stockController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Stock disponible', hintText: 'Ex: 10'),
          ),
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: _publishing ? null : _publishProduct,
            child: _publishing
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Text('Publier le produit'),
          ),
          const SizedBox(height: 8),
          const Text(
            '* Champs obligatoires',
            style: TextStyle(fontSize: 12, color: MantotaColors.grey2),
          ),
        ],
      ),
    );
  }

  void _publishProduct() async {
    if (_nameController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Veuillez saisir le nom du produit'), backgroundColor: MantotaColors.error),
      );
      return;
    }
    final price = int.tryParse(_priceController.text.trim());
    if (price == null || price <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Veuillez saisir un prix valide'), backgroundColor: MantotaColors.error),
      );
      return;
    }

    setState(() => _publishing = true);
    try {
      final svc = await ref.read(productServiceProvider.future);
      await svc.create({
        'name': _nameController.text.trim(),
        'price': price,
        'description': _descController.text.trim(),
        'category': _category,
        'stock': int.tryParse(_stockController.text.trim()) ?? 0,
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Produit publié avec succès'), backgroundColor: MantotaColors.teal),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e'), backgroundColor: MantotaColors.error),
        );
      }
    }
    if (mounted) setState(() => _publishing = false);
  }
}

class _ExampleChip extends StatelessWidget {
  final String text;

  const _ExampleChip({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: MantotaColors.surface1,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(text, style: const TextStyle(fontSize: 13, color: MantotaColors.grey3)),
    );
  }
}
