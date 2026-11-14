<?php

declare(strict_types=1);

namespace App\Console\Commands;

use App\Models\KnowledgeDocument;
use Illuminate\Console\Command;

use function Laravel\Prompts\confirm;
use function Laravel\Prompts\table;

/**
 * knowledge:approve — Valide et ingère des documents de connaissance RAG.
 *
 * Permet à l'admin de :
 *  1. Lister les documents draft (avec résumé : title, category, longueur contenu).
 *  2. Confirmer individuellement chaque approbation (jamais en masse sans confirmation).
 *  3. Déclencher l'ingestion (embeddings + chunks) via le script Tracy Core.
 *
 * Usage :
 *   php artisan knowledge:approve              # Liste tous les draft
 *   php artisan knowledge:approve 1,2,3        # Liste les draft 1, 2, 3
 *   php artisan knowledge:approve --all-benin  # Liste les draft liés au Bénin
 */
class KnowledgeApprove extends Command
{
    protected $signature = 'knowledge:approve
                            {ids? : IDs des documents à approuver, séparés par des virgules (ex: 1,2,3)}
                            {--all-benin : Approuver tous les documents draft liés au Bénin}';

    protected $description = 'Valide (approve) et ingère des documents de connaissance RAG avec confirmation interactive';

    public function handle(): int
    {
        $query = KnowledgeDocument::where('status', 'draft');

        if ($this->option('all-benin')) {
            $benin = \DB::table('countries')->where('code', 'BJ')->first();
            if (!$benin) {
                $this->error('Pays Bénin (BJ) introuvable dans la table countries.');
                return self::FAILURE;
            }
            $query->where('country_id', $benin->id);
        }

        $idsArg = $this->argument('ids');
        if ($idsArg) {
            $ids = array_filter(array_map('intval', explode(',', $idsArg)));
            if (!empty($ids)) {
                $query->whereIn('id', $ids);
            }
        }

        $documents = $query->orderBy('id')->get();

        if ($documents->isEmpty()) {
            $this->info('Aucun document draft trouvé correspondant aux critères.');
            return self::SUCCESS;
        }

        // Affiche le résumé
        $this->info("\n📋 Documents draft trouvés : " . $documents->count() . "\n");

        table(
            ['ID', 'Titre', 'Catégorie', 'Longueur contenu', 'Pays'],
            $documents->map(fn ($doc) => [
                $doc->id,
                $doc->title,
                $doc->category,
                strlen($doc->content) . ' caractères',
                $doc->country?->name ?? '—',
            ])->toArray()
        );

        $this->newLine();

        $approved = [];
        $skipped = [];

        foreach ($documents as $doc) {
            $this->newLine();
            $this->line("─── Document #{$doc->id} ───");
            $this->line("Titre : {$doc->title}");
            $this->line("Catégorie : {$doc->category}");
            $this->line("Contenu (extrait) : " . mb_substr($doc->content, 0, 200) . '...');
            $this->line("Longueur : " . strlen($doc->content) . " caractères");

            $confirmed = confirm(
                label: "Approuver le document #{$doc->id} « {$doc->title} » ?",
                default: false,
                yes: 'Oui, approuver et ingérer',
                no: 'Non, passer',
            );

            if (!$confirmed) {
                $skipped[] = $doc->id;
                $this->line("  ⏭️  Document #{$doc->id} ignoré.");
                continue;
            }

            // Change le statut en approved
            $doc->status = 'approved';
            $doc->save();

            $this->info("  ✅ Document #{$doc->id} approuvé (status = approved).");

            // Déclenche l'ingestion via le script Tracy Core
            $this->line("  🔄 Lancement de l'ingestion (embeddings + chunks)...");

            $tracyCorePath = base_path('../tracy-core');
            if (!is_dir($tracyCorePath)) {
                $tracyCorePath = base_path('tracy-core');
            }

            $venvPython = $tracyCorePath . '/.venv/bin/python';
            if (!file_exists($venvPython)) {
                $venvPython = 'python3';
            }

            $scriptPath = $tracyCorePath . '/scripts/ingest_knowledge.py';
            if (!file_exists($scriptPath)) {
                $this->warn("  ⚠️  Script d'ingestion introuvable : {$scriptPath}");
                $this->warn("  ⚠️  Document approuvé mais NON ingéré. Lancez manuellement :");
                $this->warn("      cd tracy-core && .venv/bin/python scripts/ingest_knowledge.py --document-id {$doc->id}");
                $approved[] = $doc->id;
                continue;
            }

            $command = sprintf(
                '%s %s --document-id %d 2>&1',
                escapeshellarg($venvPython),
                escapeshellarg($scriptPath),
                $doc->id
            );

            $this->line("  → Exécution : {$command}");

            $output = [];
            $exitCode = 0;
            exec($command, $output, $exitCode);

            $outputText = implode("\n", $output);

            if ($exitCode === 0) {
                $this->info("  ✅ Ingestion terminée avec succès.");
                if ($outputText) {
                    $this->line("  " . $outputText);
                }
            } else {
                $this->warn("  ⚠️  L'ingestion a échoué (exit code: {$exitCode}).");
                $this->warn("  ⚠️  Le document est approuvé mais non indexé. Relancez manuellement :");
                $this->warn("      cd tracy-core && .venv/bin/python scripts/ingest_knowledge.py --document-id {$doc->id}");
                if ($outputText) {
                    $this->line("  Sortie : " . $outputText);
                }
            }

            $approved[] = $doc->id;
        }

        // Résumé final
        $this->newLine();
        $this->info("════════════════════════════════════════");
        $this->info("  Résumé");
        $this->info("════════════════════════════════════════");
        $this->info("  Approuvés et ingérés : " . count($approved));
        if (!empty($approved)) {
            $this->info("  IDs : " . implode(', ', $approved));
        }
        $this->info("  Ignorés : " . count($skipped));
        if (!empty($skipped)) {
            $this->info("  IDs : " . implode(', ', $skipped));
        }
        $this->info("════════════════════════════════════════");

        return self::SUCCESS;
    }
}
