# LaaC Lab — Fase 2: Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar as quatro entidades de relacionamento entre jogo e usuário — `jogos_plataformas`, `biblioteca_usuario`, `avaliacoes` e `curtidas_avaliacoes` — com CRUD REST completo, chaves estrangeiras em cascata e as constraints de unicidade da seção 3.8 da spec.

**Architecture:** Mesmo padrão da Fase 1: um `apiResource` por entidade, migration + Model + Factory + Controller, validação inline, 404 por route-model binding. O que é novo nesta fase: chaves estrangeiras com `ON DELETE CASCADE`, constraints de unicidade composta (validadas na aplicação com o banco como rede de segurança), relacionamentos Eloquent, e a extração das regras de validação para um método por controller — porque a partir daqui `store` e `update` divergem apenas no `required`/`sometimes`.

**Tech Stack:** PHP 8.3, Laravel 13.17, PHPUnit 12.5, SQLite (dev e testes) / MySQL (opcional via `.env`).

**Spec:** [docs/superpowers/specs/2026-08-19-laac-lab-api-design.md](../specs/2026-08-19-laac-lab-api-design.md)

**Fase anterior:** [2026-08-19-laac-lab-fases-0-1.md](2026-08-19-laac-lab-fases-0-1.md) — entregou `usuarios`, `jogos`, `plataformas`. Ponto de partida: 50 testes verdes, 15 rotas sob `/api`.

## Global Constraints

- Tabelas e colunas em português, exatamente como no DDL: `jogos_plataformas`, `biblioteca_usuario`, `avaliacoes`, `curtidas_avaliacoes`.
- Todo Model declara `protected $table` explicitamente — o pluralizador do Eloquent é inglês e não é confiável nesses nomes.
- Todo Model declara `const CREATED_AT` e `const UPDATED_AT`. Nesta fase **nem todos são `criado_em`**: `biblioteca_usuario` usa `adicionado_em`.
- Migrations usam **exclusivamente** o Schema Builder. Nenhum `DB::statement`, nenhum SQL cru, nenhum tipo específico de vendor.
- Toda FK usa `foreignId(...)->constrained('tabela')->cascadeOnDelete()`.
- Todo `Route::apiResource` declara `->parameters()` explicitamente (spec §4.2).
- URI de cada recurso = nome exato da tabela em `snake_case`.
- Status HTTP: `index`/`show`/`update` → 200, `store` → 201, `destroy` → 204, ID inexistente → 404, validação falha → 422.
- Todo controller estende `App\Http\Controllers\Controller` e tipa o retorno de todos os métodos como `JsonResponse`.
- **Um commit por entidade de domínio completa** — migration, model, factory, controller, rotas e testes juntos, nunca pela metade.
- Nenhuma tarefa fecha com `php artisan test` vermelho.

## Decisões desta fase

**Regras de validação extraídas para `private function regras()`.** A revisão da Fase 1 apontou que `store` e `update` duplicavam quase todas as linhas do array de validação, e que a 18 entidades isso vira 36 arrays quase idênticos — onde um `max:` adicionado num e esquecido no outro é exatamente o bug que se esconde em copy-paste. Cada controller desta fase nasce com um método `regras()` chamado por ambos; a Task 5 retrofita os três controllers da Fase 1. Isso permanece dentro da spec §3.6 (validação inline, sem FormRequests).

A assinatura varia de propósito, e isso **não é inconsistência acidental**: controllers com constraint de unicidade composta recebem `regras(Request $request, ?Model $existente = null)`, porque a regra `Rule::unique(...)->where(...)` precisa ler a outra metade do par vinda da request. Os demais recebem só `regras(?Model $existente = null)`. Passar uma `Request` que o método não usa seria ruído.

**Unicidade composta validada em dois níveis.** As quatro constraints da spec §3.8 são checadas na aplicação com `Rule::unique(...)->where(...)`, devolvendo 422, e existem também como índice único no banco. Cada entidade tem um teste para cada nível: um que espera 422 pela API, e um que insere direto pelo model e espera `QueryException`. Sem o segundo, a "rede de segurança" da spec é uma afirmação não verificada.

**`update` completa o par antes de validar.** A regra `unique` composta fica pendurada em apenas um dos dois campos do par. Num `update` parcial que envia só o *outro* campo, o `sometimes` pula todas as regras do campo ausente — inclusive a checagem de unicidade — e o par duplicado chegaria ao banco como `QueryException`, virando 500 em vez do 422 que a spec §3.8 exige. Por isso cada controller com par único tem um `private function completaOPar(Request $request, Model $existente): void` que preenche na request as metades ausentes com os valores já gravados, chamado no início do `update`. Cada uma dessas entidades tem um teste que envia só o campo *sem* a regra e espera 422 — sem ele, o furo volta silenciosamente.

**Cascata testada por comportamento, não por configuração.** A Fase 0 verificou que `foreign_key_constraints` está ligado lendo o valor do config. Esta fase é a primeira com FKs de verdade, então cada entidade ganha um teste que apaga o pai e afirma que o filho sumiu — rodando em SQLite, onde a cascata é silenciosamente ignorada se o pragma não chegar à conexão.

**`nota` usa o cast `decimal:1`.** O JSON sai como `"8.5"` (string), não `8.5` (número). É o comportamento do cast `decimal` do Laravel, e o mesmo que o `Product` do esqueleto usava. A vantagem é normalização: `8` é gravado e devolvido como `"8.0"`, sempre com uma casa. Os testes afirmam a string — isso é esperado, não um bug.

**Nomes de parâmetro de rota.** O binding implícito casa o parâmetro da rota com o nome do argumento do método via `Str::snake()`. Então a rota declara `{jogo_plataforma}` e o método assina `show(JogoPlataforma $jogoPlataforma)`. Os dois precisam corresponder por essa regra; trocar um sem o outro quebra o binding.

---

### Task 1: Entidade `jogos_plataformas` completa

