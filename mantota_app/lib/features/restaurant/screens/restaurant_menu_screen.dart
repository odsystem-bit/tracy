import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/providers.dart';
import '../../../core/services/restaurant_service.dart';
import '../../../core/theme/mantota_theme.dart';

class RestaurantMenuScreen extends ConsumerStatefulWidget {
  final int restaurantId;

  const RestaurantMenuScreen({super.key, required this.restaurantId});

  @override
  ConsumerState<RestaurantMenuScreen> createState() => _RestaurantMenuScreenState();
}

class _RestaurantMenuScreenState extends ConsumerState<RestaurantMenuScreen> {
  final List<CartItem> _cart = [];
  String _orderType = 'delivery';

  void _addToCart(MenuItemInfo item) {
    setState(() {
      final existing = _cart.indexWhere((c) => c.menuItemId == item.id);
      if (existing >= 0) {
        _cart[existing] = CartItem(
          menuItemId: item.id,
          name: item.name,
          unitPrice: item.price,
          quantity: _cart[existing].quantity + 1,
        );
      } else {
        _cart.add(CartItem(
          menuItemId: item.id,
          name: item.name,
          unitPrice: item.price,
          quantity: 1,
        ));
      }
    });
  }

  void _removeFromCart(int itemId) {
    setState(() {
      final existing = _cart.indexWhere((c) => c.menuItemId == itemId);
      if (existing >= 0) {
        if (_cart[existing].quantity > 1) {
          _cart[existing] = CartItem(
            menuItemId: _cart[existing].menuItemId,
            name: _cart[existing].name,
            unitPrice: _cart[existing].unitPrice,
            quantity: _cart[existing].quantity - 1,
          );
        } else {
          _cart.removeAt(existing);
        }
      }
    });
  }

  double get _cartTotal => _cart.fold(0, (sum, item) => sum + item.totalPrice);

  int get _cartCount => _cart.fold(0, (sum, item) => sum + item.quantity);

