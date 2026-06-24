"""Models SQLAlchemy do LaaC_lab (Bugômetro).

Mapeia 1:1 o schema relacional original, com relacionamentos,
cascades e helpers de senha no usuário.
"""
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


# ============================================================
# USUÁRIOS
# ============================================================
class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome_usuario = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    idade = db.Column(db.Integer)
    avatar_url = db.Column(db.Text)
    bio = db.Column(db.Text)
    nivel = db.Column(db.Integer, default=1)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos (todos com cascade espelhando ON DELETE CASCADE)
    biblioteca = db.relationship(
        "BibliotecaUsuario", backref="usuario", cascade="all, delete-orphan"
    )
    avaliacoes = db.relationship(
        "Avaliacao", backref="usuario", cascade="all, delete-orphan"
    )
    curtidas = db.relationship(
        "CurtidaAvaliacao", backref="usuario", cascade="all, delete-orphan"
    )
    topicos = db.relationship(
        "Topico", backref="usuario", cascade="all, delete-orphan"
    )
    posts = db.relationship("Post", backref="usuario", cascade="all, delete-orphan")
    badges = db.relationship(
        "UsuarioBadge", backref="usuario", cascade="all, delete-orphan"
    )
    notificacoes = db.relationship(
        "Notificacao", backref="usuario", cascade="all, delete-orphan"
    )
    atividades = db.relationship(
        "Atividade", backref="usuario", cascade="all, delete-orphan"
    )

    # --- Helpers de senha ---
    def set_senha(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)


# ============================================================
# JOGOS
# ============================================================
class Jogo(db.Model):
    __tablename__ = "jogos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    genero = db.Column(db.String(50))
    classificacao = db.Column(db.String(10))
    desenvolvedora = db.Column(db.String(100))
    data_lancamento = db.Column(db.Date)
    capa_url = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    plataformas = db.relationship(
        "JogoPlataforma", backref="jogo", cascade="all, delete-orphan"
    )
    biblioteca = db.relationship(
        "BibliotecaUsuario", backref="jogo", cascade="all, delete-orphan"
    )
    avaliacoes = db.relationship(
        "Avaliacao", backref="jogo", cascade="all, delete-orphan"
    )
    bugometro = db.relationship(
        "BugometroStatus",
        backref="jogo",
        uselist=False,
        cascade="all, delete-orphan",
    )
    metricas = db.relationship(
        "MetricaBug", backref="jogo", cascade="all, delete-orphan"
    )
    relatos = db.relationship(
        "RelatoBug", backref="jogo", cascade="all, delete-orphan"
    )
    historico = db.relationship(
        "HistoricoBug", backref="jogo", cascade="all, delete-orphan"
    )


# ============================================================
# PLATAFORMAS
# ============================================================
class Plataforma(db.Model):
    __tablename__ = "plataformas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)

    jogos = db.relationship(
        "JogoPlataforma", backref="plataforma", cascade="all, delete-orphan"
    )


class JogoPlataforma(db.Model):
    __tablename__ = "jogos_plataformas"

    id = db.Column(db.Integer, primary_key=True)
    jogo_id = db.Column(
        db.Integer, db.ForeignKey("jogos.id", ondelete="CASCADE")
    )
    plataforma_id = db.Column(
        db.Integer, db.ForeignKey("plataformas.id", ondelete="CASCADE")
    )


# ============================================================
# BIBLIOTECA DO USUÁRIO
# ============================================================
class BibliotecaUsuario(db.Model):
    __tablename__ = "biblioteca_usuario"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE")
    )
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogos.id", ondelete="CASCADE"))
    favorito = db.Column(db.Boolean, default=False)
    adicionado_em = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# AVALIAÇÕES (REVIEWS)
# ============================================================
class Avaliacao(db.Model):
    __tablename__ = "avaliacoes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE")
    )
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogos.id", ondelete="CASCADE"))
    nota = db.Column(db.Numeric(2, 1))
    comentario = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    curtidas = db.relationship(
        "CurtidaAvaliacao", backref="avaliacao", cascade="all, delete-orphan"
    )


class CurtidaAvaliacao(db.Model):
    __tablename__ = "curtidas_avaliacoes"

    id = db.Column(db.Integer, primary_key=True)
    avaliacao_id = db.Column(
        db.Integer, db.ForeignKey("avaliacoes.id", ondelete="CASCADE")
    )
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE")
    )


# ============================================================
# BUGÔMETRO (CORE)
# ============================================================
class BugometroStatus(db.Model):
    __tablename__ = "bugometro_status"

    id = db.Column(db.Integer, primary_key=True)
    jogo_id = db.Column(
        db.Integer, db.ForeignKey("jogos.id", ondelete="CASCADE"), unique=True
    )
    pontuacao = db.Column(db.Integer)
    status = db.Column(db.String(20))
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow)


class MetricaBug(db.Model):
    __tablename__ = "metricas_bug"

    id = db.Column(db.Integer, primary_key=True)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogos.id", ondelete="CASCADE"))
    tipo = db.Column(db.String(20))
    severidade = db.Column(db.String(20))
    porcentagem = db.Column(db.Integer)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


class RelatoBug(db.Model):
    __tablename__ = "relatos_bug"

    id = db.Column(db.Integer, primary_key=True)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogos.id", ondelete="CASCADE"))
    titulo = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    severidade = db.Column(db.String(20))
    origem = db.Column(db.String(50))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


class HistoricoBug(db.Model):
    __tablename__ = "historico_bug"

    id = db.Column(db.Integer, primary_key=True)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogos.id", ondelete="CASCADE"))
    quantidade_crash = db.Column(db.Integer)
    quantidade_bug = db.Column(db.Integer)
    quantidade_fps_drop = db.Column(db.Integer)
    quantidade_stutter = db.Column(db.Integer)
    registrado_em = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# FÓRUM
# ============================================================
class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50))

    topicos = db.relationship(
        "Topico", backref="categoria", cascade="all, delete-orphan"
    )


class Topico(db.Model):
    __tablename__ = "topicos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE")
    )
    categoria_id = db.Column(
        db.Integer, db.ForeignKey("categorias.id", ondelete="CASCADE")
    )
    titulo = db.Column(db.String(100))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship("Post", backref="topico", cascade="all, delete-orphan")


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    topico_id = db.Column(
        db.Integer, db.ForeignKey("topicos.id", ondelete="CASCADE")
    )
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE")
    )
    conteudo = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# BADGES
# ============================================================
class Badge(db.Model):
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50))
    icone_url = db.Column(db.Text)

    usuarios = db.relationship(
        "UsuarioBadge", backref="badge", cascade="all, delete-orphan"
    )


class UsuarioBadge(db.Model):
    __tablename__ = "usuarios_badges"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE")
    )
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id", ondelete="CASCADE"))
    conquistado_em = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# NOTIFICAÇÕES
# ============================================================
class Notificacao(db.Model):
    __tablename__ = "notificacoes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE")
    )
    mensagem = db.Column(db.Text)
    lida = db.Column(db.Boolean, default=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# ATIVIDADES
# ============================================================
class Atividade(db.Model):
    __tablename__ = "atividades"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE")
    )
    tipo = db.Column(db.String(50))
    referencia_id = db.Column(db.Integer)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
