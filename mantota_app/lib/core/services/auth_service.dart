import '../api/api_client.dart';
import '../config/app_config.dart';
import '../models/user.dart';

/// Service d'authentification par OTP (téléphone).
///
/// Flow :
/// 1. [requestOtp] → Laravel envoie un SMS avec un code à 6 chiffres
/// 2. [verifyOtp] → Laravel valide le code, crée/connecte l'utilisateur, retourne un token
/// 3. Le token est stocké en SecureStorage via [ApiClient.setToken]
///
/// En mode mock ([AppConfig.useMockAuth] = true), contourne l'API
/// et utilise un code fixe "000000" pour le dev sans backend.
class AuthService {
  AuthService(this._api);

  final ApiClient _api;

  /// Code OTP mock utilisé en mode dev.
  static const String mockOtpCode = '000000';

  /// Demande un code OTP pour le numéro donné.
  ///
  /// Lève [ApiClientError] si le numéro est invalide.
  /// Lève [ApiNetworkError] si le serveur est injoignable.
  Future<OtpResponse> requestOtp(String phone) async {
    if (AppConfig.useMockAuth) {
      await Future.delayed(const Duration(milliseconds: 800));
      return OtpResponse(
        message: 'Code de vérification envoyé (mode démo).',
        phone: phone,
        devCode: mockOtpCode,
      );
    }

    final json = await _api.post('/auth/otp/request', data: {
      'phone': phone,
    });

    return OtpResponse.fromJson(json);
  }

  /// Vérifie le code OTP et connecte ou crée l'utilisateur.
  ///
  /// Le token retourné est automatiquement stocké dans l'ApiClient.
  /// Retourne [AuthResult] contenant l'utilisateur et le token.
  Future<AuthResult> verifyOtp({
    required String phone,
    required String code,
    String? displayName,
  }) async {
    if (AppConfig.useMockAuth) {
      await Future.delayed(const Duration(milliseconds: 800));
      if (code != mockOtpCode) {
        throw Exception('Code incorrect. Utilisez $mockOtpCode en mode démo.');
      }
      final result = AuthResult(
        message: 'Connexion réussie (mode démo).',
        isNewUser: true,
        user: User(
          id: 1,
          name: 'Utilisateur Démo',
          displayName: 'Utilisateur Démo',
          phone: phone,
          avatarUrl: null,
          modes: [
            UserMode(mode: 'buyer', isActive: true, canDeactivate: false),
          ],
        ),
        token: 'mock_token_${DateTime.now().millisecondsSinceEpoch}',
      );
      await _api.setToken(result.token);
      return result;
    }

    final json = await _api.post('/auth/otp/verify', data: {
      'phone': phone,
      'code': code,
      if (displayName != null) 'display_name': displayName,
    });

    final result = AuthResult.fromJson(json);
    await _api.setToken(result.token);
    return result;
  }

  /// Déconnexion — supprime le token local.
  Future<void> logout() async {
    await _api.clearToken();
  }

  /// Active ou désactive un mode utilisateur (buyer/vendor/partner).
  /// Appelle POST /user/modes/toggle sur le backend.
  Future<void> updateModes({required String mode, required bool active}) async {
    if (AppConfig.useMockAuth) {
      await Future.delayed(const Duration(milliseconds: 300));
      return;
    }
    await _api.post('/user/modes/toggle', data: {
      'mode': mode,
      'active': active,
    });
  }

  /// Récupère les modes de l'utilisateur courant depuis le backend.
  Future<List<UserMode>> getModes() async {
    if (AppConfig.useMockAuth) {
      return [
        UserMode(mode: 'buyer', isActive: true, canDeactivate: false),
        UserMode(mode: 'vendor', isActive: false, canDeactivate: true),
      ];
    }
    final json = await _api.get('/user/modes');
    final modes = json['modes'] as List? ?? [];
    return modes.map((e) => UserMode.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Vérifie si l'utilisateur est connecté (token présent).
  Future<bool> isAuthenticated() async {
    final token = await _api.getToken();
    return token != null && token.isNotEmpty;
  }
}

/// Réponse de la demande d'OTP.
class OtpResponse {
  final String message;
  final String phone;
  final String? devCode;

  const OtpResponse({
    required this.message,
    required this.phone,
    this.devCode,
  });

  factory OtpResponse.fromJson(Map<String, dynamic> json) => OtpResponse(
        message: json['message'] as String,
        phone: json['phone'] as String,
        devCode: json['dev_code'] as String?,
      );
}

/// Résultat de la vérification OTP — utilisateur + token.
class AuthResult {
  final String message;
  final bool isNewUser;
  final User user;
  final String token;

  const AuthResult({
    required this.message,
    required this.isNewUser,
    required this.user,
    required this.token,
  });

  factory AuthResult.fromJson(Map<String, dynamic> json) => AuthResult(
        message: json['message'] as String,
        isNewUser: json['is_new_user'] as bool,
        user: User.fromJson(json['user'] as Map<String, dynamic>),
        token: json['token'] as String,
      );
}
