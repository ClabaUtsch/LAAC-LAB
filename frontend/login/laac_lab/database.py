"""
=============================================================================
  LaaC_Lab — SQLite Database Module para Flask
=============================================================================
  Autor   : Conversão do modelo MySQL (bd_laa_c_lab_corrigido.sql)
  Engine  : SQLite 3 via módulo nativo do Python (sqlite3)
  ORM     : Sem ORM — SQL puro com helper functions
  
  ESTRUTURA:
    ├─ get_db()          → conexão com Row factory (acesso por nome de coluna)
    ├─ close_db()        → fecha a conexão ao fim do request
    ├─ init_db()         → cria todas as tabelas, índices e triggers
    ├─ seed_db()         → insere dados de domínio iniciais
    └─ init_app(app)     → registra tudo no app Flask
    
  DECISÕES DE DESIGN:
    • FOREIGN KEYS ativas via PRAGMA em cada conexão (SQLite desliga por padrão)
    • ENUM substituído por TEXT + CHECK → portabilidade e legibilidade
    • AUTOINCREMENT só onde id nunca pode ser reutilizado (histórico, avaliação)
    • Triggers para manter bugometro atualizado automaticamente
    • Índices explícitos em todas as FKs de tabelas grandes (bug, relato, histórico)
    • WAL mode ativo → melhor concorrência de leitura em APIs Flask
=============================================================================
"""

import sqlite3
import click
from flask import current_app, g


# ─────────────────────────────────────────────
#  CONEXÃO
# ─────────────────────────────────────────────

def get_db():
    """
    Retorna a conexão SQLite vinculada ao contexto do request Flask (g).
    Cria a conexão na primeira chamada do request e a reutiliza nas demais.
    
    Configurações importantes:
    - Row factory: permite acesso por nome de coluna (row['nome'] em vez de row[0])
    - PRAGMA foreign_keys: ativa integridade referencial (OFF por padrão no SQLite)
    - PRAGMA journal_mode WAL: Write-Ahead Logging — melhora concorrência de leitura
    - PRAGMA synchronous NORMAL: equilibrio entre segurança e performance
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES  # suporte a tipos Python nativos
        )
        g.db.row_factory = sqlite3.Row   # linhas acessíveis como dicionários

        # Configurações de performance e integridade
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA journal_mode = WAL")
        g.db.execute("PRAGMA synchronous = NORMAL")
        g.db.execute("PRAGMA temp_store = MEMORY")
        g.db.execute("PRAGMA cache_size = -16000")  # ~16 MB de cache

    return g.db


def close_db(e=None):
    """Remove a conexão do contexto g e fecha. Chamado pelo teardown do Flask."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ─────────────────────────────────────────────
#  DDL — CRIAÇÃO DAS TABELAS
# ─────────────────────────────────────────────

