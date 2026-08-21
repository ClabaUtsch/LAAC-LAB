# LaaC Lab — Fases 0 e 1: Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preparar a base do projeto (banco alternável, remoção do scaffolding de exemplo) e entregar o CRUD REST completo das três entidades do núcleo: `usuarios`, `jogos` e `plataformas`.

**Architecture:** API REST sem estado, um `apiResource` por entidade em `routes/api.php`. Cada entidade é uma tripla independente migration + Model + Controller, sem camadas intermediárias: validação inline no controller, serialização pelo próprio Model (`$hidden`/`$casts`), 404 pelo route-model binding. Migrations usam só o Schema Builder, então o mesmo código gera SQLite e MySQL.

**Tech Stack:** PHP 8.3, Laravel 13.17, PHPUnit 12.5, SQLite (dev e testes) / MySQL (opcional via `.env`).

**Spec:** [docs/superpowers/specs/2026-08-19-laac-lab-api-design.md](../specs/2026-08-19-laac-lab-api-design.md)

## Global Constraints

- Tabelas no plural e em português, exatamente como no DDL de origem: `usuarios`, `jogos`, `plataformas`.
- Colunas em português, exatamente como no DDL: `nome_usuario`, `senha_hash`, `data_lancamento`.
- Todo Model declara `protected $table` explicitamente — o pluralizador do Eloquent é inglês e não é confiável nesses nomes.
- Todo Model declara `const CREATED_AT = 'criado_em';` e `const UPDATED_AT = 'atualizado_em';`.
- Migrations usam **exclusivamente** o Schema Builder. Nenhum `DB::statement`, nenhum SQL cru, nenhum tipo específico de vendor.
- Toda FK usa `foreignId(...)->constrained('tabela')->cascadeOnDelete()`.
- URI de cada recurso = nome exato da tabela em `snake_case`.
- Status HTTP: `index`/`show`/`update` → 200, `store` → 201, `destroy` → 204, ID inexistente → 404, validação falha → 422.
- Todo controller estende `App\Http\Controllers\Controller` e tipa o retorno de todos os métodos como `JsonResponse`.
- `senha_hash` nunca aparece em resposta JSON.
- Nenhuma tarefa fecha com `php artisan test` vermelho.

---

### Task 1: Banco alternável entre SQLite e MySQL

Hoje o `.env` define `DB_CONNECTION=sqlite` e deixa as variáveis de MySQL comentadas. Queremos que trocar de banco seja editar uma linha.

O obstáculo: a conexão `sqlite` no `config/database.php` lê `env('DB_DATABASE')`. Se descomentarmos `DB_DATABASE=LaaC_lab` para o MySQL, o SQLite passa a tentar abrir um **arquivo chamado `LaaC_lab`**. A correção é dar ao SQLite a sua própria variável, `DB_SQLITE_DATABASE`.

**Files:**
- Modify: `config/database.php:38` (chave `database` da conexão `sqlite`)
- Modify: `.env` (bloco de banco)
- Modify: `.env.example` (bloco de banco)
- Modify: `phpunit.xml:25-26` (variáveis de banco do ambiente de teste)
- Test: `tests/Feature/ConexaoBancoTest.php`

**Interfaces:**
- Consumes: nada.
- Produces: a variável de ambiente `DB_SQLITE_DATABASE` (caminho do arquivo SQLite, default `database_path('database.sqlite')`) e `DB_DATABASE` passa a servir **só** ao MySQL. Todas as tasks seguintes rodam os testes contra SQLite in-memory.

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/Feature/ConexaoBancoTest.php`:

```php
<?php

namespace Tests\Feature;

use Tests\TestCase;

class ConexaoBancoTest extends TestCase
{
    public function test_conexao_mysql_esta_disponivel(): void
    {
        $this->assertSame('mysql', config('database.connections.mysql.driver'));
    }

    public function test_sqlite_nao_herda_o_nome_do_banco_do_mysql(): void
    {
        $this->assertNotSame(
            config('database.connections.mysql.database'),
            config('database.connections.sqlite.database'),
            'A conexao sqlite nao pode ler DB_DATABASE, senao tenta abrir um arquivo com o nome do banco MySQL.'
        );
    }

    public function test_testes_rodam_em_sqlite_em_memoria(): void
    {
        $this->assertSame('sqlite', config('database.default'));
        $this->assertSame(':memory:', config('database.connections.sqlite.database'));
    }

