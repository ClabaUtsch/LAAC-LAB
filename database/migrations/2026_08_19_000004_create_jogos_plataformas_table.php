<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('jogos_plataformas', function (Blueprint $table) {
            $table->id();
            $table->foreignId('jogo_id')->constrained('jogos')->cascadeOnDelete();
            $table->foreignId('plataforma_id')->constrained('plataformas')->cascadeOnDelete();
            $table->timestamp('criado_em')->nullable();
            $table->timestamp('atualizado_em')->nullable();

            // Nao esta no DDL de origem; ver secao 3.8 da spec. Um jogo lista
            // uma plataforma uma unica vez.
            $table->unique(['jogo_id', 'plataforma_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('jogos_plataformas');
    }
};
