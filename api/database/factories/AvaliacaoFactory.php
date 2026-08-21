<?php

namespace Database\Factories;

use App\Models\Avaliacao;
use App\Models\Jogo;
use App\Models\Usuario;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Avaliacao>
 */
class AvaliacaoFactory extends Factory
{
    protected $model = Avaliacao::class;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'usuario_id' => Usuario::factory(),
            'jogo_id' => Jogo::factory(),
            // A coluna e decimal(2,1): o maximo representavel e 9.9.
            'nota' => fake()->randomFloat(1, 0, 9.9),
            'comentario' => fake()->paragraph(),
        ];
    }
}
