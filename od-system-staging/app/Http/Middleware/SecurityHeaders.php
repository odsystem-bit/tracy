<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class SecurityHeaders
{
    public function handle(Request $request, Closure $next): Response
    {
        $response = $next($request);

        $response->headers->set('X-Frame-Options', 'SAMEORIGIN');
        $response->headers->set('X-Content-Type-Options', 'nosniff');
        $response->headers->set('X-XSS-Protection', '1; mode=block');
        $response->headers->set('Referrer-Policy', 'strict-origin-when-cross-origin');
        $response->headers->set('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=()');
        $response->headers->set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
        $csp = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://fonts.bunny.net; style-src 'self' 'unsafe-inline' https://fonts.bunny.net; font-src 'self' https://fonts.bunny.net data:; img-src 'self' data: blob: https:; connect-src 'self' wss: https:; frame-ancestors 'self'; base-uri 'self'; form-action 'self'";

        if (app()->environment('local')) {
            $csp = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' http://127.0.0.1:5173 http://localhost:5173 https://fonts.bunny.net; style-src 'self' 'unsafe-inline' http://127.0.0.1:5173 http://localhost:5173 https://fonts.bunny.net https://fonts.googleapis.com; font-src 'self' https://fonts.bunny.net https://fonts.gstatic.com data:; img-src 'self' data: blob: https:; connect-src 'self' wss: https: ws://127.0.0.1:5173 ws://localhost:5173 http://127.0.0.1:8001 https:; frame-ancestors 'self'; base-uri 'self'; form-action 'self'";
        }

        $response->headers->set('Content-Security-Policy', $csp);

        // Empecher l'indexation des pages sensibles (admin, vendor, influencer)
        $path = $request->path();
        if (str_starts_with($path, 'admin') || str_starts_with($path, 'vendor') || str_starts_with($path, 'influencer')) {
            $response->headers->set('X-Robots-Tag', 'noindex, nofollow');
        }

        return $response;
    }
}
