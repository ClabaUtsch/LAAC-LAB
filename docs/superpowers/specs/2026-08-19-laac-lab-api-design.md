# LaaC Lab — API REST: Design

**Data:** 2026-08-19
**Status:** aprovado
**Projeto:** `d:/Projects/api-laravel`

## 1. Objetivo

Transformar o esqueleto Laravel 13.8 existente numa API REST para o domínio
**LaaC Lab** — uma plataforma de catálogo de jogos com biblioteca pessoal,
avaliações, fórum, gamificação e o "Bugômetro" (métricas de instabilidade por
jogo).

O escopo são **18 entidades**, cada uma com CRUD REST completo, entregues em
**6 fases** incrementais.

## 2. Requisitos técnicos (dados pelo autor do projeto)

Cada recurso deve ter:

1. **Migration** — tabela no plural, tipos adequados, timestamps.
2. **Model** — Eloquent configurado.
3. **Controller** — de API (`make:controller XController --api`).
4. **Rotas** — em `routes/api.php` (o prefixo `/api` é automático).
5. **Respostas JSON** com status HTTP adequados (200, 201, 404, 204, …).

Padrão de rotas esperado, para um recurso `jogos`:

| Verbo | URI | Método | Status de sucesso |
|---|---|---|---|
| GET | `/api/jogos` | `index` | 200 |
| GET | `/api/jogos/{id}` | `show` | 200 |
| POST | `/api/jogos` | `store` | 201 |
| PUT/PATCH | `/api/jogos/{id}` | `update` | 200 |
| DELETE | `/api/jogos/{id}` | `destroy` | 204 |

## 3. Decisões de arquitetura

### 3.1 Banco alternável entre SQLite e MySQL

O DDL de origem é MySQL, mas o desenvolvimento roda em SQLite. Migrations usam
**exclusivamente o Schema Builder** do Laravel — nenhum SQL cru, nenhum tipo
específico de vendor — de modo que o mesmo código gera os dois bancos.

O `.env` passa a conter o bloco MySQL completo, com `DB_CONNECTION` escolhendo:

```
DB_CONNECTION=sqlite      # troque para "mysql" quando quiser
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=LaaC_lab
DB_USERNAME=root
DB_PASSWORD=
```

Trocar de banco é editar uma linha e rodar `php artisan migrate:fresh`.
O `.env.example` recebe o mesmo bloco.

**Verificação obrigatória na Fase 0:** confirmar que `config/database.php`
mantém `foreign_key_constraints => true` para SQLite — sem isso o
`ON DELETE CASCADE` é silenciosamente ignorado.

### 3.2 Nomenclatura em português

Tabelas e colunas seguem o DDL original: tabelas no plural em português
(`usuarios`, `jogos`, `avaliacoes`), colunas em português (`nome_usuario`,
`senha_hash`, `data_lancamento`).

Models em português no singular (`Usuario`, `Jogo`, `Avaliacao`). O
pluralizador do Eloquent é inglês e erra nesses nomes, então **todo model
declara `protected $table` explicitamente**, sem exceção — não se depende de
acerto acidental.

Controllers: `UsuarioController`, `JogoController`, etc.

### 3.3 Timestamps

O DDL traz apenas um timestamp de criação por tabela, com nomes variados. O
requisito 1 pede timestamps, então **toda tabela ganha o par completo**,
mantendo o nome de criação do DDL e adicionando `atualizado_em`:

| Tabela | `CREATED_AT` | `UPDATED_AT` |
|---|---|---|
| `biblioteca_usuario` | `adicionado_em` | `atualizado_em` |
| `historico_bug` | `registrado_em` | `atualizado_em` |
| `usuarios_badges` | `conquistado_em` | `atualizado_em` |
| todas as demais | `criado_em` | `atualizado_em` |

Cada Model declara as constantes correspondentes:

```php
const CREATED_AT = 'criado_em';
const UPDATED_AT = 'atualizado_em';
```

Tabelas que o DDL define sem timestamp algum (`plataformas`,
`jogos_plataformas`, `curtidas_avaliacoes`, `categorias`, `badges`) recebem
`criado_em`/`atualizado_em` por consistência. `bugometro_status`, que no DDL
tem só `atualizado_em`, ganha `criado_em`.

