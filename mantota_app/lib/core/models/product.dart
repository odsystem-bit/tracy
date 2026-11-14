import 'package:json_annotation/json_annotation.dart';

part 'product.g.dart';

@JsonSerializable()
class Product {
  final String id;
  final String name;
  final String description;
  final int price;
  @JsonKey(name: 'currency')
  final String currency;
  @JsonKey(name: 'image_url')
  final String? imageUrl;
  @JsonKey(name: 'store_name')
  final String? storeName;
  @JsonKey(name: 'store_id')
  final String? storeId;
  @JsonKey(name: 'category')
  final String? category;
  @JsonKey(name: 'stock')
  final int stock;
  @JsonKey(name: 'rating')
  final double? rating;

  Product({
    required this.id,
    required this.name,
    this.description = '',
    required this.price,
    this.currency = 'XOF',
    this.imageUrl,
    this.storeName,
    this.storeId,
    this.category,
    this.stock = 0,
    this.rating,
  });

  factory Product.fromJson(Map<String, dynamic> json) =>
      _$ProductFromJson(json);
  Map<String, dynamic> toJson() => _$ProductToJson(this);

  String get formattedPrice {
    final groups = <String>[];
    String str = price.toString();
    while (str.length > 3) {
      groups.insert(0, str.substring(str.length - 3));
      str = str.substring(0, str.length - 3);
    }
    groups.insert(0, str);
    return '${groups.join(' ')} F';
  }
}
