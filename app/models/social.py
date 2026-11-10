"""Badges, notificações, atividades, amizades e recuperação de senha."""
from app.extensions import db
from app.models.usuario import agora

STATUS_AMIZADE = ("pendente", "aceita", "recusada")


class Badge(db.Model):
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    icone_url = db.Column(db.Text)
    #: Chave estável usada pelas regras de conquista automática.
    codigo = db.Column(db.String(40), unique=True)

    usuarios = db.relationship(
        "UsuarioBadge", backref="badge", cascade="all, delete-orphan"
    )


class UsuarioBadge(db.Model):
    __tablename__ = "usuarios_badges"
    __table_args__ = (db.UniqueConstraint("usuario_id", "badge_id"),)

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"))
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id", ondelete="CASCADE"))
    conquistado_em = db.Column(db.DateTime, default=agora)


class Notificacao(db.Model):
    __tablename__ = "notificacoes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"))
    mensagem = db.Column(db.Text, nullable=False)
    lida = db.Column(db.Boolean, default=False, nullable=False)
    criado_em = db.Column(db.DateTime, default=agora)


class Atividade(db.Model):
    __tablename__ = "atividades"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"))
    tipo = db.Column(db.String(50))
    referencia_id = db.Column(db.Integer)
    criado_em = db.Column(db.DateTime, default=agora)


class Amizade(db.Model):
    __tablename__ = "amizades"
    __table_args__ = (
        db.UniqueConstraint("solicitante_id", "destinatario_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    solicitante_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    destinatario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    status = db.Column(db.String(20), default="pendente", nullable=False)
    criado_em = db.Column(db.DateTime, default=agora)
    respondido_em = db.Column(db.DateTime)

    solicitante = db.relationship("Usuario", foreign_keys=[solicitante_id])
    destinatario = db.relationship("Usuario", foreign_keys=[destinatario_id])


class RecuperacaoSenha(db.Model):
    __tablename__ = "recuperacoes_senha"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    token_hash = db.Column(db.String(128), unique=True, nullable=False)
    expira_em = db.Column(db.DateTime, nullable=False)
    usado_em = db.Column(db.DateTime)
    criado_em = db.Column(db.DateTime, default=agora)

    usuario = db.relationship("Usuario")
