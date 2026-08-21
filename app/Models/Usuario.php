<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

class Usuario extends Authenticatable
{
    /** @use HasFactory<\Database\Factories\UsuarioFactory> */
    use HasFactory, Notifiable;

    protected $table = 'usuarios';

    const CREATED_AT = 'criado_em';
    const UPDATED_AT = 'atualizado_em';

    /**
     * A tabela nao tem coluna remember_token; string vazia desliga o recurso.
     */
    protected $rememberTokenName = '';

    protected $fillable = [
        'nome_usuario',
        'email',
        'senha_hash',
        'idade',
        'avatar_url',
        'bio',
        'nivel',
    ];

    protected $hidden = [
        'senha_hash',
    ];

    /**
     * Espelha o default da migration. Sem isto, um POST que nao envia "nivel"
     * devolveria um JSON sem a chave: o default e do banco e so apareceria
     * apos um refresh().
     */
    protected $attributes = [
        'nivel' => 1,
    ];

    protected function casts(): array
    {
        return [
            'idade' => 'integer',
            'nivel' => 'integer',
            'senha_hash' => 'hashed',
        ];
    }

    /**
     * A coluna de senha se chama senha_hash, nao password.
     */
    public function getAuthPassword(): string
    {
        return $this->senha_hash;
    }

    public function jogos(): BelongsToMany
    {
        return $this->belongsToMany(
            Jogo::class,
            'biblioteca_usuario',
            'usuario_id',
            'jogo_id',
        )
            ->withPivot('favorito')
            ->withTimestamps('adicionado_em', 'atualizado_em');
    }

    public function avaliacoes(): HasMany
    {
        return $this->hasMany(Avaliacao::class, 'usuario_id');
    }
}
