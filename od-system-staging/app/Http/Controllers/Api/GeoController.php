<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Models\Quartier;
use App\Models\Ville;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Routing\Controller;

/**
 * GeoController — Résolution géographique et référentiel de quartiers.
 *
 * Endpoints publics utilisés par Tracy (bot) et l'UI pour :
 *  - résoudre un nom de lieu en quartier/ville canonique (insensible casse/accents)
 *  - lister les quartiers d'une ville (pour sélection de livraison)
 */
class GeoController extends Controller
{
    /**
     * GET /api/geo/resolve?query=Ganvié
     *
     * Recherche dans quartiers (priorité) puis villes (fallback)
     * par nom, insensible à la casse et aux accents.
     *
     * Retourne le quartier/ville canonique avec son ville_id parent.
     */
    public function resolve(Request $request): JsonResponse
    {
        $request->validate([
            'query' => 'required|string|min:2|max:100',
        ]);

        $query = trim($request->input('query'));

        // Normalisation : minuscules + suppression des accents
        $normalized = $this->normalize($query);

        // 1. Recherche dans les quartiers (priorité)
        $quartier = Quartier::with('ville')
            ->get()
            ->first(fn ($q) => $this->normalize($q->name) === $normalized
                || str_contains($this->normalize($q->name), $normalized)
                || str_contains($normalized, $this->normalize($q->name))
            );

        if ($quartier) {
            return response()->json([
                'found'        => true,
                'type'         => 'quartier',
                'id'           => $quartier->id,
                'name'         => $quartier->name,
                'arrondissement' => $quartier->arrondissement_name,
                'ville_id'     => $quartier->ville_id,
                'ville_name'   => $quartier->ville?->name,
                'department'   => $quartier->ville?->department_name,
            ]);
        }

        // 2. Fallback : recherche dans les villes
        $ville = Ville::get()
            ->first(fn ($v) => $this->normalize($v->name) === $normalized
                || str_contains($this->normalize($v->name), $normalized)
                || str_contains($normalized, $this->normalize($v->name))
            );

        if ($ville) {
            return response()->json([
                'found'      => true,
                'type'       => 'ville',
                'id'         => $ville->id,
                'name'       => $ville->name,
                'department' => $ville->department_name,
                'country_id' => $ville->country_id,
            ]);
        }

        return response()->json([
            'found'  => false,
            'query'  => $query,
            'message' => 'Aucun quartier ou ville trouvé pour cette requête.',
        ], 404);
    }

    /**
     * GET /api/villes/{id}/quartiers
     *
     * Retourne tous les quartiers d'une ville, pour l'UI de sélection.
     */
    public function villeQuartiers(int $id): JsonResponse
    {
        $ville = Ville::find($id);

        if (!$ville) {
            return response()->json([
                'message' => 'Ville introuvable.',
            ], 404);
        }

        $quartiers = $ville->quartiers()
            ->orderBy('arrondissement_name')
            ->orderBy('name')
            ->get(['id', 'name', 'arrondissement_name']);

        return response()->json([
            'ville' => [
                'id'         => $ville->id,
                'name'       => $ville->name,
                'department' => $ville->department_name,
            ],
            'quartiers' => $quartiers,
        ]);
    }

    /**
     * Normalise une chaîne : minuscules + suppression des accents/diacritiques.
     */
    private function normalize(string $text): string
    {
        $text = mb_strtolower($text, 'UTF-8');
        $text = transliterator_transliterate('Any-Latin; Latin-ASCII; Lower()', $text);
        return trim($text);
    }
}
