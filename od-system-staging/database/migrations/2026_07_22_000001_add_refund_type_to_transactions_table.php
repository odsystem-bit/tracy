<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        $driver = DB::getDriverName();
        if ($driver === 'pgsql') {
            DB::statement("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_type_check");
            DB::statement("ALTER TABLE transactions ADD CONSTRAINT transactions_type_check CHECK (type IN ('deposit','withdrawal','earning','fee','referral_bonus','refund'))");
        } else {
            DB::statement("ALTER TABLE transactions MODIFY COLUMN `type` ENUM('deposit','withdrawal','earning','fee','referral_bonus','refund') NOT NULL");
        }
    }

    public function down(): void
    {
        $driver = DB::getDriverName();
        if ($driver === 'pgsql') {
            DB::statement("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_type_check");
            DB::statement("ALTER TABLE transactions ADD CONSTRAINT transactions_type_check CHECK (type IN ('deposit','withdrawal','earning','fee','referral_bonus'))");
        } else {
            DB::statement("ALTER TABLE transactions MODIFY COLUMN `type` ENUM('deposit','withdrawal','earning','fee','referral_bonus') NOT NULL");
        }
    }
};
