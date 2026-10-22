"""Associa jogos locais à RAWG e grava a imagem principal (`background_image`).

Regras que valem aqui:

* A imagem é gravada no campo que já existe (`Jogo.capa_url`); o front-end
  e as telas continuam lendo o mesmo campo de sempre.
* Jogo com `capa_url` ou `arquivo_capa` preenchidos é imagem cadastrada:
  só é tocado com `substituir=True`, e `arquivo_capa` nunca é alterado.
* A correspondência com a RAWG nunca é "o primeiro resultado da busca":
  exige nome igual (ignorando acento, marca e pontuação) ou o mesmo slug,
  e na dúvida o jogo fica sem vínculo e é relatado como ambíguo.
* O vínculo (`rawg_id`) é persistido; jogos já vinculados são consultados
  por id, sem nova busca no catálogo.
"""
from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass, field

from app.extensions import db
from app.models.jogo import Jogo
from app.services.rawg_service import (
    RawgChaveInvalida,
    RawgErro,
    RawgIndisponivel,
    RawgLimite,
    RawgNaoConfigurada,
    RawgService,
    imagem_principal,
)

FALHAS_SEGUIDAS_PARA_ABORTAR = 3


def chave_nome(texto: str | None) -> str:
    """Forma de comparação: sem acento, sem ™®©, só letras/dígitos."""
    sem_marca = re.sub(r"[™®©]", "", texto or "")
    decomposto = unicodedata.normalize("NFKD", sem_marca)
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^0-9a-z]+", " ", sem_acento.casefold()).split())


def _ano(texto: str | None) -> str | None:
    achado = re.search(r"(?<!\d)(19|20)\d{2}(?!\d)", texto or "")
    return achado.group(0) if achado else None


def escolher_candidato(jogo: Jogo, candidatos: list[dict]) -> tuple[dict | None, str]:
    """Devolve `(registro, motivo)`. `registro` é None se não houver
    correspondência segura; `motivo` é 'sem_correspondencia' ou 'ambiguo'."""
    alvo = chave_nome(jogo.nome)
    exatos: dict[int, dict] = {}
    for item in candidatos:
        identificador = item.get("id")
        if not isinstance(identificador, int):
            continue
        mesmo_nome = chave_nome(item.get("name")) == alvo and alvo != ""
        mesmo_slug = bool(jogo.slug) and item.get("slug") == jogo.slug
        if mesmo_nome or mesmo_slug:
            exatos[identificador] = item

    if not exatos:
        return None, "sem_correspondencia"
    if len(exatos) == 1:
        return next(iter(exatos.values())), "ok"

    por_slug = [i for i in exatos.values() if jogo.slug and i.get("slug") == jogo.slug]
    if len(por_slug) == 1:
        return por_slug[0], "ok"

    ano = _ano(jogo.data_lancamento)
    if ano:
        por_ano = [i for i in exatos.values() if _ano(i.get("released")) == ano]
        if len(por_ano) == 1:
            return por_ano[0], "ok"
    return None, "ambiguo"


@dataclass
class Resumo:
    analisados: int = 0
    atualizados: int = 0
    vinculados_sem_imagem: int = 0
    ja_tinham_imagem: int = 0
    sem_correspondencia: list[str] = field(default_factory=list)
    ambiguos: list[str] = field(default_factory=list)
    conflitos: list[str] = field(default_factory=list)
    erros: list[str] = field(default_factory=list)
    abortado: str | None = None