SCHEMA_SQL = """
-- ══════════════════════════════════════════════════
--  TABELAS DE DOMÍNIO (lookup tables — sem FKs)
-- ══════════════════════════════════════════════════

-- Severidade de um bug: baixa | media | alta | critica
CREATE TABLE IF NOT EXISTS severidade_bug (
    id   INTEGER PRIMARY KEY,
    nome TEXT    NOT NULL UNIQUE
);

-- Status do ciclo de vida de um bug
CREATE TABLE IF NOT EXISTS status_bug (
    id   INTEGER PRIMARY KEY,
    nome TEXT    NOT NULL UNIQUE
);

-- Classificação de qualidade calculada pelo bugômetro
CREATE TABLE IF NOT EXISTS qualidade_bugometro (
    id   INTEGER PRIMARY KEY,
    nome TEXT    NOT NULL UNIQUE
);

-- ══════════════════════════════════════════════════
--  ENTIDADES PRINCIPAIS
-- ══════════════════════════════════════════════════

-- Usuário da plataforma
CREATE TABLE IF NOT EXISTS usuario (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_usuario     TEXT    NOT NULL UNIQUE,
    email            TEXT    NOT NULL UNIQUE,
    senha            TEXT    NOT NULL,          -- hash (werkzeug)
    data_nascimento  TEXT    NOT NULL,          -- formato ISO 8601: YYYY-MM-DD
    status           TEXT    NOT NULL DEFAULT 'ativo'
                             CHECK (status IN ('ativo', 'inativo')),
    criado_em        TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Empresa/estúdio que desenvolveu o jogo
CREATE TABLE IF NOT EXISTS desenvolvedora (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT    NOT NULL UNIQUE
);

-- Jogo cadastrado na plataforma
CREATE TABLE IF NOT EXISTS jogo (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nome             TEXT    NOT NULL,
    desenvolvedora_id INTEGER NOT NULL,
    criado_em        TEXT    NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (desenvolvedora_id)
        REFERENCES desenvolvedora(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- Gênero de jogo (ação, RPG, estratégia, etc.)
CREATE TABLE IF NOT EXISTS genero (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT    NOT NULL UNIQUE
);

-- Plataforma de jogo (PC, PS5, Xbox, Switch, etc.)
CREATE TABLE IF NOT EXISTS plataforma (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT    NOT NULL UNIQUE
);

-- ══════════════════════════════════════════════════
--  TABELAS ASSOCIATIVAS (N:N)
-- ══════════════════════════════════════════════════

-- Um jogo pode ter múltiplos gêneros
CREATE TABLE IF NOT EXISTS jogo_genero (
    jogo_id   INTEGER NOT NULL,
    genero_id INTEGER NOT NULL,

    PRIMARY KEY (jogo_id, genero_id),
    FOREIGN KEY (jogo_id)   REFERENCES jogo(id)   ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (genero_id) REFERENCES genero(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Um jogo pode estar em múltiplas plataformas
CREATE TABLE IF NOT EXISTS jogo_plataforma (
    jogo_id      INTEGER NOT NULL,
    plataforma_id INTEGER NOT NULL,

    PRIMARY KEY (jogo_id, plataforma_id),
    FOREIGN KEY (jogo_id)      REFERENCES jogo(id)      ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (plataforma_id) REFERENCES plataforma(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Biblioteca pessoal: jogos que o usuário possui
CREATE TABLE IF NOT EXISTS biblioteca_usuario (
    usuario_id   INTEGER NOT NULL,
    jogo_id      INTEGER NOT NULL,
    adicionado_em TEXT   NOT NULL DEFAULT (datetime('now')),

    PRIMARY KEY (usuario_id, jogo_id),
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (jogo_id)    REFERENCES jogo(id)    ON DELETE CASCADE ON UPDATE CASCADE
);

-- ══════════════════════════════════════════════════
--  SISTEMA DE BUGS
-- ══════════════════════════════════════════════════

-- Bug reportado em um jogo
CREATE TABLE IF NOT EXISTS bug (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    jogo_id      INTEGER NOT NULL,
    titulo       TEXT    NOT NULL,
    descricao    TEXT,
    severidade_id INTEGER NOT NULL,
    status_id    INTEGER NOT NULL,
    criado_em    TEXT    NOT NULL DEFAULT (datetime('now')),
    atualizado_em TEXT   NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (jogo_id)      REFERENCES jogo(id)          ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (severidade_id) REFERENCES severidade_bug(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (status_id)    REFERENCES status_bug(id)     ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Relato de um usuário sobre um bug específico
CREATE TABLE IF NOT EXISTS relato_bug (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    bug_id     INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    descricao  TEXT,
    criado_em  TEXT    NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (bug_id)     REFERENCES bug(id)     ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Histórico de mudanças de status de um bug (audit trail)
-- AUTOINCREMENT aqui garante que IDs nunca sejam reutilizados (importante para auditoria)
CREATE TABLE IF NOT EXISTS historico_bug (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    bug_id             INTEGER NOT NULL,
    status_anterior_id INTEGER,          -- NULL se é a criação inicial do bug
    status_novo_id     INTEGER,
    alterado_em        TEXT    NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (bug_id)             REFERENCES bug(id)      ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (status_anterior_id) REFERENCES status_bug(id),
    FOREIGN KEY (status_novo_id)     REFERENCES status_bug(id)
);

-- ══════════════════════════════════════════════════
--  BUGÔMETRO — Resumo de qualidade por jogo
-- ══════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS bugometro (
    jogo_id      INTEGER PRIMARY KEY,   -- 1:1 com jogo
    total_bugs   INTEGER NOT NULL DEFAULT 0,
    bugs_criticos INTEGER NOT NULL DEFAULT 0,
    qualidade_id INTEGER,
    atualizado_em TEXT   NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (jogo_id)     REFERENCES jogo(id)               ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (qualidade_id) REFERENCES qualidade_bugometro(id)
);

-- ══════════════════════════════════════════════════
--  AVALIAÇÕES E CURTIDAS
-- ══════════════════════════════════════════════════

-- Avaliação de um jogo por um usuário (1 por par usuario+jogo)
CREATE TABLE IF NOT EXISTS avaliacao (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    jogo_id    INTEGER NOT NULL,
    nota       INTEGER NOT NULL CHECK (nota BETWEEN 0 AND 10),
    comentario TEXT,
    criado_em  TEXT    NOT NULL DEFAULT (datetime('now')),

    UNIQUE (usuario_id, jogo_id),   -- cada usuário avalia cada jogo uma única vez
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (jogo_id)    REFERENCES jogo(id)    ON DELETE CASCADE ON UPDATE CASCADE
);

-- Curtida em uma avaliação (um usuário por avaliação)
CREATE TABLE IF NOT EXISTS curtida_avaliacao (
    avaliacao_id INTEGER NOT NULL,
    usuario_id   INTEGER NOT NULL,

    PRIMARY KEY (avaliacao_id, usuario_id),
    FOREIGN KEY (avaliacao_id) REFERENCES avaliacao(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (usuario_id)   REFERENCES usuario(id)   ON DELETE CASCADE ON UPDATE CASCADE
);

-- ══════════════════════════════════════════════════
--  FÓRUM
-- ══════════════════════════════════════════════════

-- Tópico criado por um usuário no fórum
CREATE TABLE IF NOT EXISTS topico (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    titulo     TEXT    NOT NULL,
    criado_em  TEXT    NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Resposta a um tópico do fórum
CREATE TABLE IF NOT EXISTS resposta_topico (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    topico_id  INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    conteudo   TEXT    NOT NULL,
    criado_em  TEXT    NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (topico_id)  REFERENCES topico(id)   ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)  ON DELETE CASCADE ON UPDATE CASCADE
);
"""

