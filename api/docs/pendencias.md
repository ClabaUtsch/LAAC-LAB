# Pendências para decisão pós-entrega

**Status:** aberto — a decidir **depois da Fase 5**, com o entregável completo na mão.

Este documento acumula tudo que foi encontrado durante o desenvolvimento e
deliberadamente **não** corrigido, para não interromper o fluxo das fases. Nada
aqui é bug conhecido em produção: são decisões de produto que não são minhas
para tomar, e itens técnicos cujo custo de correção não se justificava no
momento em que apareceram.

Cada item traz o que é, de onde veio, o custo de deixar como está, e o que
mudaria se for corrigido.

Atualizado até o fim da **Fase 2** (7 de 18 entidades).

---

## A. Decisões de produto

Estas dependem da sua intenção, não de análise técnica.

### A1. `nivel` é gravável por qualquer chamador

`POST /api/usuarios` e `PUT /api/usuarios/{id}` aceitam o campo `nivel`. Como
não há autenticação, qualquer um pode criar um usuário nível 9999.

**Origem:** revisão final da Fase 1.
**Custo de deixar:** quando a Fase 5 trouxer badges e feed de atividades,
`nivel` vira estado de gamificação — e o endpoint que concede nível não deveria
ser o mesmo endpoint público de cadastro. Tirar depois é breaking change no
contrato da API.
**Se corrigir:** remover `nivel` das regras de `store` e `update` no
`UsuarioController`. O default já existe em dois lugares (migration e
`$attributes` do model), então o valor continua saindo como `1`. Um teste da
Fase 1 manda `nivel => 7` de propósito e precisaria mudar.

### A2. `index` devolve a coleção inteira, sem paginação

Todos os sete recursos. Decisão explícita da spec (§4.1 e §8).

**Custo de deixar:** aceitável em catálogo. Deixa de ser teórico na Fase 3, com
`relatos_bug` e `historico_bug`, que são fluxos de métricas sem limite superior,
e já incomoda em `avaliacoes` e `curtidas_avaliacoes`.
**Se corrigir:** trocar `Model::all()` por `Model::paginate()` nos controllers
muda o formato da resposta de array para objeto com metadados — breaking change
em todos os `index`. Melhor decidir antes de a API ter consumidores.

### A3. `avaliacoes` não tem constraint de unicidade

O mesmo usuário pode avaliar o mesmo jogo quantas vezes quiser. Fiel ao DDL de
origem, e a spec §3.8 não lista essa tabela entre as que ganham `unique`.

**Custo de deixar:** nenhum, se for intencional. Há um teste travando o
comportamento como deliberado (`test_o_mesmo_usuario_pode_avaliar_o_mesmo_jogo_duas_vezes`),
justamente para ninguém "consertar" por engano.
**Se corrigir:** migration com `unique(['usuario_id', 'jogo_id'])`, regra
`Rule::unique(...)->where(...)` no controller, `completaOPar()` como nas outras
três, e o teste acima invertido.

### A4. `nota` sai como string no JSON

O cast `decimal:1` faz `8.5` virar `"8.5"` e `8` virar `"8.0"` na resposta.

**Custo de deixar:** um cliente que faça aritmética direta precisa converter.
Em compensação o formato é sempre o mesmo, com uma casa decimal.
**Se corrigir:** trocar o cast para `float` devolve número puro; três testes de
`AvaliacaoApiTest` que afirmam string precisariam mudar.

### A5. `usuario_id` chega no corpo da request

Em `biblioteca_usuario`, `avaliacoes` e `curtidas_avaliacoes` o cliente informa
quem é o usuário. Coerente com a decisão de não ter autenticação nesta entrega.

**Custo de deixar:** no dia em que Sanctum entrar, esse campo tem que vir do
usuário autenticado, não do corpo — breaking change no contrato de três
endpoints. Nada no código atual torna a autenticação mais difícil (os
controllers são finos e middleware de rota entra direto); o custo está
concentrado exatamente nesse campo.

---

## B. Itens técnicos parkados

### B1. Violação de índice único retorna 500, não 422

A spec §3.8 trata o índice único do banco como rede de segurança por trás da
validação. Não existe mapeamento de `UniqueConstraintViolationException`, então
quando a rede efetivamente pega algo, o cliente recebe 500.

**Alcançável por:** corrida entre dois POSTs idênticos simultâneos; ou qualquer
escrita futura via `Jogo::plataformas()->attach()` / `Usuario::jogos()->attach()`,
que passam ao largo da validação do controller. Nenhum dos dois existe no código
hoje.
**Se corrigir:** um único `->render()` em `bootstrap/app.php` cobre os quatro
pares únicos de uma vez.

### B2. `favorito` não tem cast no pivô

