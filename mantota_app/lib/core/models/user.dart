import 'package:json_annotation/json_annotation.dart';

part 'user.g.dart';

@JsonSerializable()
class User {
  final int id;
  final String name;
  @JsonKey(name: 'display_name')
  final String? displayName;
  final String phone;
  @JsonKey(name: 'avatar_url')
  final String? avatarUrl;
  final List<UserMode> modes;

  User({
    required this.id,
    required this.name,
    this.displayName,
    required this.phone,
    this.avatarUrl,
    required this.modes,
  });

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
  Map<String, dynamic> toJson() => _$UserToJson(this);

  String get bestName => displayName?.isNotEmpty == true ? displayName! : name;

  bool hasMode(String mode) =>
      modes.any((m) => m.mode == mode && m.isActive);
}

@JsonSerializable()
class UserMode {
  final String mode;
  @JsonKey(name: 'is_active')
  final bool isActive;
  @JsonKey(name: 'can_deactivate')
  final bool canDeactivate;

  UserMode({
    required this.mode,
    required this.isActive,
    required this.canDeactivate,
  });

  factory UserMode.fromJson(Map<String, dynamic> json) =>
      _$UserModeFromJson(json);
  Map<String, dynamic> toJson() => _$UserModeToJson(this);
}
