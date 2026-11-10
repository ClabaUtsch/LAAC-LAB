"""Composition root: monta Repository → Service e entrega ao Controller.

Vive fora de app/controllers/ de propósito: é o único lugar autorizado a
conhecer as três camadas ao mesmo tempo.
"""
from types import SimpleNamespace

from app import models as m
from app import schemas as _  # noqa: F401  (garante o pacote carregado)
from app.repositories.base import RepositorioBase
from app.repositories.jogo_repository import ORDENACAO_JOGOS
from app.repositories.usuario_repository import RepositorioUsuario
from app.schemas import bugometro as sb
from app.schemas import forum as sf
from app.schemas import jogo as sj
from app.schemas import social as ss
from app.schemas.usuario import UsuarioEntradaSchema, UsuarioSchema
from app.services.auth_service import AuthService
from app.services.base import ServicoBase
from app.services.comunidade_service import ComunidadeService
from app.services.progressao_service import ProgressaoService
from app.services.social_service import SocialService

#: (atributo, model, schema_saida, schema_entrada, nome_recurso, ordenacao)
CATALOGO = [
    ("jogos", m.Jogo, sj.JogoSchema, sj.JogoEntradaSchema, "Jogo",
     ORDENACAO_JOGOS),
    ("generos", m.Genero, sj.GeneroSchema, sj.GeneroEntradaSchema, "Gênero",
     ("nome",)),
    ("plataformas", m.Plataforma, sj.PlataformaSchema, sj.PlataformaEntradaSchema,
     "Plataforma", ("nome",)),
    ("biblioteca", m.BibliotecaUsuario, sj.BibliotecaSchema,
     sj.BibliotecaEntradaSchema, "Entrada da biblioteca", ("adicionado_em",)),
    ("avaliacoes", m.Avaliacao, sj.AvaliacaoSchema, sj.AvaliacaoEntradaSchema,
     "Avaliação", ("criado_em", "nota")),
    ("relatos_bug", m.RelatoBug, sb.RelatoBugSchema, sb.RelatoBugEntradaSchema,
     "Relato de bug", ("criado_em", "confirmacoes", "severidade")),
    ("votos_bug", m.VotoBug, sb.VotoBugSchema, sb.VotoBugEntradaSchema,
     "Voto", ("criado_em",)),
    ("alertas", m.Alerta, sb.AlertaSchema, sb.AlertaEntradaSchema, "Alerta",
     ("criado_em", "severidade")),
    ("metricas_bug", m.MetricaBug, sb.MetricaBugSchema, sb.MetricaBugEntradaSchema,
     "Métrica", ("criado_em",)),
    ("historico_bug", m.HistoricoBug, sb.HistoricoBugSchema,
     sb.HistoricoBugEntradaSchema, "Histórico", ("registrado_em",)),
    ("topicos", m.Topico, sf.TopicoSchema, sf.TopicoEntradaSchema, "Tópico",
     ("criado_em", "titulo")),
    ("posts", m.Post, sf.PostSchema, sf.PostEntradaSchema, "Post", ("criado_em",)),
    ("categorias", m.Categoria, sf.CategoriaSchema, sf.CategoriaEntradaSchema,
     "Categoria", ("nome",)),
    ("badges", m.Badge, ss.BadgeSchema, ss.BadgeEntradaSchema, "Badge", ("nome",)),
    ("bugometro_status", m.BugometroStatus, sb.BugometroStatusSchema,
     sb.BugometroStatusEntradaSchema, "Status do bugômetro", ("atualizado_em",)),
    ("notificacoes", m.Notificacao, ss.NotificacaoSchema,
     ss.NotificacaoEntradaSchema, "Notificação", ("criado_em",)),
    ("atividades", m.Atividade, ss.AtividadeSchema, ss.AtividadeEntradaSchema,
     "Atividade", ("criado_em",)),
]


