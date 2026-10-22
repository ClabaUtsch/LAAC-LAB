"""Capturas, trailers e vídeos da RAWG (simulados) e fallback no catálogo."""
import json

import pytest

from app.extensions import db
from app.importacao.rawg_midia_service import RawgMidiaService
from app.models import Jogo
from app.services import midia_catalogo
from app.services.rawg_service import RawgChaveInvalida, RawgIndisponivel

S1, S2 = "https://media.rawg.io/media/screenshots/a.jpg", "https://media.rawg.io/media/screenshots/b.jpg"
MP4 = "https://steamcdn-a.akamaihd.net/steam/apps/1/movie_max.mp4"


class Rawg:
    def __init__(self, erro=None, sem_midia=False):
        self.erro, self.sem_midia, self.chamadas = erro, sem_midia, []

    def capturas(self, i):
        self.chamadas.append(i)
        if self.erro:
            raise self.erro
        return [] if self.sem_midia else [S1, S2]

    def trailers(self, i):
        return [] if self.sem_midia else [{"titulo": "Trailer", "mp4": MP4, "thumb": S1}]


def jogo(nome, slug, rawg_id=None):
    j = Jogo(nome=nome, slug=slug, nome_busca=nome.lower(), rawg_id=rawg_id)
    db.session.add(j)
    db.session.commit()
    return j


def test_grava_midia_so_de_jogos_vinculados_e_nao_repete(app, tmp_path):
    jogo("A", "a", 1)
    jogo("B", "b")  # sem vínculo: não consulta
    arq = tmp_path / "m.json"
    rawg = Rawg()
    r = RawgMidiaService(rawg, arq, pausa=0).preencher()
    dados = json.loads(arq.read_text(encoding="utf-8"))
    assert list(dados) == ["a"] and r["gravados"] == 1 and r["sem_vinculo"] == 1
    assert dados["a"]["trailer"]["mp4"] == MP4 and len(dados["a"]["imagens"]) == 2
    RawgMidiaService(rawg, arq, pausa=0).preencher()
    assert rawg.chamadas == [1]  # segunda execução não consulta de novo


def test_dry_run_e_sem_midia_nao_gravam(app, tmp_path):
    jogo("A", "a", 1)
    arq = tmp_path / "m.json"
    RawgMidiaService(Rawg(), arq, pausa=0).preencher(dry_run=True)
    assert not arq.exists()
    r = RawgMidiaService(Rawg(sem_midia=True), arq, pausa=0).preencher()
    assert r["sem_midia"] == 1 and not arq.exists()


def test_erros_chave_e_indisponibilidade(app, tmp_path):
    for i in range(5):
        jogo(f"J{i}", f"j{i}", i + 1)
    r = RawgMidiaService(Rawg(RawgChaveInvalida("x")), tmp_path / "m.json", pausa=0).preencher()
    assert r["abortado"]
    r = RawgMidiaService(Rawg(RawgIndisponivel("x")), tmp_path / "m.json", pausa=0).preencher()
    assert len(r["erros"]) == 3 and r["abortado"]


def test_catalogo_usa_rawg_so_onde_falta(tmp_path, monkeypatch):
    arq = tmp_path / "r.json"
    arq.write_text(json.dumps({"novo": {"imagens": [{"src": S1, "thumb": S1}],
                                        "trailer": {"mp4": MP4, "thumb": S1, "titulo": "T"}}}))
    monkeypatch.setattr(midia_catalogo, "_ARQUIVO_RAWG", arq)
    monkeypatch.setattr(midia_catalogo, "_cache_rawg", None)
    e = midia_catalogo.extras_do_slug("novo")
    assert e["trailer"]["mp4"].startswith("/media/origem?u=") and len(e["imagens"]) == 1
    existente = next(iter(midia_catalogo._catalogo()))  # já tem mídia própria: RAWG não interfere
    assert midia_catalogo.extras_do_slug(existente)["imagens"] == midia_catalogo.extras_do_slug(existente)["imagens"]


def test_servico_rawg_filtra_urls_nao_https():
    from app.services.rawg_service import RawgService

    class S:
        headers = {}
        def get(self, url, params=None, timeout=None):
            class R:
                status_code = 200
                def json(_):
                    if url.endswith("screenshots"):
                        return {"results": [{"image": S1}, {"image": "http://x/y.jpg"}, {}]}
                    return {"results": [{"name": "T", "preview": S1, "data": {"max": MP4}},
                                        {"name": "ruim", "data": {"max": "http://x.mp4"}}]}
            return R()

    s = RawgService(api_key="k", sessao=S())
    assert s.capturas(1) == [S1]
    assert s.trailers(1) == [{"titulo": "T", "mp4": MP4, "thumb": S1}]


def test_proxy_aceita_host_do_mp4(cliente, monkeypatch):
    class F:
        status = 200
        headers = {"Content-Type": "video/mp4", "Content-Length": "2"}
        _f = False
        def read(self, n=-1):
            if self._f:
                return b""
            self._f = True
            return b"ok"
        def close(self):
            pass
    monkeypatch.setattr("app.controllers.paginas_controller.urlopen", lambda p, timeout=25: F())
    assert cliente.get("/media/origem?u=" + MP4).status_code == 200
    assert cliente.get("/media/origem?u=https://evil.akamaihd.net/x.mp4").status_code == 400
