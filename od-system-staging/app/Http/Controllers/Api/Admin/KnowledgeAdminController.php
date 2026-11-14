<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Admin;

use App\Http\Controllers\Controller;
use App\Models\KnowledgeDocument;
use App\Models\KnowledgeChunk;
use App\Models\KnowledgeGap;
use App\Models\Country;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\Rule;

/**
 * KnowledgeAdminController — CRUD admin pour la base de connaissances RAG.
 *
 * Permet de gérer les documents qui alimentent le système RAG de Tracy.
 * Règle fondamentale : le LLM reformule, il ne décide jamais.
 * Les documents approuvés sont indexés (embeddings calculés) via un job/artisan command.
 */
class KnowledgeAdminController extends Controller
{
    /**
     * GET /api/admin/knowledge/documents — Liste paginée des documents.
     */
    public function index(Request $request): JsonResponse
    {
        $query = KnowledgeDocument::with(['country:id,code,name', 'creator:id,name']);

        if ($request->has('status')) {
            $query->where('status', $request->input('status'));
        }
        if ($request->has('category')) {
            $query->where('category', $request->input('category'));
        }
        if ($request->has('country_id')) {
            $query->where('country_id', $request->input('country_id'));
        }

        $perPage = min((int) $request->input('per_page', 20), 100);
        $docs = $query->orderByDesc('created_at')->paginate($perPage);

        return response()->json([
            'data' => $docs->items(),
            'meta' => [
                'total'        => $docs->total(),
                'current_page' => $docs->currentPage(),
                'last_page'    => $docs->lastPage(),
            ],
        ]);
    }

    /**
     * GET /api/admin/knowledge/documents/{id} — Détail d'un document.
     */
    public function show(int $id): JsonResponse
    {
        $doc = KnowledgeDocument::with(['country:id,code,name', 'creator:id,name', 'chunks:id,document_id,chunk_index,content'])
            ->findOrFail($id);

        return response()->json(['data' => $doc]);
    }

