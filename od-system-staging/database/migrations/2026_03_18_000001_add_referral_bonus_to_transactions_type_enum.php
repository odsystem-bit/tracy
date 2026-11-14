<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

/**
 * Add 'referral_bonus' to the transactions.type ENUM.
 *
 * Required for the referral system — when a new user registers via referral link,
 * a bonus transaction is created for the referrer with type 'referral_bonus'.
 */
return new class extends Migration
{
    public function up(): void
    {
        $driver = DB::getDriverName();
        if ($driver === 'pgsql') {
            DB::statement("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_type_check");
            DB::statement("ALTER TABLE transactions ADD CONSTRAINT transactions_type_check CHECK (type IN ('deposit','withdrawal','earning','fee','referral_bonus'))");
        } else {
            DB::statement("ALTER TABLE transactions MODIFY COLUMN `type` ENUM('deposit','withdrawal','earning','fee','referral_bonus') NOT NULL");
        }
    }

    public function down(): void
    {
        $driver = DB::getDriverName();
        if ($driver === 'pgsql') {
            DB::statement("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_type_check");
            DB::statement("ALTER TABLE transactions ADD CONSTRAINT transactions_type_check CHECK (type IN ('deposit','withdrawal','earning','fee'))");
        } else {
            DB::statement("ALTER TABLE transactions MODIFY COLUMN `type` ENUM('deposit','withdrawal','earning','fee') NOT NULL");
        }
    }
};
