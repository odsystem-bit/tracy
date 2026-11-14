// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'product.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Product _$ProductFromJson(Map<String, dynamic> json) => Product(
  id: json['id'] as String,
  name: json['name'] as String,
  description: json['description'] as String? ?? '',
  price: (json['price'] as num).toInt(),
  currency: json['currency'] as String? ?? 'XOF',
  imageUrl: json['image_url'] as String?,
  storeName: json['store_name'] as String?,
  storeId: json['store_id'] as String?,
  category: json['category'] as String?,
  stock: (json['stock'] as num?)?.toInt() ?? 0,
  rating: (json['rating'] as num?)?.toDouble(),
);

Map<String, dynamic> _$ProductToJson(Product instance) => <String, dynamic>{
  'id': instance.id,
  'name': instance.name,
  'description': instance.description,
  'price': instance.price,
  'currency': instance.currency,
  'image_url': instance.imageUrl,
  'store_name': instance.storeName,
  'store_id': instance.storeId,
  'category': instance.category,
  'stock': instance.stock,
  'rating': instance.rating,
};
