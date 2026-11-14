<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Bot;

use App\Http\Controllers\Controller;
use App\Models\KnowledgeChunk;
use App\Models\KnowledgeDocument;
use App\Models\KnowledgeGap;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

/**
 * BotKnowledgeController — Endpoint de recherche RAG pour Tracy Core.
 *
 * Reçoit un embedding (généré par Tracy Core via OpenAI) et retourne les chunks
 * les plus pertinents via une recherche pgvector (distance cosinus).
 *
 * Règle fondamentale : le LLM reformule, il ne décide jamais.
 * Ce endpoint ne fait que retrouver du texte — il ne prend aucune décision métier.
 */
class BotKnowledgeController extends Controller
{
    /**
     * POST /bot/knowledge/search — Recherche vectorielle dans la base de connaissances.
     *
     * Body: {
     *   "embedding": [float, ...],  // 1536 dimensions (text-embedding-3-small)
     *   "country_id": int|null,     // filtrage par pays (null = global)
     *   "category": string|null,    // filtrage par catégorie
     *   "top_k": int                 // nombre de résultats (défaut 5)
     * }
     */
    public function search(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'embedding'  => 'required|array',
            'embedding.*' => 'numeric',
            'country_id' => 'nullable|integer',
            'category'   => 'nullable|string|max:100',
            'top_k'      => 'nullable|integer|min:1|max:20',
        ]);

        $embedding = json_encode($validated['embedding']);
        $countryId = $validated['country_id'] ?? null;
        $category  = $validated['category'] ?? null;
        $topK      = $validated['top_k'] ?? 5;

        // Recherche pgvector : distance cosinus, filtrée par metadata
        // On utilise l'opérateur <=> (cosine distance) de pgvector
        $query = DB::table('knowledge_chunks')
            ->select(
                'knowledge_chunks.id',
                'knowledge_chunks.content',
                'knowledge_chunks.metadata',
                DB::raw('1 - (embedding <=> \'' . $embedding . '\') as score'),
                'knowledge_documents.title',
                'knowledge_documents.category',
                'knowledge_documents.country_id'
            )
            ->join('knowledge_documents', 'knowledge_chunks.document_id', '=', 'knowledge_documents.id')
            ->where('knowledge_documents.status', 'approved');

        // Filtrage par pays : d'abord spécifique au pays, puis fallback global si rien
        if ($countryId) {
            $countryQuery = (clone $query)->where('knowledge_documents.country_id', $countryId);

            if ($category) {
                $countryQuery->where('knowledge_documents.category', $category);
            }

            $results = $countryQuery->orderByRaw('embedding <=> \'' . $embedding . '\'')
                ->limit($topK)
                ->get();

            // Fallback : documents globaux (country_id = null) si pas assez de résultats
            if ($results->count() < $topK) {
                $globalQuery = (clone $query)->whereNull('knowledge_documents.country_id');
                if ($category) {
                    $globalQuery->where('knowledge_documents.category', $category);
                }
                $globalResults = $globalQuery
                    ->whereNotIn('knowledge_chunks.id', $results->pluck('id'))
                    ->orderByRaw('embedding <=> \'' . $embedding . '\'')
                    ->limit($topK - $results->count())
                    ->get();
                $results = $results->concat($globalResults);
            }
        } else {
            // Pas de pays spécifié : tous les documents approved
            if ($category) {
                $query->where('knowledge_documents.category', $category);
            }
            $results = $query->orderByRaw('embedding <=> \'' . $embedding . '\'')
                ->limit($topK)
                ->get();
        }

        return response()->json([
            'results' => $results->map(fn ($r) => [
                'id'          => $r->id,
                'content'     => $r->content,
                'score'       => round((float) $r->score, 4),
                'title'       => $r->title,
                'category'    => $r->category,
                'country_id'  => $r->country_id,
            ]),
        ]);
    }

    /**
     * GET /bot/knowledge/documents — Liste des documents approved (pour le script d'ingestion).
     */
    public function documents(Request $request): JsonResponse
    {
        $query = KnowledgeDocument::where('status', 'approved');

        if ($request->has('country_id')) {
            $query->where('country_id', $request->input('country_id'));
        }

        $docs = $query->orderByDesc('updated_at')->get(['id', 'title', 'content', 'country_id', 'category', 'status']);

        return response()->json([
            'data' => $docs,
        ]);
    }

    /**
     * GET /bot/knowledge/documents/{id} — Détail d'un document (pour le script d'ingestion).
     */
    public function showDocument(int $id): JsonResponse
    {
        $doc = KnowledgeDocument::findOrFail($id);

        return response()->json([
            'data' => $doc,
        ]);
    }

    /**
     * POST /bot/knowledge/documents/{id}/chunks — Upsert des chunks avec embeddings.
     *
     * Utilisé par le script d'ingestion Tracy Core (scripts/ingest_knowledge.py).
     * Supprime les chunks existants du document et insère les nouveaux.
     */
    public function upsertChunks(Request $request, int $id): JsonResponse
    {
        $doc = KnowledgeDocument::findOrFail($id);

        $validated = $request->validate([
            'chunks'                => 'required|array',
            'chunks.*.chunk_index'  => 'required|integer',
            'chunks.*.content'      => 'required|string',
            'chunks.*.embedding'    => 'required|array',
            'chunks.*.metadata'     => 'nullable|array',
        ]);

        // Supprime les chunks existants (upsert = delete + insert)
        KnowledgeChunk::where('document_id', $id)->delete();

        $inserted = 0;
        foreach ($validated['chunks'] as $chunk) {
            $chunkId = DB::table('knowledge_chunks')->insertGetId([
                'document_id'  => $id,
                'chunk_index'  => $chunk['chunk_index'],
                'content'      => $chunk['content'],
                'metadata'     => json_encode($chunk['metadata'] ?? null),
                'created_at'   => now(),
                'updated_at'   => now(),
            ]);

            // Met à jour l'embedding avec une requête brute (pgvector)
            $embeddingStr = '[' . implode(',', array_map('floatval', $chunk['embedding'])) . ']';
            DB::statement(
                "UPDATE knowledge_chunks SET embedding = ?::vector WHERE id = ?",
                [$embeddingStr, $chunkId]
            );

            $inserted++;
        }

        return response()->json([
            'inserted'    => $inserted,
            'document_id' => $id,
        ]);
    }

    /**
     * POST /bot/knowledge/gaps/log — Enregistre ou incrémente une lacune de connaissance.
     *
     * Reçoit query_text, country_id, category_guess, query_embedding.
     * Cherche un gap existant par similarité cosinus (seuil > 0.92 = même lacune).
     * Si trouvé : incrémente occurrence_count et met à jour last_seen_at.
     * Sinon : crée un nouveau gap.
     *
     * Quand occurrence_count atteint KNOWLEDGE_GAP_THRESHOLD (configurable, défaut 5),
     * le gap passe automatiquement de "open" à "suggested".
     * Jamais à "resolved" ou "approved" — uniquement via action admin explicite.
     */
    public function logGap(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'query_text'      => 'required|string',
            'query_embedding'  => 'required|array',
            'country_id'       => 'nullable|integer|exists:countries,id',
            'category_guess'   => 'nullable|string|max:255',
        ]);

        $embeddingStr = '[' . implode(',', array_map('floatval', $validated['query_embedding'])) . ']';
        $similarityThreshold = 0.92; // seuil cosinus pour considérer que c'est la même lacune
        $gapThreshold = (int) config('app.knowledge_gap_threshold', 5);

        // Cherche un gap existant par similarité cosinus (distance < => 1 - 0.92 = 0.08)
        $existingGap = DB::selectOne(
            "SELECT id, occurrence_count FROM knowledge_gaps
             WHERE query_embedding IS NOT NULL
             AND status IN ('open', 'suggested')
             ORDER BY query_embedding <=> ?::vector
             LIMIT 1",
            [$embeddingStr]
        );

        if ($existingGap && $existingGap->id) {
            // Vérifie que la similarité est suffisante (distance cosinus < 1 - threshold)
            $distance = DB::selectOne(
                "SELECT query_embedding <=> ?::vector AS distance FROM knowledge_gaps WHERE id = ?",
                [$embeddingStr, $existingGap->id]
            );

            if ($distance && (1 - $distance->distance) >= $similarityThreshold) {
                // Même lacune : incrémente
                $newCount = $existingGap->occurrence_count + 1;
                $updateData = [
                    'occurrence_count' => $newCount,
                    'last_seen_at'     => now(),
                ];

                // Passage automatique open -> suggested si seuil atteint
                if ($newCount >= $gapThreshold) {
                    $updateData['status'] = 'suggested';
                }

                DB::table('knowledge_gaps')->where('id', $existingGap->id)->update($updateData);

                return response()->json([
                    'action'        => 'incremented',
                    'gap_id'        => $existingGap->id,
                    'occurrence_count' => $newCount,
                ]);
            }
        }

        // Nouveau gap
        $gapId = DB::table('knowledge_gaps')->insertGetId([
            'query_text'      => $validated['query_text'],
            'country_id'       => $validated['country_id'] ?? null,
            'category_guess'   => $validated['category_guess'] ?? null,
            'occurrence_count' => 1,
            'status'           => 'open',
            'first_seen_at'    => now(),
            'last_seen_at'     => now(),
            'created_at'       => now(),
            'updated_at'       => now(),
        ]);

        // Insère l'embedding via raw SQL (pgvector)
        DB::statement(
            "UPDATE knowledge_gaps SET query_embedding = ?::vector WHERE id = ?",
            [$embeddingStr, $gapId]
        );

        return response()->json([
            'action'  => 'created',
            'gap_id'  => $gapId,
        ]);
    }
}
