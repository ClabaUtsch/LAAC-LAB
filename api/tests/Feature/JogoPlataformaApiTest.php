<?php

namespace Tests\Feature;

use App\Models\Jogo;
use App\Models\JogoPlataforma;
use App\Models\Plataforma;
use Illuminate\Database\QueryException;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class JogoPlataformaApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_index_lista_os_vinculos(): void
    {
        JogoPlataforma::factory()->count(3)->create();

        $this->getJson('/api/jogos_plataformas')
            ->assertOk()
            ->assertJsonCount(3);
    }

    public function test_store_cria_vinculo_e_retorna_201(): void
    {
        $jogo = Jogo::factory()->create();
        $plataforma = Plataforma::factory()->create();

        $this->postJson('/api/jogos_plataformas', [
            'jogo_id' => $jogo->id,
            'plataforma_id' => $plataforma->id,
        ])
            ->assertCreated()
            ->assertJsonPath('jogo_id', $jogo->id)
            ->assertJsonPath('plataforma_id', $plataforma->id);

        $this->assertDatabaseHas('jogos_plataformas', [
            'jogo_id' => $jogo->id,
            'plataforma_id' => $plataforma->id,
        ]);
    }

    public function test_store_sem_dados_retorna_422(): void
    {
        $this->postJson('/api/jogos_plataformas', [])
            ->assertStatus(422)
            ->assertJsonValidationErrors(['jogo_id', 'plataforma_id']);
    }

    public function test_store_com_jogo_inexistente_retorna_422(): void
    {
        $plataforma = Plataforma::factory()->create();

        $this->postJson('/api/jogos_plataformas', [
            'jogo_id' => 999999,
            'plataforma_id' => $plataforma->id,
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('jogo_id');
    }

    public function test_store_rejeita_par_duplicado_com_422(): void
    {
        $vinculo = JogoPlataforma::factory()->create();

        $this->postJson('/api/jogos_plataformas', [
            'jogo_id' => $vinculo->jogo_id,
            'plataforma_id' => $vinculo->plataforma_id,
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('plataforma_id');
    }

    public function test_o_banco_rejeita_par_duplicado_como_rede_de_seguranca(): void
    {
        $vinculo = JogoPlataforma::factory()->create();

        $this->expectException(QueryException::class);

        JogoPlataforma::create([
            'jogo_id' => $vinculo->jogo_id,
            'plataforma_id' => $vinculo->plataforma_id,
        ]);
    }

    public function test_apagar_jogo_apaga_os_vinculos_em_cascata(): void
    {
        $vinculo = JogoPlataforma::factory()->create();

        Jogo::findOrFail($vinculo->jogo_id)->delete();

        $this->assertDatabaseMissing('jogos_plataformas', ['id' => $vinculo->id]);
    }

    public function test_apagar_plataforma_apaga_os_vinculos_em_cascata(): void
    {
        $vinculo = JogoPlataforma::factory()->create();

        Plataforma::findOrFail($vinculo->plataforma_id)->delete();

        $this->assertDatabaseMissing('jogos_plataformas', ['id' => $vinculo->id]);
    }

    public function test_o_jogo_expoe_suas_plataformas(): void
    {
        $vinculo = JogoPlataforma::factory()->create();

        $jogo = Jogo::with('plataformas')->findOrFail($vinculo->jogo_id);

        $this->assertCount(1, $jogo->plataformas);
        $this->assertSame($vinculo->plataforma_id, $jogo->plataformas->first()->id);
    }

    public function test_show_retorna_o_vinculo(): void
    {
        $vinculo = JogoPlataforma::factory()->create();

        $this->getJson("/api/jogos_plataformas/{$vinculo->id}")
            ->assertOk()
            ->assertJsonPath('id', $vinculo->id);
    }

    public function test_show_de_id_inexistente_retorna_404(): void
    {
        $this->getJson('/api/jogos_plataformas/999')->assertNotFound();
    }

    public function test_update_troca_a_plataforma(): void
    {
        $vinculo = JogoPlataforma::factory()->create();
        $outra = Plataforma::factory()->create();

        $this->putJson("/api/jogos_plataformas/{$vinculo->id}", [
            'plataforma_id' => $outra->id,
        ])
            ->assertOk()
            ->assertJsonPath('plataforma_id', $outra->id);

        $this->assertDatabaseHas('jogos_plataformas', [
            'id' => $vinculo->id,
            'plataforma_id' => $outra->id,
        ]);
    }

    public function test_update_de_jogo_para_par_ja_existente_retorna_422(): void
    {
        $vinculo = JogoPlataforma::factory()->create();
        $outroJogo = Jogo::factory()->create();

        // Ocupa o par (outroJogo, plataforma do primeiro vinculo).
        JogoPlataforma::create([
            'jogo_id' => $outroJogo->id,
            'plataforma_id' => $vinculo->plataforma_id,
        ]);

        // Mover o primeiro vinculo para outroJogo colidiria com esse segundo.
        // O update manda so jogo_id: a checagem de unicidade tem que rodar
        // mesmo assim.
        $this->putJson("/api/jogos_plataformas/{$vinculo->id}", [
            'jogo_id' => $outroJogo->id,
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('plataforma_id');
    }

    public function test_update_de_id_inexistente_retorna_404(): void
    {
        $this->putJson('/api/jogos_plataformas/999', ['plataforma_id' => 1])
            ->assertNotFound();
    }

    public function test_destroy_remove_o_vinculo_e_retorna_204(): void
    {
        $vinculo = JogoPlataforma::factory()->create();

        $this->deleteJson("/api/jogos_plataformas/{$vinculo->id}")->assertNoContent();

        $this->assertDatabaseMissing('jogos_plataformas', ['id' => $vinculo->id]);
    }

    public function test_destroy_de_id_inexistente_retorna_404(): void
    {
        $this->deleteJson('/api/jogos_plataformas/999')->assertNotFound();
    }
}
