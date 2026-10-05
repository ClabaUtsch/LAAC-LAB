from __future__ import annotations

import time
from typing import Any

from app.extensions import db
from app.models.jogo import (
    Genero,
    Jogo,
    JogoGenero,
    JogoPlataforma,
    Plataforma,
)
from app.services.jogo_service import (
    gerar_iniciais,
    gerar_slug,
    normalizar_busca,
)
from app.services.rawg_service import RawgService

PAUSA_ENTRE_DETALHES_SEGUNDOS = 0.2


class RawgImportService:
    def __init__(self, rawg: RawgService | None = None) -> None:
        self.rawg = rawg or RawgService()

    @staticmethod
    def _nomes(itens: list[dict[str, Any]] | None) -> str:
        nomes: list[str] = []

        for item in itens or []:
            nome = str(item.get("name") or "").strip()
            if nome:
                nomes.append(nome)

        return ", ".join(nomes)

    @staticmethod
    def _slug_unico(nome: str, rawg_slug: str | None = None) -> str | None:
        base = gerar_slug(nome) or (gerar_slug(rawg_slug) if rawg_slug else "")

        if not base:
            return None

        slug = base
        sufixo = 2

        while db.session.execute(
            db.select(Jogo.id).where(Jogo.slug == slug)
        ).scalars().first() is not None:
            slug = f"{base}-{sufixo}"
            sufixo += 1

        return slug

    @staticmethod
    def _buscar_jogo_existente(nome: str, slug: str | None) -> Jogo | None:
        if slug:
            jogo = db.session.execute(
                db.select(Jogo).where(Jogo.slug == slug)
            ).scalars().first()

            if jogo is not None:
                return jogo

        nome_busca = normalizar_busca(nome)

        return db.session.execute(
            db.select(Jogo).where(Jogo.nome_busca == nome_busca)
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
            genero = Genero(
                nome=nome[:80],
                slug=slug_local[:90] if slug_local else None,
            )
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

    def _associar_generos(
        self,
        jogo: Jogo,
        generos_rawg: list[dict[str, Any]] | None,
    ) -> None:
        for item in generos_rawg or []:
            nome = str(item.get("name") or "").strip()

            if not nome:
                continue

            genero = self._obter_ou_criar_genero(nome, item.get("slug"))

            existe = db.session.execute(
                db.select(JogoGenero).where(
                    JogoGenero.jogo_id == jogo.id,
                    JogoGenero.genero_id == genero.id,
                )
            ).scalars().first()

            if existe is None:
                db.session.add(
                    JogoGenero(jogo_id=jogo.id, genero_id=genero.id)
                )

    def _associar_plataformas(
        self,
        jogo: Jogo,
        plataformas_rawg: list[dict[str, Any]] | None,
    ) -> None:
        for item in plataformas_rawg or []:
            dados = item.get("platform") or {}
            nome = str(dados.get("name") or "").strip()

            if not nome:
                continue

            plataforma = self._obter_ou_criar_plataforma(nome)

            existe = db.session.execute(
                db.select(JogoPlataforma).where(
                    JogoPlataforma.jogo_id == jogo.id,
                    JogoPlataforma.plataforma_id == plataforma.id,
                )
            ).scalars().first()

            if existe is None:
                db.session.add(
                    JogoPlataforma(
                        jogo_id=jogo.id,
                        plataforma_id=plataforma.id,
                    )
                )

    def _montar_jogo(
        self,
        resumo: dict[str, Any],
        info_detalhada: dict[str, Any] | None,
        slug: str | None,
    ) -> Jogo:
        fonte = info_detalhada or resumo

        nome = str(fonte.get("name") or resumo.get("name") or "").strip()

        descricao = str(
            fonte.get("description_raw") or fonte.get("description") or ""
        ).strip()

        desenvolvedora = self._nomes(fonte.get("developers"))
        publicadora = self._nomes(fonte.get("publishers"))

        metacritic = fonte.get("metacritic")

        if not isinstance(metacritic, int):
            metacritic = None

        popularidade = resumo.get("added") or 0

        try:
            popularidade = int(popularidade)
        except (TypeError, ValueError):
            popularidade = 0

        return Jogo(
            nome=nome[:200],
            slug=slug[:140] if slug else None,
            nome_busca=normalizar_busca(nome),
            iniciais=gerar_iniciais(nome),
            descricao=descricao or None,
            desenvolvedora=desenvolvedora[:200] or None,
            publicadora=publicadora[:200] or None,
            data_lancamento=str(
                fonte.get("released") or resumo.get("released") or ""
            )[:60] or None,
            metacritic=metacritic,
            capa_url=(
                fonte.get("background_image") or resumo.get("background_image")
            ),
            popularidade=max(0, popularidade),
        )

    def importar(
        self,
        *,
        quantidade: int = 20,
        detalhes: bool = True,
        ordenacao: str = "-added",
        busca: str | None = None,
    ) -> dict[str, Any]:
        quantidade = max(1, int(quantidade))

        importados = 0
        ignorados = 0
        encontrados = 0
        erros: list[str] = []

        por_pagina = min(40, quantidade)
        pagina = 1

        while encontrados < quantidade:
            resposta = self.rawg.listar_jogos(
                pagina=pagina,
                quantidade=por_pagina,
                ordenacao=ordenacao,
                busca=busca,
            )


            resultados = resposta.get("results") or []

            if not resultados:
                break

            for resumo in resultados:
                if encontrados >= quantidade:
                    break

                encontrados += 1

                nome = str(resumo.get("name") or "").strip()
                rawg_id = resumo.get("id")

                if not nome:
                    erros.append(f"Item RAWG sem nome (id={rawg_id}).")
                    continue

                slug = self._slug_unico(nome, resumo.get("slug"))
                existente = self._buscar_jogo_existente(nome, slug)

                if existente is not None:
                    ignorados += 1
                    continue

                try:
                    info_detalhada = None

                    if detalhes and rawg_id is not None:
                        info_detalhada = self.rawg.obter_jogo(int(rawg_id))
                        if PAUSA_ENTRE_DETALHES_SEGUNDOS:
                            time.sleep(PAUSA_ENTRE_DETALHES_SEGUNDOS)

                    jogo = self._montar_jogo(resumo, info_detalhada, slug)

                    db.session.add(jogo)
                    db.session.flush()

                    self._associar_generos(jogo, resumo.get("genres"))
                    self._associar_plataformas(jogo, resumo.get("platforms"))

                    db.session.commit()
                    importados += 1

                except Exception as exc:
                    db.session.rollback()
                    erros.append(f"{nome}: {exc}")

            pagina += 1

            if not resposta.get("next"):
                break

        return {
            "solicitados": quantidade,
            "encontrados": encontrados,
            "importados": importados,
            "ignorados": ignorados,
            "erros": erros,
        }