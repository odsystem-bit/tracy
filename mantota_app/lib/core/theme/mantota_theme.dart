import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Thème Mantota — couleurs, typographie, composants réutilisables.
///
/// Les couleurs proviennent de la maquette HTML de référence.
class MantotaColors {
  const MantotaColors._();

  static const Color teal = Color(0xFF0BBFA0);
  static const Color tealDark = Color(0xFF07856F);
  static const Color tealPale = Color(0xFFE6F7F4);
  static const Color coral = Color(0xFFFF6B35);

  static const Color background = Color(0xFFFFFFFF);
  static const Color surface1 = Color(0xFFF8F9FA);
  static const Color surface2 = Color(0xFFF1F3F5);
  static const Color surface3 = Color(0xFFE9ECEF);
  static const Color surface4 = Color(0xFFDEE2E6);

  static const Color grey1 = Color(0xFF212529);
  static const Color grey2 = Color(0xFF6C757D);
  static const Color grey3 = Color(0xFF495057);
  static const Color grey4 = Color(0xFF868E96);

  static const Color white = Color(0xFFFFFFFF);
  static const Color border = Color(0x0F000000); // rgba(0,0,0,0.06)
  static const Color error = Color(0xFFEF4444);
  static const Color whatsapp = Color(0xFF25D366);
}

class MantotaTheme {
  const MantotaTheme._();

  /// Famille de police principale — Plus Jakarta Sans.
  /// Police moderne utilisée par des apps comme Cash App, Stripe.
  static TextStyle get _base => GoogleFonts.plusJakartaSans();

  static ThemeData get light => ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: MantotaColors.teal,
          primary: MantotaColors.teal,
          secondary: MantotaColors.coral,
          surface: MantotaColors.background,
          error: MantotaColors.error,
        ),
        scaffoldBackgroundColor: Colors.transparent,
        textTheme: GoogleFonts.plusJakartaSansTextTheme(
          const TextTheme(
            headlineLarge: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.w800,
              color: MantotaColors.grey1,
              letterSpacing: -0.5,
              height: 1.2,
            ),
            headlineMedium: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: MantotaColors.grey1,
              height: 1.25,
            ),
            titleLarge: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: MantotaColors.grey1,
              height: 1.3,
            ),
            titleMedium: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: MantotaColors.grey1,
              height: 1.35,
            ),
            bodyLarge: TextStyle(
              fontSize: 15,
              color: MantotaColors.grey1,
              height: 1.5,
            ),
            bodyMedium: TextStyle(
              fontSize: 14,
              color: MantotaColors.grey3,
              height: 1.5,
            ),
            bodySmall: TextStyle(
              fontSize: 13,
              color: MantotaColors.grey2,
              height: 1.5,
            ),
            labelLarge: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: MantotaColors.teal,
              height: 1.4,
            ),
            labelSmall: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: MantotaColors.grey2,
              letterSpacing: 0.5,
              height: 1.4,
            ),
          ),
        ),
        appBarTheme: AppBarTheme(
          backgroundColor: Colors.transparent,
          foregroundColor: MantotaColors.grey1,
          elevation: 0,
          centerTitle: false,
          titleTextStyle: _base.copyWith(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            color: MantotaColors.grey1,
          ),
        ),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: Colors.transparent,
          selectedItemColor: MantotaColors.teal,
          unselectedItemColor: MantotaColors.grey2,
          type: BottomNavigationBarType.fixed,
          elevation: 8,
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: MantotaColors.teal,
            foregroundColor: MantotaColors.white,
            elevation: 0,
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            textStyle: _base.copyWith(
              fontSize: 16,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: MantotaColors.surface1,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: MantotaColors.teal, width: 1.5),
          ),
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          labelStyle: _base.copyWith(color: MantotaColors.grey2, fontSize: 14),
          hintStyle: _base.copyWith(color: MantotaColors.grey4, fontSize: 14),
        ),
        cardTheme: CardThemeData(
          color: MantotaColors.surface1,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
        ),
        dividerTheme: const DividerThemeData(
          color: MantotaColors.surface3,
          thickness: 1,
        ),
      );
}
