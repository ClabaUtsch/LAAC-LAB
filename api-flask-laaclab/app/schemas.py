"""Schemas Marshmallow para serialização e validação de entrada.

Usamos ``SQLAlchemyAutoSchema`` para gerar a serialização a partir dos
models, e definimos schemas de entrada (``*InputSchema``) onde validações
explícitas são necessárias (auth, criação de recursos).

Todos os schemas herdam de ``_BaseSchema``, cujo ``Meta`` ativa
``include_fk=True`` — sem isso o marshmallow-sqlalchemy omite as colunas de
chave estrangeira (jogo_id, usuario_id, ...) do JsON, quebrando a API
relacional.
"""
from marshmallow import Schema, fields, validate

from app.extensions import ma
from app.models import (
    Atividade,
    Avaliacao,
    Badge,
    BibliotecaUsuario,
    BugometroStatus,
    Categoria,
    CurtidaAvaliacao,
    HistoricoBug,
    Jogo,
    JogoPlataforma,
    MetricaBug,
    Notificacao,
    Plataforma,
    Post,
    RelatoBug,
    Topico,
    Usuario,
    UsuarioBadge,
)


class _BaseSchema(ma.SQLAlchemyAutoSchema):
    """Base com configurações comuns a todos os schemas de model."""

    class Meta:
        load_instance = False
        include_fk = True  # expõe colunas FK (jogo_id, usuario_id, ...)


# ------------------------------------------------------------
# Schemas de saída (serialização) — auto-gerados dos models
# ------------------------------------------------------------
class UsuarioSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = Usuario
        exclude = ("senha_hash",)  # nunca expor o hash da senha


class JogoSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = Jogo


class PlataformaSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = Plataforma


class JogoPlataformaSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = JogoPlataforma


class BibliotecaUsuarioSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = BibliotecaUsuario


class AvaliacaoSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = Avaliacao


class CurtidaAvaliacaoSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = CurtidaAvaliacao


class BugometroStatusSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = BugometroStatus


class MetricaBugSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = MetricaBug


class RelatoBugSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = RelatoBug


class HistoricoBugSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = HistoricoBug


class CategoriaSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = Categoria


class TopicoSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = Topico


class PostSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = Post


class BadgeSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = Badge


class UsuarioBadgeSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = UsuarioBadge


class NotificacaoSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = Notificacao


class AtividadeSchema(_BaseSchema):
    class Meta(_BaseSchema.Meta):
        model = Atividade


# ------------------------------------------------------------
# Schemas de entrada (validação) — auth
# ------------------------------------------------------------
class RegisterSchema(Schema):
    nome_usuario = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True, validate=validate.Length(max=100))
    senha = fields.Str(required=True, validate=validate.Length(min=6, max=128))
    idade = fields.Int(required=False, validate=validate.Range(min=0, max=150))
    avatar_url = fields.Str(required=False)
    bio = fields.Str(required=False)


class LoginSchema(Schema):
    # Aceita login por nome_usuario OU email
    identificador = fields.Str(required=True)
    senha = fields.Str(required=True)
