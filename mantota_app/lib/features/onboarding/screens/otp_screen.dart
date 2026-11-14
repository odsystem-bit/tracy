import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/config/app_config.dart';
import '../../../core/providers/providers.dart';
import '../../../core/router/app_router.dart';
import '../../../core/services/auth_service.dart';
import '../../../core/theme/mantota_theme.dart';

/// Écran 02b — Vérification OTP.
///
/// L'utilisateur saisit le code à 6 chiffres reçu par SMS dans des cases
/// individuelles. Timer de renvoi de 60 secondes.
class OtpScreen extends ConsumerStatefulWidget {
  const OtpScreen({super.key});

  @override
  ConsumerState<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends ConsumerState<OtpScreen> {
  final List<TextEditingController> _controllers =
      List.generate(6, (_) => TextEditingController());
  final List<FocusNode> _focusNodes = List.generate(6, (_) => FocusNode());
  bool _isLoading = false;
  int _resendSeconds = 60;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startResendTimer();
  }

  void _startResendTimer() {
    _timer?.cancel();
    setState(() => _resendSeconds = 60);
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_resendSeconds <= 1) {
        timer.cancel();
        setState(() => _resendSeconds = 0);
      } else {
        setState(() => _resendSeconds--);
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    for (final c in _controllers) {
      c.dispose();
    }
    for (final f in _focusNodes) {
      f.dispose();
    }
    super.dispose();
  }

  String get _code => _controllers.map((c) => c.text).join();

  void _onChanged(int index, String value) {
    if (value.length == 1 && index < 5) {
      _focusNodes[index + 1].requestFocus();
    }
    if (value.isEmpty && index > 0) {
      _focusNodes[index - 1].requestFocus();
    }
    // Auto-vérification quand les 6 chiffres sont saisis
    if (_code.length == 6) {
      _verify();
    }
  }

  Future<void> _resendOtp() async {
    if (_resendSeconds > 0) return;
    final phone = GoRouterState.of(context).extra as String? ?? '';
    try {
      final auth = await ref.read(authServiceProvider.future);
      await auth.requestOtp(phone);
      _startResendTimer();
    } catch (_) {}
  }

  Future<void> _verify() async {
    if (_code.length != 6) return;

    final phone = GoRouterState.of(context).extra as String? ?? '';

    setState(() => _isLoading = true);

    try {
      final auth = await ref.read(authServiceProvider.future);
      final result = await auth.verifyOtp(phone: phone, code: _code);

      // Stocke l'utilisateur courant globalement
      ref.read(currentUserProvider.notifier).state = result.user;

      // Met à jour l'état d'auth globalement
      ref.read(authStateProvider.notifier).state = AuthState.authenticated;

      if (mounted) {
        context.go('/modes');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Code incorrect: $e'),
            backgroundColor: MantotaColors.coral,
          ),
        );
        // Clear les cases
        for (final c in _controllers) {
          c.clear();
        }
        _focusNodes[0].requestFocus();
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final phone = GoRouterState.of(context).extra as String? ?? '';

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFFFFFFFF), Color(0xFFF6FFFE)],
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // ── Back button ──
                Padding(
                  padding: const EdgeInsets.only(top: 14),
                  child: Row(
                    children: [
                      GestureDetector(
                        onTap: () => context.go('/login'),
                        child: const Icon(Icons.arrow_back_ios, size: 18, color: MantotaColors.teal),
                      ),
                      const SizedBox(width: 8),
                      const Text('Vérification', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
                    ],
                  ),
                ),

                const SizedBox(height: 30),

                // ── Icône ──
                Center(
                  child: Container(
                    width: 50,
                    height: 50,
                    decoration: const BoxDecoration(
                      color: MantotaColors.tealPale,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.lock_outline, color: MantotaColors.teal, size: 24),
                  ),
                ),
                const SizedBox(height: 14),

                // ── Titre ──
                const Text(
                  'Code de vérification',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Un SMS a été envoyé au',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 11, color: MantotaColors.grey2),
                ),
                const SizedBox(height: 4),
                Text(
                  phone,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: MantotaColors.teal),
                ),

                const SizedBox(height: 28),

                // ── Banner mode démo ──
                if (AppConfig.useMockAuth) ...[
                  Container(
                    margin: const EdgeInsets.symmetric(horizontal: 20),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: MantotaColors.tealPale,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.info_outline, size: 16, color: MantotaColors.teal),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Mode démo : utilisez le code ${AuthService.mockOtpCode}',
                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: MantotaColors.tealDark),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                ],

                // ── Cases OTP ──
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(6, (index) {
                    return Container(
                      width: 40,
                      height: 46,
                      margin: EdgeInsets.only(right: index < 5 ? 8 : 0),
                      decoration: BoxDecoration(
                        color: _controllers[index].text.isNotEmpty
                            ? MantotaColors.tealPale
                            : MantotaColors.surface3,
                        border: Border.all(
                          color: _controllers[index].text.isNotEmpty
                              ? MantotaColors.teal
                              : MantotaColors.border,
                          width: 2,
                        ),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: TextField(
                        controller: _controllers[index],
                        focusNode: _focusNodes[index],
                        keyboardType: TextInputType.number,
                        textAlign: TextAlign.center,
                        maxLength: 1,
                        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
                        decoration: const InputDecoration(
                          counterText: '',
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.zero,
                        ),
                        onChanged: (value) => _onChanged(index, value),
                      ),
                    );
                  }),
                ),

                const SizedBox(height: 24),

                // ── Bouton vérifier ──
                ElevatedButton(
                  onPressed: _isLoading ? null : _verify,
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 48),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          width: 20, height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Vérifier'),
                ),

                const SizedBox(height: 16),

                // ── Renvoyer le code ──
                Center(
                  child: _resendSeconds > 0
                      ? Text(
                          'Renvoyer le code dans ${_resendSeconds}s',
                          style: const TextStyle(fontSize: 11, color: MantotaColors.grey3),
                        )
                      : GestureDetector(
                          onTap: _resendOtp,
                          child: const Text(
                            'Renvoyer le code',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: MantotaColors.teal,
                            ),
                          ),
                        ),
                ),

                const Spacer(),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
