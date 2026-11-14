import 'package:json_annotation/json_annotation.dart';

part 'order.g.dart';

enum OrderStatus {
  @JsonValue('pending') pending,
  @JsonValue('confirmed') confirmed,
  @JsonValue('paid') paid,
  @JsonValue('shipped') shipped,
  @JsonValue('delivered') delivered,
  @JsonValue('cancelled') cancelled,
}

@JsonSerializable()
class Order {
  final String id;
  final String reference;
  @JsonKey(name: 'product_name')
  final String productName;
  @JsonKey(name: 'product_image')
  final String? productImage;
  final int quantity;
  final int total;
  final String currency;
  final OrderStatus status;
  @JsonKey(name: 'customer_name')
  final String? customerName;
  @JsonKey(name: 'store_name')
  final String? storeName;
  @JsonKey(name: 'delivery_address')
  final String? deliveryAddress;
  @JsonKey(name: 'created_at')
  final String createdAt;
  @JsonKey(name: 'updated_at')
  final String? updatedAt;

  Order({
    required this.id,
    required this.reference,
    required this.productName,
    this.productImage,
    this.quantity = 1,
    required this.total,
    this.currency = 'XOF',
    this.status = OrderStatus.pending,
    this.customerName,
    this.storeName,
    this.deliveryAddress,
    required this.createdAt,
    this.updatedAt,
  });

  factory Order.fromJson(Map<String, dynamic> json) => _$OrderFromJson(json);
  Map<String, dynamic> toJson() => _$OrderToJson(this);

  String get formattedTotal {
    final groups = <String>[];
    String str = total.toString();
    while (str.length > 3) {
      groups.insert(0, str.substring(str.length - 3));
      str = str.substring(0, str.length - 3);
    }
    groups.insert(0, str);
    return '${groups.join(' ')} F';
  }

  String get statusLabel => switch (status) {
        OrderStatus.pending => 'En attente',
        OrderStatus.confirmed => 'Confirmée',
        OrderStatus.paid => 'Payée',
        OrderStatus.shipped => 'Expédiée',
        OrderStatus.delivered => 'Livrée',
        OrderStatus.cancelled => 'Annulée',
      };
}
