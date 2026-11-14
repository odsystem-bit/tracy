<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('customers', function (Blueprint $table) {
            $table->id();
            $table->string('customer_id')->unique()->index(); // phone normalisé (ex: 2290197123456)
            $table->string('phone');
            $table->string('display_name')->nullable();
            $table->foreignId('store_id')->nullable()->constrained('users')->nullOnDelete();
            $table->string('channel_origin')->default('app'); // app, whatsapp
            $table->timestamp('last_seen_at')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('customers');
    }
};