Tabela de ligação entre jogo e plataforma. No DDL não tem timestamps nem constraint de unicidade; ganha ambos (spec §3.3 e §3.8).

**Files:**
- Create: `database/migrations/2026_08_19_000004_create_jogos_plataformas_table.php`
- Create: `app/Models/JogoPlataforma.php`
- Create: `database/factories/JogoPlataformaFactory.php`
- Create: `app/Http/Controllers/JogoPlataformaController.php`
- Modify: `app/Models/Jogo.php` (adiciona o relacionamento `plataformas()`)
- Modify: `routes/api.php`
- Test: `tests/Feature/JogoPlataformaApiTest.php`

**Interfaces:**
- Consumes: `App\Models\Jogo`, `App\Models\Plataforma`, `Database\Factories\JogoFactory`, `Database\Factories\PlataformaFactory` (Fase 1).
- Produces:
  - `App\Models\JogoPlataforma` — tabela `jogos_plataformas`, `$fillable = ['jogo_id', 'plataforma_id']`, relacionamentos `jogo()` e `plataforma()`.
  - `Database\Factories\JogoPlataformaFactory` — cria jogo e plataforma próprios via `Jogo::factory()` / `Plataforma::factory()`, então `JogoPlataforma::factory()->create()` funciona sozinho.
  - `Jogo::plataformas()` — `BelongsToMany` com `withTimestamps('criado_em', 'atualizado_em')`.
  - Rotas `jogos_plataformas.*` sob `/api/jogos_plataformas`, parâmetro `{jogo_plataforma}`.
  - O padrão `private function regras(Request $request, ?Model $existente = null)` que as Tasks 2-5 replicam.

**Commit:** um só, no Step 9.

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/Feature/JogoPlataformaApiTest.php`:

```php
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
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `php artisan test --filter=JogoPlataformaApiTest`

Expected: FAIL com `Class "App\Models\JogoPlataforma" not found`.

- [ ] **Step 3: Criar a migration**

Criar `database/migrations/2026_08_19_000004_create_jogos_plataformas_table.php`:

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('jogos_plataformas', function (Blueprint $table) {
            $table->id();
            $table->foreignId('jogo_id')->constrained('jogos')->cascadeOnDelete();
            $table->foreignId('plataforma_id')->constrained('plataformas')->cascadeOnDelete();
            $table->timestamp('criado_em')->nullable();
            $table->timestamp('atualizado_em')->nullable();

            // Nao esta no DDL de origem; ver secao 3.8 da spec. Um jogo lista
            // uma plataforma uma unica vez.
            $table->unique(['jogo_id', 'plataforma_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('jogos_plataformas');
    }
};
```

- [ ] **Step 4: Criar o Model**

Criar `app/Models/JogoPlataforma.php`:

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class JogoPlataforma extends Model
{
    /** @use HasFactory<\Database\Factories\JogoPlataformaFactory> */
    use HasFactory;

    protected $table = 'jogos_plataformas';

    const CREATED_AT = 'criado_em';
    const UPDATED_AT = 'atualizado_em';

    protected $fillable = [
        'jogo_id',
        'plataforma_id',
    ];

    protected function casts(): array
    {
        return [
            'jogo_id' => 'integer',
            'plataforma_id' => 'integer',
        ];
    }

    public function jogo(): BelongsTo
    {
        return $this->belongsTo(Jogo::class, 'jogo_id');
    }

    public function plataforma(): BelongsTo
    {
        return $this->belongsTo(Plataforma::class, 'plataforma_id');
    }
}
```

- [ ] **Step 5: Criar a Factory**

Criar `database/factories/JogoPlataformaFactory.php`:

```php
<?php

namespace Database\Factories;

use App\Models\Jogo;
use App\Models\JogoPlataforma;
use App\Models\Plataforma;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<JogoPlataforma>
 */
class JogoPlataformaFactory extends Factory
{
    protected $model = JogoPlataforma::class;

    /**
     * As FKs sao factories, nao ids fixos: assim
     * JogoPlataforma::factory()->create() funciona sem preparacao previa.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'jogo_id' => Jogo::factory(),
            'plataforma_id' => Plataforma::factory(),
        ];
    }
}
```

- [ ] **Step 6: Adicionar o relacionamento ao Model `Jogo`**

Em `app/Models/Jogo.php`, acrescentar o import e o método. O arquivo fica assim:

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;

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

    public function plataformas(): BelongsToMany
    {
        return $this->belongsToMany(
            Plataforma::class,
            'jogos_plataformas',
            'jogo_id',
            'plataforma_id',
        )->withTimestamps('criado_em', 'atualizado_em');
    }
}
```

- [ ] **Step 7: Gerar e implementar o controller**

Run: `php artisan make:controller JogoPlataformaController --api`

Substituir todo o conteúdo de `app/Http/Controllers/JogoPlataformaController.php` por:

```php
<?php

namespace App\Http\Controllers;

use App\Models\JogoPlataforma;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class JogoPlataformaController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(JogoPlataforma::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras($request));

        $vinculo = JogoPlataforma::create($dados);

        return response()->json($vinculo, 201);
    }

    public function show(JogoPlataforma $jogoPlataforma): JsonResponse
    {
        return response()->json($jogoPlataforma);
    }

    public function update(Request $request, JogoPlataforma $jogoPlataforma): JsonResponse
    {
        $this->completaOPar($request, $jogoPlataforma);

        $dados = $request->validate($this->regras($request, $jogoPlataforma));

        $jogoPlataforma->update($dados);

        return response()->json($jogoPlataforma);
    }

    public function destroy(JogoPlataforma $jogoPlataforma): JsonResponse
    {
        $jogoPlataforma->delete();

        return response()->json(null, 204);
    }

    /**
     * Regras compartilhadas por store e update. Passar $existente troca
     * "required" por "sometimes" e faz a checagem de unicidade ignorar o
     * proprio registro.
     *
     * @return array<string, mixed>
     */
    private function regras(Request $request, ?JogoPlataforma $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        // O par (jogo_id, plataforma_id) e unico. A regra pendura a checagem
        // em plataforma_id, comparando contra o jogo_id que veio na request
        // (ou o ja gravado, num update parcial).
        $parUnico = Rule::unique('jogos_plataformas')
            ->where(fn ($query) => $query->where(
                'jogo_id',
                $request->input('jogo_id', $existente?->jogo_id),
            ))
            ->ignore($existente);

        return [
            'jogo_id' => [$obrigatorio, 'integer', 'exists:jogos,id'],
            'plataforma_id' => [
                $obrigatorio, 'integer', 'exists:plataformas,id', $parUnico,
            ],
        ];
    }

    /**
     * Preenche na request as metades do par que ela nao trouxe, usando o que
     * ja esta gravado.
     *
     * Sem isto, um update que envia so jogo_id nunca dispara a checagem de
     * unicidade: ela vive nas regras de plataforma_id, que o "sometimes" pula
     * quando o campo esta ausente. O par duplicado passaria pela validacao e
     * so seria barrado pelo indice unico do banco, virando 500 em vez do 422
     * que a secao 3.8 da spec exige.
     */
    private function completaOPar(Request $request, JogoPlataforma $existente): void
    {
        $request->merge([
            'jogo_id' => $request->input('jogo_id', $existente->jogo_id),
            'plataforma_id' => $request->input('plataforma_id', $existente->plataforma_id),
        ]);
    }
}
```

- [ ] **Step 8: Registrar a rota**

Substituir todo o conteúdo de `routes/api.php` por:

```php
<?php

