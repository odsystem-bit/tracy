import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/providers/providers.dart';
import 'core/router/app_router.dart';
import 'core/theme/mantota_theme.dart';
import 'core/widgets/adinkra_background.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );
  runApp(const ProviderScope(child: MantotaApp()));
}

class MantotaApp extends ConsumerStatefulWidget {
  const MantotaApp({super.key});

  @override
  ConsumerState<MantotaApp> createState() => _MantotaAppState();
}

class _MantotaAppState extends ConsumerState<MantotaApp> {
  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    final auth = await ref.read(authServiceProvider.future);
    final isAuth = await auth.isAuthenticated();
    if (mounted) {
      ref.read(authStateProvider.notifier).state =
          isAuth ? AuthState.authenticated : AuthState.unauthenticated;
    }
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'MANTOTA',
      theme: MantotaTheme.light,
      routerConfig: router,
      builder: (context, child) {
        return Container(
          color: Colors.white,
          child: Stack(
            children: [
              // ── Motif Adinkra global ──
              const AdinkraBackground(opacity: 0.10, tileSize: 110),
              // ── Contenu de l'app ──
              child ?? const SizedBox.shrink(),
            ],
          ),
        );
      },
    );
  }
}
