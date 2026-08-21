<?php

namespace Tests\Feature;

use App\Models\Plataforma;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class PlataformaApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_index_lista_as_plataformas(): void
    {
        Plataforma::factory()->count(3)->create();

        $this->getJson('/api/plataformas')
            ->assertOk()
            ->assertJsonCount(3);
    }

    public function test_store_cria_plataforma_e_retorna_201(): void
    {
        $this->postJson('/api/plataformas', ['nome' => 'PlayStation 5'])
            ->assertCreated()
            ->assertJsonPath('nome', 'PlayStation 5');

        $this->assertDatabaseHas('plataformas', ['nome' => 'PlayStation 5']);
    }

    public function test_store_sem_nome_retorna_422(): void
    {
        $this->postJson('/api/plataformas', [])
            ->assertStatus(422)
            ->assertJsonValidationErrors('nome');
    }

    public function test_store_com_nome_longo_demais_retorna_422(): void
    {
        $this->postJson('/api/plataformas', ['nome' => str_repeat('a', 51)])
            ->assertStatus(422)
            ->assertJsonValidationErrors('nome');
    }

    public function test_show_retorna_a_plataforma(): void
    {
        $plataforma = Plataforma::factory()->create();

        $this->getJson("/api/plataformas/{$plataforma->id}")
            ->assertOk()
            ->assertJsonPath('id', $plataforma->id);
    }

    public function test_show_de_id_inexistente_retorna_404(): void
    {
        $this->getJson('/api/plataformas/999')->assertNotFound();
    }

    public function test_update_altera_a_plataforma(): void
    {
        $plataforma = Plataforma::factory()->create(['nome' => 'PS4']);

        $this->putJson("/api/plataformas/{$plataforma->id}", ['nome' => 'PS5'])
            ->assertOk()
            ->assertJsonPath('nome', 'PS5');

        $this->assertDatabaseHas('plataformas', [
            'id' => $plataforma->id,
            'nome' => 'PS5',
        ]);
    }

    public function test_update_de_id_inexistente_retorna_404(): void
    {
        $this->putJson('/api/plataformas/999', ['nome' => 'x'])->assertNotFound();
    }

    public function test_destroy_remove_a_plataforma_e_retorna_204(): void
    {
        $plataforma = Plataforma::factory()->create();

        $this->deleteJson("/api/plataformas/{$plataforma->id}")->assertNoContent();

        $this->assertDatabaseMissing('plataformas', ['id' => $plataforma->id]);
    }

    public function test_destroy_de_id_inexistente_retorna_404(): void
    {
        $this->deleteJson('/api/plataformas/999')->assertNotFound();
    }

    public function test_a_factory_gera_mais_plataformas_que_o_tamanho_da_lista(): void
    {
        Plataforma::factory()->count(20)->create();

        $this->assertDatabaseCount('plataformas', 20);
    }
}