### 3.4 `usuarios` substitui `users`

A tabela `users` do esqueleto Laravel e a `usuarios` do DDL são a mesma
entidade. Decisão: **remover** `users`.

- Apagar `app/Models/User.php`, `database/factories/UserFactory.php` e o
  bloco `Schema::create('users', …)` da migration `0001_01_01_000000`.
- `password_reset_tokens` e `sessions` permanecem na mesma migration.
  `sessions.user_id` é apenas um índice, não uma FK, então nada quebra.
- `App\Models\Usuario` estende `Illuminate\Foundation\Auth\User`
  (`Authenticatable`), deixando autenticação plug-and-play numa fase futura.
- `config/auth.php` passa a apontar `AUTH_MODEL` para `Usuario::class`.
- `DatabaseSeeder` deixa de referenciar `User`.

### 3.5 Senha

`senha_hash` nunca aparece em resposta JSON: entra em `protected $hidden`.
No `store`/`update`, o valor recebido no campo `senha` é passado por
`Hash::make()` antes de gravar em `senha_hash`.

**Não há autenticação nesta entrega.** Todos os endpoints são públicos.
Sanctum fica como fase futura, fora do escopo deste design.

### 3.6 Validação inline

Validação com `$request->validate([...])` dentro do controller, como no
`ProductController` existente. Com 18 recursos, FormRequests dobrariam a
contagem de arquivos sem ganho proporcional neste porte de projeto.

Regras derivadas mecanicamente do DDL:

| Coluna no DDL | Regra no `store` | Regra no `update` |
|---|---|---|
| `NOT NULL` | `required` | `sometimes` |
| `VARCHAR(n)` | `string` + `max:n` | idem |
| `UNIQUE` | `unique:tabela,coluna` | `unique:tabela,coluna,{id}` |
| `TEXT` nullable | `nullable` + `string` | idem |
| `INT` | `integer` | idem |
| `DECIMAL(2,1)` | `numeric` + `min:0` + `max:9.9` + `decimal:0,1` | idem |
| `BOOLEAN` | `boolean` | idem |
| `DATE` | `date` | idem |
| FK | `required` + `exists:tabela_alvo,id` | `sometimes` + `exists:…` |

### 3.7 Remoção do domínio `Product`

`app/Models/Product.php`, `app/Http/Controllers/ProductController.php`,
`database/migrations/2026_06_24_220025_create_products_table.php` e a rota
`apiResource('products')` são removidos em commit próprio na Fase 0.

### 3.8 Desvios deliberados do DDL

Quatro tabelas de relacionamento no DDL não têm constraint de unicidade,
permitindo duplicatas que são bugs de domínio. Este design **adiciona** as
constraints:

| Tabela | Constraint adicionada | Motivo |
|---|---|---|
| `curtidas_avaliacoes` | `unique(avaliacao_id, usuario_id)` | um usuário curte uma review uma vez |
| `biblioteca_usuario` | `unique(usuario_id, jogo_id)` | um jogo aparece uma vez na biblioteca |
| `usuarios_badges` | `unique(usuario_id, badge_id)` | uma badge é conquistada uma vez |
| `jogos_plataformas` | `unique(jogo_id, plataforma_id)` | um jogo lista uma plataforma uma vez |

A violação retorna 422 pela regra `unique` do validator (checagem na
aplicação), com a constraint no banco como rede de segurança.

## 4. Padrão canônico de um recurso

Referência a ser replicada nas 18 entidades. Exemplo com `jogos`:

**Migration** — `database/migrations/*_create_jogos_table.php`

```php
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
```

**Model** — `app/Models/Jogo.php`

```php
class Jogo extends Model
{
    protected $table = 'jogos';
    const CREATED_AT = 'criado_em';
    const UPDATED_AT = 'atualizado_em';

    protected $fillable = [/* colunas editáveis */];
    protected $casts = ['data_lancamento' => 'date'];

    public function plataformas(): BelongsToMany { /* … */ }
    public function avaliacoes(): HasMany { /* … */ }
}
```

**Controller** — `app/Http/Controllers/JogoController.php`, gerado com
`--api`, cinco métodos, todos com retorno tipado `JsonResponse`, usando
route-model binding em `show`/`update`/`destroy`.

**Rota** — com o parâmetro declarado explicitamente (ver seção 4.2):

