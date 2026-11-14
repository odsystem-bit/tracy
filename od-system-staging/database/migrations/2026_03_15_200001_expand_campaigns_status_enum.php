<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

/**
 * Ajoute les valeurs 'deleted' et 'expired' a l'ENUM status de campaigns.
 */
return new class extends Migration
{
    public function up(): void
    {
        $driver = DB::getDriverName();
        if ($driver === 'pgsql') {
            DB::statement("ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_status_check");
            DB::statement("ALTER TABLE campaigns ADD CONSTRAINT campaigns_status_check CHECK (status IN ('draft','active','paused','completed','deleted','expired'))");
        } else {
            DB::statement("ALTER TABLE `campaigns` MODIFY COLUMN `status` ENUM('draft','active','paused','completed','deleted','expired') NOT NULL DEFAULT 'draft'");
        }
    }

    public function down(): void
    {
        $driver = DB::getDriverName();
        if ($driver === 'pgsql') {
            DB::statement("ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_status_check");
            DB::statement("ALTER TABLE campaigns ADD CONSTRAINT campaigns_status_check CHECK (status IN ('draft','active','paused','completed'))");
        } else {
            DB::statement("ALTER TABLE `campaigns` MODIFY COLUMN `status` ENUM('draft','active','paused','completed') NOT NULL DEFAULT 'draft'");
        }
    }
};
