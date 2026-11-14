import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../theme/mantota_theme.dart';

/// Scaffold principal avec bottom navigation bar persistant.
///
/// Utilisé via StatefulShellRoute pour garder le nav visible
/// sur tous les onglets principaux (Chats, Rechercher, Découvrir, Commandes, Profil).
/// Supporte le swipe gauche/droite pour naviguer entre onglets.
/// FAB Tracy flottant en bas à droite.
class MainScaffold extends StatefulWidget {
  final StatefulNavigationShell navigationShell;

  const MainScaffold({super.key, required this.navigationShell});

  @override
  State<MainScaffold> createState() => _MainScaffoldState();
}

class _MainScaffoldState extends State<MainScaffold> {
  double _dragStart = 0;

  void _onHorizontalDragStart(DragStartDetails details) {
    _dragStart = details.globalPosition.dx;
  }

  void _onHorizontalDragEnd(DragEndDetails details) {
    final velocity = details.primaryVelocity ?? 0;
    final current = widget.navigationShell.currentIndex;

    if (velocity < -300 && current < 4) {
      // Swipe gauche → onglet suivant
      widget.navigationShell.goBranch(current + 1);
    } else if (velocity > 300 && current > 0) {
      // Swipe droite → onglet précédent
      widget.navigationShell.goBranch(current - 1);
    }
  }

  @override
  Widget build(BuildContext context) {
    final showFab = widget.navigationShell.currentIndex >= 2;
    return GestureDetector(
      onHorizontalDragStart: _onHorizontalDragStart,
      onHorizontalDragEnd: _onHorizontalDragEnd,
      child: Scaffold(
        body: widget.navigationShell,
        floatingActionButton: showFab
            ? FloatingActionButton(
                onPressed: () => context.go('/tracy'),
                backgroundColor: MantotaColors.teal,
                elevation: 4,
                child: ClipOval(
                  child: Image.asset(
                    'assets/icons/tracy_avatar.jpeg',
                    width: 56,
                    height: 56,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => const Icon(Icons.smart_toy, color: Colors.white, size: 26),
                  ),
                ),
              )
            : null,
        bottomNavigationBar: BottomNavigationBar(
          currentIndex: widget.navigationShell.currentIndex,
          onTap: (index) => widget.navigationShell.goBranch(
            index,
            initialLocation: index == widget.navigationShell.currentIndex,
          ),
          backgroundColor: MantotaColors.white,
          selectedItemColor: MantotaColors.teal,
          unselectedItemColor: MantotaColors.grey2,
          type: BottomNavigationBarType.fixed,
          elevation: 8,
          selectedFontSize: 12,
          unselectedFontSize: 11,
          selectedIconTheme: const IconThemeData(size: 26),
          unselectedIconTheme: const IconThemeData(size: 22),
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.chat_bubble_outline), label: 'Chats'),
            BottomNavigationBarItem(icon: Icon(Icons.search), label: 'Rechercher'),
            BottomNavigationBarItem(icon: Icon(Icons.explore_outlined), label: 'Découvrir'),
            BottomNavigationBarItem(icon: Icon(Icons.receipt_long_outlined), label: 'Commandes'),
            BottomNavigationBarItem(icon: Icon(Icons.person_outline), label: 'Profil'),
          ],
        ),
      ),
    );
  }
}