```php
Route::apiResource('jogos', JogoController::class)
    ->parameters(['jogos' => 'jogo']);
```

### 4.1 Contrato de resposta

| Situação | Status | Corpo |
|---|---|---|
| `index` | 200 | array de objetos |
| `show` | 200 | objeto |
| `store` ok | 201 | objeto criado |
| `update` ok | 200 | objeto atualizado |
| `destroy` ok | 204 | vazio |
| ID inexistente | 404 | `{"message": "..."}` |
| Validação falhou | 422 | `{"message": "...", "errors": {...}}` |

O 404 e o 422 vêm do próprio framework: route-model binding lança
`ModelNotFoundException` e `bootstrap/app.php` já força renderização JSON em
`api/*` via `shouldRenderJsonWhen`.

`index` retorna a coleção completa, sem paginação — coerente com "listar
todos". Paginação fica fora do escopo.

### 4.2 Nomes de URI

A URI de cada recurso é **o nome exato da tabela**, em `snake_case`, sem
tradução para kebab-case. Assim o endpoint é sempre derivável do schema:

| Tabela | URI |
|---|---|
| `jogos` | `/api/jogos` |
| `jogos_plataformas` | `/api/jogos_plataformas` |
| `biblioteca_usuario` | `/api/biblioteca_usuario` |
| `bugometro_status` | `/api/bugometro_status` |
| `curtidas_avaliacoes` | `/api/curtidas_avaliacoes` |

Duas tabelas do DDL têm nome no singular (`biblioteca_usuario`,
`bugometro_status`). Mantemos o nome do DDL em vez de pluralizar, porque
divergir do schema custa mais do que a inconsistência de nomenclatura.

Todo `Route::apiResource` declara `->parameters()` explicitamente, pelo mesmo
motivo de todo model declarar `$table`: o pluralizador/singularizador do
Eloquent é inglês e erra nos nomes em português. `apiResource` usa esse mesmo
inflector para derivar o parâmetro de rota do route-model binding a partir do
nome do recurso — sem declarar explicitamente, `avaliacoes` viraria
`{avaliaco}`, `notificacoes` viraria `{notificaco}` e `curtidas_avaliacoes`
viraria `{curtidas_avaliaco}`, quebrando o binding com um erro de container
em vez de um 404 limpo. Não se depende de acerto acidental, o mesmo raciocínio
de `$table`:

```php
Route::apiResource('jogos', JogoController::class)
    ->parameters(['jogos' => 'jogo']);
```

Todos os controllers estendem `App\Http\Controllers\Controller`.

## 5. Modelo de dados

Tipos abaixo já traduzidos para Schema Builder. Toda FK usa
`foreignId(...)->constrained('tabela')->cascadeOnDelete()`, que também cria o
índice — cobrindo os três `CREATE INDEX` do DDL original.

### Fase 1 — Núcleo

**`usuarios`** — `nome_usuario` string(50) unique, `email` string(100) unique,
`senha_hash` string(255), `idade` integer nullable, `avatar_url` text nullable,
`bio` text nullable, `nivel` integer default 1.

**`jogos`** — `nome` string(100), `descricao` text nullable, `genero`
string(50) nullable, `classificacao` string(10) nullable, `desenvolvedora`
string(100) nullable, `data_lancamento` date nullable, `capa_url` text
nullable.

**`plataformas`** — `nome` string(50).

### Fase 2 — Relações jogo ↔ usuário

**`jogos_plataformas`** — `jogo_id` FK, `plataforma_id` FK, unique do par.

**`biblioteca_usuario`** — `usuario_id` FK, `jogo_id` FK, `favorito` boolean
default false, unique do par. `CREATED_AT = 'adicionado_em'`.

**`avaliacoes`** — `usuario_id` FK, `jogo_id` FK, `nota` decimal(2,1) nullable,
`comentario` text nullable.

**`curtidas_avaliacoes`** — `avaliacao_id` FK, `usuario_id` FK, unique do par.

### Fase 3 — Bugômetro

**`bugometro_status`** — `jogo_id` FK **unique** (relação 1:1 com jogo),
`pontuacao` integer nullable, `status` string(20) nullable.

**`metricas_bug`** — `jogo_id` FK, `tipo` string(20), `severidade` string(20),
`porcentagem` integer.

