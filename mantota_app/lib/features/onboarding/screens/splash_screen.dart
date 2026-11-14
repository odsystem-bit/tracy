import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/router/app_router.dart';
import '../../../core/theme/mantota_theme.dart';
import '../../../core/widgets/adinkra_background.dart';

/// Écran 01 — Splash Screen.
///
/// Logo Mantota centré avec anneaux Adinkra, gradient et tagline.
/// Transition automatique après 2,5 secondes vers /login ou /chats
/// selon l'état d'authentification.
class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _animController;
  late final Animation<double> _logoScale;
  late final Animation<double> _logoFade;
  late final Animation<double> _textFade;
  late final Animation<double> _ringExpand;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    );

    _logoScale = Tween<double>(begin: 0.6, end: 1.0).animate(
      CurvedAnimation(
        parent: _animController,
        curve: const Interval(0.0, 0.5, curve: Curves.easeOutBack),
      ),
    );

    _logoFade = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _animController,
        curve: const Interval(0.0, 0.4, curve: Curves.easeIn),
      ),
    );

    _textFade = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _animController,
        curve: const Interval(0.3, 0.7, curve: Curves.easeIn),
      ),
    );

    _ringExpand = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _animController,
        curve: const Interval(0.0, 0.8, curve: Curves.easeOutCubic),
      ),
    );

    _animController.forward();
    _navigate();
  }

  Future<void> _navigate() async {
    await Future.delayed(const Duration(milliseconds: 2500));
    if (!mounted) return;

    // Vérifie si l'utilisateur est déjà connecté
    try {
      final auth = await ref.read(authServiceProvider.future);
      final isAuth = await auth.isAuthenticated();

      if (mounted) {
        if (isAuth) {
          ref.read(authStateProvider.notifier).state = AuthState.authenticated;
          context.go('/chats');
        } else {
          ref.read(authStateProvider.notifier).state = AuthState.unauthenticated;
          context.go('/login');
        }
      }
    } catch (_) {
      if (mounted) {
        ref.read(authStateProvider.notifier).state = AuthState.unauthenticated;
        context.go('/login');
      }
    }
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFFFFFFFF), Color(0xFFE6F7F4)],
          ),
        ),
        child: Stack(
          children: [
            // ── Motif Adinkra en fond (identique au web) ──
            const AdinkraBackground(opacity: 0.06),

            // ── Halo teal subtil ──
            Center(
              child: AnimatedBuilder(
                animation: _ringExpand,
                builder: (context, child) {
                  return Container(
                    width: 320 * _ringExpand.value,
                    height: 320 * _ringExpand.value,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: RadialGradient(
                        colors: [
                          MantotaColors.teal.withValues(alpha: 0.10),
                          MantotaColors.teal.withValues(alpha: 0.0),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),

            // ── Contenu central ──
            Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Logo avec animation
                  AnimatedBuilder(
                    animation: _animController,
                    builder: (context, child) {
                      return Opacity(
                        opacity: _logoFade.value,
                        child: Transform.scale(
                          scale: _logoScale.value,
                          child: Container(
                            width: 100,
                            height: 100,
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(28),
                              boxShadow: [
                                BoxShadow(
                                  color: MantotaColors.teal.withValues(alpha: 0.25),
                                  blurRadius: 30,
                                  spreadRadius: 2,
                                  offset: const Offset(0, 8),
                                ),
                              ],
                            ),
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(28),
                              child: Image.asset(
                                'assets/icons/mantota_logo.png',
                                fit: BoxFit.cover,
                              ),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 20),
                  // Nom + tagline
                  AnimatedBuilder(
                    animation: _animController,
                    builder: (context, child) {
                      return Opacity(
                        opacity: _textFade.value,
                        child: const Column(
                          children: [
                            Text(
                              'MANTOTA',
                              style: TextStyle(
                                fontSize: 26,
                                fontWeight: FontWeight.w900,
                                letterSpacing: -0.5,
                                color: MantotaColors.grey1,
                              ),
                            ),
                            SizedBox(height: 6),
                            Text(
                              'DISCUTER · VENDRE · PAYER',
                              style: TextStyle(
                                fontSize: 9,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 3,
                                color: MantotaColors.teal,
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 44),
                  SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: MantotaColors.teal.withValues(alpha: 0.6),
                    ),
                  ),
                ],
              ),
            ),

            // ── Footer OD SYSTÈME ──
            Positioned(
              bottom: 38,
              left: 0,
              right: 0,
              child: Center(
                child: Text(
                  'OD SYSTÈME',
                  style: TextStyle(
                    fontSize: 8,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 1,
                    color: MantotaColors.grey2.withValues(alpha: 0.6),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
