"""Cliente da RAWG Video Games Database API.

Roda só no back-end. A chave vem de `RAWG_API_KEY` (arquivo `.env`) e
nunca é devolvida em resposta, log ou mensagem de erro: as exceções
abaixo são levantadas sem encadear a original (`from None`), porque a
mensagem das exceções do `requests` traz a URL completa — com `?key=`.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests

BASE_PADRAO = "https://api.rawg.io/api"
TIMEOUT_PADRAO = 10.0


class RawgErro(RuntimeError):
    """Falha ao falar com a RAWG. A mensagem nunca contém a chave."""


class RawgNaoConfigurada(RawgErro):
    """`RAWG_API_KEY` ausente."""


class RawgChaveInvalida(RawgErro):
    """A RAWG recusou a chave (401/403)."""


class RawgLimite(RawgErro):
    """Limite de requisições atingido (429)."""


class RawgIndisponivel(RawgErro):
    """Timeout, rede fora do ar ou erro 5xx."""


class RawgRespostaInvalida(RawgErro):
    """A RAWG respondeu algo que não é o JSON esperado."""


class RawgService:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        tentativas: int = 2,
        espera_entre_tentativas: float = 1.0,
        sessao: requests.Session | None = None,
    ) -> None:
        self._api_key = (
            api_key if api_key is not None else os.getenv("RAWG_API_KEY", "")
        ).strip()
        if not self._api_key:
            raise RawgNaoConfigurada(
                "RAWG_API_KEY não configurada. Copie .env.example para .env "
                "e preencha a chave."
            )
        self.base_url = (
            base_url or os.getenv("RAWG_BASE_URL") or BASE_PADRAO
        ).rstrip("/")
        self.timeout = float(
            timeout
            if timeout is not None
            else os.getenv("RAWG_TIMEOUT") or TIMEOUT_PADRAO
        )
        self.tentativas = max(1, int(tentativas))
        self.espera = espera_entre_tentativas
        self.sessao = sessao or requests.Session()
        self.sessao.headers.update(
            {"Accept": "application/json", "User-Agent": "LAAC-LAB-Bugometro/1.0"}
        )

    def __repr__(self) -> str:  # nunca expõe a chave
        return f"<RawgService base_url={self.base_url!r}>"

    # ------------------------------------------------------------------
    def _get(self, caminho: str, params: dict[str, Any] | None = None) -> dict:
        parametros = dict(params or {})
        parametros["key"] = self._api_key
        url = f"{self.base_url}/{caminho.lstrip('/')}"
        ultimo: RawgErro | None = None

        for tentativa in range(1, self.tentativas + 1):
            try:
                resposta = self.sessao.get(url, params=parametros, timeout=self.timeout)
            except requests.Timeout:
                ultimo = RawgIndisponivel("Tempo esgotado ao consultar a RAWG.")
            except requests.RequestException:
                ultimo = RawgIndisponivel("RAWG indisponível (falha de conexão).")
            else:
                status = resposta.status_code
                if status in (401, 403):
                    raise RawgChaveInvalida(
                        "A RAWG recusou a chave (RAWG_API_KEY inválida ou sem permissão)."
                    ) from None
                if status == 404:
                    raise RawgRespostaInvalida(
                        "Registro não encontrado na RAWG."
                    ) from None
                if status == 429:
                    raise RawgLimite(
                        "Limite de requisições da RAWG atingido. Tente mais tarde."
                    ) from None
                if status >= 500:
                    ultimo = RawgIndisponivel(f"RAWG indisponível (HTTP {status}).")
                elif status >= 400:
                    raise RawgErro(f"A RAWG recusou a consulta (HTTP {status}).") from None
                else:
                    try:
                        dados = resposta.json()
                    except ValueError:
                        raise RawgRespostaInvalida(
                            "A RAWG devolveu uma resposta que não é JSON."
                        ) from None
                    if not isinstance(dados, dict):
                        raise RawgRespostaInvalida(
                            "Formato de resposta inesperado da RAWG."
                        ) from None
                    return dados

            if tentativa < self.tentativas and self.espera:
                time.sleep(self.espera * tentativa)

        assert ultimo is not None
        raise ultimo from None

    # ------------------------------------------------------------------
    def listar_jogos(
        self,
        *,
        pagina: int = 1,
        quantidade: int = 20,
        ordenacao: str = "-added",
        busca: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {
            "page": max(1, int(pagina)),
            "page_size": max(1, min(int(quantidade), 40)),
            "ordering": ordenacao,
        }
        if busca:
            params["search"] = busca
            params["search_precise"] = "true"
        return self._get("games", params)

    def buscar_por_nome(self, nome: str, quantidade: int = 10) -> list[dict]:
        """Candidatos para `nome`. A escolha é de quem chama: este método
        não decide qual resultado é o jogo certo."""
        dados = self.listar_jogos(
            quantidade=quantidade, busca=nome, ordenacao="-added"
        )
        resultados = dados.get("results")
        return [r for r in resultados if isinstance(r, dict)] if isinstance(resultados, list) else []

    def obter_jogo(self, rawg_id: int) -> dict:
        return self._get(f"games/{int(rawg_id)}")

    def capturas(self, rawg_id: int) -> list[str]:
        """URLs https das capturas de tela do jogo."""
        dados = self._get(f"games/{int(rawg_id)}/screenshots", {"page_size": 20})
        itens = dados.get("results") if isinstance(dados.get("results"), list) else []
        urls = [str((i or {}).get("image") or "").strip() for i in itens if isinstance(i, dict)]
        return [u for u in urls if u.lower().startswith("https://")]

    def trailers(self, rawg_id: int) -> list[dict]:
        """Vídeos do jogo: `[{titulo, mp4, thumb}]` (só https)."""
        dados = self._get(f"games/{int(rawg_id)}/movies")
        itens = dados.get("results") if isinstance(dados.get("results"), list) else []
        saida = []
        for item in itens:
            if not isinstance(item, dict):
                continue
            arq = item.get("data") if isinstance(item.get("data"), dict) else {}
            mp4 = str(arq.get("max") or arq.get("480") or "").strip()
            if not mp4.lower().startswith("https://"):
                continue
            thumb = str(item.get("preview") or "").strip()
            saida.append({
                "titulo": str(item.get("name") or "Trailer").strip() or "Trailer",
                "mp4": mp4,
                "thumb": thumb if thumb.lower().startswith("https://") else "",
            })
        return saida


def imagem_principal(registro: dict | None) -> str:
    """`background_image` válido (https) ou string vazia."""
    url = ((registro or {}).get("background_image") or "").strip()
    return url if url.lower().startswith("https://") else ""
