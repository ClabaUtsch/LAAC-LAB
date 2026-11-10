"""Camada Model — tabelas em português."""
from app.models.bugometro import (
    CATEGORIAS_BUG,
    SEVERIDADES,
    SEVERIDADES_ALERTA,
    STATUS_RELATO,
    Alerta,
    BugometroStatus,
    HistoricoBug,
    MetricaBug,
    RelatoBug,
    VotoBug,
)
from app.models.forum import (
    TIPOS_TOPICO,
    Categoria,
    MembroComunidade,
    Post,
    Topico,
)
from app.models.jogo import (
    Avaliacao,
    BibliotecaUsuario,
    CurtidaAvaliacao,
    Genero,
    Jogo,
    JogoGenero,
    JogoPlataforma,
    Plataforma,
)
from app.models.social import (
    STATUS_AMIZADE,
    Amizade,
    Atividade,
    Badge,
    Notificacao,
    RecuperacaoSenha,
    UsuarioBadge,
)
from app.models.usuario import Usuario, agora

__all__ = [
    "Alerta", "Amizade", "Atividade", "Avaliacao", "Badge", "BibliotecaUsuario",
    "BugometroStatus", "CATEGORIAS_BUG", "Categoria", "CurtidaAvaliacao",
    "Genero", "HistoricoBug", "Jogo", "JogoGenero", "JogoPlataforma",
    "MembroComunidade", "MetricaBug", "Notificacao", "Plataforma", "Post",
    "RecuperacaoSenha", "RelatoBug", "SEVERIDADES", "SEVERIDADES_ALERTA",
    "STATUS_AMIZADE", "STATUS_RELATO", "TIPOS_TOPICO", "Topico", "Usuario",
    "UsuarioBadge", "VotoBug", "agora",
]