  @override
  Widget build(BuildContext context) {
    final menuAsync = ref.watch(restaurantMenuProvider(widget.restaurantId));

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 22),
          onPressed: () => context.pop(),
        ),
        title: const Text('Menu', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
      ),
      body: menuAsync.when(
        data: (menu) => _buildMenu(context, menu),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, __) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 40, color: MantotaColors.grey3),
              const SizedBox(height: 12),
              const Text('Menu indisponible', style: TextStyle(fontSize: 14, color: MantotaColors.grey2)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.refresh(restaurantMenuProvider(widget.restaurantId)),
                child: const Text('Réessayer'),
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: _cart.isNotEmpty ? _buildCartBar(context) : null,
    );
  }

  Widget _buildMenu(BuildContext context, RestaurantMenu menu) {
    return Stack(
      children: [
        CustomScrollView(
          slivers: [
            SliverToBoxAdapter(child: _buildHeader(menu.restaurant)),
            ...menu.categories.map((cat) => _buildCategorySliver(cat)),
            const SliverPadding(padding: EdgeInsets.only(bottom: 100)),
          ],
        ),
      ],
    );
  }

  Widget _buildHeader(RestaurantInfo info) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (info.shopLogo != null)
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: CachedNetworkImage(
                    imageUrl: info.shopLogo!,
                    width: 60, height: 60,
                    fit: BoxFit.cover,
                    placeholder: (_, __) => Container(width: 60, height: 60, color: MantotaColors.surface1),
                    errorWidget: (_, __, ___) => Container(width: 60, height: 60, color: MantotaColors.surface1, child: const Icon(Icons.restaurant, color: MantotaColors.grey3)),
                  ),
                )
              else
                Container(
                  width: 60, height: 60,
                  decoration: BoxDecoration(color: MantotaColors.surface1, borderRadius: BorderRadius.circular(12)),
                  child: const Icon(Icons.restaurant, color: MantotaColors.grey3),
                ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(info.shopName, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: MantotaColors.grey1)),
                    if (info.address != null)
                      Text(info.address!, style: const TextStyle(fontSize: 12, color: MantotaColors.grey2), maxLines: 1, overflow: TextOverflow.ellipsis),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: info.isOpenNow ? MantotaColors.teal.withValues(alpha: 0.1) : Colors.red.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  info.isOpenNow ? 'Ouvert' : 'Fermé',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: info.isOpenNow ? MantotaColors.teal : Colors.red),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  SliverToBoxAdapter _buildCategorySliver(MenuCategoryInfo category) {
    return SliverToBoxAdapter(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Text(
              category.name,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: MantotaColors.grey1),
            ),
          ),
          ...category.items.map((item) => _MenuItemTile(
            item: item,
            cartQuantity: _cart.where((c) => c.menuItemId == item.id).fold(0, (sum, c) => sum + c.quantity),
            onAdd: () => _addToCart(item),
            onRemove: () => _removeFromCart(item.id),
          )),
        ],
      ),
    );
  }

  Widget _buildCartBar(BuildContext context) {
    return SafeArea(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: MantotaColors.surface3, width: 1)),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(color: MantotaColors.teal, borderRadius: BorderRadius.circular(20)),
              child: Text(
                '$_cartCount',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('Total', style: TextStyle(fontSize: 11, color: MantotaColors.grey2)),
                  Text(
                    '${_cartTotal.toStringAsFixed(0)} F',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: MantotaColors.grey1),
                  ),
                ],
              ),
            ),
            GestureDetector(
              onTap: () => _showCheckout(context),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                decoration: BoxDecoration(color: MantotaColors.teal, borderRadius: BorderRadius.circular(24)),
                child: const Text('Commander', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showCheckout(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom),
        child: _CheckoutSheet(
          cart: _cart,
          total: _cartTotal,
          orderType: _orderType,
          onOrderTypeChanged: (t) => setState(() => _orderType = t),
          onConfirm: () {
            Navigator.pop(ctx);
            _placeOrder();
          },
        ),
      ),
    );
  }

  Future<void> _placeOrder() async {
    final svc = await ref.read(restaurantServiceProvider.future);
    final result = await svc.createOrder(
      restaurantId: widget.restaurantId,
      orderType: _orderType,
      items: _cart,
    );

    if (!mounted) return;

    if (result.success) {
      setState(() => _cart.clear());
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Commande ${result.orderNumber} passée ! Total: ${result.total.toStringAsFixed(0)} F'),
          backgroundColor: MantotaColors.teal,
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result.error ?? 'Erreur lors de la commande'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}

class _MenuItemTile extends StatelessWidget {
  final MenuItemInfo item;
  final int cartQuantity;
  final VoidCallback onAdd;
  final VoidCallback onRemove;

  const _MenuItemTile({
    required this.item,
    required this.cartQuantity,
    required this.onAdd,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: MantotaColors.surface3, width: 1),
      ),
      child: Row(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: CachedNetworkImage(
              imageUrl: item.imageUrl,
              width: 72, height: 72,
              fit: BoxFit.cover,
              placeholder: (_, __) => Container(width: 72, height: 72, color: MantotaColors.surface1),
              errorWidget: (_, __, ___) => Container(width: 72, height: 72, color: MantotaColors.surface1, child: const Icon(Icons.fastfood, color: MantotaColors.grey3)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: MantotaColors.grey1), maxLines: 2, overflow: TextOverflow.ellipsis),
                if (item.description != null)
                  Text(item.description!, style: const TextStyle(fontSize: 12, color: MantotaColors.grey2), maxLines: 1, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text('${item.price.toStringAsFixed(0)} F', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: MantotaColors.teal)),
                    const SizedBox(width: 8),
                    if (item.isVegetarian)
                      const Icon(Icons.eco, size: 14, color: Colors.green),
                    if (item.isHalal)
                      const Padding(padding: EdgeInsets.only(left: 4), child: Text('Halal', style: TextStyle(fontSize: 10, color: Colors.green, fontWeight: FontWeight.w500))),
                    const Spacer(),
                    if (item.preparationTimeMin > 0)
                      Row(children: [const Icon(Icons.timer, size: 12, color: MantotaColors.grey3), const SizedBox(width: 2), Text('${item.preparationTimeMin}min', style: const TextStyle(fontSize: 11, color: MantotaColors.grey3))]),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          if (cartQuantity > 0)
            Row(
              children: [
                _QtyButton(icon: Icons.remove, onTap: onRemove),
                Padding(padding: const EdgeInsets.symmetric(horizontal: 6), child: Text('$cartQuantity', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700))),
                _QtyButton(icon: Icons.add, onTap: onAdd),
              ],
            )
          else
            GestureDetector(
              onTap: onAdd,
              child: Container(
                width: 32, height: 32,
                decoration: const BoxDecoration(color: MantotaColors.teal, shape: BoxShape.circle),
                child: const Icon(Icons.add, color: Colors.white, size: 18),
              ),
            ),
        ],
      ),
    );
  }
}

