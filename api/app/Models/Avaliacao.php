<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Avaliacao extends Model
{
    /** @use HasFactory<\Database\Factories\AvaliacaoFactory> */
    use HasFactory;

    protected $table = 'avaliacoes';

    const CREATED_AT = 'criado_em';
    const UPDATED_AT = 'atualizado_em';

    protected $fillable = [
        'usuario_id',
        'jogo_id',
        'nota',
        'comentario',
    ];

    protected function casts(): array
    {
        return [
            'usuario_id' => 'integer',
            'jogo_id' => 'integer',
            // decimal:1 devolve string no JSON ("8.0"), sempre com uma casa.
            'nota' => 'decimal:1',
        ];
    }

    public function usuario(): BelongsTo
    {
        return $this->belongsTo(Usuario::class, 'usuario_id');
    }

    public function jogo(): BelongsTo
    {
        return $this->belongsTo(Jogo::class, 'jogo_id');
    }

    public function curtidas(): HasMany
    {
        return $this->hasMany(CurtidaAvaliacao::class, 'avaliacao_id');
    }
}
