<?php

namespace Tests\Feature;

use App\Models\BibliotecaUsuario;
use App\Models\Jogo;
use App\Models\Usuario;
use Illuminate\Database\QueryException;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class BibliotecaUsuarioApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_index_lista_os_itens(): void
    {
        BibliotecaUsuario::factory()->count(3)->create();

        $this->getJson('/api/biblioteca_usuario')
            ->assertOk()
            ->assertJsonCount(3);
    }

    public function test_store_adiciona_jogo_e_retorna_201(): void
    {
        $usuario = Usuario::factory()->create();
        $jogo = Jogo::factory()->create();

        $this->postJson('/api/biblioteca_usuario', [
            'usuario_id' => $usuario->id,
            'jogo_id' => $jogo->id,
        ])
            ->assertCreated()
            ->assertJsonPath('usuario_id', $usuario->id)
            ->assertJsonPath('favorito', false);

        $this->assertDatabaseHas('biblioteca_usuario', [
            'usuario_id' => $usuario->id,
            'jogo_id' => $jogo->id,
        ]);
    }

    public function test_store_aceita_favorito_verdadeiro(): void
    {
        $usuario = Usuario::factory()->create();
        $jogo = Jogo::factory()->create();

        $this->postJson('/api/biblioteca_usuario', [
            'usuario_id' => $usuario->id,
            'jogo_id' => $jogo->id,
            'favorito' => true,
        ])
            ->assertCreated()
            ->assertJsonPath('favorito', true);
    }

    public function test_store_sem_dados_retorna_422(): void
    {
        $this->postJson('/api/biblioteca_usuario', [])
            ->assertStatus(422)
            ->assertJsonValidationErrors(['usuario_id', 'jogo_id']);
    }

    public function test_store_rejeita_jogo_repetido_na_biblioteca_com_422(): void
    {
        $item = BibliotecaUsuario::factory()->create();

        $this->postJson('/api/biblioteca_usuario', [
            'usuario_id' => $item->usuario_id,
            'jogo_id' => $item->jogo_id,
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('jogo_id');
    }

    public function test_o_banco_rejeita_jogo_repetido_como_rede_de_seguranca(): void
    {
        $item = BibliotecaUsuario::factory()->create();

        $this->expectException(QueryException::class);

        BibliotecaUsuario::create([
            'usuario_id' => $item->usuario_id,
            'jogo_id' => $item->jogo_id,
        ]);
    }

    public function test_apagar_usuario_esvazia_sua_biblioteca_em_cascata(): void
    {
        $item = BibliotecaUsuario::factory()->create();

        Usuario::findOrFail($item->usuario_id)->delete();

        $this->assertDatabaseMissing('biblioteca_usuario', ['id' => $item->id]);
    }

    public function test_apagar_jogo_remove_o_item_das_bibliotecas_em_cascata(): void
    {
        $item = BibliotecaUsuario::factory()->create();

        Jogo::findOrFail($item->jogo_id)->delete();

        $this->assertDatabaseMissing('biblioteca_usuario', ['id' => $item->id]);
    }

    public function test_o_usuario_expoe_seus_jogos_com_o_pivo(): void
    {
        $item = BibliotecaUsuario::factory()->create(['favorito' => true]);

        $usuario = Usuario::with('jogos')->findOrFail($item->usuario_id);

        $this->assertCount(1, $usuario->jogos);
        $this->assertSame($item->jogo_id, $usuario->jogos->first()->id);
        $this->assertTrue((bool) $usuario->jogos->first()->pivot->favorito);
    }

    public function test_show_retorna_o_item(): void
    {
        $item = BibliotecaUsuario::factory()->create();

        $this->getJson("/api/biblioteca_usuario/{$item->id}")
            ->assertOk()
            ->assertJsonPath('id', $item->id);
    }

    public function test_show_de_id_inexistente_retorna_404(): void
    {
        $this->getJson('/api/biblioteca_usuario/999')->assertNotFound();
    }

    public function test_update_marca_como_favorito(): void
    {
        $item = BibliotecaUsuario::factory()->create(['favorito' => false]);

        $this->putJson("/api/biblioteca_usuario/{$item->id}", ['favorito' => true])
            ->assertOk()
            ->assertJsonPath('favorito', true);

        $this->assertDatabaseHas('biblioteca_usuario', [
            'id' => $item->id,
            'favorito' => true,
        ]);
    }

    public function test_update_de_usuario_para_par_ja_existente_retorna_422(): void
    {
        $item = BibliotecaUsuario::factory()->create();
        $outroUsuario = Usuario::factory()->create();

        // Ocupa o par (outroUsuario, jogo do primeiro item).
        BibliotecaUsuario::create([
            'usuario_id' => $outroUsuario->id,
            'jogo_id' => $item->jogo_id,
        ]);

        // O update manda so usuario_id: a checagem de unicidade tem que rodar
        // mesmo assim.
        $this->putJson("/api/biblioteca_usuario/{$item->id}", [
            'usuario_id' => $outroUsuario->id,
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('jogo_id');
    }

    public function test_update_de_id_inexistente_retorna_404(): void
    {
        $this->putJson('/api/biblioteca_usuario/999', ['favorito' => true])
            ->assertNotFound();
    }

    public function test_destroy_remove_o_item_e_retorna_204(): void
    {
        $item = BibliotecaUsuario::factory()->create();

        $this->deleteJson("/api/biblioteca_usuario/{$item->id}")->assertNoContent();

        $this->assertDatabaseMissing('biblioteca_usuario', ['id' => $item->id]);
    }

    public function test_destroy_de_id_inexistente_retorna_404(): void
    {
        $this->deleteJson('/api/biblioteca_usuario/999')->assertNotFound();
    }
}
