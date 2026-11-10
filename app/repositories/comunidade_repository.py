"""Membros de praça e posts do fórum."""
from app.extensions import db
from app.models import MembroComunidade, Post, Topico
from app.repositories.base import RepositorioBase


class RepositorioMembroComunidade(RepositorioBase):
    def __init__(self):
        super().__init__(MembroComunidade, ordenacao_permitida=("entrou_em",))

    def obter_par(self, usuario_id: int, jogo_id: int):
        consulta = db.select(MembroComunidade).where(
            MembroComunidade.usuario_id == usuario_id,
            MembroComunidade.jogo_id == jogo_id,
        )
        return db.session.execute(consulta).scalars().first()

    def contar_por_jogo(self, jogo_id: int) -> int:
        consulta = db.select(db.func.count()).select_from(MembroComunidade).where(
            MembroComunidade.jogo_id == jogo_id
        )
        return int(db.session.execute(consulta).scalar_one())


class RepositorioPost(RepositorioBase):
    def __init__(self):
        super().__init__(Post, ordenacao_permitida=("criado_em",))

    def listar_do_topico(self, topico_id: int):
        consulta = (
            db.select(Post)
            .where(Post.topico_id == topico_id, Post.oculto.is_(False))
            .order_by(Post.criado_em.asc())
        )
        return list(db.session.execute(consulta).scalars().all())


class RepositorioTopicoForum(RepositorioBase):
    def __init__(self):
        super().__init__(Topico, ordenacao_permitida=("criado_em", "titulo"))