`BibliotecaUsuario` faz cast de `favorito` para boolean, mas
`Usuario::jogos()->withPivot('favorito')` não — então o mesmo campo sai como
`false`/`true` pelo endpoint e `0`/`1` pela relação.

**Custo de deixar:** nulo enquanto nada serializar `Usuario::with('jogos')`.
Vira inconsistência de contrato no dia em que algo expuser.
**Se corrigir:** uma subclasse pequena de `Pivot` com `$casts`, mais `->using()`
na relação.

### B3. `regras()` e `completaOPar()` duplicados

Três controllers (`JogoPlataforma`, `BibliotecaUsuario`, `CurtidaAvaliacao`) têm
esses dois métodos quase idênticos, mudando só os nomes dos campos.

**Gatilho combinado para extrair um trait:** `usuarios_badges`, na Fase 5 — a
quarta entidade com par único. Abstrair antes seria generalizar de três amostras
sem a quarta à vista, e a Fase 3 não acrescenta nenhuma entidade com par
composto.

### B4. `.env.example` traz credenciais concretas

`DB_DATABASE=LaaC_lab`, `DB_USERNAME=root`, senha vazia, em vez de placeholders
genéricos. São os valores que a própria spec §3.1 prescreve, e `.env.example` é
um template feito para ser editado — nenhuma credencial real exposta. Vale um
comentário dizendo que `DB_PASSWORD` precisa ser preenchida fora do ambiente
local.

### B5. Sem autenticação

Decisão explícita da spec §3.5: todos os endpoints são públicos, Sanctum fica
para fase futura. `Usuario` já estende `Authenticatable` e `config/auth.php` já
aponta para ele, então a base está pronta. Ver A5 para o custo real.

---

## C. Lacunas de cobertura de teste

Nenhuma indica comportamento quebrado — são pontos onde o código está correto
mas nada trava contra regressão.

- `ConexaoBancoTest::test_conexao_mysql_esta_disponivel` afirma apenas um default
  de fábrica do Laravel; valor quase nulo como guarda de regressão.
- O fallback de `DB_SQLITE_DATABASE` ausente para `database_path()` só foi
  verificado manualmente.
- Não há teste de duplicidade de `nome_usuario` (só de `email`), embora a
  constraint e a regra existam.
- As regras `exists:` não são exercitadas com id inexistente em
  `biblioteca_usuario` nem em `curtidas_avaliacoes`.
- A unicidade composta em update parcial é testada numa direção só em
  `biblioteca_usuario`; a simétrica foi verificada por simetria de código.
- Não há teste direto de `Usuario::avaliacoes()` (só de `Jogo::avaliacoes()`).
- Nenhum `PUT` de corpo vazio exercita diretamente o ramo "nenhum campo do par"
  de `completaOPar()`.

---

## D. Armadilhas conhecidas, para as próximas fases

Não são pendências — são coisas que custaram tempo e não deveriam custar de novo.

### D1. `bugometro_status` NÃO deve copiar o `completaOPar()`

O `jogo_id` de `bugometro_status` é único de **coluna única** (relação 1:1), não
par composto. A regra fica no próprio campo que está mudando, então o `sometimes`
pulá-la quando o campo está ausente é o comportamento **correto** ali — ausente
significa inalterado, que não pode colidir. Precisa apenas de
`regras(?BugometroStatus $existente = null)` com
`Rule::unique('bugometro_status', 'jogo_id')->ignore($existente)`, **sem
`Request` e sem `completaOPar`**. A semelhança de forma com a Fase 2 é
exatamente o que convida ao erro.

Na migration, o modificador vem antes do `constrained()`:
`$table->foreignId('jogo_id')->unique()->constrained('jogos')->cascadeOnDelete();`

### D2. Timestamps irregulares exigem acordo em três lugares

`historico_bug` usa `registrado_em` como timestamp de criação, e
`usuarios_badges` usa `conquistado_em`. Já existe precedente funcionando em
`biblioteca_usuario` com `adicionado_em`. Três lugares precisam concordar: a
coluna na migration, a constante `CREATED_AT` no model, e qualquer
`withTimestamps()` que toque na tabela.

### D3. Cascata se prova por comportamento, não por configuração

Cada FK nova merece um teste que apaga o pai e afirma que o filho sumiu. A Fase
2 quase escapou com 6 das 8 FKs cobertas — a leitura "um teste de cascata por
entidade" é o que produz o buraco. A regra certa é por FK, não por entidade.

### D4. `--filter` casa por substring

`php artisan test --filter=UsuarioApiTest` também roda `BibliotecaUsuarioApiTest`.
Quando o nome de um teste for prefixo de outro, use o caminho do arquivo.
