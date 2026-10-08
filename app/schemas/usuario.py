"""Schemas de usuário e autenticação."""
from datetime import date
from marshmallow import Schema, fields, validate, ValidationError

from app.models import Usuario
from app.schemas.base import SchemaBase, SchemaEntradaBase


def validar_idade(data_nasci):
    hoje = date.today()
    # Calcula a idade subtraindo o ano e verificando se o mês/dia do aniversário já passou este ano
    idade = hoje.year - data_nasci.year - ((hoje.month, hoje.day) < (data_nasci.month, data_nasci.day))
    
    if idade < 16:
        raise ValidationError("É necessário ter pelo menos 16 anos para criar uma conta.")


class UsuarioSchema(SchemaBase):
    class Meta(SchemaBase.Meta):
        model = Usuario
        exclude = ("senha_hash", "email", "senha_alterada_em", "versao_sessao")


class UsuarioEntradaSchema(SchemaEntradaBase):
    class Meta(SchemaEntradaBase.Meta):
        model = Usuario
        exclude = ("senha_hash",)
        dump_only = ("id", "criado_em", "atualizado_em", "senha_alterada_em", "versao_sessao")


class RegistroSchema(Schema):
    nome_usuario = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True, validate=validate.Length(max=100))
    
    # Validação de idade adicionada aqui
    data_nascimento = fields.Date(
        required=True, 
        validate=validar_idade,
        error_messages={"required": "A data de nascimento é obrigatória."}
    )
    
    senha = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    apelido = fields.Str(load_default="", validate=validate.Length(max=50))
    idade = fields.Int(load_default=None, allow_none=True)
    bio = fields.Str(load_default="", validate=validate.Length(max=280))


class LoginSchema(Schema):
    """``identificador`` aceita nome_usuario OU email."""

    identificador = fields.Str(required=True, validate=validate.Length(min=3))
    senha = fields.Str(required=True)