    /**
     * Sem isto o ON DELETE CASCADE das FKs e silenciosamente ignorado no
     * SQLite. Exigido pela secao 3.1 da spec.
     */
    public function test_sqlite_aplica_as_constraints_de_chave_estrangeira(): void
    {
        $this->assertTrue(config('database.connections.sqlite.foreign_key_constraints'));
    }
}
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `php artisan test --filter=ConexaoBancoTest`

Expected: FAIL. `test_sqlite_nao_herda_o_nome_do_banco_do_mysql` falha porque hoje as duas conexões leem a mesma `DB_DATABASE` (ambas resolvem para `:memory:` no ambiente de teste).

- [ ] **Step 3: Dar ao SQLite a sua própria variável**

Em `config/database.php`, na conexão `sqlite`, trocar a linha:

```php
            'database' => env('DB_DATABASE', database_path('database.sqlite')),
```

por:

```php
            // DB_DATABASE e exclusiva do MySQL. O SQLite usa a sua propria
            // variavel para que trocar DB_CONNECTION nao quebre o outro banco.
            'database' => env('DB_SQLITE_DATABASE', database_path('database.sqlite')),
```

- [ ] **Step 4: Apontar os testes para a nova variável**

Em `phpunit.xml`, trocar as duas linhas:

```xml
        <env name="DB_CONNECTION" value="sqlite"/>
        <env name="DB_DATABASE" value=":memory:"/>
```

por:

```xml
        <env name="DB_CONNECTION" value="sqlite"/>
        <env name="DB_SQLITE_DATABASE" value=":memory:"/>
```

- [ ] **Step 5: Escrever o bloco de banco no `.env`**

Substituir o bloco atual do `.env`:

```
DB_CONNECTION=sqlite
# DB_HOST=127.0.0.1
# DB_PORT=3306
# DB_DATABASE=laravel
# DB_USERNAME=root
```

por:

```
# Troque para "mysql" e rode: php artisan migrate:fresh
DB_CONNECTION=sqlite

# Usado apenas quando DB_CONNECTION=sqlite.
# Comentado = usa database/database.sqlite (o default do config).
# DB_SQLITE_DATABASE=

# Usados apenas quando DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=LaaC_lab
DB_USERNAME=root
DB_PASSWORD=
```

`DB_SQLITE_DATABASE` fica comentada de propósito: assim o SQLite resolve o
caminho pelo `database_path()` do próprio Laravel, sem depender de caminho
relativo no `.env`.

- [ ] **Step 6: Replicar o mesmo bloco no `.env.example`**

Aplicar exatamente a substituição do Step 5 em `.env.example`. Este arquivo é versionado, então é ele que documenta o toggle para quem clonar o projeto.

- [ ] **Step 7: Rodar os testes e confirmar que passam**

Run: `php artisan test`

Expected: PASS. `ConexaoBancoTest` verde (4 testes) e os 2 `ExampleTest` continuam verdes.

- [ ] **Step 8: Confirmar que o SQLite de desenvolvimento ainda abre**

Run: `php artisan migrate:status`

Expected: as 4 migrations listadas como `Ran`. Se aparecer erro de "database file does not exist", `DB_SQLITE_DATABASE` está com caminho errado.

- [ ] **Step 9: Commit**

```bash
git add config/database.php phpunit.xml .env.example tests/Feature/ConexaoBancoTest.php
git commit -m "feat: permite alternar entre SQLite e MySQL pelo .env"
```

Nota: `.env` é gitignored e não entra no commit — por isso o Step 6 existe.

---

### Task 2: Remover o domínio Product

`Product` era scaffolding de exemplo. Sai inteiro, em commit próprio, para ser trivialmente reversível.

**Files:**
- Delete: `app/Models/Product.php`
- Delete: `app/Http/Controllers/ProductController.php`
- Delete: `database/migrations/2026_06_24_220025_create_products_table.php`
- Modify: `routes/api.php`

**Interfaces:**
- Consumes: nada.
- Produces: `routes/api.php` fica vazio de rotas, pronto para receber `apiResource('usuarios', ...)` na Task 3.

- [ ] **Step 1: Apagar os três arquivos**

```bash
rm app/Models/Product.php
rm app/Http/Controllers/ProductController.php
rm database/migrations/2026_06_24_220025_create_products_table.php
```

