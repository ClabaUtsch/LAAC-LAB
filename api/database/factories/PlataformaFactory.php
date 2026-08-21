<?php

namespace Database\Factories;

use App\Models\Plataforma;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Plataforma>
 */
class PlataformaFactory extends Factory
{
    protected $model = Plataforma::class;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'nome' => fake()->randomElement([
                'PlayStation 5', 'Xbox Series X', 'Nintendo Switch',
                'PC', 'Steam Deck', 'PlayStation 4', 'Xbox One',
            ]),
        ];
    }
}