use App\Http\Controllers\JogoController;
use App\Http\Controllers\JogoPlataformaController;
use App\Http\Controllers\PlataformaController;
use App\Http\Controllers\UsuarioController;
use Illuminate\Support\Facades\Route;

// As rotas deste arquivo ja recebem o prefixo /api automaticamente.

// O parametro de rota e sempre declarado explicitamente com ->parameters():
// o pluralizador do Eloquent usado por apiResource() para singularizar o
// nome do recurso e ingles e erra em nomes portugueses (ex.: "avaliacoes"
// viraria "avaliaco"), quebrando o route-model binding. Mesmo motivo pelo
// qual todo model declara "protected $table" explicitamente.
Route::apiResource('usuarios', UsuarioController::class)
    ->parameters(['usuarios' => 'usuario']);
Route::apiResource('jogos', JogoController::class)
    ->parameters(['jogos' => 'jogo']);
Route::apiResource('plataformas', PlataformaController::class)
    ->parameters(['plataformas' => 'plataforma']);
Route::apiResource('jogos_plataformas', JogoPlataformaController::class)
    ->parameters(['jogos_plataformas' => 'jogo_plataforma']);
```

- [ ] **Step 9: Rodar o teste, conferir as rotas e commitar**

Run: `php artisan test --filter=JogoPlataformaApiTest`
Expected: PASS, 16 testes.

Run: `php artisan test`
Expected: PASS, 66 testes (50 da Fase 1 + 16).

Run: `php artisan route:list --path=api`
Expected: 20 rotas; as novas usam o parâmetro `{jogo_plataforma}`.

```bash
git add -A
git commit -m "feat: entidade jogos_plataformas completa"
```

---

### Task 2: Entidade `biblioteca_usuario` completa

A biblioteca pessoal: quais jogos um usuário tem, e quais marcou como favoritos. Nome no singular no DDL — mantido (spec §4.2). O timestamp de criação chama `adicionado_em`, não `criado_em` (spec §3.3).

**Files:**
- Create: `database/migrations/2026_08_19_000005_create_biblioteca_usuario_table.php`
- Create: `app/Models/BibliotecaUsuario.php`
- Create: `database/factories/BibliotecaUsuarioFactory.php`
- Create: `app/Http/Controllers/BibliotecaUsuarioController.php`
- Modify: `app/Models/Usuario.php` (adiciona o relacionamento `jogos()`)
- Modify: `routes/api.php`
- Test: `tests/Feature/BibliotecaUsuarioApiTest.php`

**Interfaces:**
- Consumes: `App\Models\Usuario`, `App\Models\Jogo` e suas factories.
- Produces:
  - `App\Models\BibliotecaUsuario` — tabela `biblioteca_usuario`, `CREATED_AT = 'adicionado_em'`, `$fillable = ['usuario_id', 'jogo_id', 'favorito']`, `$attributes = ['favorito' => false]`.
  - `Database\Factories\BibliotecaUsuarioFactory`.
  - `Usuario::jogos()` — `BelongsToMany` com `withPivot('favorito')` e `withTimestamps('adicionado_em', 'atualizado_em')`.
  - Rotas `biblioteca_usuario.*` sob `/api/biblioteca_usuario`, parâmetro `{biblioteca_usuario}`.

**Commit:** um só, no Step 9.

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/Feature/BibliotecaUsuarioApiTest.php`:

```php
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
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `php artisan test --filter=BibliotecaUsuarioApiTest`

Expected: FAIL com `Class "App\Models\BibliotecaUsuario" not found`.

- [ ] **Step 3: Criar a migration**

Criar `database/migrations/2026_08_19_000005_create_biblioteca_usuario_table.php`:

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Nome no singular, como no DDL de origem. Ver secao 4.2 da spec.
        Schema::create('biblioteca_usuario', function (Blueprint $table) {
            $table->id();
            $table->foreignId('usuario_id')->constrained('usuarios')->cascadeOnDelete();
            $table->foreignId('jogo_id')->constrained('jogos')->cascadeOnDelete();
            $table->boolean('favorito')->default(false);
            $table->timestamp('adicionado_em')->nullable();
            $table->timestamp('atualizado_em')->nullable();

            // Ver secao 3.8 da spec: um jogo aparece uma vez por biblioteca.
            $table->unique(['usuario_id', 'jogo_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('biblioteca_usuario');
    }
};
```