**`relatos_bug`** — `jogo_id` FK, `titulo` string(100), `descricao` text,
`severidade` string(20), `origem` string(50).

**`historico_bug`** — `jogo_id` FK, `quantidade_crash` integer,
`quantidade_bug` integer, `quantidade_fps_drop` integer,
`quantidade_stutter` integer. `CREATED_AT = 'registrado_em'`.

### Fase 4 — Fórum

**`categorias`** — `nome` string(50).

**`topicos`** — `usuario_id` FK, `categoria_id` FK, `titulo` string(100).

**`posts`** — `topico_id` FK, `usuario_id` FK, `conteudo` text.

### Fase 5 — Gamificação e feed

**`badges`** — `nome` string(50), `icone_url` text nullable.

**`usuarios_badges`** — `usuario_id` FK, `badge_id` FK, unique do par.
`CREATED_AT = 'conquistado_em'`.

**`notificacoes`** — `usuario_id` FK, `mensagem` text, `lida` boolean default
false.

**`atividades`** — `usuario_id` FK, `tipo` string(50), `referencia_id` integer
nullable.

### 5.1 Relacionamentos Eloquent

| Model | Relação | Alvo |
|---|---|---|
| `Usuario` | hasMany | `avaliacoes`, `topicos`, `posts`, `notificacoes`, `atividades` |
| `Usuario` | belongsToMany | `jogos` (via `biblioteca_usuario`), `badges` (via `usuarios_badges`) |
| `Jogo` | belongsToMany | `plataformas` (via `jogos_plataformas`) |
| `Jogo` | hasMany | `avaliacoes`, `metricas_bug`, `relatos_bug`, `historico_bug` |
| `Jogo` | hasOne | `bugometro_status` |
| `Avaliacao` | belongsTo | `Usuario`, `Jogo` |
| `Avaliacao` | hasMany | `curtidas_avaliacoes` |
| `Topico` | belongsTo | `Usuario`, `Categoria` |
| `Topico` | hasMany | `posts` |
| `Post` | belongsTo | `Topico`, `Usuario` |

Relacionamentos são declarados junto com o Model da fase correspondente. Um
relacionamento cujo alvo ainda não existe é adicionado na fase que cria o alvo.

## 6. Testes

Cada recurso ganha um teste de feature em `tests/Feature/` cobrindo os cinco
endpoints e os caminhos de erro:

- `index` retorna 200 e a lista
- `store` válido retorna 201 e persiste
- `store` inválido retorna 422
- `show` retorna 200; ID inexistente retorna 404
- `update` retorna 200 e persiste; ID inexistente retorna 404
- `destroy` retorna 204 e remove; ID inexistente retorna 404
- `senha_hash` nunca aparece no JSON (apenas em `usuarios`)

Testes usam `RefreshDatabase` sobre SQLite in-memory. Cada entidade ganha uma
Factory em `database/factories/`.

Fase alguma é dada por concluída com `php artisan test` vermelho.

## 7. Fases

| Fase | Entidades | Entrega |
|---|---|---|
| **0** | — | git, `.env` dual, remoção de `Product` e `users`, `Usuario` como model de auth |
| **1** | `usuarios`, `jogos`, `plataformas` | Núcleo do catálogo — 3 CRUDs |
| **2** | `jogos_plataformas`, `biblioteca_usuario`, `avaliacoes`, `curtidas_avaliacoes` | Biblioteca, favoritos e reviews |
| **3** | `bugometro_status`, `metricas_bug`, `relatos_bug`, `historico_bug` | Bugômetro |
| **4** | `categorias`, `topicos`, `posts` | Fórum |
| **5** | `badges`, `usuarios_badges`, `notificacoes`, `atividades` | Gamificação e feed |

Um commit por entidade; cada fase fecha com a suíte verde.

## 8. Fora de escopo

Autenticação e autorização (Sanctum, policies), paginação, API Resources /
transformers, filtros e busca, soft deletes, rate limiting, cálculo automático
do Bugômetro a partir das métricas, frontend e build Vite, deploy.

`bugometro_status`, `metricas_bug` e `historico_bug` são CRUDs simples nesta
entrega — a lógica que os alimentaria automaticamente é trabalho futuro.
