"""Autenticação: registro, login, recuperação de senha e carga do usuário."""
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from marshmallow import ValidationError

from app.errors import Conflito, DadosInvalidos, NaoAutorizado
from app.repositories.social_repository import RepositorioRecuperacao
from app.schemas.usuario import (
    LoginSchema,
    PedidoRecuperacaoSchema,
    RedefinirSenhaSchema,
    RegistroSchema,
    calcular_idade,
)
from app.services.cpf import limpar_cpf


@dataclass(frozen=True)
class UsuarioAutenticado:
    id: int
    is_admin: bool


class AuthService:
    def __init__(self, repositorio, schema_saida, progressao=None, repo_recuperacao=None):
        self.repositorio = repositorio
        self.schema_saida = schema_saida
        self.progressao = progressao
        self.recuperacoes = repo_recuperacao or RepositorioRecuperacao()
        self._registro = RegistroSchema()
        self._login = LoginSchema()
        self._pedido_recuperacao = PedidoRecuperacaoSchema()
        self._redefinir = RedefinirSenhaSchema()

    def registrar(self, dados_brutos: dict) -> tuple[dict, int]:
        dados = self._validar(self._registro, dados_brutos)

        if self.repositorio.existe(nome_usuario=dados["nome_usuario"]):
            raise Conflito("nome_usuario já está em uso.")
        if self.repositorio.existe(email=dados["email"]):
            raise Conflito("email já está em uso.")
        cpf = limpar_cpf(dados["cpf"])
        if self.repositorio.existe_cpf(cpf):
            raise Conflito("cpf já está em uso.")

        senha = dados.pop("senha")
        dados.pop("aceite_termos", None)
        dados["cpf"] = cpf
        dados["idade"] = calcular_idade(dados["data_nascimento"])
        dados["aceite_termos_em"] = datetime.now(timezone.utc)
        dados["apelido"] = dados.get("apelido") or dados["nome_usuario"]

        usuario = self.repositorio.model(**dados)
        usuario.definir_senha(senha)
        self.repositorio.persistir(usuario)
        if self.progressao:
            self.progressao.marcar_presenca(usuario.id)
        return self.schema_saida.dump(usuario), 201

    def autenticar(self, dados_brutos: dict) -> tuple[dict, int]:
        dados = self._validar(self._login, dados_brutos)
        usuario = self.repositorio.buscar_por_identificador(dados["identificador"])

        if usuario is None or not usuario.checar_senha(dados["senha"]):
            raise NaoAutorizado("Credenciais inválidas.")

        if self.progressao:
            self.progressao.marcar_presenca(usuario.id)
        return self.schema_saida.dump(usuario), 200

    def carregar_autenticado(self, usuario_id: int) -> UsuarioAutenticado:
        usuario = self.repositorio.obter(usuario_id)
        if usuario is None:
            raise NaoAutorizado("Autenticação necessária.")
        return UsuarioAutenticado(id=usuario.id, is_admin=usuario.is_admin)

    def obter_perfil(self, usuario_id: int) -> dict:
        usuario = self.repositorio.obter(usuario_id)
        if usuario is None:
            raise NaoAutorizado("Autenticação necessária.")
        return self.schema_saida.dump(usuario)

    def obter_entidade(self, usuario_id: int):
        usuario = self.repositorio.obter(usuario_id)
        if usuario is None:
            raise NaoAutorizado("Autenticação necessária.")
        return usuario

    def trocar_senha(self, usuario_id: int, dados_brutos: dict) -> None:
        usuario = self.repositorio.obter(usuario_id)
        if usuario is None:
            raise NaoAutorizado("Autenticação necessária.")

        dados = dados_brutos or {}
        atual = dados.get("senha_atual") or ""
        nova = dados.get("senha_nova") or ""

        erros = {}
        if not usuario.checar_senha(atual):
            erros["senha_atual"] = ["Senha atual incorreta."]
        if not 8 <= len(nova) <= 128:
            erros["senha_nova"] = ["A senha precisa ter de 8 a 128 caracteres."]
        if erros:
            raise DadosInvalidos("Dados inválidos.", erros=erros)

        usuario.definir_senha(nova)
        usuario.senha_alterada_em = datetime.now(timezone.utc).replace(microsecond=0)
        usuario.versao_sessao = (usuario.versao_sessao or 0) + 1
        self.repositorio.persistir(usuario)

    def pedir_recuperacao(self, dados_brutos: dict) -> dict:
        dados = self._validar(self._pedido_recuperacao, dados_brutos)
        usuario = self.repositorio.buscar_por_email(dados["email"].strip())
        resposta = {
            "mensagem": (
                "Se o e-mail estiver cadastrado, enviamos um link de verificação "
                "para redefinir a senha."
            )
        }
        if usuario is None:
            return resposta

        token = secrets.token_urlsafe(32)
        self.recuperacoes.criar(
            usuario_id=usuario.id,
            token_hash=self._hash_token(token),
            expira_em=datetime.now(timezone.utc) + timedelta(hours=2),
        )
        resposta["destino"] = usuario.email
        resposta["token_dev"] = token
        return resposta

    def redefinir_senha(self, dados_brutos: dict) -> dict:
        dados = self._validar(self._redefinir, dados_brutos)
        token_hash = self._hash_token(dados["token"])
        agora_utc = datetime.now(timezone.utc)
        registro = self.recuperacoes.por_token_hash(token_hash)
        if registro is None:
            raise DadosInvalidos("Token inválido ou já utilizado.")
        expira = registro.expira_em
        if expira.tzinfo is None:
            expira = expira.replace(tzinfo=timezone.utc)
        if expira < agora_utc:
            raise DadosInvalidos("Token expirado. Solicite uma nova recuperação.")

        usuario = registro.usuario
        usuario.definir_senha(dados["senha_nova"])
        usuario.senha_alterada_em = agora_utc.replace(microsecond=0)
        usuario.versao_sessao = (usuario.versao_sessao or 0) + 1
        usuario.email_verificado = True
        registro.usado_em = agora_utc
        self.repositorio.persistir(usuario)
        self.recuperacoes.persistir(registro)
        return {"mensagem": "Senha redefinida. Entre com a nova senha."}

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _validar(schema, dados_brutos: dict) -> dict:
        try:
            return schema.load(dados_brutos or {})
        except ValidationError as erro:
            raise DadosInvalidos("Dados inválidos.", erros=erro.messages) from erro
