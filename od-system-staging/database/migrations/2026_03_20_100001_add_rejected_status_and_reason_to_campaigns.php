<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        $driver = DB::getDriverName();
        if ($driver === 'pgsql') {
            DB::statement("ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_status_check");
            DB::statement("ALTER TABLE campaigns ADD CONSTRAINT campaigns_status_check CHECK (status IN ('draft','active','paused','completed','deleted','expired','rejected'))");
        } else {
            DB::statement("ALTER TABLE `campaigns` MODIFY COLUMN `status` ENUM('draft','active','paused','completed','deleted','expired','rejected') NOT NULL DEFAULT 'draft'");
        }

        Schema::table('campaigns', function (Blueprint $table) {
            $table->text('rejection_reason')->nullable()->after('status');
        });
    }

    public function down(): void
    {
        Schema::table('campaigns', function (Blueprint $table) {
            $table->dropColumn('rejection_reason');
        });

        $driver = DB::getDriverName();
        if ($driver === 'pgsql') {
            DB::statement("ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_status_check");
            DB::statement("ALTER TABLE campaigns ADD CONSTRAINT campaigns_status_check CHECK (status IN ('draft','active','paused','completed','deleted','expired'))");
        } else {
            DB::statement("ALTER TABLE `campaigns` MODIFY COLUMN `status` ENUM('draft','active','paused','completed','deleted','expired') NOT NULL DEFAULT 'draft'");
        }
    }
};
