<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('curtidas_avaliacoes', function (Blueprint $table) {
            $table->id();
            $table->foreignId('avaliacao_id')->constrained('avaliacoes')->cascadeOnDelete();
            $table->foreignId('usuario_id')->constrained('usuarios')->cascadeOnDelete();
            $table->timestamp('criado_em')->nullable();
            $table->timestamp('atualizado_em')->nullable();

            // Ver secao 3.8 da spec: um usuario curte uma review uma vez.
            $table->unique(['avaliacao_id', 'usuario_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('curtidas_avaliacoes');
    }
};
