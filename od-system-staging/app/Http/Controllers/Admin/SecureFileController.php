<?php

declare(strict_types=1);

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use Illuminate\Support\Facades\Storage;
use Symfony\Component\HttpFoundation\StreamedResponse;

class SecureFileController extends Controller
{
    public function kycDocument(string $path): StreamedResponse
    {
        if (str_contains($path, '..')) {
            abort(403);
        }

        $fullPath = 'kyc/' . $path;

        // fileExists() et non exists() : exists() renvoie true pour un
        // repertoire (ex. kyc/1), ce qui faisait ensuite planter mimeType().
        if (! Storage::disk('local')->fileExists($fullPath)) {
            abort(404);
        }

        $mimeType = Storage::disk('local')->mimeType($fullPath);

        return Storage::disk('local')->response($fullPath, null, [
            'Content-Type' => $mimeType,
            'Cache-Control' => 'no-store, no-cache, must-revalidate, max-age=0',
        ]);
    }
}
