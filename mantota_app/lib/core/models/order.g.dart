// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'order.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Order _$OrderFromJson(Map<String, dynamic> json) => Order(
  id: json['id'] as String,
  reference: json['reference'] as String,
  productName: json['product_name'] as String,
  productImage: json['product_image'] as String?,
  quantity: (json['quantity'] as num?)?.toInt() ?? 1,
  total: (json['total'] as num).toInt(),
  currency: json['currency'] as String? ?? 'XOF',
  status:
      $enumDecodeNullable(_$OrderStatusEnumMap, json['status']) ??
      OrderStatus.pending,
  customerName: json['customer_name'] as String?,
  storeName: json['store_name'] as String?,
  deliveryAddress: json['delivery_address'] as String?,
  createdAt: json['created_at'] as String,
  updatedAt: json['updated_at'] as String?,
);

Map<String, dynamic> _$OrderToJson(Order instance) => <String, dynamic>{
  'id': instance.id,
  'reference': instance.reference,
  'product_name': instance.productName,
  'product_image': instance.productImage,
  'quantity': instance.quantity,
  'total': instance.total,
  'currency': instance.currency,
  'status': _$OrderStatusEnumMap[instance.status]!,
  'customer_name': instance.customerName,
  'store_name': instance.storeName,
  'delivery_address': instance.deliveryAddress,
  'created_at': instance.createdAt,
  'updated_at': instance.updatedAt,
};

const _$OrderStatusEnumMap = {
  OrderStatus.pending: 'pending',
  OrderStatus.confirmed: 'confirmed',
  OrderStatus.paid: 'paid',
  OrderStatus.shipped: 'shipped',
  OrderStatus.delivered: 'delivered',
  OrderStatus.cancelled: 'cancelled',
};