- [ ] **Step 2: Esvaziar `routes/api.php`**

Substituir todo o conteúdo de `routes/api.php` por:

```php
<?php

use Illuminate\Support\Facades\Route;

// As rotas deste arquivo ja recebem o prefixo /api automaticamente.
```

- [ ] **Step 3: Recriar o banco sem a tabela `products`**

Run: `php artisan migrate:fresh`

Expected: 3 migrations rodam (`users`, `cache`, `jobs`). Nenhuma menção a `products`.

- [ ] **Step 4: Confirmar que a rota sumiu**

Run: `php artisan route:list`

Expected: nenhuma linha contendo `products`. Restam `GET /`, `storage/{path}` e `up`.

- [ ] **Step 5: Rodar os testes**

Run: `php artisan test`

Expected: PASS, 6 testes (4 de `ConexaoBancoTest`, 2 de `ExampleTest`).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: remove o CRUD de exemplo Product"
```

---

### Task 3: Entidade `usuarios` completa (substitui `users`)

A tabela `users` do esqueleto e a `usuarios` do DDL são a mesma entidade. Esta task troca uma pela outra e entrega o recurso inteiro — migration, model, factory, controller, rotas e testes — **num único commit**, para o projeto nunca ficar num estado onde `config/auth.php` aponta para uma classe inexistente e para o histórico ter uma entidade de domínio completa por commit.

O `Usuario` estende `Authenticatable` (deixando Sanctum plug-and-play numa fase futura), com dois ajustes: a coluna de senha se chama `senha_hash`, não `password`, e a tabela não tem `remember_token`.

**Files:**
- Delete: `app/Models/User.php`
- Delete: `database/factories/UserFactory.php`
- Rename: `database/migrations/0001_01_01_000000_create_users_table.php` → `database/migrations/0001_01_01_000000_create_sessions_table.php`
- Create: `database/migrations/2026_08_19_000001_create_usuarios_table.php`
- Create: `app/Models/Usuario.php`
- Create: `database/factories/UsuarioFactory.php`
- Create: `app/Http/Controllers/UsuarioController.php`
- Modify: `config/auth.php:3` e `config/auth.php:67`
- Modify: `database/seeders/DatabaseSeeder.php`
- Modify: `routes/api.php`
- Test: `tests/Feature/UsuarioModelTest.php`
- Test: `tests/Feature/UsuarioApiTest.php`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `App\Models\Usuario` — tabela `usuarios`; `$fillable` = `nome_usuario`, `email`, `senha_hash`, `idade`, `avatar_url`, `bio`, `nivel`; `$hidden` = `senha_hash`; `$attributes = ['nivel' => 1]`; cast `senha_hash => 'hashed'` (atribuir texto puro grava hash); `getAuthPassword(): string`.
  - `Database\Factories\UsuarioFactory` — `Usuario::factory()` produz usuário válido com senha `'senha-secreta'`.
  - As rotas `usuarios.index|store|show|update|destroy` sob `/api/usuarios`. O endpoint aceita o campo de entrada **`senha`** (texto puro), que o controller grava na coluna `senha_hash`.
  - As Fases 2+ referenciam `usuarios.id` nas FKs.

**Commit:** um só, no Step 20. Nenhum step intermediário commita.

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/Feature/UsuarioModelTest.php`:

```php
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
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `php artisan test --filter=UsuarioModelTest`

Expected: FAIL com `Class "App\Models\Usuario" not found`.

- [ ] **Step 3: Remover a tabela `users` da migration do esqueleto**

Renomear o arquivo e remover o bloco `users`:

```bash
git mv database/migrations/0001_01_01_000000_create_users_table.php \
       database/migrations/0001_01_01_000000_create_sessions_table.php
```

Substituir todo o conteúdo do arquivo renomeado por:

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * A tabela de pessoas deste projeto e "usuarios", nao a "users" do
     * esqueleto Laravel. Aqui ficam so as tabelas de infraestrutura.
     */
    public function up(): void
    {
        Schema::create('password_reset_tokens', function (Blueprint $table) {
            $table->string('email')->primary();
            $table->string('token');
            $table->timestamp('created_at')->nullable();
        });

        Schema::create('sessions', function (Blueprint $table) {
            $table->string('id')->primary();
            $table->foreignId('user_id')->nullable()->index();
            $table->string('ip_address', 45)->nullable();
            $table->text('user_agent')->nullable();
            $table->longText('payload');
            $table->integer('last_activity')->index();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('password_reset_tokens');
        Schema::dropIfExists('sessions');
    }
};
```

