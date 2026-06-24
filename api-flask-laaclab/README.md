# LaaC_lab API — Bugômetro 🎮🐛

API REST em **Flask + SQLAlchemy** para a plataforma *Bugômetro*: catálogo de
jogos, avaliações, fórum, badges, notificações e o módulo central de métricas
de bugs.

- **Dev:** SQLite (zero configuração)
- **Prod:** MySQL/MariaDB (PyMySQL)
- Troca automática pelo `FLASK_ENV` no `.env`
- Autenticação **JWT** com senha hasheada (Werkzeug)
- CRUD completo para todas as entidades + paginação

---

## 📁 Estrutura

```
api-flask/
├── app/
│   ├── __init__.py      # application factory
│   ├── extensions.py    # db, migrate, jwt, marshmallow
│   ├── models.py        # todos os models (18 tabelas)
│   ├── schemas.py       # serialização/validação (Marshmallow)
│   ├── crud.py          # fábrica genérica de blueprints CRUD
│   ├── auth.py          # register / login / me (JWT)
│   ├── usuarios.py      # CRUD de usuários (com regras de senha/dono)
│   ├── routes.py        # registro de todos os blueprints
│   └── seed.py          # comandos CLI: init-db, seed-db
├── config.py            # DevelopmentConfig / ProductionConfig / TestingConfig
├── wsgi.py              # ponto de entrada
├── requirements.txt
├── .env.example         # copie para .env
├── .flaskenv            # FLASK_APP=wsgi.py
└── README.md
```

---

## 🚀 Começando

### 1. Ambiente virtual + dependências

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Variáveis de ambiente

```powershell
Copy-Item .env.example .env
# edite .env se necessário (chaves secretas, credenciais MySQL...)
```

### 3. Criar e popular o banco

```powershell
flask init-db    # cria as tabelas
flask seed-db    # insere dados de exemplo (opcional)
```

> O seed cria dois usuários:
> - `admin` / `admin123`
> - `jogador1` / `senha123`

### 4. Rodar

```powershell
python wsgi.py
# API em http://127.0.0.1:5000
```

Health check: `GET http://127.0.0.1:5000/health`

---

## 🔁 Alternar Dev ↔ Prod

No `.env`:

```ini
# Desenvolvimento (SQLite)
FLASK_ENV=development

# Produção (MySQL) — preencha as credenciais MYSQL_*
FLASK_ENV=production
```

Em produção, use um servidor WSGI real:

```bash
gunicorn "wsgi:app" --bind 0.0.0.0:8000
```

> ⚠️ **Produção:** gere chaves fortes para `SECRET_KEY` e `JWT_SECRET_KEY`
> (mínimo 32 bytes). Ex.: `python -c "import secrets; print(secrets.token_hex(32))"`

---

## 🔐 Autenticação

| Método | Rota                  | Descrição                                  |
|--------|-----------------------|--------------------------------------------|
| POST   | `/api/auth/register`  | Cria usuário, retorna `usuario` + `access_token` |
| POST   | `/api/auth/login`     | Login por `identificador` (nome ou email)  |
| GET    | `/api/auth/me`        | Dados do usuário logado (requer token)     |

**Registro**

```http
POST /api/auth/register
Content-Type: application/json

{
  "nome_usuario": "maria_qa",
  "email": "maria@laac.dev",
  "senha": "segura123",
  "idade": 28
}
```

**Login**

```http
POST /api/auth/login
Content-Type: application/json

{ "identificador": "maria_qa", "senha": "segura123" }
```

Use o token nas rotas protegidas:

```http
Authorization: Bearer <access_token>
```

---

## 📚 Recursos CRUD

Leitura (`GET`) é **pública**; escrita (`POST`/`PUT`/`PATCH`/`DELETE`) **exige JWT**.

| Recurso             | Prefixo                    |
|---------------------|----------------------------|
| Usuários            | `/api/usuarios`            |
| Jogos               | `/api/jogos`               |
| Plataformas         | `/api/plataformas`         |
| Jogos × Plataformas | `/api/jogos-plataformas`   |
| Biblioteca          | `/api/biblioteca`          |
| Avaliações          | `/api/avaliacoes`          |
| Curtidas            | `/api/curtidas`            |
| **Bugômetro**       | `/api/bugometro`           |
| Métricas de bug     | `/api/metricas`            |
| Relatos de bug      | `/api/relatos`             |
| Histórico de bug    | `/api/historico`           |
| Categorias (fórum)  | `/api/categorias`          |
| Tópicos             | `/api/topicos`             |
| Posts               | `/api/posts`               |
| Badges              | `/api/badges`              |
| Usuários × Badges   | `/api/usuarios-badges`     |
| Notificações        | `/api/notificacoes`        |
| Atividades          | `/api/atividades`          |

### Operações padrão (exemplo: `jogos`)

| Método        | Rota                | Auth | Descrição                |
|---------------|---------------------|------|--------------------------|
| GET           | `/api/jogos`        | —    | Lista (paginada)         |
| GET           | `/api/jogos/<id>`   | —    | Detalhe                  |
| POST          | `/api/jogos`        | ✅   | Cria                     |
| PUT / PATCH   | `/api/jogos/<id>`   | ✅   | Atualiza (parcial)       |
| DELETE        | `/api/jogos/<id>`   | ✅   | Remove                   |

**Paginação:** `?page=1&per_page=20` (máx. 100 por página). Resposta:

```json
{
  "items": [ ... ],
  "page": 1,
  "per_page": 20,
  "total": 42,
  "pages": 3
}
```

### Exemplo: criar um relato de bug

```http
POST /api/relatos
Authorization: Bearer <token>
Content-Type: application/json

{
  "jogo_id": 1,
  "titulo": "Crash ao salvar",
  "descricao": "O jogo fecha ao salvar na fase 3.",
  "severidade": "alta",
  "origem": "usuario"
}
```

---

## 👤 Regras especiais de usuário

- Criação de usuário é feita **apenas** via `/api/auth/register` (a senha é
  hasheada). Não há `POST /api/usuarios`.
- `PUT/PATCH/DELETE /api/usuarios/<id>` só funcionam para o **próprio usuário**
  (o `id` do token precisa bater com o da rota), retornando `403` caso contrário.
- Se um `PUT` de usuário incluir o campo `senha`, ela é **re-hasheada**
  (nunca gravada em texto puro).

---

## 🧪 Migrations (opcional)

Para evoluir o schema com Flask-Migrate / Alembic:

```powershell
flask db init        # primeira vez
flask db migrate -m "mensagem"
flask db upgrade
```

> Para começar do zero, `flask init-db` (db.create_all) já basta.

---

## 📦 Respostas de erro

| Código | Significado                              |
|--------|------------------------------------------|
| 400    | Requisição malformada                    |
| 401    | Token ausente/inválido/expirado          |
| 403    | Sem permissão (ex.: editar outro usuário)|
| 404    | Recurso não encontrado                   |
| 409    | Conflito (nome_usuario/email já em uso)  |
| 422    | Erro de validação (corpo inválido)       |

Corpo de erro padrão:

```json
{ "erro": "mensagem" }
```

ou, para validação:

```json
{ "erros": { "campo": ["mensagem"] } }
```
