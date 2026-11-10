"""Amizades e perfis públicos."""
from app.errors import AcessoNegado, Conflito, DadosInvalidos, NaoEncontrado
from app.models import Amizade, agora
from app.repositories.social_repository import RepositorioAmizade
from app.repositories.usuario_repository import RepositorioUsuario
from app.services.formatacao import tempo_relativo
from app.services.progressao_service import ProgressaoService


class SocialService:
    def __init__(
        self,
        progressao: ProgressaoService | None = None,
        repo_amizade: RepositorioAmizade | None = None,
        repo_usuario: RepositorioUsuario | None = None,
    ):
        self.progressao = progressao or ProgressaoService()
        self.amizades = repo_amizade or RepositorioAmizade()
        self.usuarios = repo_usuario or RepositorioUsuario()

    def perfil_publico(self, usuario_id: int, visitante_id: int | None = None) -> dict:
        usuario = self.usuarios.obter(usuario_id)
        if usuario is None:
            raise NaoEncontrado("Usuário não encontrado.")
        amizade = None
        if visitante_id and visitante_id != usuario_id:
            amizade = self.amizades.entre(visitante_id, usuario_id)
        return {
            "id": usuario.id,
            "nome_usuario": usuario.nome_usuario,
            "apelido": usuario.apelido or usuario.nome_usuario,
            "bio": usuario.bio or "",
            "nivel": usuario.nivel,
            "xp": usuario.xp,
            "xp_max": usuario.xp_max,
            "cor_avatar": usuario.cor_avatar,
            "avatar_url": usuario.avatar_url or "",
            "conquistas": usuario.conquistas,
            "amigos": usuario.amigos,
            "dias_ativo": usuario.dias_ativo,
            "relacao": self._status_para(amizade, visitante_id) if amizade else (
                "eu" if visitante_id == usuario_id else "nenhuma"
            ),
            "amizade_id": amizade.id if amizade else None,
        }

    def listar_amigos(self, usuario_id: int) -> dict:
        return {
            "amigos": [
                self._cartao_amigo(a, usuario_id)
                for a in self.amizades.listar_aceitas(usuario_id)
            ],
            "pendentes": [
                self._cartao_amigo(a, usuario_id)
                for a in self.amizades.listar_pendentes_recebidas(usuario_id)
            ],
            "enviadas": [
                self._cartao_amigo(a, usuario_id)
                for a in self.amizades.listar_pendentes_enviadas(usuario_id)
            ],
        }

    def buscar_pessoas(self, consulta: str, excluir_id: int, limite: int = 20) -> list[dict]:
        q = (consulta or "").strip()
        if len(q) < 2:
            return []
        saida = []
        for p in self.usuarios.buscar_pessoas(q, excluir_id, limite=limite):
            rel = self.amizades.entre(excluir_id, p.id)
            saida.append(
                {
                    "id": p.id,
                    "nome_usuario": p.nome_usuario,
                    "apelido": p.apelido or p.nome_usuario,
                    "avatar_url": p.avatar_url or "",
                    "cor_avatar": p.cor_avatar,
                    "nivel": p.nivel,
                    "relacao": self._status_para(rel, excluir_id) if rel else "nenhuma",
                    "amizade_id": rel.id if rel else None,
                }
            )
        return saida

    def solicitar(self, solicitante_id: int, destinatario_id: int) -> dict:
        if solicitante_id == destinatario_id:
            raise DadosInvalidos("Não é possível adicionar a si mesmo.")
        destino = self.usuarios.obter(destinatario_id)
        if destino is None:
            raise NaoEncontrado("Usuário não encontrado.")
        existente = self.amizades.entre(solicitante_id, destinatario_id)
        if existente:
            if existente.status == "aceita":
                raise Conflito("Vocês já são amigos.")
            if existente.status == "pendente":
                raise Conflito("Já existe um pedido pendente.")
            existente.status = "pendente"
            existente.solicitante_id = solicitante_id
            existente.destinatario_id = destinatario_id
            existente.respondido_em = None
            self.amizades.persistir(existente)
            return self._cartao_amigo(existente, solicitante_id)

        amizade = Amizade(
            solicitante_id=solicitante_id,
            destinatario_id=destinatario_id,
            status="pendente",
        )
        self.amizades.persistir(amizade)
        return self._cartao_amigo(amizade, solicitante_id)

    def responder(self, usuario_id: int, amizade_id: int, aceitar: bool) -> dict:
        amizade = self.amizades.obter(amizade_id)
        if amizade is None:
            raise NaoEncontrado("Pedido não encontrado.")
        if amizade.destinatario_id != usuario_id:
            raise AcessoNegado("Só quem recebeu o pedido pode responder.")
        if amizade.status != "pendente":
            raise Conflito("Este pedido já foi respondido.")
        amizade.status = "aceita" if aceitar else "recusada"
        amizade.respondido_em = agora()
        if aceitar:
            for uid in (amizade.solicitante_id, amizade.destinatario_id):
                u = self.usuarios.obter(uid)
                if u:
                    u.amigos = (u.amigos or 0) + 1
                    self.usuarios.persistir(u)
            self.amizades.persistir(amizade)
            self.progressao.registrar_acao(amizade.solicitante_id, "amizade", amizade.id)
            self.progressao.registrar_acao(amizade.destinatario_id, "amizade", amizade.id)
        else:
            self.amizades.persistir(amizade)
        return self._cartao_amigo(amizade, usuario_id)

    @staticmethod
    def _status_para(amizade: Amizade, eu_id: int | None) -> str:
        if amizade.status == "aceita":
            return "amigos"
        if amizade.status == "recusada":
            return "recusada"
        if eu_id == amizade.solicitante_id:
            return "enviada"
        if eu_id == amizade.destinatario_id:
            return "pendente"
        return amizade.status

    def _cartao_amigo(self, amizade: Amizade, eu_id: int) -> dict:
        outro_id = (
            amizade.destinatario_id
            if amizade.solicitante_id == eu_id
            else amizade.solicitante_id
        )
        outro = self.usuarios.obter(outro_id)
        return {
            "amizade_id": amizade.id,
            "status": self._status_para(amizade, eu_id),
            "quando": tempo_relativo(amizade.criado_em),
            "usuario": {
                "id": outro.id if outro else outro_id,
                "nome_usuario": outro.nome_usuario if outro else "",
                "apelido": (outro.apelido or outro.nome_usuario) if outro else "",
                "avatar_url": (outro.avatar_url or "") if outro else "",
                "cor_avatar": outro.cor_avatar if outro else "#6b7cff",
                "nivel": outro.nivel if outro else 1,
            },
        }
