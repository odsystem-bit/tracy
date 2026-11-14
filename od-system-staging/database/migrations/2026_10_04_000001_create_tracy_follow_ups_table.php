<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('tracy_follow_ups', function (Blueprint $table) {
            $table->id();
            $table->foreignId('vendor_id')->constrained('users')->cascadeOnDelete();
            $table->string('customer_id', 40); // téléphone (whatsapp) ou id utilisateur (app)
            $table->string('channel', 10); // whatsapp, app
            $table->string('context_key', 80); // dédup : ex "nego:{product_id}"
            $table->text('message');
            $table->timestamp('send_at');
            $table->timestamp('sent_at')->nullable();
            $table->string('status', 10)->default('pending'); // pending, sent, failed
            $table->timestamps();

            $table->index(['status', 'send_at']);
            $table->unique(['vendor_id', 'customer_id', 'context_key', 'status']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('tracy_follow_ups');
    }
};
