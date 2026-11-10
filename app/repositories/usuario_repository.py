"""Consultas específicas de usuário."""
from app.extensions import db
from app.models import Usuario
from app.repositories.base import RepositorioBase


class RepositorioUsuario(RepositorioBase):
    def __init__(self):
        super().__init__(
            Usuario, ordenacao_permitida=("nome_usuario", "nivel", "xp", "criado_em")
        )

    def buscar_por_identificador(self, identificador: str):
        """Aceita nome_usuario OU email — o formulário de login tem um campo só."""
        consulta = db.select(Usuario).where(
            (Usuario.nome_usuario == identificador) | (Usuario.email == identificador)
        )
        return db.session.execute(consulta).scalars().first()

    def listar_ranking_por_xp(self, limite: int = 50):
        """Busca os usuários ordenados do maior para o menor XP para formar o Leaderboard."""
        consulta = db.select(Usuario).order_by(Usuario.xp.desc()).limit(limite)
        return db.session.execute(consulta).scalars().all()

    def buscar_por_email(self, email: str):
        consulta = db.select(Usuario).where(Usuario.email == email)
        return db.session.execute(consulta).scalars().first()

    def existe_cpf(self, cpf: str) -> bool:
        consulta = db.select(Usuario.id).where(Usuario.cpf == cpf)
        return db.session.execute(consulta).scalars().first() is not None

    def buscar_pessoas(self, consulta_texto: str, excluir_id: int, limite: int = 20):
        like = f"%{(consulta_texto or '').strip()}%"
        consulta = (
            db.select(Usuario)
            .where(
                Usuario.id != excluir_id,
                (Usuario.nome_usuario.ilike(like)) | (Usuario.apelido.ilike(like)),
            )
            .order_by(Usuario.nome_usuario)
            .limit(limite)
        )
        return list(db.session.execute(consulta).scalars().all())