import itertools

import pytest

from app import create_app
from app.extensions import db as _db
from config import TestingConfig

_contador_cpf = itertools.count(1)


def cpf_valido_de(seed: int) -> str:
    base = f"{seed % 10**9:09d}"
    def dv(digitos, pesos):
        soma = sum(int(n) * p for n, p in zip(digitos, pesos))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)
    d1 = dv(base, range(10, 1, -1))
    d2 = dv(base + d1, range(11, 1, -1))
    return base + d1 + d2


def payload_registro(nome_usuario="gamer", email=None, senha="senha123", **extra):
    """Payload mínimo válido do cadastro (16+, CPF e aceite de termos)."""
    corpo = {
        "nome_usuario": nome_usuario,
        "email": email or f"{nome_usuario}@l.dev",
        "senha": senha,
        "data_nascimento": "2000-01-15",
        "cpf": cpf_valido_de(next(_contador_cpf)),
        "aceite_termos": True,
    }
    corpo.update(extra)
    return corpo


@pytest.fixture
def app():
    aplicacao = create_app(TestingConfig)
    with aplicacao.app_context():
        _db.create_all()
        yield aplicacao
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def cliente(app):
    return app.test_client()


@pytest.fixture
def sessao(app):
    return _db.session