# ─────────────────────────────────────────────
#  DDL — ÍNDICES
# ─────────────────────────────────────────────
# Criados separadamente (SQLite não suporta INDEX dentro do CREATE TABLE)
# Cobrem todas as chaves estrangeiras + colunas de filtro/ordenação frequentes

INDEXES_SQL = """
-- Índices em jogo
CREATE INDEX IF NOT EXISTS idx_jogo_desenvolvedora  ON jogo(desenvolvedora_id);
CREATE INDEX IF NOT EXISTS idx_jogo_criado_em       ON jogo(criado_em);

-- Índices em bug (tabela mais consultada da aplicação)
CREATE INDEX IF NOT EXISTS idx_bug_jogo             ON bug(jogo_id);
CREATE INDEX IF NOT EXISTS idx_bug_status           ON bug(status_id);
CREATE INDEX IF NOT EXISTS idx_bug_severidade       ON bug(severidade_id);
CREATE INDEX IF NOT EXISTS idx_bug_criado_em        ON bug(criado_em);
-- Índice composto: filtragem por jogo + status (query mais comum na API)
CREATE INDEX IF NOT EXISTS idx_bug_jogo_status      ON bug(jogo_id, status_id);

-- Índices em relato_bug
CREATE INDEX IF NOT EXISTS idx_relato_bug           ON relato_bug(bug_id);
CREATE INDEX IF NOT EXISTS idx_relato_usuario       ON relato_bug(usuario_id);

-- Índices em historico_bug
CREATE INDEX IF NOT EXISTS idx_historico_bug        ON historico_bug(bug_id);
CREATE INDEX IF NOT EXISTS idx_historico_alterado   ON historico_bug(alterado_em);

-- Índices em avaliacao
CREATE INDEX IF NOT EXISTS idx_avaliacao_jogo       ON avaliacao(jogo_id);
CREATE INDEX IF NOT EXISTS idx_avaliacao_usuario    ON avaliacao(usuario_id);
CREATE INDEX IF NOT EXISTS idx_avaliacao_nota       ON avaliacao(nota);

-- Índices em curtida_avaliacao
CREATE INDEX IF NOT EXISTS idx_curtida_avaliacao    ON curtida_avaliacao(avaliacao_id);

-- Índices em topico / resposta
CREATE INDEX IF NOT EXISTS idx_topico_usuario       ON topico(usuario_id);
CREATE INDEX IF NOT EXISTS idx_topico_criado_em     ON topico(criado_em);
CREATE INDEX IF NOT EXISTS idx_resposta_topico      ON resposta_topico(topico_id);
CREATE INDEX IF NOT EXISTS idx_resposta_usuario     ON resposta_topico(usuario_id);

-- Índices em biblioteca_usuario
CREATE INDEX IF NOT EXISTS idx_biblioteca_jogo      ON biblioteca_usuario(jogo_id);
"""

# ─────────────────────────────────────────────
#  DDL — TRIGGERS
# ─────────────────────────────────────────────
# O bugômetro é mantido automaticamente pelos triggers abaixo,
# eliminando a necessidade de lógica de negócio na API para essa tarefa.