`sessions.user_id` é apenas um índice, não uma FK, então continua válido sem a tabela `users`.

- [ ] **Step 4: Criar a migration de `usuarios`**

Criar `database/migrations/2026_08_19_000001_create_usuarios_table.php`:

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('usuarios', function (Blueprint $table) {
            $table->id();
            $table->string('nome_usuario', 50)->unique();
            $table->string('email', 100)->unique();
            $table->string('senha_hash');
            $table->integer('idade')->nullable();
            $table->text('avatar_url')->nullable();
            $table->text('bio')->nullable();
            $table->integer('nivel')->default(1);
            $table->timestamp('criado_em')->nullable();
            $table->timestamp('atualizado_em')->nullable();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('usuarios');
    }
};
```

- [ ] **Step 5: Criar o Model `Usuario`**

Criar `app/Models/Usuario.php`:

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

class Usuario extends Authenticatable
{
    /** @use HasFactory<\Database\Factories\UsuarioFactory> */
    use HasFactory, Notifiable;

    protected $table = 'usuarios';

    const CREATED_AT = 'criado_em';
    const UPDATED_AT = 'atualizado_em';

    /**
     * A tabela nao tem coluna remember_token; string vazia desliga o recurso.
     */
    protected $rememberTokenName = '';

    protected $fillable = [
        'nome_usuario',
        'email',
        'senha_hash',
        'idade',
        'avatar_url',
        'bio',
        'nivel',
    ];

    protected $hidden = [
        'senha_hash',
    ];

    /**
     * Espelha o default da migration. Sem isto, um POST que nao envia "nivel"
     * devolveria um JSON sem a chave: o default e do banco e so apareceria
     * apos um refresh().
     */
    protected $attributes = [
        'nivel' => 1,
    ];

    protected function casts(): array
    {
        return [
            'idade' => 'integer',
            'nivel' => 'integer',
            'senha_hash' => 'hashed',
        ];
    }

    /**
     * A coluna de senha se chama senha_hash, nao password.
     */
    public function getAuthPassword(): string
    {
        return $this->senha_hash;
    }
}
```

O cast `hashed` faz o hash na escrita e ignora valores que já são hash, então nem o controller nem a factory precisam chamar `Hash::make()`.

- [ ] **Step 6: Criar a `UsuarioFactory`**

Criar `database/factories/UsuarioFactory.php`:

```php
<?php

namespace Database\Factories;

use App\Models\Usuario;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Usuario>
 */
class UsuarioFactory extends Factory
{
    protected $model = Usuario::class;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'nome_usuario' => fake()->unique()->userName(),
            'email' => fake()->unique()->safeEmail(),
            'senha_hash' => 'senha-secreta',
            'idade' => fake()->numberBetween(13, 80),
            'avatar_url' => fake()->imageUrl(),
            'bio' => fake()->sentence(),
            'nivel' => 1,
        ];
    }
}
```

- [ ] **Step 7: Apagar `User` e `UserFactory`**

```bash
rm app/Models/User.php
rm database/factories/UserFactory.php
```

- [ ] **Step 8: Apontar `config/auth.php` para `Usuario`**

Na linha 3, trocar `use App\Models\User;` por `use App\Models\Usuario;`.

Na linha 67, trocar `'model' => env('AUTH_MODEL', User::class),` por `'model' => env('AUTH_MODEL', Usuario::class),`.

- [ ] **Step 9: Atualizar o `DatabaseSeeder`**

Substituir todo o conteúdo de `database/seeders/DatabaseSeeder.php` por:

```php
<?php

namespace Database\Seeders;

use App\Models\Usuario;
use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    use WithoutModelEvents;

    public function run(): void
    {
        Usuario::factory()->create([
            'nome_usuario' => 'teste',
            'email' => 'teste@laac.test',
        ]);
    }
}
```

- [ ] **Step 10: Rodar os testes e confirmar que passam**

Run: `php artisan test --filter=UsuarioModelTest`

Expected: PASS, 6 testes.

- [ ] **Step 11: Recriar o banco de desenvolvimento e semear**

