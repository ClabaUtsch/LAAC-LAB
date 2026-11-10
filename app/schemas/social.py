"""Schemas de badges, notificações, atividades e amizades."""
from marshmallow import Schema, fields, validate

from app.models import Amizade, Atividade, Badge, Notificacao, UsuarioBadge
from app.schemas.base import SchemaBase, SchemaEntradaBase


class BadgeSchema(SchemaBase):
    class Meta(SchemaBase.Meta):
        model = Badge


class BadgeEntradaSchema(SchemaEntradaBase):
    nome = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    codigo = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=40))

    class Meta(SchemaEntradaBase.Meta):
        model = Badge


class AmizadeSchema(SchemaBase):
    class Meta(SchemaBase.Meta):
        model = Amizade


class PedidoAmizadeSchema(Schema):
    destinatario_id = fields.Int(required=True)


class RespostaAmizadeSchema(Schema):
    aceitar = fields.Bool(required=True)


class UsuarioBadgeSchema(SchemaBase):
    class Meta(SchemaBase.Meta):
        model = UsuarioBadge


class UsuarioBadgeEntradaSchema(SchemaEntradaBase):
    badge_id = fields.Int(required=True)

    class Meta(SchemaEntradaBase.Meta):
        model = UsuarioBadge
        dump_only = ("id", "conquistado_em")


class NotificacaoSchema(SchemaBase):
    class Meta(SchemaBase.Meta):
        model = Notificacao


class NotificacaoEntradaSchema(SchemaEntradaBase):
    mensagem = fields.Str(required=True, validate=validate.Length(min=1))

    class Meta(SchemaEntradaBase.Meta):
        model = Notificacao
        dump_only = ("id", "criado_em")


class AtividadeSchema(SchemaBase):
    class Meta(SchemaBase.Meta):
        model = Atividade


class AtividadeEntradaSchema(SchemaEntradaBase):
    tipo = fields.Str(required=True, validate=validate.Length(min=1, max=50))

    class Meta(SchemaEntradaBase.Meta):
        model = Atividade
        dump_only = ("id", "criado_em")
