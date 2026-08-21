<?php

namespace Tests\Feature;

use App\Models\Avaliacao;
use App\Models\Jogo;
use App\Models\Usuario;
use Illuminate\Database\QueryException;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class AvaliacaoApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_index_lista_as_avaliacoes(): void
    {
        Avaliacao::factory()->count(3)->create();

        $this->getJson('/api/avaliacoes')
            ->assertOk()
            ->assertJsonCount(3);
    }

    public function test_store_cria_avaliacao_e_retorna_201(): void
    {
        $usuario = Usuario::factory()->create();
        $jogo = Jogo::factory()->create();

        // O cast decimal:1 devolve string: 8.5 entra, "8.5" sai.
        $this->postJson('/api/avaliacoes', [
            'usuario_id' => $usuario->id,
            'jogo_id' => $jogo->id,
            'nota' => 8.5,
            'comentario' => 'Divertido, mas cheio de bugs.',
        ])
            ->assertCreated()
            ->assertJsonPath('nota', '8.5')
            ->assertJsonPath('comentario', 'Divertido, mas cheio de bugs.');

        $this->assertDatabaseHas('avaliacoes', ['usuario_id' => $usuario->id]);
    }

    public function test_a_nota_e_normalizada_para_uma_casa_decimal(): void
    {
        $usuario = Usuario::factory()->create();
        $jogo = Jogo::factory()->create();

        $this->postJson('/api/avaliacoes', [
            'usuario_id' => $usuario->id,
            'jogo_id' => $jogo->id,
            'nota' => 8,
        ])
            ->assertCreated()
            ->assertJsonPath('nota', '8.0');
    }

    public function test_store_sem_dados_retorna_422(): void
    {
        $this->postJson('/api/avaliacoes', [])
            ->assertStatus(422)
            ->assertJsonValidationErrors(['usuario_id', 'jogo_id']);
    }

    public function test_store_rejeita_nota_acima_do_maximo(): void
    {
        $usuario = Usuario::factory()->create();
        $jogo = Jogo::factory()->create();

        $this->postJson('/api/avaliacoes', [
            'usuario_id' => $usuario->id,
            'jogo_id' => $jogo->id,
            'nota' => 10,
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('nota');
    }

    public function test_store_rejeita_nota_com_casas_decimais_demais(): void
    {
        $usuario = Usuario::factory()->create();
        $jogo = Jogo::factory()->create();

        // decimal(2,1) guarda uma casa. 8.55 seria arredondado no MySQL e
        // gravado literal no SQLite — bancos divergentes a partir da mesma
        // entrada.
        $this->postJson('/api/avaliacoes', [
            'usuario_id' => $usuario->id,
            'jogo_id' => $jogo->id,
            'nota' => 8.55,
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('nota');
    }

    public function test_store_com_usuario_inexistente_retorna_422(): void
    {
        $jogo = Jogo::factory()->create();

        $this->postJson('/api/avaliacoes', [
            'usuario_id' => 999999,
            'jogo_id' => $jogo->id,
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('usuario_id');
    }

    public function test_o_banco_rejeita_avaliacao_de_usuario_inexistente(): void
    {
        $jogo = Jogo::factory()->create();

        $this->expectException(QueryException::class);

        Avaliacao::create([
            'usuario_id' => 999999,
            'jogo_id' => $jogo->id,
            'nota' => 5.0,
        ]);
    }

    public function test_apagar_jogo_apaga_suas_avaliacoes_em_cascata(): void
    {
        $avaliacao = Avaliacao::factory()->create();

        Jogo::findOrFail($avaliacao->jogo_id)->delete();

        $this->assertDatabaseMissing('avaliacoes', ['id' => $avaliacao->id]);
    }

    public function test_apagar_usuario_apaga_suas_avaliacoes_em_cascata(): void
    {
        $avaliacao = Avaliacao::factory()->create();

        Usuario::findOrFail($avaliacao->usuario_id)->delete();

        $this->assertDatabaseMissing('avaliacoes', ['id' => $avaliacao->id]);
    }

    public function test_o_jogo_expoe_suas_avaliacoes(): void
    {
        $avaliacao = Avaliacao::factory()->create();

        $jogo = Jogo::with('avaliacoes')->findOrFail($avaliacao->jogo_id);

        $this->assertCount(1, $jogo->avaliacoes);
    }

    public function test_o_mesmo_usuario_pode_avaliar_o_mesmo_jogo_duas_vezes(): void
    {
        $avaliacao = Avaliacao::factory()->create();

        $this->postJson('/api/avaliacoes', [
            'usuario_id' => $avaliacao->usuario_id,
            'jogo_id' => $avaliacao->jogo_id,
            'nota' => 3.0,
        ])->assertCreated();
    }

    public function test_show_retorna_a_avaliacao(): void
    {
        $avaliacao = Avaliacao::factory()->create();

        $this->getJson("/api/avaliacoes/{$avaliacao->id}")
            ->assertOk()
            ->assertJsonPath('id', $avaliacao->id);
    }

    public function test_show_de_id_inexistente_retorna_404(): void
    {
        $this->getJson('/api/avaliacoes/999')->assertNotFound();
    }

    public function test_update_altera_o_comentario(): void
    {
        $avaliacao = Avaliacao::factory()->create();

        $this->putJson("/api/avaliacoes/{$avaliacao->id}", [
            'comentario' => 'Mudei de ideia, corrigiram os bugs.',
        ])
            ->assertOk()
            ->assertJsonPath('comentario', 'Mudei de ideia, corrigiram os bugs.');

        $this->assertDatabaseHas('avaliacoes', [
            'id' => $avaliacao->id,
            'comentario' => 'Mudei de ideia, corrigiram os bugs.',
        ]);
    }

    public function test_update_de_id_inexistente_retorna_404(): void
    {
        $this->putJson('/api/avaliacoes/999', ['comentario' => 'x'])
            ->assertNotFound();
    }

    public function test_destroy_remove_a_avaliacao_e_retorna_204(): void
    {
        $avaliacao = Avaliacao::factory()->create();

        $this->deleteJson("/api/avaliacoes/{$avaliacao->id}")->assertNoContent();

        $this->assertDatabaseMissing('avaliacoes', ['id' => $avaliacao->id]);
    }

    public function test_destroy_de_id_inexistente_retorna_404(): void
    {
        $this->deleteJson('/api/avaliacoes/999')->assertNotFound();
    }
}
