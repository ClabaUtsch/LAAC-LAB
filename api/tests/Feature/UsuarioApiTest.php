<?php

namespace Tests\Feature;

use App\Models\Usuario;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Tests\TestCase;

class UsuarioApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_index_lista_os_usuarios(): void
    {
        Usuario::factory()->count(3)->create();

        $this->getJson('/api/usuarios')
            ->assertOk()
            ->assertJsonCount(3);
    }

    public function test_store_cria_usuario_e_retorna_201(): void
    {
        $this->postJson('/api/usuarios', [
            'nome_usuario' => 'jogador1',
            'email' => 'jogador1@laac.test',
            'senha' => 'senha-secreta',
            'bio' => 'so mais um caçador de bugs',
        ])
            ->assertCreated()
            ->assertJsonPath('nome_usuario', 'jogador1')
            ->assertJsonPath('nivel', 1);

        $this->assertDatabaseHas('usuarios', ['email' => 'jogador1@laac.test']);
    }

    public function test_store_grava_a_senha_com_hash(): void
    {
        $this->postJson('/api/usuarios', [
            'nome_usuario' => 'jogador2',
            'email' => 'jogador2@laac.test',
            'senha' => 'senha-secreta',
        ])->assertCreated();

        $usuario = Usuario::where('email', 'jogador2@laac.test')->firstOrFail();

        $this->assertNotSame('senha-secreta', $usuario->senha_hash);
        $this->assertTrue(Hash::check('senha-secreta', $usuario->senha_hash));
    }

    public function test_senha_hash_nunca_aparece_na_resposta(): void
    {
        $usuario = Usuario::factory()->create();

        $this->getJson("/api/usuarios/{$usuario->id}")
            ->assertOk()
            ->assertJsonMissingPath('senha_hash');
    }

    public function test_store_sem_dados_retorna_422(): void
    {
        $this->postJson('/api/usuarios', [])
            ->assertStatus(422)
            ->assertJsonValidationErrors(['nome_usuario', 'email', 'senha']);
    }

    public function test_store_rejeita_email_duplicado(): void
    {
        Usuario::factory()->create(['email' => 'repetido@laac.test']);

        $this->postJson('/api/usuarios', [
            'nome_usuario' => 'outro',
            'email' => 'repetido@laac.test',
            'senha' => 'senha-secreta',
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('email');
    }

    public function test_show_retorna_o_usuario(): void
    {
        $usuario = Usuario::factory()->create();

        $this->getJson("/api/usuarios/{$usuario->id}")
            ->assertOk()
            ->assertJsonPath('id', $usuario->id);
    }

    public function test_show_de_id_inexistente_retorna_404(): void
    {
        $this->getJson('/api/usuarios/999')->assertNotFound();
    }

    public function test_update_altera_o_usuario(): void
    {
        $usuario = Usuario::factory()->create(['bio' => 'bio antiga']);

        $this->putJson("/api/usuarios/{$usuario->id}", ['bio' => 'bio nova'])
            ->assertOk()
            ->assertJsonPath('bio', 'bio nova');

        $this->assertDatabaseHas('usuarios', [
            'id' => $usuario->id,
            'bio' => 'bio nova',
        ]);
    }

    public function test_update_aceita_o_proprio_email_sem_conflito(): void
    {
        $usuario = Usuario::factory()->create(['email' => 'meu@laac.test']);

        $this->putJson("/api/usuarios/{$usuario->id}", [
            'email' => 'meu@laac.test',
            'nivel' => 7,
        ])
            ->assertOk()
            ->assertJsonPath('nivel', 7);
    }

    public function test_update_de_id_inexistente_retorna_404(): void
    {
        $this->putJson('/api/usuarios/999', ['bio' => 'x'])->assertNotFound();
    }

    public function test_update_troca_a_senha(): void
    {
        $usuario = Usuario::factory()->create();

        $this->putJson("/api/usuarios/{$usuario->id}", ['senha' => 'outra-senha-8'])
            ->assertOk();

        $this->assertTrue(Hash::check('outra-senha-8', $usuario->fresh()->senha_hash));
    }

    public function test_update_rejeita_email_de_outro_usuario(): void
    {
        $outro = Usuario::factory()->create(['email' => 'ocupado@laac.test']);
        $usuario = Usuario::factory()->create();

        $this->putJson("/api/usuarios/{$usuario->id}", ['email' => 'ocupado@laac.test'])
            ->assertStatus(422)
            ->assertJsonValidationErrors('email');
    }

    public function test_destroy_remove_o_usuario_e_retorna_204(): void
    {
        $usuario = Usuario::factory()->create();

        $this->deleteJson("/api/usuarios/{$usuario->id}")->assertNoContent();

        $this->assertDatabaseMissing('usuarios', ['id' => $usuario->id]);
    }

    public function test_destroy_de_id_inexistente_retorna_404(): void
    {
        $this->deleteJson('/api/usuarios/999')->assertNotFound();
    }
}