    /**
     * POST /api/admin/knowledge/documents — Crée un nouveau document (statut draft par défaut).
     */
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'title'      => 'required|string|max:255',
            'content'    => 'required|string',
            'country_id' => 'nullable|exists:countries,id',
            'category'   => 'required|string|max:100',
            'status'     => ['sometimes', Rule::in(['draft', 'pending', 'approved', 'archived'])],
        ]);

        $doc = KnowledgeDocument::create([
            'title'      => $validated['title'],
            'content'    => $validated['content'],
            'country_id' => $validated['country_id'] ?? null,
            'category'   => $validated['category'],
            'status'     => $validated['status'] ?? 'draft',
            'version'    => 1,
            'created_by' => $request->user()->id,
        ]);

        return response()->json(['data' => $doc], 201);
    }

    /**
     * PUT /api/admin/knowledge/documents/{id} — Met à jour un document.
     * Si le contenu change et que le document était approved, il repasse en draft
     * pour nécessiter une re-validation et une ré-indexation.
     */
    public function update(Request $request, int $id): JsonResponse
    {
        $doc = KnowledgeDocument::findOrFail($id);

        $validated = $request->validate([
            'title'      => 'sometimes|string|max:255',
            'content'    => 'sometimes|string',
            'country_id' => 'nullable|exists:countries,id',
            'category'   => 'sometimes|string|max:100',
        ]);

        $contentChanged = isset($validated['content']) && $validated['content'] !== $doc->content;

        $doc->fill($validated);

        if ($contentChanged && $doc->status === 'approved') {
            $doc->status = 'draft';
            $doc->version += 1;
        }

        $doc->save();

        return response()->json(['data' => $doc]);
    }

    /**
     * PATCH /api/admin/knowledge/documents/{id}/status — Change le statut d'un document.
     * Transition vers "approved" déclenche l'indexation (calcul des embeddings).
     */
    public function changeStatus(Request $request, int $id): JsonResponse
    {
        $doc = KnowledgeDocument::findOrFail($id);

        $validated = $request->validate([
            'status' => ['required', Rule::in(['draft', 'pending', 'approved', 'archived'])],
        ]);

        $wasApproved = $doc->status === 'approved';
        $doc->status = $validated['status'];
        $doc->save();

        // Si on passe à approved, on déclenche l'indexation
        if ($validated['status'] === 'approved' && !$wasApproved) {
            // L'indexation est faite via artisan command ou job — on signale juste qu'elle est nécessaire
            // Le job d'indexation est lancé séparément (scripts/ingest_knowledge.py côté Tracy Core)
        }

        return response()->json(['data' => $doc]);
    }

    /**
     * DELETE /api/admin/knowledge/documents/{id} — Supprime un document et ses chunks.
     */
    public function destroy(int $id): JsonResponse
    {
        $doc = KnowledgeDocument::findOrFail($id);
        $doc->delete(); // cascade supprime les chunks

        return response()->json(['message' => 'Document supprimé.']);
    }

    /**
     * GET /api/admin/knowledge/countries — Liste des pays pour filtrage.
     */
    public function countries(): JsonResponse
    {
        $countries = Country::where('is_active', true)->orderBy('name')->get(['id', 'code', 'name']);

        return response()->json(['data' => $countries]);
    }

    /**
     * POST /api/admin/knowledge/documents/{id}/chunks — Upsert des chunks avec embeddings.
     *
     * Utilisé par le script d'ingestion Tracy Core (scripts/ingest_knowledge.py).
     * Supprime les chunks existants du document et insère les nouveaux.
     */
    public function upsertChunks(Request $request, int $id): JsonResponse
    {
        $doc = KnowledgeDocument::findOrFail($id);

        $validated = $request->validate([
            'chunks'             => 'required|array',
            'chunks.*.chunk_index'  => 'required|integer',
            'chunks.*.content'      => 'required|string',
            'chunks.*.embedding'    => 'required|array',
            'chunks.*.metadata'     => 'nullable|array',
        ]);

        // Supprime les chunks existants (upsert = delete + insert)
        KnowledgeChunk::where('document_id', $id)->delete();

        $inserted = 0;
        foreach ($validated['chunks'] as $chunk) {
            // Insère le chunk sans l'embedding d'abord
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

    // ── Knowledge Gaps (RAG Correctif) ─────────────────────────────

    /**
     * GET /api/admin/knowledge/gaps — Liste des lacunes de connaissance.
     *
     * Triées par occurrence_count décroissant. Filtrable par status, country_id, category_guess.
     */
    public function gapsIndex(Request $request): JsonResponse
    {
        $query = KnowledgeGap::query();

        if ($request->has('status')) {
            $query->where('status', $request->input('status'));
        }
        if ($request->has('country_id')) {
            $query->where('country_id', $request->input('country_id'));
        }
        if ($request->has('category_guess')) {
            $query->where('category_guess', 'like', '%' . $request->input('category_guess') . '%');
        }

        $gaps = $query->orderByDesc('occurrence_count')
            ->orderByDesc('last_seen_at')
            ->paginate(20);

        return response()->json($gaps);
    }

    /**
     * PATCH /api/admin/knowledge/gaps/{id} — Change le statut d'une lacune.
     *
     * L'admin peut : passer en "suggested" manuellement, "ignored" si non pertinent,
     * ou "resolved" avec un resolved_document_id.
     * Jamais d'approbation automatique.
     */
    public function gapsUpdate(Request $request, int $id): JsonResponse
    {
        $gap = KnowledgeGap::findOrFail($id);

        $validated = $request->validate([
            'status'                => ['required', Rule::in(['open', 'suggested', 'resolved', 'ignored'])],
            'resolved_document_id'  => 'nullable|exists:knowledge_documents,id',
        ]);

        $gap->status = $validated['status'];
        if (isset($validated['resolved_document_id'])) {
            $gap->resolved_document_id = $validated['resolved_document_id'];
        }
        $gap->save();

        return response()->json(['data' => $gap]);
    }
}
