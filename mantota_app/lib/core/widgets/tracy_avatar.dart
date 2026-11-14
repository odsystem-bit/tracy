import 'package:flutter/material.dart';

import '../theme/mantota_theme.dart';

/// Avatar réutilisable de Tracy.
/// Affiche le logo Tracy avec fallback icône si l'image n'est pas disponible.
class TracyAvatar extends StatelessWidget {
  final double size;
  final double borderRadius;

  const TracyAvatar({super.key, this.size = 32, this.borderRadius = 16});

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: Image.asset(
        'assets/icons/tracy_avatar.jpeg',
        width: size,
        height: size,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) => Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: MantotaColors.tealPale,
            borderRadius: BorderRadius.circular(borderRadius),
          ),
          child: Icon(Icons.smart_toy, color: MantotaColors.teal, size: size * 0.6),
        ),
      ),
    );
  }
}