- [ ] **Step 4: Criar o Model**

Criar `app/Models/BibliotecaUsuario.php`:

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class BibliotecaUsuario extends Model
{
    /** @use HasFactory<\Database\Factories\BibliotecaUsuarioFactory> */
    use HasFactory;

    protected $table = 'biblioteca_usuario';

    // O DDL chama o timestamp de criacao de "adicionado_em" nesta tabela.
    const CREATED_AT = 'adicionado_em';
    const UPDATED_AT = 'atualizado_em';

    protected $fillable = [
        'usuario_id',
        'jogo_id',
        'favorito',
    ];

    /**
     * Espelha o default da migration, para o POST que nao envia "favorito"
     * devolver a chave em vez de omiti-la.
     */
    protected $attributes = [
        'favorito' => false,
    ];

    protected function casts(): array
    {
        return [
            'usuario_id' => 'integer',
            'jogo_id' => 'integer',
            'favorito' => 'boolean',
        ];
    }

    public function usuario(): BelongsTo
    {
        return $this->belongsTo(Usuario::class, 'usuario_id');
    }

    public function jogo(): BelongsTo
    {
        return $this->belongsTo(Jogo::class, 'jogo_id');
    }
}
```

- [ ] **Step 5: Criar a Factory**

Criar `database/factories/BibliotecaUsuarioFactory.php`:

```php
<?php

namespace Database\Factories;

use App\Models\BibliotecaUsuario;
use App\Models\Jogo;
use App\Models\Usuario;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<BibliotecaUsuario>
 */
class BibliotecaUsuarioFactory extends Factory
{
    protected $model = BibliotecaUsuario::class;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'usuario_id' => Usuario::factory(),
            'jogo_id' => Jogo::factory(),
            'favorito' => false,
        ];
    }
}
```

- [ ] **Step 6: Adicionar o relacionamento ao Model `Usuario`**

Em `app/Models/Usuario.php`: acrescentar o import
`use Illuminate\Database\Eloquent\Relations\BelongsToMany;` junto aos outros
imports, e o método abaixo depois de `getAuthPassword()`:

```php
    public function jogos(): BelongsToMany
    {
        return $this->belongsToMany(
            Jogo::class,
            'biblioteca_usuario',
            'usuario_id',
            'jogo_id',
        )
            ->withPivot('favorito')
            ->withTimestamps('adicionado_em', 'atualizado_em');
    }
```

Não alterar nada mais no arquivo — `$fillable`, `$hidden`, `$attributes`, os casts e `getAuthPassword()` ficam como estão.

- [ ] **Step 7: Gerar e implementar o controller**

Run: `php artisan make:controller BibliotecaUsuarioController --api`

Substituir todo o conteúdo de `app/Http/Controllers/BibliotecaUsuarioController.php` por:

```php
<?php

namespace App\Http\Controllers;

use App\Models\BibliotecaUsuario;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class BibliotecaUsuarioController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(BibliotecaUsuario::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras($request));

        $item = BibliotecaUsuario::create($dados);

        return response()->json($item, 201);
    }

    public function show(BibliotecaUsuario $bibliotecaUsuario): JsonResponse
    {
        return response()->json($bibliotecaUsuario);
    }

    public function update(Request $request, BibliotecaUsuario $bibliotecaUsuario): JsonResponse
    {
        $this->completaOPar($request, $bibliotecaUsuario);

        $dados = $request->validate($this->regras($request, $bibliotecaUsuario));

        $bibliotecaUsuario->update($dados);

        return response()->json($bibliotecaUsuario);
    }

    public function destroy(BibliotecaUsuario $bibliotecaUsuario): JsonResponse
    {
        $bibliotecaUsuario->delete();

        return response()->json(null, 204);
    }

    /**
     * Regras compartilhadas por store e update.
     *
     * @return array<string, mixed>
     */
    private function regras(Request $request, ?BibliotecaUsuario $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        $parUnico = Rule::unique('biblioteca_usuario')
            ->where(fn ($query) => $query->where(
                'usuario_id',
                $request->input('usuario_id', $existente?->usuario_id),
            ))
            ->ignore($existente);

        return [
            'usuario_id' => [$obrigatorio, 'integer', 'exists:usuarios,id'],
            'jogo_id' => [
                $obrigatorio, 'integer', 'exists:jogos,id', $parUnico,
            ],
            'favorito' => 'sometimes|boolean',
        ];
    }

    /**
     * Preenche na request as metades do par que ela nao trouxe, usando o que
     * ja esta gravado.
     *
     * Sem isto, um update que envia so usuario_id nunca dispara a checagem de
     * unicidade: ela vive nas regras de jogo_id, que o "sometimes" pula quando
     * o campo esta ausente. O par duplicado passaria pela validacao e so seria
     * barrado pelo indice unico do banco, virando 500 em vez do 422 que a
     * secao 3.8 da spec exige.
     */
    private function completaOPar(Request $request, BibliotecaUsuario $existente): void
    {
        $request->merge([
            'usuario_id' => $request->input('usuario_id', $existente->usuario_id),
            'jogo_id' => $request->input('jogo_id', $existente->jogo_id),
        ]);
    }
}
```

- [ ] **Step 8: Registrar a rota**

Em `routes/api.php`, adicionar o import
`use App\Http\Controllers\BibliotecaUsuarioController;` (mantendo a ordem
alfabética dos imports) e, ao final do arquivo, a rota:

```php
Route::apiResource('biblioteca_usuario', BibliotecaUsuarioController::class)
    ->parameters(['biblioteca_usuario' => 'biblioteca_usuario']);
