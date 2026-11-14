/// Données de suivi de commande (GET /orders/{id}/track).
class OrderTrackData {
  final TrackOrder order;
  final List<TimelineStep> timeline;

  const OrderTrackData({required this.order, required this.timeline});

  factory OrderTrackData.fromJson(Map<String, dynamic> json) {
    final orderJson = json['order'] as Map<String, dynamic>? ?? {};
    final timelineJson = json['timeline'] as List? ?? [];

    return OrderTrackData(
      order: TrackOrder.fromJson(orderJson),
      timeline: timelineJson
          .map((e) => TimelineStep.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

/// Commande simplifiée pour le suivi.
class TrackOrder {
  final String id;
  final String reference;
  final String status;
  final String? deliveryGuyName;
  final String? deliveryGuyPhone;
  final String? deliveryCompany;
  final String? deliveryDeadline;
  final String? productName;
  final String? deliveryPin;

  const TrackOrder({
    required this.id,
    required this.reference,
    required this.status,
    this.deliveryGuyName,
    this.deliveryGuyPhone,
    this.deliveryCompany,
    this.deliveryDeadline,
    this.productName,
    this.deliveryPin,
  });

  factory TrackOrder.fromJson(Map<String, dynamic> json) {
    final product = json['product'] as Map<String, dynamic>?;
    return TrackOrder(
      id: json['id']?.toString() ?? '',
      reference: json['reference'] as String? ?? '',
      status: (json['status'] as String?) ?? 'pending',
      deliveryGuyName: json['delivery_guy_name'] as String?,
      deliveryGuyPhone: json['delivery_guy_phone'] as String?,
      deliveryCompany: json['delivery_company'] as String?,
      deliveryDeadline: json['delivery_deadline'] as String?,
      productName: product?['name'] as String?,
      deliveryPin: json['delivery_pin'] as String?,
    );
  }
}

/// Étape de la timeline de suivi.
class TimelineStep {
  final String date;
  final String label;
  final String detail;
  final String status;

  const TimelineStep({
    required this.date,
    required this.label,
    this.detail = '',
    required this.status,
  });

  factory TimelineStep.fromJson(Map<String, dynamic> json) => TimelineStep(
        date: json['date'] as String? ?? '',
        label: json['label'] as String? ?? '',
        detail: json['detail'] as String? ?? '',
        status: json['status'] as String? ?? 'pending',
      );
}
