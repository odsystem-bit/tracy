<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('whatsapp_connections', function (Blueprint $table) {
            $table->id();
            $table->foreignId('vendor_id')->constrained('users')->cascadeOnDelete();
            $table->string('phone_number');
            $table->string('phone_number_id')->nullable(); // Meta Phone Number ID
            $table->string('waba_id')->nullable(); // WhatsApp Business Account ID
            $table->string('status')->default('pending'); // pending, connected, disconnected
            $table->boolean('tracy_active')->default(true); // Tracy répond sur WhatsApp
            $stringColumns = [
                'hybrid_mode' => '30s', // immediate, 30s, 1min, 5min
            ];
            $table->string('hybrid_delay')->default('30s');
            $table->integer('monthly_conversation_count')->default(0);
            $table->integer('monthly_conversation_limit')->default(50); // Free = 50, paid = unlimited (0)
            $table->timestamp('connected_at')->nullable();
            $table->timestamps();

            $table->unique('vendor_id');
            $table->index('phone_number');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('whatsapp_connections');
    }
};
