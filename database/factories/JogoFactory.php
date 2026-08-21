<?php

namespace Database\Factories;

use App\Models\Jogo;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Jogo>
 */
class JogoFactory extends Factory
{
    protected $model = Jogo::class;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'nome' => fake()->unique()->words(3, true),
            'descricao' => fake()->paragraph(),
            'genero' => fake()->randomElement(['RPG', 'FPS', 'Estratégia', 'Corrida', 'Puzzle']),
            'classificacao' => fake()->randomElement(['L', '10', '12', '14', '16', '18']),
            'desenvolvedora' => fake()->company(),
            'data_lancamento' => fake()->date(),
            'capa_url' => fake()->imageUrl(),
        ];
    }
}