Run: `php artisan migrate:fresh --seed`

Expected: 4 migrations rodam (`sessions`, `cache`, `jobs`, `usuarios`), seeder cria o usuário `teste`. Sem erro sobre a classe `User`.

- [ ] **Step 12: Rodar a suíte inteira**

Run: `php artisan test`

Expected: PASS, 12 testes.

Ainda **sem commit**: a entidade `usuarios` só entra no histórico quando
estiver completa. Os steps seguintes fecham a parte de API — controller, rota
e testes de endpoint — e o Step 20 commita a entidade inteira de uma vez.

- [ ] **Step 13: Escrever o teste de API que falha**

Criar `tests/Feature/UsuarioApiTest.php`:

```php
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
```

- [ ] **Step 14: Rodar o teste e confirmar que falha**

Run: `php artisan test --filter=UsuarioApiTest`

Expected: FAIL. As rotas não existem, então tudo retorna 404 em vez dos status esperados.

- [ ] **Step 15: Gerar o controller**

Run: `php artisan make:controller UsuarioController --api`

- [ ] **Step 16: Implementar o controller**

Substituir todo o conteúdo de `app/Http/Controllers/UsuarioController.php` por:

```php
<?php

namespace App\Http\Controllers;

use App\Models\Usuario;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class UsuarioController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(Usuario::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate([
            'nome_usuario' => 'required|string|max:50|unique:usuarios,nome_usuario',
            'email'        => 'required|email|max:100|unique:usuarios,email',
            'senha'        => 'required|string|min:8',
            'idade'        => 'nullable|integer|min:0|max:150',
            'avatar_url'   => 'nullable|string',
            'bio'          => 'nullable|string',
            'nivel'        => 'sometimes|integer|min:1',
        ]);

        $usuario = Usuario::create($this->trocaSenhaPelaColuna($dados));

        return response()->json($usuario, 201);
    }

    public function show(Usuario $usuario): JsonResponse
    {
        return response()->json($usuario);
    }

    public function update(Request $request, Usuario $usuario): JsonResponse
    {
        $dados = $request->validate([
            'nome_usuario' => [
                'sometimes', 'string', 'max:50',
                Rule::unique('usuarios', 'nome_usuario')->ignore($usuario),
            ],
            'email' => [
                'sometimes', 'email', 'max:100',
                Rule::unique('usuarios', 'email')->ignore($usuario),
            ],
            'senha'      => 'sometimes|string|min:8',
            'idade'      => 'nullable|integer|min:0|max:150',
            'avatar_url' => 'nullable|string',
            'bio'        => 'nullable|string',
            'nivel'      => 'sometimes|integer|min:1',
        ]);

        $usuario->update($this->trocaSenhaPelaColuna($dados));

        return response()->json($usuario);
    }

    public function destroy(Usuario $usuario): JsonResponse
    {
        $usuario->delete();

        return response()->json(null, 204);
    }

    /**
     * A API recebe "senha" em texto puro; a coluna e "senha_hash".
     * O hash em si e aplicado pelo cast "hashed" do model.
     *
     * @param  array<string, mixed>  $dados
     * @return array<string, mixed>
     */
    private function trocaSenhaPelaColuna(array $dados): array
    {
        if (isset($dados['senha'])) {
            $dados['senha_hash'] = $dados['senha'];
            unset($dados['senha']);
        }

        return $dados;
    }
}
```

- [ ] **Step 17: Registrar a rota**

Substituir todo o conteúdo de `routes/api.php` por:

```php
<?php

use App\Http\Controllers\UsuarioController;
use Illuminate\Support\Facades\Route;

// As rotas deste arquivo ja recebem o prefixo /api automaticamente.
Route::apiResource('usuarios', UsuarioController::class);
```

- [ ] **Step 18: Rodar o teste e confirmar que passa**

Run: `php artisan test --filter=UsuarioApiTest`

Expected: PASS, 13 testes.

- [ ] **Step 19: Conferir as rotas geradas**

Run: `php artisan route:list --path=api`

Expected: exatamente 5 linhas — `GET api/usuarios`, `POST api/usuarios`, `GET api/usuarios/{usuario}`, `PUT|PATCH api/usuarios/{usuario}`, `DELETE api/usuarios/{usuario}`.

- [ ] **Step 20: Commit**