```

- [ ] **Step 9: Rodar o teste, conferir as rotas e commitar**

Run: `php artisan test --filter=BibliotecaUsuarioApiTest`
Expected: PASS, 15 testes.

Run: `php artisan test`
Expected: PASS, 81 testes.

Run: `php artisan route:list --path=api`
Expected: 25 rotas; as novas usam o parâmetro `{biblioteca_usuario}`.

```bash
git add -A
git commit -m "feat: entidade biblioteca_usuario completa"
```

---

### Task 3: Entidade `avaliacoes` completa

As reviews que um usuário escreve sobre um jogo. Diferente das duas anteriores, **não tem constraint de unicidade** — o DDL permite que o mesmo usuário avalie o mesmo jogo mais de uma vez, e a spec §3.8 não lista essa tabela entre as que ganham `unique`. Não adicione uma.

**Files:**
- Create: `database/migrations/2026_08_19_000006_create_avaliacoes_table.php`
- Create: `app/Models/Avaliacao.php`
- Create: `database/factories/AvaliacaoFactory.php`
- Create: `app/Http/Controllers/AvaliacaoController.php`
- Modify: `app/Models/Usuario.php` (adiciona `avaliacoes()`)
- Modify: `app/Models/Jogo.php` (adiciona `avaliacoes()`)
- Modify: `routes/api.php`
- Test: `tests/Feature/AvaliacaoApiTest.php`

**Interfaces:**
- Consumes: `App\Models\Usuario`, `App\Models\Jogo` e suas factories.
- Produces:
  - `App\Models\Avaliacao` — tabela `avaliacoes`, `$fillable = ['usuario_id', 'jogo_id', 'nota', 'comentario']`, cast `nota => 'decimal:1'`, relacionamentos `usuario()` e `jogo()`.
  - `Database\Factories\AvaliacaoFactory`.
  - `Usuario::avaliacoes()` e `Jogo::avaliacoes()` — `HasMany`.
  - Rotas `avaliacoes.*` sob `/api/avaliacoes`, parâmetro `{avaliacao}` — **este é o caso que motivou a regra do `->parameters()`**: sem ele o Laravel geraria `{avaliaco}`.
  - A Task 4 referencia `avaliacoes.id`.

**Commit:** um só, no Step 10.

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/Feature/AvaliacaoApiTest.php`:

```php
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
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `php artisan test --filter=AvaliacaoApiTest`

Expected: FAIL com `Class "App\Models\Avaliacao" not found`.

- [ ] **Step 3: Criar a migration**

Criar `database/migrations/2026_08_19_000006_create_avaliacoes_table.php`:

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('avaliacoes', function (Blueprint $table) {
            $table->id();
            $table->foreignId('usuario_id')->constrained('usuarios')->cascadeOnDelete();
            $table->foreignId('jogo_id')->constrained('jogos')->cascadeOnDelete();
            $table->decimal('nota', 2, 1)->nullable();
            $table->text('comentario')->nullable();
            $table->timestamp('criado_em')->nullable();
            $table->timestamp('atualizado_em')->nullable();
        });

        // Sem unique: o DDL permite o mesmo usuario avaliar o mesmo jogo mais
        // de uma vez, e a secao 3.8 da spec nao lista esta tabela.
    }

    public function down(): void
    {
        Schema::dropIfExists('avaliacoes');
    }
};
```

- [ ] **Step 4: Criar o Model**

Criar `app/Models/Avaliacao.php`:

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Avaliacao extends Model
{
    /** @use HasFactory<\Database\Factories\AvaliacaoFactory> */
    use HasFactory;

    protected $table = 'avaliacoes';

    const CREATED_AT = 'criado_em';
    const UPDATED_AT = 'atualizado_em';

    protected $fillable = [
        'usuario_id',
        'jogo_id',
        'nota',
        'comentario',
    ];

    protected function casts(): array
    {
        return [
            'usuario_id' => 'integer',
            'jogo_id' => 'integer',
            // decimal:1 devolve string no JSON ("8.0"), sempre com uma casa.
            'nota' => 'decimal:1',
        ];
    }

    public function usuario(): BelongsTo
    {
        return $this->belongsTo(Usuario::class, 'usuario_id');
    }

    public function jogo(): BelongsTo
    {
        return $this->belongsTo(Jogo::class, 'jogo_id');
    }
}
```

- [ ] **Step 5: Criar a Factory**

Criar `database/factories/AvaliacaoFactory.php`:

```php
<?php

namespace Database\Factories;

use App\Models\Avaliacao;
use App\Models\Jogo;
use App\Models\Usuario;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Avaliacao>
 */
class AvaliacaoFactory extends Factory
{
    protected $model = Avaliacao::class;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'usuario_id' => Usuario::factory(),
            'jogo_id' => Jogo::factory(),
            // A coluna e decimal(2,1): o maximo representavel e 9.9.
            'nota' => fake()->randomFloat(1, 0, 9.9),
            'comentario' => fake()->paragraph(),
        ];
    }
}
```

- [ ] **Step 6: Adicionar `avaliacoes()` ao Model `Usuario`**

Em `app/Models/Usuario.php`: acrescentar o import
`use Illuminate\Database\Eloquent\Relations\HasMany;` e o método abaixo,
depois de `jogos()`:

```php
    public function avaliacoes(): HasMany
    {
        return $this->hasMany(Avaliacao::class, 'usuario_id');
    }
```

- [ ] **Step 7: Adicionar `avaliacoes()` ao Model `Jogo`**

Em `app/Models/Jogo.php`: acrescentar o import
`use Illuminate\Database\Eloquent\Relations\HasMany;` e o método abaixo,
depois de `plataformas()`:

```php
    public function avaliacoes(): HasMany
    {
        return $this->hasMany(Avaliacao::class, 'jogo_id');
    }
```

- [ ] **Step 8: Gerar e implementar o controller**

Run: `php artisan make:controller AvaliacaoController --api`

Substituir todo o conteúdo de `app/Http/Controllers/AvaliacaoController.php` por:

```php
<?php

namespace App\Http\Controllers;

