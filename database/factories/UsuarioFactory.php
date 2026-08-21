<?php

namespace Database\Factories;

use App\Models\Usuario;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Usuario>
 */
class UsuarioFactory extends Factory
{
    protected $model = Usuario::class;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'nome_usuario' => fake()->unique()->userName(),
            'email' => fake()->unique()->safeEmail(),
            'senha_hash' => 'senha-secreta',
            'idade' => fake()->numberBetween(13, 80),
            'avatar_url' => fake()->imageUrl(),
            'bio' => fake()->sentence(),
            'nivel' => 1,
        ];
    }
}
