import 'package:geolocator/geolocator.dart';

/// Position approximative du client, envoyée à Tracy pour proposer
/// des produits proches. Aucune position n'est stockée côté app.
class UserLocation {
  const UserLocation({required this.latitude, required this.longitude});

  final double latitude;
  final double longitude;
}

/// Service de localisation (permission demandée une seule fois).
///
/// Retourne `null` si le service est désactivé ou la permission refusée :
/// Tracy retombe alors sur le pays du profil et demande la ville au client.
class LocationService {
  UserLocation? _cached;
  DateTime? _cachedAt;
  bool _denied = false;

  static const _ttl = Duration(minutes: 10);

  Future<UserLocation?> current() async {
    final at = _cachedAt;
    if (_cached != null && at != null && DateTime.now().difference(at) < _ttl) {
      return _cached;
    }
    if (_denied) return null;

    try {
      if (!await Geolocator.isLocationServiceEnabled()) return null;

      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        _denied = true;
        return null;
      }

      final pos = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.low,
          timeLimit: Duration(seconds: 6),
        ),
      );
      _cached = UserLocation(latitude: pos.latitude, longitude: pos.longitude);
      _cachedAt = DateTime.now();
      return _cached;
    } catch (_) {
      return _cached;
    }
  }
}
