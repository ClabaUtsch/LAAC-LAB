"""Schemas de usuário e autenticação."""
from datetime import date

from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from app.models import Usuario
from app.schemas.base import SchemaBase, SchemaEntradaBase
from app.services.cpf import cpf_valido, limpar_cpf


def calcular_idade(data_nasci: date, hoje: date | None = None) -> int:
    hoje = hoje or date.today()
    return hoje.year - data_nasci.year - (
        (hoje.month, hoje.day) < (data_nasci.month, data_nasci.day)
    )


def validar_idade(data_nasci):
    if calcular_idade(data_nasci) < 16:
        raise ValidationError(
            "É necessário ter pelo menos 16 anos para criar uma conta."
        )


def validar_cpf_campo(valor):
    if not cpf_valido(valor):
        raise ValidationError("CPF inválido.")
    return limpar_cpf(valor)


class UsuarioSchema(SchemaBase):
    class Meta(SchemaBase.Meta):
        model = Usuario
        exclude = (
            "senha_hash",
            "email",
            "senha_alterada_em",
            "versao_sessao",
            "cpf",
        )


class UsuarioEntradaSchema(SchemaEntradaBase):
    """Perfil editável. Idade/CPF/nascimento não entram: não dá para mudar
    idade nas configurações; `is_admin` continua loadável e o Service
    bloqueia quem não é admin via `campos_de_admin`."""

    class Meta(SchemaEntradaBase.Meta):
        model = Usuario
        exclude = (
            "senha_hash",
            "cpf",
            "data_nascimento",
            "idade",
            "aceite_termos_em",
            "ultimo_dia_ativo",
            "email_verificado",
        )
        dump_only = (
            "id",
            "criado_em",
            "atualizado_em",
            "senha_alterada_em",
            "versao_sessao",
            "nivel",
            "xp",
            "xp_max",
            "conquistas",
            "amigos",
            "dias_ativo",
            "nome_usuario",
            "email",
        )


class RegistroSchema(Schema):
    nome_usuario = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True, validate=validate.Length(max=100))
    data_nascimento = fields.Date(
        required=True,
        validate=validar_idade,
        error_messages={"required": "A data de nascimento é obrigatória."},
    )
    cpf = fields.Str(required=True, validate=validar_cpf_campo)
    senha = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    apelido = fields.Str(load_default="", validate=validate.Length(max=50))
    bio = fields.Str(load_default="", validate=validate.Length(max=280))
    aceite_termos = fields.Bool(required=True)

    @validates_schema
    def exigir_termos(self, dados, **_kwargs):
        if not dados.get("aceite_termos"):
            raise ValidationError(
                {"aceite_termos": ["É obrigatório aceitar os termos de uso."]}
            )


class LoginSchema(Schema):
    """``identificador`` aceita nome_usuario OU email."""

    identificador = fields.Str(required=True, validate=validate.Length(min=3))
    senha = fields.Str(required=True)


class PedidoRecuperacaoSchema(Schema):
    email = fields.Email(required=True)


class RedefinirSenhaSchema(Schema):
    token = fields.Str(required=True, validate=validate.Length(min=20, max=200))
    senha_nova = fields.Str(required=True, validate=validate.Length(min=8, max=128))
