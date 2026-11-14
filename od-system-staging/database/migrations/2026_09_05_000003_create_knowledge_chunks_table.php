<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        // La table knowledge_documents doit exister (migration 2026_09_05_000002)
        // et l'extension pgvector doit être activée.

        Schema::create('knowledge_chunks', function (Blueprint $table) {
            $table->id();
            $table->foreignId('document_id')->constrained('knowledge_documents')->cascadeOnDelete();
            $table->integer('chunk_index')->default(0);
            $table->longText('content');
            // vector(1536) — dimension pour text-embedding-3-small d'OpenAI
            // Colonne brute car Blueprint ne supporte pas le type vector nativement
            $table->jsonb('metadata')->nullable();
            $table->timestamps();

            $table->index(['document_id', 'chunk_index']);
            $table->index('metadata');
        });

        $hasVector = (bool) DB::selectOne("SELECT extname FROM pg_extension WHERE extname = 'vector'");
        if ($hasVector) {
            // Ajoute la colonne embedding de type vector(1536)
            DB::statement("ALTER TABLE knowledge_chunks ADD COLUMN embedding vector(1536)");

            // Index pour recherche vectorielle rapide (IVFFlat)
            // 100 lists — adapté pour quelques milliers de chunks
            DB::statement("CREATE INDEX knowledge_chunks_embedding_idx ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)");
        } else {
            // Fallback sans pgvector : tableau JSON de floats (même pattern que product_image_embeddings)
            DB::statement("ALTER TABLE knowledge_chunks ADD COLUMN embedding text NULL");
        }
    }

    public function down(): void
    {
        Schema::dropIfExists('knowledge_chunks');
    }
};
