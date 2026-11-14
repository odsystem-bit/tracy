/// Configuration de l'application Mantota.
///
/// Centralise les URLs et constantes selon l'environnement.
/// En production, ces valeurs seront injectées via --dart-define.
class AppConfig {
  const AppConfig._();

  /// Mode mock — contourne l'API pour le dev sans backend.
  /// Désactivé par défaut en production. Activer avec --dart-define=USE_MOCK_AUTH=true
  static const bool useMockAuth = bool.fromEnvironment(
    'USE_MOCK_AUTH',
    defaultValue: false,
  );

  /// URL de l'API Laravel (Mantota).
  /// En production : https://api.mantota.com/api
  /// En dev local : http://10.118.141.113:8000/api (IP LAN pour test sur téléphone physique)
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.118.141.113:8000/api',
  );

  /// URL WebSocket (Laravel Reverb).
  static const String wsUrl = String.fromEnvironment(
    'WS_URL',
    defaultValue: 'wss://ws.mantota.com',
  );

  /// Timeout des requêtes HTTP (millisecondes).
  static const int connectTimeout = 15000;
  static const int receiveTimeout = 30000;
}
