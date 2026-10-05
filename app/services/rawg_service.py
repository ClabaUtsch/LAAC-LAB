from __future__ import annotations

import os
from typing import Any

import requests


class RawgErro(RuntimeError):
    pass


class RawgService:
    def __init__(self) -> None:
        self.base_url = os.getenv(
            "RAWG_BASE_URL",
            "https://api.rawg.io/api",
        ).rstrip("/")

        self.api_key = os.getenv("RAWG_API_KEY", "").strip()

        if not self.api_key:
            raise RawgErro(
                "RAWG_API_KEY não configurada. "
                "Adicione a chave no arquivo .env."
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "LAAC-LAB-Bugometro/1.0",
            }
        )

    def _get(
        self,
        caminho: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        parametros = dict(params or {})
        parametros["key"] = self.api_key

        try:
            resposta = self.session.get(
                f"{self.base_url}/{caminho.lstrip('/')}",
                params=parametros,
                timeout=20,
            )
            resposta.raise_for_status()
        except requests.RequestException as exc:
            raise RawgErro(
    "Falha ao consultar a RAWG. Confira sua chave, "
    "a conexão e o limite de requisições."
) from exc

        try:
            dados = resposta.json()
        except ValueError as exc:
            raise RawgErro(
                "A RAWG retornou uma resposta que não é JSON válido."
            ) from exc

        if not isinstance(dados, dict):
            raise RawgErro("Formato de resposta inesperado da RAWG.")

        return dados

    def listar_jogos(
        self,
        *,
        pagina: int = 1,
        quantidade: int = 20,
        ordenacao: str = "-added",
        busca: str | None = None,
    ) -> dict[str, Any]:
        quantidade = max(1, min(int(quantidade), 40))
        pagina = max(1, int(pagina))

        params: dict[str, Any] = {
            "page": pagina,
            "page_size": quantidade,
            "ordering": ordenacao,
        }

        if busca:
            params["search"] = busca
            params["search_precise"] = "true"

        return self._get("games", params=params)

    def obter_jogo(self, rawg_id: int) -> dict[str, Any]:
        return self._get(f"games/{int(rawg_id)}")