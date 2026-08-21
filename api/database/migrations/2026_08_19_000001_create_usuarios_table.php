<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('usuarios', function (Blueprint $table) {
            $table->id();
            $table->string('nome_usuario', 50)->unique();
            $table->string('email', 100)->unique();
            $table->string('senha_hash');
            $table->integer('idade')->nullable();
            $table->text('avatar_url')->nullable();
            $table->text('bio')->nullable();
            $table->integer('nivel')->default(1);
            $table->timestamp('criado_em')->nullable();
            $table->timestamp('atualizado_em')->nullable();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('usuarios');
    }
};
