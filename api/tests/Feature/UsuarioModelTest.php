<?php

namespace Tests\Feature;

use App\Models\Usuario;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Schema;
use Tests\TestCase;

class UsuarioModelTest extends TestCase
{
    use RefreshDatabase;

    public function test_a_tabela_usuarios_existe_com_as_colunas_do_ddl(): void
    {
        $this->assertTrue(Schema::hasTable('usuarios'));
        $this->assertTrue(Schema::hasColumns('usuarios', [
            'id', 'nome_usuario', 'email', 'senha_hash', 'idade',
            'avatar_url', 'bio', 'nivel', 'criado_em', 'atualizado_em',
        ]));
    }

    public function test_a_tabela_users_do_esqueleto_nao_existe_mais(): void
    {
        $this->assertFalse(Schema::hasTable('users'));
    }

    public function test_a_factory_produz_um_usuario_persistivel(): void
    {
        $usuario = Usuario::factory()->create();

        $this->assertDatabaseHas('usuarios', ['id' => $usuario->id]);
        $this->assertSame(1, $usuario->nivel);
    }

    public function test_timestamps_usam_os_nomes_em_portugues(): void
    {
        $usuario = Usuario::factory()->create();

        $this->assertNotNull($usuario->criado_em);
        $this->assertNotNull($usuario->atualizado_em);
    }

    public function test_a_senha_e_gravada_com_hash(): void
    {
        $usuario = Usuario::factory()->create(['senha_hash' => 'senha-secreta']);

        $this->assertNotSame('senha-secreta', $usuario->senha_hash);
        $this->assertTrue(Hash::check('senha-secreta', $usuario->senha_hash));
    }

    public function test_senha_hash_fica_fora_da_serializacao(): void
    {
        $usuario = Usuario::factory()->create();

        $this->assertArrayNotHasKey('senha_hash', $usuario->toArray());
    }
}
