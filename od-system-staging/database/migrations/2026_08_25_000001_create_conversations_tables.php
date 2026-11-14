<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('conversations', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user1_id')->constrained('users')->cascadeOnDelete();
            $table->foreignId('user2_id')->constrained('users')->cascadeOnDelete();
            $table->string('last_message')->nullable();
            $table->timestamp('last_message_time')->nullable();
            $table->timestamp('user1_last_read')->nullable();
            $table->timestamp('user2_last_read')->nullable();
            $table->timestamps();

            $table->unique(['user1_id', 'user2_id']);
            $table->index(['user1_id', 'user2_id']);
        });

        Schema::create('conversation_messages', function (Blueprint $table) {
            $table->id();
            $table->foreignId('conversation_id')->constrained('conversations')->cascadeOnDelete();
            $table->foreignId('sender_id')->constrained('users')->cascadeOnDelete();
            $table->enum('type', ['text', 'image', 'audio', 'product', 'order', 'system'])->default('text');
            $table->text('content');
            $table->enum('channel', ['app', 'whatsapp'])->default('app');
            $table->boolean('is_from_tracy')->default(false);
            $table->timestamps();

            $table->index('conversation_id');
            $table->index('sender_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('conversation_messages');
        Schema::dropIfExists('conversations');
    }
};
