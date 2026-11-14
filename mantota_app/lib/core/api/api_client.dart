import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../config/app_config.dart';

/// Clé de stockage du token d'authentification.
const kAuthTokenKey = 'auth_token';

/// Erreurs normalisées de l'API Mantota.
///
/// Permet à l'UI de réagir de façon cohérente selon le type d'erreur.
sealed class ApiError implements Exception {
  final String message;
  final int? statusCode;

  const ApiError(this.message, [this.statusCode]);

  @override
  String toString() => message;
}

class ApiNetworkError extends ApiError {
  const ApiNetworkError(super.message);
}

class ApiUnauthorized extends ApiError {
  const ApiUnauthorized([String message = 'Session expirée'])
      : super(message, 401);
}

class ApiServerError extends ApiError {
  const ApiServerError(super.message, super.statusCode);
}

class ApiClientError extends ApiError {
  final Map<String, dynamic>? errors;

  const ApiClientError(super.message, super.statusCode, [this.errors]);
}

class ApiTimeout extends ApiError {
  const ApiTimeout(
      [String message = 'Délai dépassé. Vérifiez votre connexion.'])
      : super(message);
}

/// Client HTTP pour l'API Laravel Mantota.
///
/// Fonctionnalités :
/// - Attachement automatique du token Bearer via interceptor
/// - Retry automatique sur erreurs réseau (1 tentative)
/// - Normalisation des erreurs en [ApiError]
/// - Suppression du token sur 401
class ApiClient {
  ApiClient._(this._dio, this._storage);

  final Dio _dio;
  final FlutterSecureStorage _storage;

  /// Crée une instance d'ApiClient avec tous les interceptors configurés.
  static Future<ApiClient> create() async {
    const storage = FlutterSecureStorage();
    final token = await storage.read(key: kAuthTokenKey);

    final dio = Dio(BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: const Duration(milliseconds: AppConfig.connectTimeout),
      receiveTimeout: const Duration(milliseconds: AppConfig.receiveTimeout),
      sendTimeout: const Duration(milliseconds: AppConfig.connectTimeout),
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    ));

    dio.interceptors.add(_AuthInterceptor(storage, token));
    dio.interceptors.add(_RetryInterceptor());
    dio.interceptors.add(_LogInterceptor());

    return ApiClient._(dio, storage);
  }

  /// Met à jour le token stocké (après login/refresh).
  Future<void> setToken(String token) async {
    await _storage.write(key: kAuthTokenKey, value: token);
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  /// Supprime le token (logout).
  Future<void> clearToken() async {
    await _storage.delete(key: kAuthTokenKey);
    _dio.options.headers.remove('Authorization');
  }

  /// Récupère le token actuel.
  Future<String?> getToken() => _storage.read(key: kAuthTokenKey);

  // ── Méthodes HTTP ──

  Future<Map<String, dynamic>> get(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) async {
    try {
      final response =
          await _dio.get<dynamic>(path, queryParameters: queryParameters);
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  Future<Map<String, dynamic>> post(
    String path, {
    dynamic data,
  }) async {
    try {
      final response = await _dio.post<dynamic>(path, data: data);
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  Future<Map<String, dynamic>> put(
    String path, {
    dynamic data,
  }) async {
    try {
      final response = await _dio.put<dynamic>(path, data: data);
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  Future<Map<String, dynamic>> patch(
    String path, {
    dynamic data,
  }) async {
    try {
      final response = await _dio.patch<dynamic>(path, data: data);
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  Future<void> delete(String path) async {
    try {
      await _dio.delete<dynamic>(path);
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  /// Convertit une [DioException] en [ApiError] typé.
  ApiError _mapError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.transformTimeout:
        return const ApiTimeout();

      case DioExceptionType.connectionError:
        return const ApiNetworkError(
          'Connexion impossible. Vérifiez votre réseau.',
        );

      case DioExceptionType.badCertificate:
        return const ApiNetworkError('Certificat SSL invalide.');

      case DioExceptionType.badResponse:
        final statusCode = e.response?.statusCode ?? 0;
        final data = e.response?.data;

        if (statusCode == 401) {
          return const ApiUnauthorized();
        }

        if (statusCode >= 500) {
          return ApiServerError(
            'Erreur serveur ($statusCode). Réessayez plus tard.',
            statusCode,
          );
        }

        // 4xx — erreur client (validation, etc.)
        String message = 'Erreur';
        Map<String, dynamic>? errors;

        if (data is Map<String, dynamic>) {
          message = data['message'] as String? ?? message;
          errors = data['errors'] as Map<String, dynamic>?;
        }

        return ApiClientError(message, statusCode, errors);

      case DioExceptionType.cancel:
        return const ApiNetworkError('Requête annulée.');

      case DioExceptionType.unknown:
        return const ApiNetworkError('Une erreur inattendue est survenue.');
    }
  }
}

// ──────────────────────────────────────────────
//  Interceptors
// ──────────────────────────────────────────────

/// Attache le token Bearer à chaque requête.
class _AuthInterceptor extends Interceptor {
  _AuthInterceptor(this._storage, this._initialToken);

  final FlutterSecureStorage _storage;
  final String? _initialToken;
  String? _token;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    _token ??= _initialToken;
    if (_token != null && _token!.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $_token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (err.response?.statusCode == 401) {
      _token = null;
      _storage.delete(key: kAuthTokenKey);
    }
    handler.next(err);
  }
}

/// Retry automatique sur erreurs réseau (1 seule tentative).
class _RetryInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final isNetworkError = err.type == DioExceptionType.connectionError ||
        err.type == DioExceptionType.connectionTimeout;

    final hasRetried = err.requestOptions.extra['retry_attempted'] == true;

    if (isNetworkError && !hasRetried) {
      err.requestOptions.extra['retry_attempted'] = true;
      try {
        final response = await Dio().fetch(err.requestOptions);
        handler.resolve(response);
        return;
      } on DioException catch (e) {
        handler.next(e);
        return;
      }
    }
    handler.next(err);
  }
}

/// Logging en mode debug uniquement.
class _LogInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (kDebugMode) {
      debugPrint('→ ${options.method} ${options.path}');
    }
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    if (kDebugMode) {
      debugPrint('← ${response.statusCode} ${response.requestOptions.path}');
    }
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (kDebugMode) {
      debugPrint('✕ ${err.type} ${err.requestOptions.path} — ${err.message}');
    }
    handler.next(err);
  }
}
