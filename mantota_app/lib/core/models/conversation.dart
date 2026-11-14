import 'package:json_annotation/json_annotation.dart';

part 'conversation.g.dart';

enum MessageChannel { app, whatsapp }

enum MessageType { text, image, audio, product, order, system }

@JsonSerializable()
class Conversation {
  final String id;
  final String name;
  @JsonKey(name: 'avatar_url')
  final String? avatarUrl;
  @JsonKey(name: 'last_message')
  final String? lastMessage;
  @JsonKey(name: 'last_message_time')
  final String? lastMessageTime;
  @JsonKey(name: 'unread_count')
  final int unreadCount;
  final MessageChannel channel;
  @JsonKey(name: 'is_online')
  final bool isOnline;
  @JsonKey(name: 'is_tracy')
  final bool isTracy;

  Conversation({
    required this.id,
    required this.name,
    this.avatarUrl,
    this.lastMessage,
    this.lastMessageTime,
    this.unreadCount = 0,
    this.channel = MessageChannel.app,
    this.isOnline = false,
    this.isTracy = false,
  });

  factory Conversation.fromJson(Map<String, dynamic> json) =>
      _$ConversationFromJson(json);
  Map<String, dynamic> toJson() => _$ConversationToJson(this);

  String get timeLabel => lastMessageTime ?? '';
  String get channelString => channel.name;
}

@JsonSerializable()
class Message {
  final String id;
  final String text;
  @JsonKey(name: 'is_from_me')
  final bool isFromMe;
  @JsonKey(name: 'is_from_tracy')
  final bool isFromTracy;
  final MessageType type;
  @JsonKey(name: 'created_at')
  final String createdAt;
  @JsonKey(name: 'channel')
  final MessageChannel channel;

  Message({
    required this.id,
    required this.text,
    this.isFromMe = false,
    this.isFromTracy = false,
    this.type = MessageType.text,
    required this.createdAt,
    this.channel = MessageChannel.app,
  });

  factory Message.fromJson(Map<String, dynamic> json) =>
      _$MessageFromJson(json);
  Map<String, dynamic> toJson() => _$MessageToJson(this);
}
