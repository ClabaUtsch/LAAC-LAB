"""Consultas de amizade, badges, atividades e recuperação de senha."""
from sqlalchemy import and_, or_

from app.extensions import db
from app.models import (
    Amizade,
    Atividade,
    Badge,
    RecuperacaoSenha,
    Usuario,
    UsuarioBadge,
)
from app.repositories.base import RepositorioBase


class RepositorioAmizade(RepositorioBase):
    def __init__(self):
        super().__init__(Amizade, ordenacao_permitida=("criado_em",))

    def entre(self, a: int, b: int):
        consulta = db.select(Amizade).where(
            or_(
                and_(Amizade.solicitante_id == a, Amizade.destinatario_id == b),
                and_(Amizade.solicitante_id == b, Amizade.destinatario_id == a),
            )
        )
        return db.session.execute(consulta).scalars().first()

    def listar_aceitas(self, usuario_id: int):
        consulta = db.select(Amizade).where(
            Amizade.status == "aceita",
            or_(
                Amizade.solicitante_id == usuario_id,
                Amizade.destinatario_id == usuario_id,
            ),
        )
        return list(db.session.execute(consulta).scalars().all())

    def listar_pendentes_recebidas(self, usuario_id: int):
        consulta = db.select(Amizade).where(
            Amizade.status == "pendente",
            Amizade.destinatario_id == usuario_id,
        )
        return list(db.session.execute(consulta).scalars().all())

    def listar_pendentes_enviadas(self, usuario_id: int):
        consulta = db.select(Amizade).where(
            Amizade.status == "pendente",
            Amizade.solicitante_id == usuario_id,
        )
        return list(db.session.execute(consulta).scalars().all())


class RepositorioProgressao:
    def obter_usuario(self, usuario_id: int):
        return db.session.get(Usuario, usuario_id)

    def persistir(self, entidade):
        db.session.add(entidade)
        db.session.commit()
        return entidade

    def flush(self, entidade):
        db.session.add(entidade)
        db.session.flush()
        return entidade

    def contar_atividades(self, usuario_id: int, tipo: str) -> int:
        consulta = db.select(db.func.count()).select_from(Atividade).where(
            Atividade.usuario_id == usuario_id,
            Atividade.tipo == tipo,
        )
        return int(db.session.execute(consulta).scalar_one())

    def badge_por_codigo(self, codigo: str):
        consulta = db.select(Badge).where(Badge.codigo == codigo)
        return db.session.execute(consulta).scalars().first()

    def usuario_badge(self, usuario_id: int, badge_id: int):
        consulta = db.select(UsuarioBadge).where(
            UsuarioBadge.usuario_id == usuario_id,
            UsuarioBadge.badge_id == badge_id,
        )
        return db.session.execute(consulta).scalars().first()

    def listar_conquistas(self, usuario_id: int):
        consulta = (
            db.select(UsuarioBadge, Badge)
            .join(Badge, Badge.id == UsuarioBadge.badge_id)
            .where(UsuarioBadge.usuario_id == usuario_id)
            .order_by(UsuarioBadge.conquistado_em.desc())
        )
        return list(db.session.execute(consulta).all())


class RepositorioRecuperacao(RepositorioBase):
    def __init__(self):
        super().__init__(RecuperacaoSenha, ordenacao_permitida=("criado_em",))

    def por_token_hash(self, token_hash: str):
        consulta = db.select(RecuperacaoSenha).where(
            RecuperacaoSenha.token_hash == token_hash,
            RecuperacaoSenha.usado_em.is_(None),
        )
        return db.session.execute(consulta).scalars().first()