```bash
git add -A
git commit -m "feat: entidade usuarios completa (migration, model, API REST)"
```

---

### Task 4: CRUD REST de `jogos`

Mesma estrutura da Task 3, sem o tratamento de senha. `data_lancamento` usa o cast `date:Y-m-d` para o JSON sair como `"2020-01-01"` em vez de um datetime ISO completo.

**Files:**
- Create: `database/migrations/2026_08_19_000002_create_jogos_table.php`
- Create: `app/Models/Jogo.php`
- Create: `database/factories/JogoFactory.php`
- Create: `app/Http/Controllers/JogoController.php`
- Modify: `routes/api.php`
- Test: `tests/Feature/JogoApiTest.php`

**Interfaces:**
- Consumes: nada da Task 3 (entidade independente).
- Produces: `App\Models\Jogo` (tabela `jogos`), `Database\Factories\JogoFactory`, e as rotas `jogos.*` sob `/api/jogos`. As Fases 2 e 3 referenciam `jogos.id` nas FKs.

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/Feature/JogoApiTest.php`:

```php
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
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `php artisan test --filter=JogoApiTest`

Expected: FAIL com `Class "App\Models\Jogo" not found`.

- [ ] **Step 3: Criar a migration**

Criar `database/migrations/2026_08_19_000002_create_jogos_table.php`:

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('jogos', function (Blueprint $table) {
            $table->id();
            $table->string('nome', 100);
            $table->text('descricao')->nullable();
            $table->string('genero', 50)->nullable();
            $table->string('classificacao', 10)->nullable();
            $table->string('desenvolvedora', 100)->nullable();
            $table->date('data_lancamento')->nullable();
            $table->text('capa_url')->nullable();
            $table->timestamp('criado_em')->nullable();
            $table->timestamp('atualizado_em')->nullable();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('jogos');
    }
};
```

- [ ] **Step 4: Criar o Model**

Criar `app/Models/Jogo.php`:

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Jogo extends Model
{
    /** @use HasFactory<\Database\Factories\JogoFactory> */
    use HasFactory;

    protected $table = 'jogos';

    const CREATED_AT = 'criado_em';
    const UPDATED_AT = 'atualizado_em';

    protected $fillable = [
        'nome',
        'descricao',
        'genero',
        'classificacao',
        'desenvolvedora',
        'data_lancamento',
        'capa_url',
    ];

    protected function casts(): array
    {
        return [
            // Y-m-d para o JSON sair como "2020-12-10", nao datetime ISO.
            'data_lancamento' => 'date:Y-m-d',
        ];
    }
}
```

- [ ] **Step 5: Criar a Factory**

Criar `database/factories/JogoFactory.php`:

```php
<?php

namespace Database\Factories;

use App\Models\Jogo;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Jogo>
 */
class JogoFactory extends Factory
{
    protected $model = Jogo::class;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'nome' => fake()->unique()->words(3, true),
            'descricao' => fake()->paragraph(),
            'genero' => fake()->randomElement(['RPG', 'FPS', 'Estratégia', 'Corrida', 'Puzzle']),
            'classificacao' => fake()->randomElement(['L', '10', '12', '14', '16', '18']),
            'desenvolvedora' => fake()->company(),
            'data_lancamento' => fake()->date(),
            'capa_url' => fake()->imageUrl(),
        ];
    }
}
```

- [ ] **Step 6: Gerar e implementar o controller**

Run: `php artisan make:controller JogoController --api`

Substituir todo o conteúdo de `app/Http/Controllers/JogoController.php` por:

```php
<?php

namespace App\Http\Controllers;

use App\Models\Jogo;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class JogoController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(Jogo::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate([
            'nome'            => 'required|string|max:100',
            'descricao'       => 'nullable|string',
            'genero'          => 'nullable|string|max:50',
            'classificacao'   => 'nullable|string|max:10',
            'desenvolvedora'  => 'nullable|string|max:100',
            'data_lancamento' => 'nullable|date',
            'capa_url'        => 'nullable|string',
        ]);

        $jogo = Jogo::create($dados);

        return response()->json($jogo, 201);
    }

    public function show(Jogo $jogo): JsonResponse
    {
        return response()->json($jogo);
    }

    public function update(Request $request, Jogo $jogo): JsonResponse
    {
        $dados = $request->validate([
            'nome'            => 'sometimes|string|max:100',
            'descricao'       => 'nullable|string',
            'genero'          => 'nullable|string|max:50',
            'classificacao'   => 'nullable|string|max:10',
            'desenvolvedora'  => 'nullable|string|max:100',
            'data_lancamento' => 'nullable|date',
            'capa_url'        => 'nullable|string',
        ]);

        $jogo->update($dados);

        return response()->json($jogo);
    }

    public function destroy(Jogo $jogo): JsonResponse
    {
        $jogo->delete();

        return response()->json(null, 204);
    }
}
```

