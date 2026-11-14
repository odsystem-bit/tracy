import 'dart:math';
import 'package:flutter/material.dart';

/// Peint le motif Adinkra exact du web MANTOTA en pattern subtil.
///
/// Le pattern web est un SVG 80x80 répété avec :
/// - Cercles concentriques (r=16, r=8) au centre
/// - Croix (lignes horizontales + verticales)
/// - Diagonales (4 coins)
/// - Cercle externe pointillé (r=28, dasharray 4 5)
/// - Petit losange en haut
///
/// Opacité web : 0.08 — couleur : teal #0BBFA0, stroke 0.8px
class AdinkraPatternPainter extends CustomPainter {
  AdinkraPatternPainter({
    this.opacity = 0.08,
    this.tileSize = 80,
    this.color,
  });

  final double opacity;
  final double tileSize;
  final Color? color;

  @override
  void paint(Canvas canvas, Size size) {
    final paintColor = (color ?? const Color(0xFF0BBFA0)).withValues(alpha: opacity);
    final paint = Paint()
      ..color = paintColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.8;

    final cols = (size.width / tileSize).ceil() + 1;
    final rows = (size.height / tileSize).ceil() + 1;

    for (int row = 0; row < rows; row++) {
      for (int col = 0; col < cols; col++) {
        final cx = col * tileSize + tileSize / 2;
        final cy = row * tileSize + tileSize / 2;
        _drawTile(canvas, cx, cy, paint);
      }
    }
  }

  void _drawTile(Canvas canvas, double cx, double cy, Paint paint) {
    // Cercle concentriques (r=16, r=8) — échelle tileSize/80
    final s = tileSize / 80;
    canvas.drawCircle(Offset(cx, cy), 16 * s, paint);
    canvas.drawCircle(Offset(cx, cy), 8 * s, paint);

    // Croix (lignes du centre vers extérieur)
    canvas.drawLine(Offset(cx, cy - 16 * s), Offset(cx, cy - 30 * s), paint);
    canvas.drawLine(Offset(cx, cy + 16 * s), Offset(cx, cy + 30 * s), paint);
    canvas.drawLine(Offset(cx - 16 * s, cy), Offset(cx - 30 * s, cy), paint);
    canvas.drawLine(Offset(cx + 16 * s, cy), Offset(cx + 30 * s, cy), paint);

    // Diagonales (vers les coins)
    canvas.drawLine(Offset(cx - 11 * s, cy - 11 * s), Offset(cx - 22 * s, cy - 22 * s), paint);
    canvas.drawLine(Offset(cx + 11 * s, cy + 11 * s), Offset(cx + 22 * s, cy + 22 * s), paint);
    canvas.drawLine(Offset(cx + 11 * s, cy - 11 * s), Offset(cx + 22 * s, cy - 22 * s), paint);
    canvas.drawLine(Offset(cx - 11 * s, cy + 11 * s), Offset(cx - 22 * s, cy + 22 * s), paint);

    // Cercle externe pointillé (r=28, dasharray 4 5)
    _drawDashedCircle(canvas, cx, cy, 28 * s, 4 * s, 5 * s, paint);

    // Petit losange en haut
    final diamond = Path()
      ..moveTo(cx, cy - 28 * s)
      ..lineTo(cx + 4 * s, cy - 20 * s)
      ..lineTo(cx, cy - 18 * s)
      ..lineTo(cx - 4 * s, cy - 20 * s)
      ..close();
    canvas.drawPath(diamond, paint);
  }

  void _drawDashedCircle(
    Canvas canvas,
    double cx,
    double cy,
    double radius,
    double dashLen,
    double gapLen,
    Paint paint,
  ) {
    final circumference = 2 * pi * radius;
    final dashCount = (circumference / (dashLen + gapLen)).floor();
    final angleStep = 2 * pi / dashCount;

    for (int i = 0; i < dashCount; i++) {
      final startAngle = i * angleStep;
      final sweep = (dashLen / circumference) * 2 * pi;
      final rect = Rect.fromCircle(center: Offset(cx, cy), radius: radius);
      canvas.drawArc(rect, startAngle, sweep, false, paint);
    }
  }

  @override
  bool shouldRepaint(covariant AdinkraPatternPainter oldDelegate) =>
      opacity != oldDelegate.opacity ||
      tileSize != oldDelegate.tileSize ||
      color != oldDelegate.color;
}

/// Widget réutilisable qui affiche un fond avec motifs Adinkra.
///
/// Usage :
/// ```dart
/// Stack(
///   children: [
///     const AdinkraBackground(opacity: 0.04),
///     // contenu par-dessus
///   ],
/// )
/// ```
class AdinkraBackground extends StatelessWidget {
  const AdinkraBackground({
    super.key,
    this.opacity = 0.08,
    this.tileSize = 80,
    this.color,
  });

  final double opacity;
  final double tileSize;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Positioned.fill(
      child: CustomPaint(
        painter: AdinkraPatternPainter(
          opacity: opacity,
          tileSize: tileSize,
          color: color,
        ),
      ),
    );
  }
}