TRIGGERS_SQL = """
-- ── Trigger 1: Atualiza bugômetro ao INSERIR um bug ──────────────────────────
CREATE TRIGGER IF NOT EXISTS trg_bug_insert
AFTER INSERT ON bug
BEGIN
    -- Garante que o bugômetro existe para o jogo
    INSERT OR IGNORE INTO bugometro (jogo_id, total_bugs, bugs_criticos)
    VALUES (NEW.jogo_id, 0, 0);

    -- Incrementa total e bugs_criticos (se severidade for a última — id 4 = critica)
    UPDATE bugometro
    SET
        total_bugs    = total_bugs + 1,
        bugs_criticos = bugs_criticos + (
            SELECT CASE WHEN NEW.severidade_id = s.id THEN 1 ELSE 0 END
            FROM severidade_bug s WHERE s.nome = 'critica'
        ),
        qualidade_id  = (
            SELECT q.id FROM qualidade_bugometro q
            WHERE q.nome = CASE
                WHEN (bugs_criticos + (SELECT CASE WHEN NEW.severidade_id = s.id THEN 1 ELSE 0 END
                                       FROM severidade_bug s WHERE s.nome = 'critica')) > 10 THEN 'ruim'
                WHEN (bugs_criticos + (SELECT CASE WHEN NEW.severidade_id = s.id THEN 1 ELSE 0 END
                                       FROM severidade_bug s WHERE s.nome = 'critica')) > 5  THEN 'regular'
                WHEN (total_bugs + 1) > 20 THEN 'bom'
                ELSE 'excelente'
            END
        ),
        atualizado_em = datetime('now')
    WHERE jogo_id = NEW.jogo_id;
END;

-- ── Trigger 2: Atualiza bugômetro ao DELETAR um bug ──────────────────────────
CREATE TRIGGER IF NOT EXISTS trg_bug_delete
AFTER DELETE ON bug
BEGIN
    UPDATE bugometro
    SET
        total_bugs    = MAX(0, total_bugs - 1),
        bugs_criticos = MAX(0, bugs_criticos - (
            SELECT CASE WHEN OLD.severidade_id = s.id THEN 1 ELSE 0 END
            FROM severidade_bug s WHERE s.nome = 'critica'
        )),
        atualizado_em = datetime('now')
    WHERE jogo_id = OLD.jogo_id;
END;

-- ── Trigger 3: Grava histórico ao mudar status de um bug ─────────────────────
CREATE TRIGGER IF NOT EXISTS trg_bug_status_change
AFTER UPDATE OF status_id ON bug
WHEN OLD.status_id != NEW.status_id
BEGIN
    INSERT INTO historico_bug (bug_id, status_anterior_id, status_novo_id)
    VALUES (NEW.id, OLD.status_id, NEW.status_id);

    -- Atualiza timestamp do bug
    UPDATE bug SET atualizado_em = datetime('now') WHERE id = NEW.id;
END;
"""

# ─────────────────────────────────────────────
#  DADOS INICIAIS (SEED)
# ─────────────────────────────────────────────

SEED_SQL = """
-- Tabelas de domínio (INSERT OR IGNORE = idempotente, seguro re-executar)
INSERT OR IGNORE INTO severidade_bug (nome) VALUES
    ('baixa'), ('media'), ('alta'), ('critica');

INSERT OR IGNORE INTO status_bug (nome) VALUES
    ('aberto'), ('em_andamento'), ('resolvido'), ('fechado');

INSERT OR IGNORE INTO qualidade_bugometro (nome) VALUES
    ('ruim'), ('regular'), ('bom'), ('excelente');
"""


# ─────────────────────────────────────────────
#  FUNÇÕES DE INICIALIZAÇÃO
# ─────────────────────────────────────────────

def init_db():
    """
    Executa todo o DDL: cria tabelas, índices e triggers.
    Seguro para executar múltiplas vezes (IF NOT EXISTS / OR IGNORE).
    """
    db = get_db()
    # Executar scripts separados (executescript não está dentro de transação automática)
    db.executescript(SCHEMA_SQL)
    db.executescript(INDEXES_SQL)
    db.executescript(TRIGGERS_SQL)
    db.commit()


def seed_db():
    """
    Insere os dados de domínio iniciais.
    Usa INSERT OR IGNORE — não duplica se já existir.
    """
    db = get_db()
    db.executescript(SEED_SQL)
    db.commit()


# ─────────────────────────────────────────────
#  CLI COMMANDS (flask init-db / flask seed-db)
# ─────────────────────────────────────────────

@click.command('init-db')
def init_db_command():
    """Cria todas as tabelas, índices e triggers do banco de dados."""
    init_db()
    click.echo('✅ Banco de dados inicializado com sucesso.')


@click.command('seed-db')
def seed_db_command():
    """Insere os dados de domínio iniciais (severidade, status, qualidade)."""
    seed_db()
    click.echo('✅ Dados iniciais inseridos com sucesso.')


# ─────────────────────────────────────────────
#  REGISTRO NO APP FLASK
# ─────────────────────────────────────────────

def init_app(app):
    """
    Registra o módulo de banco de dados no app Flask:
    - teardown: fecha a conexão ao final de cada request
    - CLI: comandos `flask init-db` e `flask seed-db`
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command)
