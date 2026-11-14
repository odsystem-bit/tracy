// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'conversation.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Conversation _$ConversationFromJson(Map<String, dynamic> json) => Conversation(
  id: json['id'] as String,
  name: json['name'] as String,
  avatarUrl: json['avatar_url'] as String?,
  lastMessage: json['last_message'] as String?,
  lastMessageTime: json['last_message_time'] as String?,
  unreadCount: (json['unread_count'] as num?)?.toInt() ?? 0,
  channel:
      $enumDecodeNullable(_$MessageChannelEnumMap, json['channel']) ??
      MessageChannel.app,
  isOnline: json['is_online'] as bool? ?? false,
  isTracy: json['is_tracy'] as bool? ?? false,
);

Map<String, dynamic> _$ConversationToJson(Conversation instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'avatar_url': instance.avatarUrl,
      'last_message': instance.lastMessage,
      'last_message_time': instance.lastMessageTime,
      'unread_count': instance.unreadCount,
      'channel': _$MessageChannelEnumMap[instance.channel]!,
      'is_online': instance.isOnline,
      'is_tracy': instance.isTracy,
    };

const _$MessageChannelEnumMap = {
  MessageChannel.app: 'app',
  MessageChannel.whatsapp: 'whatsapp',
};

Message _$MessageFromJson(Map<String, dynamic> json) => Message(
  id: json['id'] as String,
  text: json['text'] as String,
  isFromMe: json['is_from_me'] as bool? ?? false,
  isFromTracy: json['is_from_tracy'] as bool? ?? false,
  type:
      $enumDecodeNullable(_$MessageTypeEnumMap, json['type']) ??
      MessageType.text,
  createdAt: json['created_at'] as String,
  channel:
      $enumDecodeNullable(_$MessageChannelEnumMap, json['channel']) ??
      MessageChannel.app,
);

Map<String, dynamic> _$MessageToJson(Message instance) => <String, dynamic>{
  'id': instance.id,
  'text': instance.text,
  'is_from_me': instance.isFromMe,
  'is_from_tracy': instance.isFromTracy,
  'type': _$MessageTypeEnumMap[instance.type]!,
  'created_at': instance.createdAt,
  'channel': _$MessageChannelEnumMap[instance.channel]!,
};

const _$MessageTypeEnumMap = {
  MessageType.text: 'text',
  MessageType.image: 'image',
  MessageType.audio: 'audio',
  MessageType.product: 'product',
  MessageType.order: 'order',
  MessageType.system: 'system',
};