class TopicoComProgressao(ServicoBase):
    """Cria tópico e registra XP/conquista."""

    def __init__(self, *args, progressao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.progressao = progressao

    def criar(self, dados_brutos: dict, usuario=None) -> dict:
        resultado = super().criar(dados_brutos, usuario=usuario)
        if usuario is not None and self.progressao:
            self.progressao.registrar_acao(usuario.id, "topico", resultado.get("id"))
        return resultado


class RelatoComProgressao(ServicoBase):
    """Proxy: o BugometroService já é o dono; este wrapper só existe se
    precisarmos envolver. Na prática usamos o hook abaixo no bugometro."""


def montar_servicos(vitrine_habilitada: bool = False) -> SimpleNamespace:
    repositorio_usuario = RepositorioUsuario()
    progressao = ProgressaoService()

    servicos = SimpleNamespace(
        progressao=progressao,
        social=SocialService(progressao=progressao),
        comunidade=ComunidadeService(progressao=progressao),
        auth=AuthService(
            repositorio=repositorio_usuario,
            schema_saida=UsuarioSchema(),
            progressao=progressao,
        ),
        usuarios=ServicoBase(
            repositorio=repositorio_usuario,
            schema_saida=UsuarioSchema(),
            schema_entrada=UsuarioEntradaSchema(),
            nome_recurso="Usuário",
        ),
    )
    servicos.usuarios.campo_dono = "id"
    servicos.usuarios.campo_autor = None
    servicos.usuarios.campos_de_admin = ("is_admin",)

    for atributo, model, saida, entrada, nome, ordenacao in CATALOGO:
        if atributo == "topicos":
            setattr(
                servicos,
                atributo,
                TopicoComProgressao(
                    repositorio=RepositorioBase(model, ordenacao_permitida=ordenacao),
                    schema_saida=saida(),
                    schema_entrada=entrada(),
                    nome_recurso=nome,
                    progressao=progressao,
                ),
            )
        else:
            setattr(
                servicos,
                atributo,
                ServicoBase(
                    repositorio=RepositorioBase(model, ordenacao_permitida=ordenacao),
                    schema_saida=saida(),
                    schema_entrada=entrada(),
                    nome_recurso=nome,
                ),
            )

    from app.models import Alerta, BugometroStatus, HistoricoBug, Jogo, RelatoBug, VotoBug
    from app.repositories.jogo_repository import RepositorioJogos
    from app.services.alerta_service import AlertaService
    from app.services.bugometro_service import BugometroService
    from app.services.jogo_service import JogoService

    servicos.jogos = JogoService(
        repositorio=RepositorioJogos(),
        schema_saida=sj.JogoSchema(),
        schema_entrada=sj.JogoEntradaSchema(),
        nome_recurso="Jogo",
    )

    from app.repositories.voto_repository import RepositorioVotosBug

    class BugometroComProgressao(BugometroService):
        def criar(self, dados_brutos: dict, usuario=None) -> dict:
            resultado = super().criar(dados_brutos, usuario=usuario)
            if usuario is not None:
                progressao.registrar_acao(usuario.id, "relato_bug", resultado.get("id"))
            return resultado

    servicos.bugometro = BugometroComProgressao(
        repositorio=RepositorioBase(
            RelatoBug,
            ordenacao_permitida=("criado_em", "confirmacoes", "severidade"),
        ),
        schema_saida=sb.RelatoBugSchema(),
        schema_entrada=sb.RelatoBugEntradaSchema(),
        nome_recurso="Relato de bug",
        repositorio_status=RepositorioBase(BugometroStatus),
        repositorio_jogos=RepositorioBase(Jogo),
        repositorio_votos=RepositorioVotosBug(),
        repositorio_historico=RepositorioBase(
            HistoricoBug, ordenacao_permitida=("registrado_em",)
        ),
    )

    servicos.bugometro.campos_de_admin = ("status", "confirmacoes")
    servicos.relatos_bug = servicos.bugometro

    from app.services.voto_service import VotoService

    servicos.votos_bug = VotoService(
        repositorio=RepositorioBase(VotoBug, ordenacao_permitida=("criado_em",)),
        schema_saida=sb.VotoBugSchema(),
        schema_entrada=sb.VotoBugEntradaSchema(),
        nome_recurso="Voto",
        servico_bugometro=servicos.bugometro,
        repositorio_relatos=RepositorioBase(RelatoBug),
    )

    servicos.alertas = AlertaService(
        repositorio=RepositorioBase(
            Alerta, ordenacao_permitida=("criado_em", "severidade")
        ),
        schema_saida=sb.AlertaSchema(),
        schema_entrada=sb.AlertaEntradaSchema(),
        nome_recurso="Alerta",
    )

    for atributo in ("topicos", "posts", "avaliacoes", "relatos_bug"):
        getattr(servicos, atributo).campo_oculto = "oculto"

    for atributo in ("jogos", "generos", "plataformas", "alertas", "categorias",
                     "badges", "metricas_bug", "historico_bug", "bugometro_status"):
        servico = getattr(servicos, atributo)
        servico.campo_dono = None
        servico.somente_admin = True
        servico.campo_autor = None

    from app.services.tela_service import TelaService

    fonte_vitrine = None
    if vitrine_habilitada:
        from app.integracoes.vitrine_externa import obter_vitrine

        fonte_vitrine = obter_vitrine

    servicos.telas = TelaService(
        servico_jogos=servicos.jogos,
        servico_alertas=servicos.alertas,
        servico_topicos=servicos.topicos,
        servico_biblioteca=servicos.biblioteca,
        servico_auth=servicos.auth,
        servico_avaliacoes=servicos.avaliacoes,
        servico_bugometro=servicos.bugometro,
        servico_posts=servicos.posts,
        servico_usuarios=servicos.usuarios,
        servico_generos=servicos.generos,
        fonte_vitrine=fonte_vitrine,
        servico_comunidade=servicos.comunidade,
        servico_social=servicos.social,
        servico_progressao=progressao,
    )

    return servicos
