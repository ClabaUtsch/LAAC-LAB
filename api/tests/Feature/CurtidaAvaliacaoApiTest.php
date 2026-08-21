<?php

namespace Tests\Feature;

use App\Models\Avaliacao;
use App\Models\CurtidaAvaliacao;
use App\Models\Usuario;
use Illuminate\Database\QueryException;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class CurtidaAvaliacaoApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_index_lista_as_curtidas(): void
    {
        CurtidaAvaliacao::factory()->count(3)->create();

        $this->getJson('/api/curtidas_avaliacoes')
            ->assertOk()
            ->assertJsonCount(3);
    }

    public function test_store_cria_curtida_e_retorna_201(): void
    {
        $avaliacao = Avaliacao::factory()->create();
        $usuario = Usuario::factory()->create();

        $this->postJson('/api/curtidas_avaliacoes', [
            'avaliacao_id' => $avaliacao->id,
            'usuario_id' => $usuario->id,
        ])
            ->assertCreated()
            ->assertJsonPath('avaliacao_id', $avaliacao->id)
            ->assertJsonPath('usuario_id', $usuario->id);

        $this->assertDatabaseHas('curtidas_avaliacoes', [
            'avaliacao_id' => $avaliacao->id,
            'usuario_id' => $usuario->id,
        ]);
    }

    public function test_store_sem_dados_retorna_422(): void
    {
        $this->postJson('/api/curtidas_avaliacoes', [])
            ->assertStatus(422)
            ->assertJsonValidationErrors(['avaliacao_id', 'usuario_id']);
    }

    public function test_store_rejeita_curtida_repetida_com_422(): void
    {
        $curtida = CurtidaAvaliacao::factory()->create();

        $this->postJson('/api/curtidas_avaliacoes', [
            'avaliacao_id' => $curtida->avaliacao_id,
            'usuario_id' => $curtida->usuario_id,
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('usuario_id');
    }

    public function test_o_banco_rejeita_curtida_repetida_como_rede_de_seguranca(): void
    {
        $curtida = CurtidaAvaliacao::factory()->create();

        $this->expectException(QueryException::class);

        CurtidaAvaliacao::create([
            'avaliacao_id' => $curtida->avaliacao_id,
            'usuario_id' => $curtida->usuario_id,
        ]);
    }

    public function test_apagar_avaliacao_apaga_suas_curtidas_em_cascata(): void
    {
        $curtida = CurtidaAvaliacao::factory()->create();

        Avaliacao::findOrFail($curtida->avaliacao_id)->delete();

        $this->assertDatabaseMissing('curtidas_avaliacoes', ['id' => $curtida->id]);
    }

    public function test_apagar_usuario_apaga_avaliacao_e_curtidas_em_cascata(): void
    {
        $curtida = CurtidaAvaliacao::factory()->create();
        $avaliacao = Avaliacao::findOrFail($curtida->avaliacao_id);

        // Apaga o AUTOR da avaliacao, nao quem curtiu: a cascata tem que
        // percorrer usuario -> avaliacao -> curtida.
        Usuario::findOrFail($avaliacao->usuario_id)->delete();

        $this->assertDatabaseMissing('avaliacoes', ['id' => $avaliacao->id]);
        $this->assertDatabaseMissing('curtidas_avaliacoes', ['id' => $curtida->id]);
    }

    public function test_a_avaliacao_expoe_suas_curtidas(): void
    {
        $curtida = CurtidaAvaliacao::factory()->create();

        $avaliacao = Avaliacao::with('curtidas')->findOrFail($curtida->avaliacao_id);

        $this->assertCount(1, $avaliacao->curtidas);
    }

    public function test_show_retorna_a_curtida(): void
    {
        $curtida = CurtidaAvaliacao::factory()->create();

        $this->getJson("/api/curtidas_avaliacoes/{$curtida->id}")
            ->assertOk()
            ->assertJsonPath('id', $curtida->id);
    }

    public function test_show_de_id_inexistente_retorna_404(): void
    {
        $this->getJson('/api/curtidas_avaliacoes/999')->assertNotFound();
    }

    public function test_update_troca_o_usuario_da_curtida(): void
    {
        $curtida = CurtidaAvaliacao::factory()->create();
        $outro = Usuario::factory()->create();

        $this->putJson("/api/curtidas_avaliacoes/{$curtida->id}", [
            'usuario_id' => $outro->id,
        ])
            ->assertOk()
            ->assertJsonPath('usuario_id', $outro->id);

        $this->assertDatabaseHas('curtidas_avaliacoes', [
            'id' => $curtida->id,
            'usuario_id' => $outro->id,
        ]);
    }

    public function test_update_de_avaliacao_para_par_ja_existente_retorna_422(): void
    {
        $curtida = CurtidaAvaliacao::factory()->create();
        $outraAvaliacao = Avaliacao::factory()->create();

        // Ocupa o par (outraAvaliacao, usuario da primeira curtida).
        CurtidaAvaliacao::create([
            'avaliacao_id' => $outraAvaliacao->id,
            'usuario_id' => $curtida->usuario_id,
        ]);

        // O update manda so avaliacao_id: a checagem de unicidade tem que
        // rodar mesmo assim.
        $this->putJson("/api/curtidas_avaliacoes/{$curtida->id}", [
            'avaliacao_id' => $outraAvaliacao->id,
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('usuario_id');
    }

    public function test_update_de_id_inexistente_retorna_404(): void
    {
        $this->putJson('/api/curtidas_avaliacoes/999', ['usuario_id' => 1])
            ->assertNotFound();
    }

    public function test_destroy_remove_a_curtida_e_retorna_204(): void
    {
        $curtida = CurtidaAvaliacao::factory()->create();

        $this->deleteJson("/api/curtidas_avaliacoes/{$curtida->id}")->assertNoContent();

        $this->assertDatabaseMissing('curtidas_avaliacoes', ['id' => $curtida->id]);
    }

    public function test_destroy_de_id_inexistente_retorna_404(): void
    {
        $this->deleteJson('/api/curtidas_avaliacoes/999')->assertNotFound();
    }
}