- [ ] **Step 7: Registrar a rota**

Em `routes/api.php`, adicionar o import e a rota, deixando o arquivo assim:

```php
<?php

use App\Http\Controllers\JogoController;
use App\Http\Controllers\UsuarioController;
use Illuminate\Support\Facades\Route;

// As rotas deste arquivo ja recebem o prefixo /api automaticamente.
Route::apiResource('usuarios', UsuarioController::class);
Route::apiResource('jogos', JogoController::class);
```

- [ ] **Step 8: Rodar o teste e confirmar que passa**

Run: `php artisan test --filter=JogoApiTest`

Expected: PASS, 11 testes.

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat: CRUD REST de jogos"
```

---

### Task 5: CRUD REST de `plataformas` e fechamento da Fase 1

`plataformas` é a entidade mais simples do schema — só `id` e `nome`. No DDL ela não tem timestamp; ganha `criado_em`/`atualizado_em` por consistência com as demais.

Esta task fecha a Fase 1, então termina com a suíte completa e o banco recriado do zero.

**Files:**
- Create: `database/migrations/2026_08_19_000003_create_plataformas_table.php`
- Create: `app/Models/Plataforma.php`
- Create: `database/factories/PlataformaFactory.php`
- Create: `app/Http/Controllers/PlataformaController.php`
- Modify: `routes/api.php`
- Modify: `README.md`
- Test: `tests/Feature/PlataformaApiTest.php`

**Interfaces:**
- Consumes: nada.
- Produces: `App\Models\Plataforma` (tabela `plataformas`), `Database\Factories\PlataformaFactory`, e as rotas `plataformas.*` sob `/api/plataformas`. A Fase 2 liga `plataformas.id` a `jogos.id` pela tabela `jogos_plataformas`.

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/Feature/PlataformaApiTest.php`:

```php
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
}
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `php artisan test --filter=PlataformaApiTest`

Expected: FAIL com `Class "App\Models\Plataforma" not found`.

- [ ] **Step 3: Criar a migration**

Criar `database/migrations/2026_08_19_000003_create_plataformas_table.php`:

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('plataformas', function (Blueprint $table) {
            $table->id();
            $table->string('nome', 50);
            $table->timestamp('criado_em')->nullable();
            $table->timestamp('atualizado_em')->nullable();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('plataformas');
    }
};
```

- [ ] **Step 4: Criar o Model**

Criar `app/Models/Plataforma.php`:

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Plataforma extends Model
{
    /** @use HasFactory<\Database\Factories\PlataformaFactory> */
    use HasFactory;

    protected $table = 'plataformas';

    const CREATED_AT = 'criado_em';
    const UPDATED_AT = 'atualizado_em';

    protected $fillable = [
        'nome',
    ];
}
```

- [ ] **Step 5: Criar a Factory**

Criar `database/factories/PlataformaFactory.php`:

```php
<?php

namespace Database\Factories;

use App\Models\Plataforma;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Plataforma>
 */
class PlataformaFactory extends Factory
{
    protected $model = Plataforma::class;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'nome' => fake()->unique()->randomElement([
                'PlayStation 5', 'Xbox Series X', 'Nintendo Switch',
                'PC', 'Steam Deck', 'PlayStation 4', 'Xbox One',
            ]),
        ];
    }
}
```

- [ ] **Step 6: Gerar e implementar o controller**

Run: `php artisan make:controller PlataformaController --api`

Substituir todo o conteúdo de `app/Http/Controllers/PlataformaController.php` por:

```php
<?php

namespace App\Http\Controllers;

