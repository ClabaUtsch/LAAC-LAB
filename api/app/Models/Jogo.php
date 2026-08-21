<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Jogo extends Model
{
    /** @use HasFactory<\Database\Factories\JogoFactory> */
    use HasFactory;

    protected $table = 'jogos';

    const CREATED_AT = 'criado_em';
    const UPDATED_AT = 'atualizado_em';

    protected $fillable = [
        'nome',
        'descricao',
        'genero',
        'classificacao',
        'desenvolvedora',
        'data_lancamento',
        'capa_url',
    ];

    protected function casts(): array
    {
        return [
            // Y-m-d para o JSON sair como "2020-12-10", nao datetime ISO.
            'data_lancamento' => 'date:Y-m-d',
        ];
    }

    public function plataformas(): BelongsToMany
    {
        return $this->belongsToMany(
            Plataforma::class,
            'jogos_plataformas',
            'jogo_id',
            'plataforma_id',
        )->withTimestamps('criado_em', 'atualizado_em');
    }

    public function avaliacoes(): HasMany
    {
        return $this->hasMany(Avaliacao::class, 'jogo_id');
    }
}
