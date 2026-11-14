<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('memory_entries', function (Blueprint $table) {
            $table->id();
            $table->string('scope', 50)->index();
            $table->string('entity_id', 100)->index();
            $table->string('key', 255);
            $table->text('value');
            $table->string('source', 50)->default('inferred');
            $table->timestamp('expires_at')->nullable();
            $table->timestamps();

            $table->index(['scope', 'entity_id', 'key']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('memory_entries');
    }
};
