"""Importação de jogos da RAWG para o banco do LAAC-LAB.

Cada jogo novo já nasce com `rawg_id` e com a imagem principal
(`background_image`) em `capa_url`. Jogo que já existe não é duplicado:
é reconhecido por `rawg_id`, depois por slug e por nome; se estiver sem
vínculo ou sem imagem, só essas lacunas são preenchidas — nada
cadastrado é sobrescrito.
"""
from __future__ import annotations

import time
from typing import Any

from app.extensions import db
from app.models.jogo import Genero, Jogo, JogoGenero, JogoPlataforma, Plataforma
from app.services.jogo_service import gerar_iniciais, gerar_slug, normalizar_busca
from app.services.rawg_service import RawgService, imagem_principal

PAUSA_ENTRE_DETALHES_SEGUNDOS = 0.2


class RawgImportService:
    def __init__(self, rawg: RawgService | None = None, pausa: float = PAUSA_ENTRE_DETALHES_SEGUNDOS) -> None:
        self._rawg = rawg
        self.pausa = pausa

    @property
    def rawg(self) -> RawgService:
        if self._rawg is None:
            self._rawg = RawgService()
        return self._rawg

    # -- helpers --------------------------------------------------------
    @staticmethod
    def _nomes(itens: list[dict[str, Any]] | None) -> str:
        nomes = [str(i.get("name") or "").strip() for i in itens or []]
        return ", ".join(n for n in nomes if n)

    @staticmethod
    def _slug_unico(nome: str, rawg_slug: str | None = None) -> str | None:
        base = gerar_slug(nome) or (gerar_slug(rawg_slug) if rawg_slug else "")
        if not base:
            return None
        slug, sufixo = base, 2
        while db.session.execute(
            db.select(Jogo.id).where(Jogo.slug == slug)
        ).scalars().first() is not None:
            slug = f"{base}-{sufixo}"
            sufixo += 1
        return slug

    @staticmethod
    def _buscar_existente(rawg_id: int | None, nome: str, slug_rawg: str | None) -> Jogo | None:
        if rawg_id is not None:
            jogo = db.session.execute(
                db.select(Jogo).where(Jogo.rawg_id == rawg_id)
            ).scalars().first()
            if jogo is not None:
                return jogo
        for slug in {gerar_slug(nome), gerar_slug(slug_rawg or "")} - {""}:
            jogo = db.session.execute(
                db.select(Jogo).where(Jogo.slug == slug)
            ).scalars().first()
            if jogo is not None:
                return jogo
        return db.session.execute(
            db.select(Jogo).where(Jogo.nome_busca == normalizar_busca(nome))
        ).scalars().first()

    @staticmethod
    def _obter_ou_criar_genero(nome: str, slug: str | None) -> Genero:
        slug_local = gerar_slug(slug or nome)
        genero = None
        if slug_local:
            genero = db.session.execute(
                db.select(Genero).where(Genero.slug == slug_local)
            ).scalars().first()
        if genero is None:
            genero = db.session.execute(
                db.select(Genero).where(Genero.nome == nome)
            ).scalars().first()
        if genero is None:
            genero = Genero(nome=nome[:80], slug=slug_local[:90] if slug_local else None)
            db.session.add(genero)
            db.session.flush()
        return genero

    @staticmethod
    def _obter_ou_criar_plataforma(nome: str) -> Plataforma:
        nome = nome.strip()[:50]
        plataforma = db.session.execute(
            db.select(Plataforma).where(Plataforma.nome == nome)
        ).scalars().first()
        if plataforma is None:
            plataforma = Plataforma(nome=nome)
            db.session.add(plataforma)
            db.session.flush()
        return plataforma

    def _associar_generos(self, jogo: Jogo, generos: list[dict] | None) -> None:
        for item in generos or []:
            nome = str(item.get("name") or "").strip()
            if not nome:
                continue
            genero = self._obter_ou_criar_genero(nome, item.get("slug"))
            if db.session.execute(
                db.select(JogoGenero).where(
                    JogoGenero.jogo_id == jogo.id, JogoGenero.genero_id == genero.id
                )
            ).scalars().first() is None:
                db.session.add(JogoGenero(jogo_id=jogo.id, genero_id=genero.id))

    def _associar_plataformas(self, jogo: Jogo, plataformas: list[dict] | None) -> None:
        for item in plataformas or []:
            nome = str((item.get("platform") or {}).get("name") or "").strip()
            if not nome:
                continue
            plataforma = self._obter_ou_criar_plataforma(nome)
            if db.session.execute(
                db.select(JogoPlataforma).where(
                    JogoPlataforma.jogo_id == jogo.id,
                    JogoPlataforma.plataforma_id == plataforma.id,
                )
            ).scalars().first() is None:
                db.session.add(JogoPlataforma(jogo_id=jogo.id, plataforma_id=plataforma.id))

    def _montar_jogo(self, resumo: dict, detalhe: dict | None, slug: str | None) -> Jogo:
        fonte = detalhe or resumo
        nome = str(fonte.get("name") or resumo.get("name") or "").strip()
        descricao = str(fonte.get("description_raw") or fonte.get("description") or "").strip()
        desenvolvedora = self._nomes(fonte.get("developers"))
        publicadora = self._nomes(fonte.get("publishers"))
        metacritic = fonte.get("metacritic")
        if not isinstance(metacritic, int):
            metacritic = None
        try:
            popularidade = max(0, int(resumo.get("added") or 0))
        except (TypeError, ValueError):
            popularidade = 0
        return Jogo(
            rawg_id=resumo.get("id") if isinstance(resumo.get("id"), int) else None,
            nome=nome[:200],
            slug=slug[:140] if slug else None,
            nome_busca=normalizar_busca(nome),
            iniciais=gerar_iniciais(nome),
            descricao=descricao or None,
            desenvolvedora=desenvolvedora[:200] or None,
            publicadora=publicadora[:200] or None,
            data_lancamento=str(fonte.get("released") or resumo.get("released") or "")[:60] or None,
            metacritic=metacritic,
            capa_url=imagem_principal(fonte) or imagem_principal(resumo) or None,
            popularidade=popularidade,
        )

    # -- fluxo ----------------------------------------------------------
    def _completar_existente(self, jogo: Jogo, resumo: dict) -> bool:
        """Preenche só o que falta (vínculo e imagem). True se mudou algo."""
        mudou = False
        rawg_id = resumo.get("id")
        if jogo.rawg_id is None and isinstance(rawg_id, int):
            livre = db.session.execute(
                db.select(Jogo.id).where(Jogo.rawg_id == rawg_id)
            ).scalars().first() is None
            if livre:
                jogo.rawg_id = rawg_id
                mudou = True
        if (
            jogo.rawg_id == rawg_id
            and not (jogo.capa_url or "").strip()
            and not (jogo.arquivo_capa or "").strip()
        ):
            imagem = imagem_principal(resumo)
            if imagem:
                jogo.capa_url = imagem
                mudou = True
        if mudou:
            db.session.commit()
        return mudou

    def importar(
        self,
        *,
        quantidade: int = 20,
        detalhes: bool = True,
        ordenacao: str = "-added",
        busca: str | None = None,
    ) -> dict[str, Any]:
        quantidade = max(1, int(quantidade))
        importados = ignorados = encontrados = atualizados = 0
        erros: list[str] = []
        pagina = 1
        por_pagina = min(40, quantidade)

        while encontrados < quantidade:
            resposta = self.rawg.listar_jogos(
                pagina=pagina, quantidade=por_pagina, ordenacao=ordenacao, busca=busca
            )
            resultados = resposta.get("results") or []
            if not resultados:
                break

            for resumo in resultados:
                if encontrados >= quantidade:
                    break
                encontrados += 1
                nome = str(resumo.get("name") or "").strip()
                rawg_id = resumo.get("id") if isinstance(resumo.get("id"), int) else None
                if not nome:
                    erros.append(f"Item RAWG sem nome (id={resumo.get('id')}).")
                    continue

                existente = self._buscar_existente(rawg_id, nome, resumo.get("slug"))
                if existente is not None:
                    if self._completar_existente(existente, resumo):
                        atualizados += 1
                    else:
                        ignorados += 1
                    continue

                try:
                    info = None
                    if detalhes and rawg_id is not None:
                        info = self.rawg.obter_jogo(rawg_id)
                        if self.pausa:
                            time.sleep(self.pausa)
                    jogo = self._montar_jogo(resumo, info, self._slug_unico(nome, resumo.get("slug")))
                    db.session.add(jogo)
                    db.session.flush()
                    self._associar_generos(jogo, resumo.get("genres"))
                    self._associar_plataformas(jogo, resumo.get("platforms"))
                    db.session.commit()
                    importados += 1
                except Exception as exc:  # um jogo ruim não derruba o lote
                    db.session.rollback()
                    erros.append(f"{nome}: {exc}")

            pagina += 1
            if not resposta.get("next"):
                break

        return {
            "solicitados": quantidade,
            "encontrados": encontrados,
            "importados": importados,
            "atualizados": atualizados,
            "ignorados": ignorados,
            "erros": erros,
        }
