import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/adinkra_background.dart';
import '../widgets/country_picker_sheet.dart';
import '../../../core/models/country.dart';

/// Écran 02a — Connexion par numéro de téléphone.
///
/// L'utilisateur sélectionne son pays puis saisit son numéro.
/// Un OTP est envoyé par SMS via l'API Laravel.
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _phoneController = TextEditingController();
  bool _isLoading = false;
  Country _selectedCountry = supportedCountries.first;

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _sendOtp() async {
    final phone = _phoneController.text.trim();
    if (phone.length < 6) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Numéro invalide'),
          backgroundColor: MantotaColors.coral,
        ),
      );
      return;
    }

    final fullPhone = '$_selectedCountry.dialCode $phone';

    setState(() => _isLoading = true);

    try {
      final auth = await ref.read(authServiceProvider.future);
      await auth.requestOtp(fullPhone);

      if (mounted) {
        context.go('/otp', extra: fullPhone);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erreur: $e'),
            backgroundColor: MantotaColors.coral,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFFFFFFFF), Color(0xFFF6FFFE)],
          ),
        ),
        child: Stack(
          children: [
            const AdinkraBackground(opacity: 0.05),
            SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // ── Header avec logo ──
                const SizedBox(height: 40),
                Center(
                  child: Container(
                    width: 60,
                    height: 60,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(18),
                      boxShadow: [
                        BoxShadow(
                          color: MantotaColors.teal.withValues(alpha: 0.15),
                          blurRadius: 15,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(18),
                      child: Image.asset(
                        'assets/icons/mantota_logo.png',
                        fit: BoxFit.cover,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Bienvenue sur MANTOTA 👋',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Entrez votre numéro pour commencer',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 11, color: MantotaColors.grey2),
                ),

                const SizedBox(height: 32),

                // ── Sélecteur de pays ──
                const _FieldLabel(text: 'Pays'),
                const SizedBox(height: 6),
                GestureDetector(
                  onTap: () async {
                    final country = await showCountryPicker(context);
                    if (country != null) {
                      setState(() => _selectedCountry = country);
                    }
                  },
                  child: Container(
                    height: 48,
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    decoration: BoxDecoration(
                      color: MantotaColors.surface2,
                      border: Border.all(color: MantotaColors.border),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        Text(_selectedCountry.flag, style: const TextStyle(fontSize: 18)),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            '${_selectedCountry.name} (${_selectedCountry.dialCode})',
                            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                          ),
                        ),
                        const Icon(Icons.keyboard_arrow_down, color: MantotaColors.grey3, size: 20),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 14),

                // ── Champ numéro ──
                const _FieldLabel(text: 'Numéro de téléphone'),
                const SizedBox(height: 6),
                Container(
                  height: 48,
                  decoration: BoxDecoration(
                    color: MantotaColors.surface2,
                    border: Border.all(color: MantotaColors.teal, width: 1.5),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      Padding(
                        padding: const EdgeInsets.only(left: 12),
                        child: Text(
                          _selectedCountry.dialCode,
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: MantotaColors.grey3),
                        ),
                      ),
                      Container(
                        width: 1,
                        height: 20,
                        margin: const EdgeInsets.symmetric(horizontal: 10),
                        color: MantotaColors.surface3,
                      ),
                      Expanded(
                        child: TextField(
                          controller: _phoneController,
                          keyboardType: TextInputType.phone,
                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                          decoration: const InputDecoration(
                            hintText: '01 52 16 82 23',
                            border: InputBorder.none,
                            contentPadding: EdgeInsets.zero,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 20),

                // ── Bouton d'envoi ──
                ElevatedButton(
                  onPressed: _isLoading ? null : _sendOtp,
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 48),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          width: 20, height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Recevoir le code SMS'),
                ),

                const SizedBox(height: 14),

                // ── Conditions ──
                const Text(
                  "En continuant, vous acceptez les\nconditions d'utilisation",
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 10, color: MantotaColors.grey3, height: 1.6),
                ),

                const Spacer(),

                // ── Footer ──
                const Padding(
                  padding: EdgeInsets.only(bottom: 24),
                  child: Text(
                    'OD SYSTÈME',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 8, color: MantotaColors.grey4, letterSpacing: 1),
                  ),
                ),
              ],
            ),
          ),
        ),
          ],
        ),
      ),
    );
  }
}

class _FieldLabel extends StatelessWidget {
  final String text;

  const _FieldLabel({required this.text});

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 10,
        fontWeight: FontWeight.w700,
        letterSpacing: 1.5,
        color: MantotaColors.grey2,
      ),
    );
  }
}