use App\Models\Plataforma;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class PlataformaController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(Plataforma::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate([
            'nome' => 'required|string|max:50',
        ]);

        $plataforma = Plataforma::create($dados);

        return response()->json($plataforma, 201);
    }

    public function show(Plataforma $plataforma): JsonResponse
    {
        return response()->json($plataforma);
    }

    public function update(Request $request, Plataforma $plataforma): JsonResponse
    {
        $dados = $request->validate([
            'nome' => 'sometimes|string|max:50',
        ]);

        $plataforma->update($dados);

        return response()->json($plataforma);
    }

    public function destroy(Plataforma $plataforma): JsonResponse
    {
        $plataforma->delete();

        return response()->json(null, 204);
    }
}
```

- [ ] **Step 7: Registrar a rota**

Substituir todo o conteúdo de `routes/api.php` por:

```php
<?php

use App\Http\Controllers\JogoController;
use App\Http\Controllers\PlataformaController;
use App\Http\Controllers\UsuarioController;
use Illuminate\Support\Facades\Route;

// As rotas deste arquivo ja recebem o prefixo /api automaticamente.
Route::apiResource('usuarios', UsuarioController::class);
Route::apiResource('jogos', JogoController::class);
Route::apiResource('plataformas', PlataformaController::class);
```

- [ ] **Step 8: Rodar o teste e confirmar que passa**

Run: `php artisan test --filter=PlataformaApiTest`

Expected: PASS, 10 testes.

- [ ] **Step 9: Rodar a suíte inteira**

Run: `php artisan test`

Expected: PASS, 46 testes (4 `ConexaoBanco` + 2 `Example` + 6 `UsuarioModel` + 13 `UsuarioApi` + 11 `JogoApi` + 10 `PlataformaApi`).

- [ ] **Step 10: Recriar o banco de desenvolvimento do zero**

Run: `php artisan migrate:fresh --seed`

Expected: 6 migrations rodam sem erro (`sessions`, `cache`, `jobs`, `usuarios`, `jogos`, `plataformas`).

- [ ] **Step 11: Conferir as 15 rotas da Fase 1**

Run: `php artisan route:list --path=api`

Expected: 15 linhas — 5 para cada um de `usuarios`, `jogos`, `plataformas`.

- [ ] **Step 12: Documentar os endpoints no README**

Acrescentar ao final do `README.md`:

```markdown
## LaaC Lab — API

Banco alternável pelo `.env`: `DB_CONNECTION=sqlite` (padrão) ou `mysql`.
Depois de trocar, rode `php artisan migrate:fresh`.

### Endpoints da Fase 1

Cada recurso expõe os cinco verbos REST:

| Verbo | URI | Ação |
|---|---|---|
| GET | `/api/{recurso}` | lista todos (200) |
| GET | `/api/{recurso}/{id}` | busca um (200 / 404) |
| POST | `/api/{recurso}` | cria (201 / 422) |
| PUT/PATCH | `/api/{recurso}/{id}` | atualiza (200 / 404 / 422) |
| DELETE | `/api/{recurso}/{id}` | remove (204 / 404) |

Recursos disponíveis: `usuarios`, `jogos`, `plataformas`.

Em `usuarios`, a senha é enviada no campo `senha` (texto puro) e gravada com
hash na coluna `senha_hash`, que nunca aparece nas respostas.
```

- [ ] **Step 13: Commit**

```bash
git add -A
git commit -m "feat: CRUD REST de plataformas e documentacao da Fase 1"
```

---

## Estado esperado ao fim do plano

- 6 migrations, 3 models de domínio, 3 controllers de API, 3 factories.
- 15 rotas sob `/api`, cobertas por 46 testes verdes.
- Banco alternável entre SQLite e MySQL por uma linha do `.env`.
- 5 commits deste plano, um por unidade completa:

| Commit | Conteúdo |
|---|---|
| Task 1 | infraestrutura — toggle SQLite/MySQL |
| Task 2 | remoção do domínio `Product` |
| Task 3 | entidade `usuarios` completa |
| Task 4 | entidade `jogos` completa |
| Task 5 | entidade `plataformas` completa + README |

Cada entidade de domínio entra no histórico num único commit, com migration,
model, factory, controller, rotas e testes juntos — nunca pela metade.

## Próximo passo (fora deste plano)

Fase 2 — `jogos_plataformas`, `biblioteca_usuario`, `avaliacoes` e
`curtidas_avaliacoes`, incluindo as constraints `unique` da seção 3.8 da spec e
os relacionamentos Eloquent da seção 5.1. Ganha o seu próprio plano.
