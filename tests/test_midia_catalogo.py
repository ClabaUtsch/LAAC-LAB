import json
from pathlib import Path

from app.services.jogo_service import gerar_slug
from app.services.midia_catalogo import extras_do_slug

RAIZ = Path(__file__).resolve().parents[1]


def test_palworld_traz_trailer_imagens_historia_e_requisitos():
    extras = extras_do_slug("palworld")
    assert extras["legenda"]
    assert "Pals" in extras["historia"]
    assert extras["tempo_medio"] == "40h"
    trailer = extras["trailer"] or {}
    assert trailer["embed"].startswith("https://www.youtube.com/embed/")
    assert extras["imagens"][0]["src"].startswith("/estatico/vitrine/palworld/")
    assert len(extras["imagens"]) >= 4
    assert extras["requisitos"]["minimo"]
    assert extras["requisitos"]["recomendado"]


def test_slug_com_marca_e_sem_marca_acham_a_mesma_midia():
    com_tm = extras_do_slug("helldiverstm-2")
    sem_tm = extras_do_slug("helldivers-2")
    assert com_tm["trailer"]["embed"] == sem_tm["trailer"]["embed"]
    assert sem_tm["imagens"]
    assert gerar_slug("Helldivers™ 2") == "helldivers-2"
    extras = extras_do_slug("jogo-que-nao-existe")
    assert extras["imagens"] == []
    assert extras["trailer"] is None
    assert extras["requisitos"]["minimo"] == []
    assert extras["tags"] == []


def test_catalogo_usa_youtube_como_o_palworld():
    jogos = json.loads((RAIZ / "dados" / "jogos_steam.json").read_text(encoding="utf-8"))
    for jogo in jogos:
        slug = jogo.get("slug") or gerar_slug(jogo["name"])
        extras = extras_do_slug(slug)
        trailer = extras["trailer"] or {}
        assert (trailer.get("embed") or "").startswith("https://www.youtube.com/embed/"), slug
        assert extras["imagens"][0]["src"].startswith("/estatico/vitrine/"), slug
        assert all(f["src"].startswith("/estatico/vitrine/") for f in extras["imagens"]), slug
        assert extras["tempo_medio"], slug
