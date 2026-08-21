<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('avaliacoes', function (Blueprint $table) {
            $table->id();
            $table->foreignId('usuario_id')->constrained('usuarios')->cascadeOnDelete();
            $table->foreignId('jogo_id')->constrained('jogos')->cascadeOnDelete();
            $table->decimal('nota', 2, 1)->nullable();
            $table->text('comentario')->nullable();
            $table->timestamp('criado_em')->nullable();
            $table->timestamp('atualizado_em')->nullable();
        });

        // Sem unique: o DDL permite o mesmo usuario avaliar o mesmo jogo mais
        // de uma vez, e a secao 3.8 da spec nao lista esta tabela.
    }

    public function down(): void
    {
        Schema::dropIfExists('avaliacoes');
    }
};
