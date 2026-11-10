"""Participação em praças e thread de tópicos."""
from app.errors import AcessoNegado, Conflito, DadosInvalidos, NaoEncontrado
from app.models import Post
from app.repositories.base import RepositorioBase
from app.repositories.comunidade_repository import (
    RepositorioMembroComunidade,
    RepositorioPost,
    RepositorioTopicoForum,
)
from app.services.formatacao import tempo_relativo
from app.services.progressao_service import ProgressaoService
from app.services.rotulos import nivel_tipo, rotulo_tipo


class ComunidadeService:
    def __init__(
        self,
        progressao: ProgressaoService | None = None,
        repo_membros: RepositorioMembroComunidade | None = None,
        repo_posts: RepositorioPost | None = None,
        repo_topicos: RepositorioTopicoForum | None = None,
        repo_jogos: RepositorioBase | None = None,
    ):
        from app.models import Jogo

        self.progressao = progressao or ProgressaoService()
        self.membros = repo_membros or RepositorioMembroComunidade()
        self.posts = repo_posts or RepositorioPost()
        self.topicos = repo_topicos or RepositorioTopicoForum()
        self.jogos = repo_jogos or RepositorioBase(Jogo)

    def entrar(self, usuario_id: int, jogo_id: int) -> dict:
        jogo = self.jogos.obter(jogo_id)
        if jogo is None:
            raise NaoEncontrado("Jogo não encontrado.")
        if self.membros.obter_par(usuario_id, jogo_id):
            raise Conflito("Você já participa desta praça.")
        self.membros.criar(usuario_id=usuario_id, jogo_id=jogo_id)
        self.progressao.registrar_acao(usuario_id, "entrar_praca", jogo_id)
        return {"jogo_id": jogo_id, "membro": True}

    def sair(self, usuario_id: int, jogo_id: int) -> None:
        membro = self.membros.obter_par(usuario_id, jogo_id)
        if membro is None:
            raise NaoEncontrado("Você não participa desta praça.")
        self.membros.remover(membro)

    def eh_membro(self, usuario_id: int, jogo_id: int) -> bool:
        return self.membros.obter_par(usuario_id, jogo_id) is not None

    def contar_membros(self, jogo_id: int) -> int:
        return self.membros.contar_por_jogo(jogo_id)

    def detalhe_topico(self, topico_id: int, usuario_id: int | None = None) -> dict:
        topico = self.topicos.obter(topico_id)
        if topico is None or topico.oculto:
            raise NaoEncontrado("Tópico não encontrado.")
        posts = self.posts.listar_do_topico(topico_id)
        return {
            "id": topico.id,
            "titulo": topico.titulo,
            "corpo": topico.corpo or "",
            "tipo": topico.tipo,
            "tipo_rotulo": rotulo_tipo(topico.tipo),
            "nivel": nivel_tipo(topico.tipo),
            "autor": topico.usuario.nome_usuario if topico.usuario else "",
            "autor_id": topico.usuario_id,
            "quando": tempo_relativo(topico.criado_em),
            "jogo_id": topico.jogo_id,
            "jogo_slug": topico.jogo.slug if topico.jogo else "",
            "jogo_nome": topico.jogo.nome if topico.jogo else "",
            "membro": (
                self.eh_membro(usuario_id, topico.jogo_id)
                if usuario_id and topico.jogo_id
                else False
            ),
            "posts": [self._post_em_card(p, usuario_id) for p in posts],
        }

    def responder(
        self,
        usuario_id: int,
        topico_id: int,
        conteudo: str,
        parent_id: int | None = None,
    ) -> dict:
        topico = self.topicos.obter(topico_id)
        if topico is None or topico.oculto:
            raise NaoEncontrado("Tópico não encontrado.")
        if topico.jogo_id and not self.eh_membro(usuario_id, topico.jogo_id):
            raise AcessoNegado("Entre na praça deste jogo para participar do fórum.")
        texto = (conteudo or "").strip()
        if not texto:
            raise DadosInvalidos("Escreva uma resposta.")
        if parent_id:
            pai = self.posts.obter(parent_id)
            if pai is None or pai.topico_id != topico_id or pai.oculto:
                raise NaoEncontrado("Comentário pai não encontrado.")
        post = self.posts.criar(
            topico_id=topico_id,
            usuario_id=usuario_id,
            parent_id=parent_id,
            conteudo=texto,
        )
        self.progressao.registrar_acao(usuario_id, "resposta", post.id)
        return self._post_em_card(post, usuario_id)

    def apagar_post(self, usuario_id: int, post_id: int, is_admin: bool = False) -> None:
        post = self.posts.obter(post_id)
        if post is None:
            raise NaoEncontrado("Comentário não encontrado.")
        if post.usuario_id != usuario_id and not is_admin:
            raise AcessoNegado("Só o autor pode apagar este comentário.")
        post.oculto = True
        self.posts.persistir(post)

    def _post_em_card(self, post: Post, usuario_id: int | None) -> dict:
        autor = post.usuario
        return {
            "id": post.id,
            "parent_id": post.parent_id,
            "conteudo": post.conteudo,
            "autor": autor.nome_usuario if autor else "",
            "autor_id": post.usuario_id,
            "avatar_url": (autor.avatar_url or "") if autor else "",
            "cor_avatar": autor.cor_avatar if autor else "#6b7cff",
            "quando": tempo_relativo(post.criado_em),
            "pode_apagar": bool(usuario_id and usuario_id == post.usuario_id),
        }
