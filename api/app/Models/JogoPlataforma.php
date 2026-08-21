<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class JogoPlataforma extends Model
{
    /** @use HasFactory<\Database\Factories\JogoPlataformaFactory> */
    use HasFactory;

    protected $table = 'jogos_plataformas';

    const CREATED_AT = 'criado_em';
    const UPDATED_AT = 'atualizado_em';

    protected $fillable = [
        'jogo_id',
        'plataforma_id',
    ];

    protected function casts(): array
    {
        return [
            'jogo_id' => 'integer',
            'plataforma_id' => 'integer',
        ];
    }

    public function jogo(): BelongsTo
    {
        return $this->belongsTo(Jogo::class, 'jogo_id');
    }

    public function plataforma(): BelongsTo
    {
        return $this->belongsTo(Plataforma::class, 'plataforma_id');
    }
}
