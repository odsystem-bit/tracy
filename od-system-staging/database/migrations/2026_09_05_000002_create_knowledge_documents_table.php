<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        // Active l'extension pgvector si elle est installée côté serveur (VPS prod).
        // On teste pg_available_extensions AVANT : un CREATE EXTENSION qui échoue
        // met la transaction en état "aborted" (25P02) et fait échouer tout le reste.
        // Sans pgvector, les colonnes embedding tombent en fallback text dans les
        // migrations suivantes (recherche vectorielle inactive, schéma identique).
        $canVector = (bool) DB::selectOne(
            "SELECT name FROM pg_available_extensions WHERE name = 'vector'"
        );
        if ($canVector) {
            DB::statement('CREATE EXTENSION IF NOT EXISTS vector');
        }

        Schema::create('knowledge_documents', function (Blueprint $table) {
            $table->id();
            $table->string('title');
            $table->longText('content');
            $table->foreignId('country_id')->nullable()->constrained('countries')->nullOnDelete();
            $table->string('category');
            // Statut : draft → pending → approved → archived
            $table->enum('status', ['draft', 'pending', 'approved', 'archived'])->default('draft');
            $table->integer('version')->default(1);
            $table->foreignId('created_by')->nullable()->constrained('users')->nullOnDelete();
            $table->timestamps();

            $table->index(['status', 'country_id']);
            $table->index('category');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('knowledge_documents');
    }
};
