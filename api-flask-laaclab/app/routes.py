"""Registro centralizado de todos os blueprints CRUD da API."""
from app.auth import auth_bp
from app.crud import make_crud_blueprint
from app.usuarios import usuarios_bp
from app import models, schemas

# (nome, model, schema, prefixo)
_CRUD_RESOURCES = [
    ("jogos", models.Jogo, schemas.JogoSchema, "/api/jogos"),
    ("plataformas", models.Plataforma, schemas.PlataformaSchema, "/api/plataformas"),
    (
        "jogos_plataformas",
        models.JogoPlataforma,
        schemas.JogoPlataformaSchema,
        "/api/jogos-plataformas",
    ),
    (
        "biblioteca",
        models.BibliotecaUsuario,
        schemas.BibliotecaUsuarioSchema,
        "/api/biblioteca",
    ),
    ("avaliacoes", models.Avaliacao, schemas.AvaliacaoSchema, "/api/avaliacoes"),
    (
        "curtidas",
        models.CurtidaAvaliacao,
        schemas.CurtidaAvaliacaoSchema,
        "/api/curtidas",
    ),
    (
        "bugometro",
        models.BugometroStatus,
        schemas.BugometroStatusSchema,
        "/api/bugometro",
    ),
    ("metricas", models.MetricaBug, schemas.MetricaBugSchema, "/api/metricas"),
    ("relatos", models.RelatoBug, schemas.RelatoBugSchema, "/api/relatos"),
    ("historico", models.HistoricoBug, schemas.HistoricoBugSchema, "/api/historico"),
    ("categorias", models.Categoria, schemas.CategoriaSchema, "/api/categorias"),
    ("topicos", models.Topico, schemas.TopicoSchema, "/api/topicos"),
    ("posts", models.Post, schemas.PostSchema, "/api/posts"),
    ("badges", models.Badge, schemas.BadgeSchema, "/api/badges"),
    (
        "usuarios_badges",
        models.UsuarioBadge,
        schemas.UsuarioBadgeSchema,
        "/api/usuarios-badges",
    ),
    (
        "notificacoes",
        models.Notificacao,
        schemas.NotificacaoSchema,
        "/api/notificacoes",
    ),
    ("atividades", models.Atividade, schemas.AtividadeSchema, "/api/atividades"),
]


def register_blueprints(app):
    """Registra auth, usuários e todos os CRUDs no app."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(usuarios_bp)

    for name, model, schema_cls, prefix in _CRUD_RESOURCES:
        bp = make_crud_blueprint(name, model, schema_cls, prefix)
        app.register_blueprint(bp)