class _QtyButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;

  const _QtyButton({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 28, height: 28,
        decoration: BoxDecoration(border: Border.all(color: MantotaColors.surface3), shape: BoxShape.circle),
        child: Icon(icon, size: 16, color: MantotaColors.grey1),
      ),
    );
  }
}

class _CheckoutSheet extends StatelessWidget {
  final List<CartItem> cart;
  final double total;
  final String orderType;
  final ValueChanged<String> onOrderTypeChanged;
  final VoidCallback onConfirm;

  const _CheckoutSheet({
    required this.cart,
    required this.total,
    required this.orderType,
    required this.onOrderTypeChanged,
    required this.onConfirm,
  });

  @override
  Widget build(BuildContext context) {
    final deliveryFee = orderType == 'delivery' ? 1000.0 : 0.0;
    final grandTotal = total + deliveryFee;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(color: MantotaColors.surface3, borderRadius: BorderRadius.circular(2)))),
            const SizedBox(height: 16),
            const Text('Récapitulatif', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: MantotaColors.grey1)),
            const SizedBox(height: 16),

            ...cart.map((item) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                children: [
                  Text('${item.quantity}x', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: MantotaColors.grey2)),
                  const SizedBox(width: 8),
                  Expanded(child: Text(item.name, style: const TextStyle(fontSize: 14, color: MantotaColors.grey1))),
                  Text('${item.totalPrice.toStringAsFixed(0)} F', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: MantotaColors.grey1)),
                ],
              ),
            )),

            const Divider(height: 24),

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Sous-total', style: TextStyle(fontSize: 14, color: MantotaColors.grey2)),
                Text('${total.toStringAsFixed(0)} F', style: const TextStyle(fontSize: 14, color: MantotaColors.grey1)),
              ],
            ),
            const SizedBox(height: 8),

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Frais livraison', style: TextStyle(fontSize: 14, color: MantotaColors.grey2)),
                Text('${deliveryFee.toStringAsFixed(0)} F', style: const TextStyle(fontSize: 14, color: MantotaColors.grey1)),
              ],
            ),
            const SizedBox(height: 12),

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Total', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: MantotaColors.grey1)),
                Text('${grandTotal.toStringAsFixed(0)} F', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: MantotaColors.teal)),
              ],
            ),

            const SizedBox(height: 20),

            const Text('Type de commande', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: MantotaColors.grey1)),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: GestureDetector(
                    onTap: () => onOrderTypeChanged('delivery'),
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      decoration: BoxDecoration(
                        color: orderType == 'delivery' ? MantotaColors.teal.withValues(alpha: 0.1) : Colors.transparent,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: orderType == 'delivery' ? MantotaColors.teal : MantotaColors.surface3),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.delivery_dining, size: 18, color: orderType == 'delivery' ? MantotaColors.teal : MantotaColors.grey3),
                          const SizedBox(width: 6),
                          Text('Livraison', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: orderType == 'delivery' ? MantotaColors.teal : MantotaColors.grey2)),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: GestureDetector(
                    onTap: () => onOrderTypeChanged('pickup'),
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      decoration: BoxDecoration(
                        color: orderType == 'pickup' ? MantotaColors.teal.withValues(alpha: 0.1) : Colors.transparent,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: orderType == 'pickup' ? MantotaColors.teal : MantotaColors.surface3),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.store, size: 18, color: orderType == 'pickup' ? MantotaColors.teal : MantotaColors.grey3),
                          const SizedBox(width: 6),
                          Text('Retrait', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: orderType == 'pickup' ? MantotaColors.teal : MantotaColors.grey2)),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: onConfirm,
                style: ElevatedButton.styleFrom(
                  backgroundColor: MantotaColors.teal,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: const Text('Confirmer la commande', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
              ),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }
}