use App\Models\Avaliacao;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class AvaliacaoController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(Avaliacao::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras());

        $avaliacao = Avaliacao::create($dados);

        return response()->json($avaliacao, 201);
    }

    public function show(Avaliacao $avaliacao): JsonResponse
    {
        return response()->json($avaliacao);
    }

    public function update(Request $request, Avaliacao $avaliacao): JsonResponse
    {
        $dados = $request->validate($this->regras($avaliacao));

        $avaliacao->update($dados);

        return response()->json($avaliacao);
    }

    public function destroy(Avaliacao $avaliacao): JsonResponse
    {
        $avaliacao->delete();

        return response()->json(null, 204);
    }

    /**
     * Regras compartilhadas por store e update. Esta tabela nao tem
     * constraint de unicidade, entao nao precisa da Request.
     *
     * @return array<string, mixed>
     */
    private function regras(?Avaliacao $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        return [
            'usuario_id' => "$obrigatorio|integer|exists:usuarios,id",
            'jogo_id' => "$obrigatorio|integer|exists:jogos,id",
            // decimal(2,1) representa no maximo 9.9.
            'nota' => 'nullable|numeric|min:0|max:9.9',
            'comentario' => 'nullable|string|max:5000',
        ];
    }
}
```

- [ ] **Step 9: Registrar a rota**

Em `routes/api.php`, adicionar o import
`use App\Http\Controllers\AvaliacaoController;` (mantendo a ordem alfabética)
e, ao final do arquivo, a rota:

```php
Route::apiResource('avaliacoes', AvaliacaoController::class)
    ->parameters(['avaliacoes' => 'avaliacao']);
```

- [ ] **Step 10: Rodar o teste, conferir as rotas e commitar**

Run: `php artisan test --filter=AvaliacaoApiTest`
Expected: PASS, 17 testes.

Run: `php artisan test`
Expected: PASS, 98 testes.

Run: `php artisan route:list --path=api`
Expected: 30 rotas. **Conferir explicitamente que o parâmetro é `{avaliacao}` e não `{avaliaco}`** — é o caso que motivou a regra do `->parameters()`.

```bash
git add -A
git commit -m "feat: entidade avaliacoes completa"
```

---

### Task 4: Entidade `curtidas_avaliacoes` completa

Curtidas em reviews. No DDL não tem timestamps nem unicidade; ganha ambos (spec §3.3 e §3.8).

**Files:**
- Create: `database/migrations/2026_08_19_000007_create_curtidas_avaliacoes_table.php`
- Create: `app/Models/CurtidaAvaliacao.php`
- Create: `database/factories/CurtidaAvaliacaoFactory.php`
- Create: `app/Http/Controllers/CurtidaAvaliacaoController.php`
- Modify: `app/Models/Avaliacao.php` (adiciona `curtidas()`)
- Modify: `routes/api.php`
- Test: `tests/Feature/CurtidaAvaliacaoApiTest.php`

**Interfaces:**
- Consumes: `App\Models\Avaliacao`, `App\Models\Usuario` e suas factories (Task 3 e Fase 1).
- Produces:
  - `App\Models\CurtidaAvaliacao` — tabela `curtidas_avaliacoes`, `$fillable = ['avaliacao_id', 'usuario_id']`.
  - `Database\Factories\CurtidaAvaliacaoFactory`.
  - `Avaliacao::curtidas()` — `HasMany`.
  - Rotas `curtidas_avaliacoes.*` sob `/api/curtidas_avaliacoes`, parâmetro `{curtida_avaliacao}`.

**Commit:** um só, no Step 9.

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/Feature/CurtidaAvaliacaoApiTest.php`:

```php
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
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `php artisan test --filter=CurtidaAvaliacaoApiTest`

Expected: FAIL com `Class "App\Models\CurtidaAvaliacao" not found`.

- [ ] **Step 3: Criar a migration**

Criar `database/migrations/2026_08_19_000007_create_curtidas_avaliacoes_table.php`:

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('curtidas_avaliacoes', function (Blueprint $table) {
            $table->id();
            $table->foreignId('avaliacao_id')->constrained('avaliacoes')->cascadeOnDelete();
            $table->foreignId('usuario_id')->constrained('usuarios')->cascadeOnDelete();
            $table->timestamp('criado_em')->nullable();
            $table->timestamp('atualizado_em')->nullable();

            // Ver secao 3.8 da spec: um usuario curte uma review uma vez.
            $table->unique(['avaliacao_id', 'usuario_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('curtidas_avaliacoes');
    }
};
```

- [ ] **Step 4: Criar o Model**

Criar `app/Models/CurtidaAvaliacao.php`:

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class CurtidaAvaliacao extends Model
{
    /** @use HasFactory<\Database\Factories\CurtidaAvaliacaoFactory> */
    use HasFactory;

    protected $table = 'curtidas_avaliacoes';

    const CREATED_AT = 'criado_em';
    const UPDATED_AT = 'atualizado_em';

    protected $fillable = [
        'avaliacao_id',
        'usuario_id',
    ];

    protected function casts(): array
    {
        return [
            'avaliacao_id' => 'integer',
            'usuario_id' => 'integer',
        ];
    }

    public function avaliacao(): BelongsTo
    {
        return $this->belongsTo(Avaliacao::class, 'avaliacao_id');
    }

    public function usuario(): BelongsTo
    {
        return $this->belongsTo(Usuario::class, 'usuario_id');
    }
}
```

- [ ] **Step 5: Criar a Factory**

Criar `database/factories/CurtidaAvaliacaoFactory.php`:

```php
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
```

- [ ] **Step 6: Adicionar `curtidas()` ao Model `Avaliacao`**

Em `app/Models/Avaliacao.php`: acrescentar o import
`use Illuminate\Database\Eloquent\Relations\HasMany;` e o método abaixo,
depois de `jogo()`:

```php
    public function curtidas(): HasMany
    {
        return $this->hasMany(CurtidaAvaliacao::class, 'avaliacao_id');
    }
