<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class BibliotecaUsuario extends Model
{
    /** @use HasFactory<\Database\Factories\BibliotecaUsuarioFactory> */
    use HasFactory;

    protected $table = 'biblioteca_usuario';

    // O DDL chama o timestamp de criacao de "adicionado_em" nesta tabela.
    const CREATED_AT = 'adicionado_em';
    const UPDATED_AT = 'atualizado_em';

    protected $fillable = [
        'usuario_id',
        'jogo_id',
        'favorito',
    ];

    /**
     * Espelha o default da migration, para o POST que nao envia "favorito"
     * devolver a chave em vez de omiti-la.
     */
    protected $attributes = [
        'favorito' => false,
    ];

    protected function casts(): array
    {
        return [
            'usuario_id' => 'integer',
            'jogo_id' => 'integer',
            'favorito' => 'boolean',
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
}
