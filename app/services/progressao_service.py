"""XP, nível, dias ativos e conquistas personalizadas pelo uso."""
from datetime import date

from app.models import Atividade, Badge, UsuarioBadge
from app.repositories.social_repository import RepositorioProgressao

XP_POR_ACAO = {
    "login_diario": 25,
    "topico": 40,
    "resposta": 20,
    "relato_bug": 50,
    "avaliacao": 15,
    "entrar_praca": 30,
    "amizade": 35,
    "avatar": 10,
}

CONQUISTAS = (
    ("primeiro_passo", "Primeiro passo", "login_diario", 1),
    ("voz_ativa", "Voz ativa", "topico", 1),
    ("responde_tudo", "Responde tudo", "resposta", 3),
    ("cacador_de_bugs", "Caçador de bugs", "relato_bug", 1),
    ("circulo_social", "Círculo social", "amizade", 1),
    ("morador", "Morador da praça", "entrar_praca", 1),
    ("rosto", "Rosto na comunidade", "avatar", 1),
)

XP_BASE = 2000


class ProgressaoService:
    def __init__(self, repositorio: RepositorioProgressao | None = None):
        self.repo = repositorio or RepositorioProgressao()

    def registrar_acao(self, usuario_id: int, tipo: str, referencia_id: int | None = None) -> dict:
        usuario = self.repo.obter_usuario(usuario_id)
        if usuario is None:
            return {}

        self._atualizar_dias_ativos(usuario)
        xp = XP_POR_ACAO.get(tipo, 0)
        if xp:
            usuario.xp = (usuario.xp or 0) + xp
            self._recalcular_nivel(usuario)

        self.repo.flush(
            Atividade(usuario_id=usuario.id, tipo=tipo, referencia_id=referencia_id)
        )
        conquistadas = self._avaliar_conquistas(usuario, tipo)
        self.repo.persistir(usuario)
        return {
            "xp_ganho": xp,
            "nivel": usuario.nivel,
            "xp": usuario.xp,
            "xp_max": usuario.xp_max,
            "dias_ativo": usuario.dias_ativo,
            "conquistas": usuario.conquistas,
            "novas_conquistas": conquistadas,
        }

    def marcar_presenca(self, usuario_id: int) -> None:
        usuario = self.repo.obter_usuario(usuario_id)
        if usuario is None:
            return
        mudou = self._atualizar_dias_ativos(usuario)
        if mudou:
            usuario.xp = (usuario.xp or 0) + XP_POR_ACAO["login_diario"]
            self._recalcular_nivel(usuario)
            self.repo.flush(
                Atividade(usuario_id=usuario.id, tipo="login_diario", referencia_id=None)
            )
            self._avaliar_conquistas(usuario, "login_diario")
            self.repo.persistir(usuario)

    @staticmethod
    def _atualizar_dias_ativos(usuario) -> bool:
        hoje = date.today()
        if usuario.ultimo_dia_ativo == hoje:
            return False
        usuario.ultimo_dia_ativo = hoje
        usuario.dias_ativo = (usuario.dias_ativo or 0) + 1
        return True

    @staticmethod
    def _recalcular_nivel(usuario) -> None:
        xp = max(0, usuario.xp or 0)
        nivel = 1
        teto = XP_BASE
        restante = xp
        while restante >= teto:
            restante -= teto
            nivel += 1
            teto = XP_BASE + (nivel - 1) * 500
        usuario.nivel = nivel
        usuario.xp_max = teto

    def _avaliar_conquistas(self, usuario, tipo: str) -> list[str]:
        novas = []
        for codigo, nome, tipo_req, minimo in CONQUISTAS:
            if tipo_req != tipo:
                continue
            contagem = self.repo.contar_atividades(usuario.id, tipo_req)
            if contagem < minimo:
                continue
            badge = self._garantir_badge(codigo, nome)
            if self.repo.usuario_badge(usuario.id, badge.id):
                continue
            self.repo.flush(UsuarioBadge(usuario_id=usuario.id, badge_id=badge.id))
            usuario.conquistas = (usuario.conquistas or 0) + 1
            novas.append(nome)
        return novas

    def _garantir_badge(self, codigo: str, nome: str) -> Badge:
        badge = self.repo.badge_por_codigo(codigo)
        if badge:
            return badge
        return self.repo.flush(Badge(nome=nome, codigo=codigo))

    def listar_conquistas(self, usuario_id: int) -> list[dict]:
        rows = self.repo.listar_conquistas(usuario_id)
        return [
            {
                "codigo": badge.codigo or "",
                "nome": badge.nome,
                "quando": ub.conquistado_em.isoformat() if ub.conquistado_em else "",
            }
            for ub, badge in rows
        ]

    def salvar_avatar(self, usuario_id: int, avatar_url: str, cor_avatar: str | None = None) -> dict:
        usuario = self.repo.obter_usuario(usuario_id)
        if usuario is None:
            from app.errors import NaoAutorizado

            raise NaoAutorizado("Autenticação necessária.")
        usuario.avatar_url = avatar_url
        if cor_avatar:
            usuario.cor_avatar = str(cor_avatar)[:9]
        self.repo.persistir(usuario)
        self.registrar_acao(usuario_id, "avatar", usuario_id)
        return {"avatar_url": usuario.avatar_url or "", "cor_avatar": usuario.cor_avatar}