class RawgImagemService:
    def __init__(self, rawg: RawgService | None = None, pausa: float = 0.25) -> None:
        self._rawg = rawg
        self.pausa = pausa

    @property
    def rawg(self) -> RawgService:
        if self._rawg is None:
            self._rawg = RawgService()
        return self._rawg

    # ------------------------------------------------------------------
    @staticmethod
    def tem_imagem_cadastrada(jogo: Jogo) -> bool:
        return bool((jogo.capa_url or "").strip() or (jogo.arquivo_capa or "").strip())

    @staticmethod
    def _dono_do_rawg_id(rawg_id: int, jogo: Jogo) -> Jogo | None:
        return db.session.execute(
            db.select(Jogo).where(Jogo.rawg_id == rawg_id, Jogo.id != jogo.id)
        ).scalars().first()

    def aplicar(
        self, jogo: Jogo, registro: dict, *, substituir: bool = False, gravar: bool = True
    ) -> str:
        """Grava vínculo e imagem. Retorna 'atualizado', 'sem_imagem',
        'ja_tem_imagem' ou 'conflito'."""
        rawg_id = registro.get("id")
        if not isinstance(rawg_id, int):
            return "conflito"
        if jogo.rawg_id not in (None, rawg_id):
            return "conflito"  # já vinculado a outro registro: não sobrescreve
        if self._dono_do_rawg_id(rawg_id, jogo) is not None:
            return "conflito"

        imagem = imagem_principal(registro)
        pode_gravar = substituir or not (jogo.capa_url or "").strip()
        if not pode_gravar:
            resultado = "ja_tem_imagem"
        elif imagem:
            resultado = "atualizado"
        else:
            resultado = "sem_imagem"

        if gravar:
            jogo.rawg_id = rawg_id
            if resultado == "atualizado":
                jogo.capa_url = imagem
            db.session.commit()
        return resultado

    # ------------------------------------------------------------------
    def processar(self, jogo: Jogo, *, substituir: bool = False, gravar: bool = True) -> tuple[str, str]:
        """Retorna `(status, detalhe)` para um jogo."""
        if jogo.rawg_id:
            registro = self.rawg.obter_jogo(jogo.rawg_id)
        else:
            candidatos = self.rawg.buscar_por_nome(jogo.nome)
            registro, motivo = escolher_candidato(jogo, candidatos)
            if registro is None:
                return motivo, jogo.nome
        status = self.aplicar(jogo, registro, substituir=substituir, gravar=gravar)
        return status, f"{jogo.nome} → RAWG #{registro.get('id')}"

    def preencher(
        self,
        *,
        slug: str | None = None,
        limite: int | None = None,
        substituir: bool = False,
        dry_run: bool = False,
        aviso=None,
    ) -> Resumo:
        consulta = db.select(Jogo).order_by(Jogo.id)
        if slug:
            consulta = consulta.where(Jogo.slug == slug)
        elif not substituir:
            consulta = consulta.where(
                db.func.coalesce(Jogo.capa_url, "") == "",
                db.func.coalesce(Jogo.arquivo_capa, "") == "",
            )
        if limite:
            consulta = consulta.limit(limite)

        resumo = Resumo()
        seguidas = 0
        for jogo in db.session.execute(consulta).scalars().all():
            if not substituir and not slug and self.tem_imagem_cadastrada(jogo):
                continue
            resumo.analisados += 1
            try:
                status, detalhe = self.processar(
                    jogo, substituir=substituir, gravar=not dry_run
                )
                seguidas = 0
            except (RawgNaoConfigurada, RawgChaveInvalida, RawgLimite) as exc:
                db.session.rollback()
                resumo.abortado = str(exc)
                break
            except RawgIndisponivel as exc:
                db.session.rollback()
                resumo.erros.append(f"{jogo.nome}: {exc}")
                seguidas += 1
                if seguidas >= FALHAS_SEGUIDAS_PARA_ABORTAR:
                    resumo.abortado = "RAWG indisponível por várias consultas seguidas."
                    break
                continue
            except RawgErro as exc:
                db.session.rollback()
                resumo.erros.append(f"{jogo.nome}: {exc}")
                continue

            if status == "atualizado":
                resumo.atualizados += 1
            elif status == "sem_imagem":
                resumo.vinculados_sem_imagem += 1
            elif status == "ja_tem_imagem":
                resumo.ja_tinham_imagem += 1
            elif status == "sem_correspondencia":
                resumo.sem_correspondencia.append(detalhe)
            elif status == "ambiguo":
                resumo.ambiguos.append(detalhe)
            elif status == "conflito":
                resumo.conflitos.append(detalhe)
            if aviso:
                aviso(status, detalhe)
            if self.pausa:
                time.sleep(self.pausa)
        return resumo

    def vincular(self, jogo: Jogo, rawg_id: int, *, substituir: bool = False) -> str:
        """Vínculo manual (resolve casos ambíguos). Confere o registro."""
        registro = self.rawg.obter_jogo(rawg_id)
        if not isinstance(registro.get("id"), int):
            registro = {**registro, "id": int(rawg_id)}
        return self.aplicar(jogo, registro, substituir=substituir)
