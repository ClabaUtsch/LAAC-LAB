"""Fórum: categoria, tópico, post e membros de praça por jogo."""
from app.extensions import db
from app.models.usuario import agora

TIPOS_TOPICO = ("discussao", "bug", "dica", "noticia")


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)

    topicos = db.relationship(
        "Topico", backref="categoria", cascade="all, delete-orphan"
    )


class Topico(db.Model):
    __tablename__ = "topicos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"))
    categoria_id = db.Column(
        db.Integer, db.ForeignKey("categorias.id", ondelete="CASCADE"), nullable=True
    )
    jogo_id = db.Column(
        db.Integer, db.ForeignKey("jogos.id", ondelete="CASCADE"), nullable=True
    )
    titulo = db.Column(db.String(200), nullable=False)
    corpo = db.Column(db.Text, default="")
    tipo = db.Column(db.String(20), default="discussao", nullable=False)
    oculto = db.Column(db.Boolean, default=False, nullable=False)
    criado_em = db.Column(db.DateTime, default=agora)

    posts = db.relationship("Post", backref="topico", cascade="all, delete-orphan")


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    topico_id = db.Column(db.Integer, db.ForeignKey("topicos.id", ondelete="CASCADE"))
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"))
    #: Resposta a outro post (ou ao tópico quando nulo).
    parent_id = db.Column(
        db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=True
    )
    conteudo = db.Column(db.Text, nullable=False)
    oculto = db.Column(db.Boolean, default=False, nullable=False)
    criado_em = db.Column(db.DateTime, default=agora)

    respostas = db.relationship(
        "Post",
        backref=db.backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",
    )


class MembroComunidade(db.Model):
    """Participação na praça (fórum) de um jogo."""

    __tablename__ = "membros_comunidade"
    __table_args__ = (db.UniqueConstraint("usuario_id", "jogo_id"),)

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    jogo_id = db.Column(
        db.Integer, db.ForeignKey("jogos.id", ondelete="CASCADE"), nullable=False
    )
    entrou_em = db.Column(db.DateTime, default=agora)

    usuario = db.relationship("Usuario", backref="membros_comunidade")
    jogo = db.relationship("Jogo", backref="membros_comunidade")
