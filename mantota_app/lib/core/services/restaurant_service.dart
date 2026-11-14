import '../api/api_client.dart';

class RestaurantService {
  RestaurantService(this._api);

  final ApiClient _api;

  Future<List<RestaurantSummary>> listRestaurants({double? lat, double? lng}) async {
    final query = <String, dynamic>{};
    if (lat != null) query['lat'] = lat;
    if (lng != null) query['lng'] = lng;
    final json = await _api.get('/restaurants', queryParameters: query);
    return (json['restaurants'] as List? ?? [])
        .map((e) => RestaurantSummary.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<RestaurantMenu> getMenu(int restaurantId) async {
    final json = await _api.get('/restaurants/$restaurantId/menu');
    return RestaurantMenu.fromJson(json);
  }

  Future<RestaurantOrderResult> createOrder({
    required int restaurantId,
    required String orderType,
    required List<CartItem> items,
    String? deliveryAddress,
    double? deliveryLatitude,
    double? deliveryLongitude,
    String? notes,
  }) async {
    final json = await _api.post('/restaurants/orders', data: {
      'restaurant_id': restaurantId,
      'order_type': orderType,
      'items': items.map((e) => e.toJson()).toList(),
      if (deliveryAddress != null) 'delivery_address': deliveryAddress,
      if (deliveryLatitude != null) 'delivery_latitude': deliveryLatitude,
      if (deliveryLongitude != null) 'delivery_longitude': deliveryLongitude,
      if (notes != null) 'notes': notes,
    });
    return RestaurantOrderResult.fromJson(json);
  }

  Future<List<MyRestaurantOrder>> getMyOrders() async {
    final json = await _api.get('/restaurants/orders');
    return (json['orders'] as List? ?? [])
        .map((e) => MyRestaurantOrder.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<RestaurantOrderStatus> getOrderStatus(int orderId) async {
    final json = await _api.get('/restaurants/orders/$orderId');
    return RestaurantOrderStatus.fromJson(json);
  }
}

// ── Models ──

class RestaurantSummary {
  final int id;
  final String shopName;
  final String? shopLogo;
  final String shopType;
  final String? address;
  final double latitude;
  final double longitude;
  final bool isOpenNow;
  final double rating;

  const RestaurantSummary({
    required this.id,
    required this.shopName,
    this.shopLogo,
    required this.shopType,
    this.address,
    required this.latitude,
    required this.longitude,
    required this.isOpenNow,
    this.rating = 0,
  });

  factory RestaurantSummary.fromJson(Map<String, dynamic> json) => RestaurantSummary(
        id: json['id'] as int,
        shopName: json['shop_name'] as String? ?? 'Restaurant',
        shopLogo: json['shop_logo'] as String?,
        shopType: json['shop_type'] as String? ?? 'restaurant_online',
        address: json['address'] as String?,
        latitude: (json['latitude'] as num?)?.toDouble() ?? 0,
        longitude: (json['longitude'] as num?)?.toDouble() ?? 0,
        isOpenNow: json['is_open_now'] as bool? ?? false,
        rating: (json['rating'] as num?)?.toDouble() ?? 0,
      );
}

class RestaurantMenu {
  final RestaurantInfo restaurant;
  final List<MenuCategoryInfo> categories;
  final List<RestaurantHourInfo> hours;

  const RestaurantMenu({
    required this.restaurant,
    required this.categories,
    required this.hours,
  });

  factory RestaurantMenu.fromJson(Map<String, dynamic> json) => RestaurantMenu(
        restaurant: RestaurantInfo.fromJson(json['restaurant'] as Map<String, dynamic>),
        categories: (json['categories'] as List? ?? [])
            .map((e) => MenuCategoryInfo.fromJson(e as Map<String, dynamic>))
            .toList(),
        hours: (json['hours'] as List? ?? [])
            .map((e) => RestaurantHourInfo.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class RestaurantInfo {
  final int id;
  final String shopName;
  final String? shopLogo;
  final String shopType;
  final String? address;
  final String? phone;
  final bool isOpenNow;

  const RestaurantInfo({
    required this.id,
    required this.shopName,
    this.shopLogo,
    required this.shopType,
    this.address,
    this.phone,
    required this.isOpenNow,
  });

  factory RestaurantInfo.fromJson(Map<String, dynamic> json) => RestaurantInfo(
        id: json['id'] as int,
        shopName: json['shop_name'] as String? ?? 'Restaurant',
        shopLogo: json['shop_logo'] as String?,
        shopType: json['shop_type'] as String? ?? 'restaurant_online',
        address: json['address'] as String?,
        phone: json['phone'] as String?,
        isOpenNow: json['is_open_now'] as bool? ?? false,
      );
}

class MenuCategoryInfo {
  final int id;
  final String name;
  final List<MenuItemInfo> items;

  const MenuCategoryInfo({required this.id, required this.name, required this.items});

  factory MenuCategoryInfo.fromJson(Map<String, dynamic> json) => MenuCategoryInfo(
        id: json['id'] as int,
        name: json['name'] as String? ?? '',
        items: (json['items'] as List? ?? [])
            .map((e) => MenuItemInfo.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class MenuItemInfo {
  final int id;
  final String name;
  final String? description;
  final double price;
  final String imageUrl;
  final int preparationTimeMin;
  final int? calories;
  final bool isVegetarian;
  final bool isHalal;
  final List<MenuOptionInfo> options;

  const MenuItemInfo({
    required this.id,
    required this.name,
    this.description,
    required this.price,
    required this.imageUrl,
    required this.preparationTimeMin,
    this.calories,
    required this.isVegetarian,
    required this.isHalal,
    required this.options,
  });

  factory MenuItemInfo.fromJson(Map<String, dynamic> json) => MenuItemInfo(
        id: json['id'] as int,
        name: json['name'] as String? ?? '',
        description: json['description'] as String?,
        price: (json['price'] as num?)?.toDouble() ?? 0,
        imageUrl: json['image_url'] as String? ?? '',
        preparationTimeMin: (json['preparation_time_min'] as num?)?.toInt() ?? 15,
        calories: json['calories'] as int?,
        isVegetarian: json['is_vegetarian'] as bool? ?? false,
        isHalal: json['is_halal'] as bool? ?? false,
        options: (json['options'] as List? ?? [])
            .map((e) => MenuOptionInfo.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class MenuOptionInfo {
  final int id;
  final String name;
  final String type;
  final bool isRequired;
  final int maxSelections;
  final List<MenuOptionValueInfo> values;

  const MenuOptionInfo({
    required this.id,
    required this.name,
    required this.type,
    required this.isRequired,
    required this.maxSelections,
    required this.values,
  });

  factory MenuOptionInfo.fromJson(Map<String, dynamic> json) => MenuOptionInfo(
        id: json['id'] as int,
        name: json['name'] as String? ?? '',
        type: json['type'] as String? ?? 'single_choice',
        isRequired: json['is_required'] as bool? ?? false,
        maxSelections: (json['max_selections'] as num?)?.toInt() ?? 1,
        values: (json['values'] as List? ?? [])
            .map((e) => MenuOptionValueInfo.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class MenuOptionValueInfo {
  final int id;
  final String name;
  final double priceModifier;
  final bool isDefault;

  const MenuOptionValueInfo({
    required this.id,
    required this.name,
    required this.priceModifier,
    required this.isDefault,
  });

  factory MenuOptionValueInfo.fromJson(Map<String, dynamic> json) => MenuOptionValueInfo(
        id: json['id'] as int,
        name: json['name'] as String? ?? '',
        priceModifier: (json['price_modifier'] as num?)?.toDouble() ?? 0,
        isDefault: json['is_default'] as bool? ?? false,
      );
}

class RestaurantHourInfo {
  final int dayOfWeek;
  final String openTime;
  final String closeTime;
  final bool isClosed;

  const RestaurantHourInfo({
    required this.dayOfWeek,
    required this.openTime,
    required this.closeTime,
    required this.isClosed,
  });

  factory RestaurantHourInfo.fromJson(Map<String, dynamic> json) => RestaurantHourInfo(
        dayOfWeek: (json['day_of_week'] as num?)?.toInt() ?? 0,
        openTime: json['open_time'] as String? ?? '',
        closeTime: json['close_time'] as String? ?? '',
        isClosed: json['is_closed'] as bool? ?? false,
      );
}

class CartItem {
  final int menuItemId;
  final String name;
  final double unitPrice;
  final int quantity;
  final List<Map<String, dynamic>> selectedOptions;
  final String? specialInstructions;

  const CartItem({
    required this.menuItemId,
    required this.name,
    required this.unitPrice,
    required this.quantity,
    this.selectedOptions = const [],
    this.specialInstructions,
  });

  double get totalPrice => unitPrice * quantity;

  Map<String, dynamic> toJson() => {
        'menu_item_id': menuItemId,
        'quantity': quantity,
        if (selectedOptions.isNotEmpty) 'selected_options': selectedOptions,
        if (specialInstructions != null) 'special_instructions': specialInstructions,
      };
}

class RestaurantOrderResult {
  final bool success;
  final int orderId;
  final String orderNumber;
  final double subtotal;
  final double deliveryFee;
  final double total;
  final String? estimatedDeliveryAt;
  final String? error;

  const RestaurantOrderResult({
    required this.success,
    this.orderId = 0,
    this.orderNumber = '',
    this.subtotal = 0,
    this.deliveryFee = 0,
    this.total = 0,
    this.estimatedDeliveryAt,
    this.error,
  });

  factory RestaurantOrderResult.fromJson(Map<String, dynamic> json) => RestaurantOrderResult(
        success: json['success'] as bool? ?? false,
        orderId: (json['order_id'] as num?)?.toInt() ?? 0,
        orderNumber: json['order_number'] as String? ?? '',
        subtotal: (json['subtotal'] as num?)?.toDouble() ?? 0,
        deliveryFee: (json['delivery_fee'] as num?)?.toDouble() ?? 0,
        total: (json['total'] as num?)?.toDouble() ?? 0,
        estimatedDeliveryAt: json['estimated_delivery_at'] as String?,
        error: json['error'] as String?,
      );
}

class MyRestaurantOrder {
  final int id;
  final String orderNumber;
  final String orderType;
  final String status;
  final double subtotal;
  final double deliveryFee;
  final double total;
  final String? estimatedDeliveryAt;
  final String? restaurantName;
  final String? restaurantLogo;
  final List<OrderItemInfo> items;
  final String? createdAt;

  const MyRestaurantOrder({
    required this.id,
    required this.orderNumber,
    required this.orderType,
    required this.status,
    required this.subtotal,
    required this.deliveryFee,
    required this.total,
    this.estimatedDeliveryAt,
    this.restaurantName,
    this.restaurantLogo,
    required this.items,
    this.createdAt,
  });

  factory MyRestaurantOrder.fromJson(Map<String, dynamic> json) => MyRestaurantOrder(
        id: json['id'] as int,
        orderNumber: json['order_number'] as String? ?? '',
        orderType: json['order_type'] as String? ?? 'delivery',
        status: json['status'] as String? ?? 'pending',
        subtotal: (json['subtotal'] as num?)?.toDouble() ?? 0,
        deliveryFee: (json['delivery_fee'] as num?)?.toDouble() ?? 0,
        total: (json['total'] as num?)?.toDouble() ?? 0,
        estimatedDeliveryAt: json['estimated_delivery_at'] as String?,
        restaurantName: json['restaurant_name'] as String?,
        restaurantLogo: json['restaurant_logo'] as String?,
        items: (json['items'] as List? ?? [])
            .map((e) => OrderItemInfo.fromJson(e as Map<String, dynamic>))
            .toList(),
        createdAt: json['created_at'] as String?,
      );
}

class OrderItemInfo {
  final String name;
  final int quantity;
  final double unitPrice;
  final double totalPrice;
  final String? specialInstructions;

  const OrderItemInfo({
    required this.name,
    required this.quantity,
    required this.unitPrice,
    required this.totalPrice,
    this.specialInstructions,
  });

  factory OrderItemInfo.fromJson(Map<String, dynamic> json) => OrderItemInfo(
        name: json['name'] as String? ?? '',
        quantity: (json['quantity'] as num?)?.toInt() ?? 1,
        unitPrice: (json['unit_price'] as num?)?.toDouble() ?? 0,
        totalPrice: (json['total_price'] as num?)?.toDouble() ?? 0,
        specialInstructions: json['special_instructions'] as String?,
      );
}

class RestaurantOrderStatus {
  final int id;
  final String orderNumber;
  final String status;
  final String orderType;
  final double total;
  final String? estimatedDeliveryAt;
  final String? deliveredAt;
  final List<OrderItemInfo> items;

  const RestaurantOrderStatus({
    required this.id,
    required this.orderNumber,
    required this.status,
    required this.orderType,
    required this.total,
    this.estimatedDeliveryAt,
    this.deliveredAt,
    required this.items,
  });

  factory RestaurantOrderStatus.fromJson(Map<String, dynamic> json) => RestaurantOrderStatus(
        id: json['id'] as int,
        orderNumber: json['order_number'] as String? ?? '',
        status: json['status'] as String? ?? 'pending',
        orderType: json['order_type'] as String? ?? 'delivery',
        total: (json['total'] as num?)?.toDouble() ?? 0,
        estimatedDeliveryAt: json['estimated_delivery_at'] as String?,
        deliveredAt: json['delivered_at'] as String?,
        items: (json['items'] as List? ?? [])
            .map((e) => OrderItemInfo.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
