// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'user.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

User _$UserFromJson(Map<String, dynamic> json) => User(
  id: (json['id'] as num).toInt(),
  name: json['name'] as String,
  displayName: json['display_name'] as String?,
  phone: json['phone'] as String,
  avatarUrl: json['avatar_url'] as String?,
  modes: (json['modes'] as List<dynamic>)
      .map((e) => UserMode.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$UserToJson(User instance) => <String, dynamic>{
  'id': instance.id,
  'name': instance.name,
  'display_name': instance.displayName,
  'phone': instance.phone,
  'avatar_url': instance.avatarUrl,
  'modes': instance.modes,
};

UserMode _$UserModeFromJson(Map<String, dynamic> json) => UserMode(
  mode: json['mode'] as String,
  isActive: json['is_active'] as bool,
  canDeactivate: json['can_deactivate'] as bool,
);

Map<String, dynamic> _$UserModeToJson(UserMode instance) => <String, dynamic>{
  'mode': instance.mode,
  'is_active': instance.isActive,
  'can_deactivate': instance.canDeactivate,
};
