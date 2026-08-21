<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class CurtidaAvaliacao extends Model
{
    /** @use HasFactory<\Database\Factories\CurtidaAvaliacaoFactory> */
    use HasFactory;

    protected $table = 'curtidas_avaliacoes';

    const CREATED_AT = 'criado_em';
    const UPDATED_AT = 'atualizado_em';

    protected $fillable = [
        'avaliacao_id',
        'usuario_id',
    ];

    protected function casts(): array
    {
        return [
            'avaliacao_id' => 'integer',
            'usuario_id' => 'integer',
        ];
    }

    public function avaliacao(): BelongsTo
    {
        return $this->belongsTo(Avaliacao::class, 'avaliacao_id');
    }

    public function usuario(): BelongsTo
    {
        return $this->belongsTo(Usuario::class, 'usuario_id');
    }
}
