<?php

namespace Database\Factories;

use App\Models\BibliotecaUsuario;
use App\Models\Jogo;
use App\Models\Usuario;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<BibliotecaUsuario>
 */
class BibliotecaUsuarioFactory extends Factory
{
    protected $model = BibliotecaUsuario::class;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'usuario_id' => Usuario::factory(),
            'jogo_id' => Jogo::factory(),
            'favorito' => false,
        ];
    }
}
