<?php

namespace Database\Factories;

use App\Models\Jogo;
use App\Models\JogoPlataforma;
use App\Models\Plataforma;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<JogoPlataforma>
 */
class JogoPlataformaFactory extends Factory
{
    protected $model = JogoPlataforma::class;

    /**
     * As FKs sao factories, nao ids fixos: assim
     * JogoPlataforma::factory()->create() funciona sem preparacao previa.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'jogo_id' => Jogo::factory(),
            'plataforma_id' => Plataforma::factory(),
        ];
    }
}
