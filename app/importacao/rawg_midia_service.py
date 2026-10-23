"""Imagens, trailers e vídeos da RAWG para a tela de detalhe.

O projeto já guarda a mídia extra fora do banco (`dados/midia_jogos.json`,
lido por `midia_catalogo`). Esta etapa segue o mesmo desenho: grava
`dados/midia_rawg.json`, indexado por slug, que a tela usa só onde o
catálogo original não tem mídia. As telas não consultam a RAWG: leem o
arquivo persistido.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from app.extensions import db
from app.models.jogo import Jogo
from app.services.rawg_service import (
    RawgChaveInvalida, RawgErro, RawgIndisponivel, RawgLimite,
    RawgNaoConfigurada, RawgService,
)

ARQUIVO_PADRAO = Path(__file__).resolve().parents[2] / "dados" / "midia_rawg.json"
MAX_IMAGENS = 8
FALHAS_SEGUIDAS_PARA_ABORTAR = 3


def ler(arquivo: Path) -> dict:
    try:
        dados = json.loads(Path(arquivo).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return dados if isinstance(dados, dict) else {}


def gravar(arquivo: Path, dados: dict) -> None:
    arquivo = Path(arquivo)
    tmp = arquivo.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, arquivo)  # troca atômica: nunca deixa JSON pela metade


class RawgMidiaService:
    def __init__(self, rawg: RawgService | None = None, arquivo: Path | None = None,
                 pausa: float = 0.25) -> None:
        self._rawg = rawg
        self.arquivo = Path(arquivo or ARQUIVO_PADRAO)
        self.pausa = pausa

    @property
    def rawg(self) -> RawgService:
        if self._rawg is None:
            self._rawg = RawgService()
        return self._rawg

    def coletar(self, rawg_id: int) -> dict:
        imagens = [{"src": u, "thumb": u} for u in self.rawg.capturas(rawg_id)[:MAX_IMAGENS]]
        videos = self.rawg.trailers(rawg_id)
        entrada: dict = {"rawg_id": rawg_id, "imagens": imagens}
        if videos:
            entrada["trailer"] = videos[0]
            entrada["videos"] = videos[1:5]
        return entrada

    def preencher(self, *, slug: str | None = None, limite: int | None = None,
                  substituir: bool = False, dry_run: bool = False, aviso=None) -> dict:
        consulta = db.select(Jogo).where(Jogo.rawg_id.is_not(None)).order_by(Jogo.id)
        if slug:
            consulta = consulta.where(Jogo.slug == slug)
        jogos = db.session.execute(consulta).scalars().all()
        sem_vinculo = db.session.execute(
            db.select(db.func.count(Jogo.id)).where(Jogo.rawg_id.is_(None))
        ).scalar_one()

        catalogo = ler(self.arquivo)
        r = {"analisados": 0, "gravados": 0, "sem_midia": 0, "ja_tinham": 0,
             "sem_vinculo": sem_vinculo, "erros": [], "abortado": None}
        seguidas = 0
        for jogo in jogos:
            if jogo.slug in catalogo and not substituir:
                r["ja_tinham"] += 1
                continue
            if limite and r["analisados"] >= limite:
                break
            r["analisados"] += 1
            try:
                entrada = self.coletar(jogo.rawg_id)
                seguidas = 0
            except (RawgNaoConfigurada, RawgChaveInvalida, RawgLimite) as exc:
                r["abortado"] = str(exc)
                break
            except RawgIndisponivel as exc:
                r["erros"].append(f"{jogo.nome}: {exc}")
                seguidas += 1
                if seguidas >= FALHAS_SEGUIDAS_PARA_ABORTAR:
                    r["abortado"] = "RAWG indisponível por várias consultas seguidas."
                    break
                continue
            except RawgErro as exc:
                r["erros"].append(f"{jogo.nome}: {exc}")
                continue
            if not entrada["imagens"] and "trailer" not in entrada:
                r["sem_midia"] += 1
                status = "sem mídia na RAWG"
            else:
                r["gravados"] += 1
                status = f"{len(entrada['imagens'])} imagem(ns)" + (", trailer" if "trailer" in entrada else "")
                if not dry_run:
                    catalogo[jogo.slug] = entrada
                    gravar(self.arquivo, catalogo)  # progresso salvo a cada jogo
            if aviso:
                aviso(status, jogo.nome)
            if self.pausa:
                time.sleep(self.pausa)
        return r
