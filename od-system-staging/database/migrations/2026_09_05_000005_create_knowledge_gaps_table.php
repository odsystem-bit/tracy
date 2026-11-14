<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        // L'extension pgvector doit déjà être activée (migration knowledge_chunks)
        Schema::create('knowledge_gaps', function (Blueprint $table) {
            $table->id();
            $table->text('query_text');
            // query_embedding sera ajouté via raw SQL (vector(1536))
            $table->foreignId('country_id')->nullable()->constrained('countries')->nullOnDelete();
            $table->string('category_guess')->nullable();
            $table->integer('occurrence_count')->default(1);
            $table->timestamp('first_seen_at')->useCurrent();
            $table->timestamp('last_seen_at')->useCurrent();
            $table->enum('status', ['open', 'suggested', 'resolved', 'ignored'])->default('open');
            $table->foreignId('resolved_document_id')->nullable()
                ->constrained('knowledge_documents')->nullOnDelete();
            $table->timestamps();
        });

        $hasVector = (bool) DB::selectOne("SELECT extname FROM pg_extension WHERE extname = 'vector'");
        if ($hasVector) {
            // Ajoute la colonne embedding vector(1536)
            DB::statement("ALTER TABLE knowledge_gaps ADD COLUMN query_embedding vector(1536)");

            // Index pour la recherche par similarité sur les embeddings de gaps
            DB::statement("CREATE INDEX knowledge_gaps_embedding_idx ON knowledge_gaps USING ivfflat (query_embedding vector_cosine_ops) WITH (lists = 50)");
        } else {
            // Fallback sans pgvector : tableau JSON de floats
            DB::statement("ALTER TABLE knowledge_gaps ADD COLUMN query_embedding text NULL");
        }

        // Index pour le filtrage admin
        Schema::table('knowledge_gaps', function (Blueprint $table) {
            $table->index(['status', 'occurrence_count']);
            $table->index('country_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('knowledge_gaps');
    }
};