```

- [ ] **Step 7: Gerar e implementar o controller**

Run: `php artisan make:controller CurtidaAvaliacaoController --api`

Substituir todo o conteúdo de `app/Http/Controllers/CurtidaAvaliacaoController.php` por:

```php
<?php

namespace App\Http\Controllers;

use App\Models\CurtidaAvaliacao;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class CurtidaAvaliacaoController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(CurtidaAvaliacao::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras($request));

        $curtida = CurtidaAvaliacao::create($dados);

        return response()->json($curtida, 201);
    }

    public function show(CurtidaAvaliacao $curtidaAvaliacao): JsonResponse
    {
        return response()->json($curtidaAvaliacao);
    }

    public function update(Request $request, CurtidaAvaliacao $curtidaAvaliacao): JsonResponse
    {
        $this->completaOPar($request, $curtidaAvaliacao);

        $dados = $request->validate($this->regras($request, $curtidaAvaliacao));

        $curtidaAvaliacao->update($dados);

        return response()->json($curtidaAvaliacao);
    }

    public function destroy(CurtidaAvaliacao $curtidaAvaliacao): JsonResponse
    {
        $curtidaAvaliacao->delete();

        return response()->json(null, 204);
    }

    /**
     * Regras compartilhadas por store e update.
     *
     * @return array<string, mixed>
     */
    private function regras(Request $request, ?CurtidaAvaliacao $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        $parUnico = Rule::unique('curtidas_avaliacoes')
            ->where(fn ($query) => $query->where(
                'avaliacao_id',
                $request->input('avaliacao_id', $existente?->avaliacao_id),
            ))
            ->ignore($existente);

        return [
            'avaliacao_id' => [$obrigatorio, 'integer', 'exists:avaliacoes,id'],
            'usuario_id' => [
                $obrigatorio, 'integer', 'exists:usuarios,id', $parUnico,
            ],
        ];
    }

    /**
     * Preenche na request as metades do par que ela nao trouxe, usando o que
     * ja esta gravado.
     *
     * Sem isto, um update que envia so avaliacao_id nunca dispara a checagem
     * de unicidade: ela vive nas regras de usuario_id, que o "sometimes" pula
     * quando o campo esta ausente. O par duplicado passaria pela validacao e
     * so seria barrado pelo indice unico do banco, virando 500 em vez do 422
     * que a secao 3.8 da spec exige.
     */
    private function completaOPar(Request $request, CurtidaAvaliacao $existente): void
    {
        $request->merge([
            'avaliacao_id' => $request->input('avaliacao_id', $existente->avaliacao_id),
            'usuario_id' => $request->input('usuario_id', $existente->usuario_id),
        ]);
    }
}
```

- [ ] **Step 8: Registrar a rota**

Em `routes/api.php`, adicionar o import
`use App\Http\Controllers\CurtidaAvaliacaoController;` (mantendo a ordem
alfabética) e, ao final do arquivo, a rota:

```php
Route::apiResource('curtidas_avaliacoes', CurtidaAvaliacaoController::class)
    ->parameters(['curtidas_avaliacoes' => 'curtida_avaliacao']);
```

- [ ] **Step 9: Rodar o teste, conferir as rotas e commitar**

Run: `php artisan test --filter=CurtidaAvaliacaoApiTest`
Expected: PASS, 14 testes.

Run: `php artisan test`
Expected: PASS, 112 testes.

Run: `php artisan route:list --path=api`
Expected: 35 rotas; as novas usam o parâmetro `{curtida_avaliacao}`.

```bash
git add -A
git commit -m "feat: entidade curtidas_avaliacoes completa"
```

---

### Task 5: Uniformizar os controllers da Fase 1 e fechar a fase

As quatro entidades desta fase nasceram com `private function regras()`. Os três controllers da Fase 1 ainda duplicam os arrays entre `store` e `update`. Esta task alinha os sete e fecha a fase com as verificações e a documentação.

Isto é uma refatoração pura: **nenhum teste muda, nenhum teste novo é escrito, e os 112 testes continuam verdes exatamente como estão.** Se algum teste quebrar, a refatoração mudou comportamento e está errada.

**Files:**
- Modify: `app/Http/Controllers/UsuarioController.php`
- Modify: `app/Http/Controllers/JogoController.php`
- Modify: `app/Http/Controllers/PlataformaController.php`
- Modify: `README.md`

**Interfaces:**
- Consumes: nada novo.
- Produces: o padrão `regras()` presente nos sete controllers, que as Fases 3-5 replicam.

**Commit:** um só, no Step 7.

- [ ] **Step 1: Rodar a suíte e anotar o ponto de partida**

Run: `php artisan test`

Expected: PASS, 112 testes. Este é o número que deve permanecer idêntico ao final.

- [ ] **Step 2: Refatorar o `UsuarioController`**

Em `app/Http/Controllers/UsuarioController.php`, substituir os corpos de
`store` e `update` e acrescentar o método `regras`. Os métodos ficam assim
(o resto do arquivo — `index`, `show`, `destroy` e
`trocaSenhaPelaColuna` — não muda):

```php
    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras());

        $usuario = Usuario::create($this->trocaSenhaPelaColuna($dados));

        return response()->json($usuario, 201);
    }

    public function update(Request $request, Usuario $usuario): JsonResponse
    {
        $dados = $request->validate($this->regras($usuario));

        $usuario->update($this->trocaSenhaPelaColuna($dados));

        return response()->json($usuario);
    }

    /**
     * Regras compartilhadas por store e update. Passar $existente troca
     * "required" por "sometimes" e faz as checagens de unicidade ignorarem
     * o proprio registro.
     *
     * @return array<string, mixed>
     */
    private function regras(?Usuario $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        return [
            'nome_usuario' => [
                $obrigatorio, 'string', 'max:50',
                Rule::unique('usuarios', 'nome_usuario')->ignore($existente),
            ],
            'email' => [
                $obrigatorio, 'email', 'max:100',
                Rule::unique('usuarios', 'email')->ignore($existente),
            ],
            'senha' => "$obrigatorio|string|min:8",
            'idade' => 'nullable|integer|min:0|max:150',
            'avatar_url' => 'nullable|string|max:2048|url',
            'bio' => 'nullable|string|max:5000',
            'nivel' => 'sometimes|integer|min:1',
        ];
    }
