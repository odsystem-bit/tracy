<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('shop_negotiation_configs', function (Blueprint $table) {
            $table->enum('address_form', ['tu', 'vous'])->default('tu')->after('currency');
        });
    }

    public function down(): void
    {
        Schema::table('shop_negotiation_configs', function (Blueprint $table) {
            $table->dropColumn('address_form');
        });
    }
};
