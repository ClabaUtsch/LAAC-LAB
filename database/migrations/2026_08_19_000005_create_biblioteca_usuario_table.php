<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Nome no singular, como no DDL de origem. Ver secao 4.2 da spec.
        Schema::create('biblioteca_usuario', function (Blueprint $table) {
            $table->id();
            $table->foreignId('usuario_id')->constrained('usuarios')->cascadeOnDelete();
            $table->foreignId('jogo_id')->constrained('jogos')->cascadeOnDelete();
            $table->boolean('favorito')->default(false);
            $table->timestamp('adicionado_em')->nullable();
            $table->timestamp('atualizado_em')->nullable();

            // Ver secao 3.8 da spec: um jogo aparece uma vez por biblioteca.
            $table->unique(['usuario_id', 'jogo_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('biblioteca_usuario');
    }
};