```

`Rule::unique(...)->ignore(null)` é seguro: com `null` a regra não ignora
registro nenhum, que é exatamente o comportamento desejado no `store`.

`nivel` permanece `sometimes` nos dois casos, como já era — não alterar.

- [ ] **Step 3: Rodar os testes de usuário**

Run: `php artisan test --filter=UsuarioApiTest`

Expected: PASS, 15 testes. Nenhuma mudança de comportamento.

- [ ] **Step 4: Refatorar o `JogoController`**

Em `app/Http/Controllers/JogoController.php`, mesma transformação:

```php
    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras());

        $jogo = Jogo::create($dados);

        return response()->json($jogo, 201);
    }

    public function update(Request $request, Jogo $jogo): JsonResponse
    {
        $dados = $request->validate($this->regras($jogo));

        $jogo->update($dados);

        return response()->json($jogo);
    }

    /**
     * Regras compartilhadas por store e update.
     *
     * @return array<string, mixed>
     */
    private function regras(?Jogo $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        return [
            'nome' => "$obrigatorio|string|max:100",
            'descricao' => 'nullable|string|max:5000',
            'genero' => 'nullable|string|max:50',
            'classificacao' => 'nullable|string|max:10',
            'desenvolvedora' => 'nullable|string|max:100',
            'data_lancamento' => 'nullable|date_format:Y-m-d',
            'capa_url' => 'nullable|string|max:2048|url',
        ];
    }
```

- [ ] **Step 5: Refatorar o `PlataformaController`**

Em `app/Http/Controllers/PlataformaController.php`:

```php
    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras());

        $plataforma = Plataforma::create($dados);

        return response()->json($plataforma, 201);
    }

    public function update(Request $request, Plataforma $plataforma): JsonResponse
    {
        $dados = $request->validate($this->regras($plataforma));

        $plataforma->update($dados);

        return response()->json($plataforma);
    }

    /**
     * Regras compartilhadas por store e update.
     *
     * @return array<string, mixed>
     */
    private function regras(?Plataforma $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        return [
            'nome' => "$obrigatorio|string|max:50",
        ];
    }
```

- [ ] **Step 6: Verificações de fechamento da fase**

Run: `php artisan test`
Expected: PASS, **112 testes** — o mesmo número do Step 1. Qualquer diferença significa que a refatoração mudou comportamento.

Run: `php artisan migrate:fresh --seed`
Expected: 10 migrations rodam sem erro, na ordem: `sessions`, `cache`, `jobs`, `usuarios`, `jogos`, `plataformas`, `jogos_plataformas`, `biblioteca_usuario`, `avaliacoes`, `curtidas_avaliacoes`.

Run: `php artisan route:list --path=api`
Expected: 35 rotas — 5 para cada um dos 7 recursos.

- [ ] **Step 7: Documentar e commitar**

Em `README.md`, na seção "LaaC Lab — API", substituir a linha que lista os
recursos disponíveis por:

```markdown
Recursos disponíveis: `usuarios`, `jogos`, `plataformas`, `jogos_plataformas`,
`biblioteca_usuario`, `avaliacoes`, `curtidas_avaliacoes`.

Os quatro últimos são relacionamentos e exigem os ids dos registros que ligam.
Apagar um registro pai apaga os dependentes em cascata: apagar um jogo remove
seus vínculos de plataforma, suas entradas em bibliotecas e suas avaliações;
apagar uma avaliação remove suas curtidas.

Pares que não podem repetir — `(jogo_id, plataforma_id)`,
`(usuario_id, jogo_id)` na biblioteca e `(avaliacao_id, usuario_id)` nas
curtidas — retornam 422. A nota de uma avaliação vai de 0 a 9.9 e é devolvida
como string com uma casa decimal (`"8.0"`).
```

Não alterar o resto do README.

```bash
git add -A
git commit -m "refactor: extrai regras de validacao nos controllers da Fase 1 e documenta a Fase 2"
```

---

## Estado esperado ao fim do plano

- 10 migrations, 7 models de domínio, 7 controllers de API, 7 factories.
- 35 rotas sob `/api`, cobertas por 112 testes verdes.
- FKs em cascata verificadas por comportamento, não por configuração.
- As quatro constraints de unicidade da spec §3.8 verificadas nos dois níveis: 422 pela API e `QueryException` pelo banco.
- 5 commits, um por unidade completa:

| Commit | Conteúdo |
|---|---|
| Task 1 | entidade `jogos_plataformas` completa |
| Task 2 | entidade `biblioteca_usuario` completa |
| Task 3 | entidade `avaliacoes` completa |
| Task 4 | entidade `curtidas_avaliacoes` completa |
| Task 5 | uniformização dos controllers + README |

## Próximo passo (fora deste plano)

Fase 3 — o Bugômetro: `bugometro_status` (1:1 com jogo, `jogo_id` único),
`metricas_bug`, `relatos_bug` e `historico_bug`. `historico_bug` usa
`registrado_em` como `CREATED_AT`. Ganha o seu próprio plano.

Duas questões em aberto que a Fase 1 deixou e que valem decidir antes:
`nivel` continua gravável por qualquer chamador anônimo no POST/PUT de
`usuarios`, e `index` segue sem paginação em todos os recursos — com
`avaliacoes` e `curtidas_avaliacoes`, que crescem sem limite, isso deixa de
ser teórico.
