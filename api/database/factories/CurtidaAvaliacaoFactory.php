<?php

namespace Database\Factories;

use App\Models\Avaliacao;
use App\Models\CurtidaAvaliacao;
use App\Models\Usuario;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<CurtidaAvaliacao>
 */
class CurtidaAvaliacaoFactory extends Factory
{
    protected $model = CurtidaAvaliacao::class;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'avaliacao_id' => Avaliacao::factory(),
            'usuario_id' => Usuario::factory(),
        ];
    }
}
