<?php

namespace Tests\Feature;

use App\Models\Jogo;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class JogoApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_index_lista_os_jogos(): void
    {
        Jogo::factory()->count(3)->create();

        $this->getJson('/api/jogos')
            ->assertOk()
            ->assertJsonCount(3);
    }

    public function test_store_cria_jogo_e_retorna_201(): void
    {
        $this->postJson('/api/jogos', [
            'nome' => 'Cyberbug 2077',
            'descricao' => 'RPG de mundo aberto',
            'genero' => 'RPG',
            'classificacao' => '18',
            'desenvolvedora' => 'LaaC Studio',
            'data_lancamento' => '2020-12-10',
            'capa_url' => 'https://exemplo.test/capa.png',
        ])
            ->assertCreated()
            ->assertJsonPath('nome', 'Cyberbug 2077')
            ->assertJsonPath('data_lancamento', '2020-12-10');

        $this->assertDatabaseHas('jogos', ['nome' => 'Cyberbug 2077']);
    }

    public function test_store_aceita_apenas_o_nome(): void
    {
        $this->postJson('/api/jogos', ['nome' => 'Jogo Minimo'])
            ->assertCreated()
            ->assertJsonPath('descricao', null);
    }

    public function test_store_sem_nome_retorna_422(): void
    {
        $this->postJson('/api/jogos', [])
            ->assertStatus(422)
            ->assertJsonValidationErrors('nome');
    }

    public function test_store_com_data_invalida_retorna_422(): void
    {
        $this->postJson('/api/jogos', [
            'nome' => 'Jogo',
            'data_lancamento' => 'ontem',
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('data_lancamento');
    }

    public function test_store_rejeita_data_em_formato_ambiguo(): void
    {
        $this->postJson('/api/jogos', [
            'nome' => 'Jogo',
            'data_lancamento' => '10/12/2020',
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('data_lancamento');
    }

    public function test_show_retorna_o_jogo(): void
    {
        $jogo = Jogo::factory()->create();

        $this->getJson("/api/jogos/{$jogo->id}")
            ->assertOk()
            ->assertJsonPath('id', $jogo->id);
    }

    public function test_show_de_id_inexistente_retorna_404(): void
    {
        $this->getJson('/api/jogos/999')->assertNotFound();
    }

    public function test_update_altera_o_jogo(): void
    {
        $jogo = Jogo::factory()->create(['genero' => 'Ação']);

        $this->putJson("/api/jogos/{$jogo->id}", ['genero' => 'Estratégia'])
            ->assertOk()
            ->assertJsonPath('genero', 'Estratégia');

        $this->assertDatabaseHas('jogos', [
            'id' => $jogo->id,
            'genero' => 'Estratégia',
        ]);
    }

    public function test_update_de_id_inexistente_retorna_404(): void
    {
        $this->putJson('/api/jogos/999', ['nome' => 'x'])->assertNotFound();
    }

    public function test_destroy_remove_o_jogo_e_retorna_204(): void
    {
        $jogo = Jogo::factory()->create();

        $this->deleteJson("/api/jogos/{$jogo->id}")->assertNoContent();

        $this->assertDatabaseMissing('jogos', ['id' => $jogo->id]);
    }

    public function test_destroy_de_id_inexistente_retorna_404(): void
    {
        $this->deleteJson('/api/jogos/999')->assertNotFound();
    }
}
