"""Vitrine externa: normalização sem rede, e o endpoint desligado na suíte."""
from app.integracoes.vitrine_externa import obter_vitrine


def _loja():
    return {
        "new_releases": {
            "items": [
                {
                    "id": 10,
                    "name": "Hades II",
                    "header_image": "https://cdn.cloudflare.steamstatic.com/steam/apps/10/header.jpg",
                },
                {
                    "id": "javascript:alert(1)",
                    "name": "Injeção",
                    "header_image": "javascript:alert(1)",
                },
            ]
        },
        "coming_soon": {
            "items": [
                {
                    "id": 11,
                    "name": "Silksong",
                    "large_capsule_image": "https://shared.akamai.steamstatic.com/x.jpg",
                }
            ]
        },
        "specials": {
            "items": [
                {
                    "id": 12,
                    "name": "Celeste",
                    "discounted": True,
                    "discount_percent": 50,
                    "header_image": "https://evil.example/a.jpg",
                }
            ]
        },
    }


def _noticias():
    return {
        "appnews": {
            "newsitems": [
                {
                    "title": "Patch [b]1.2[/b]",
                    "contents": "<b>Corrigiu</b> o crash do ato 2",
                    "url": "https://store.steampowered.com/news/app/10",
                    "date": 1_700_000_000,
                },
                {
                    "title": "Fora",
                    "url": "javascript:alert(1)",
                    "contents": "x",
                    "date": "nao",
                },
            ]
        }
    }


def _buscar(url):
    if "featuredcategories" in url:
        return _loja()
    if "GetNewsForApp" in url:
        return _noticias()
    raise AssertionError(url)


def test_steam_limpa_html_e_recusa_url_fora_da_loja():
    corpo = obter_vitrine(
        buscar=_buscar,
        habilitado=True,
        cache={"ate": 0.0, "corpo": {"itens": [], "fonte": ""}},
        relogio=lambda: 0,
    )
    assert corpo["fonte"] == "Steam"
    por_titulo = {item["titulo"]: item for item in corpo["itens"]}

    hades = por_titulo["Hades II"]
    assert hades["tipo"] == "lancamento"
    assert hades["imagem_capa"].startswith("https://cdn.cloudflare.steamstatic.com/")
    assert hades["url_externa"] == "https://store.steampowered.com/app/10"
    assert hades["jogo_slug"] == ""

    celeste = por_titulo["Celeste"]
    assert celeste["tipo"] == "oferta"
    assert celeste["imagem_capa"] == ""
    assert "50" in celeste["resumo"]

    injecao = por_titulo["Injeção"]
    assert injecao["url_externa"] == ""
    assert injecao["imagem_capa"] == ""

    patch = por_titulo["Patch 1.2"]
    assert patch["tipo"] == "noticia"
    assert "<" not in patch["resumo"]
    assert "[b]" not in patch["titulo"]
    assert patch["url_externa"].startswith("https://store.steampowered.com/")

    fora = por_titulo["Fora"]
    assert fora["url_externa"] == ""


def test_cache_nao_repete_a_rede():
    chamadas = {"n": 0}
    cache = {"ate": 0.0, "corpo": {"itens": [], "fonte": ""}}

    def buscar(url):
        chamadas["n"] += 1
        return _buscar(url)

    obter_vitrine(buscar=buscar, habilitado=True, cache=cache, relogio=lambda: 10)
    primeiro = chamadas["n"]
    de_novo = obter_vitrine(buscar=buscar, habilitado=True, cache=cache, relogio=lambda: 20)
    assert primeiro >= 1
    assert chamadas["n"] == primeiro
    assert de_novo["itens"]


def test_fonte_desligada_nao_chama_a_rede():
    def buscar(_url):
        raise AssertionError("não deveria buscar")

    assert obter_vitrine(buscar=buscar, habilitado=False) == {"itens": [], "fonte": ""}


def test_endpoint_exige_sessao_e_vem_vazio_na_suíte(cliente):
    assert cliente.get("/api/v1/telas/vitrine").status_code == 401

    entrada = cliente.post(
        "/api/auth/registro",
        json={"nome_usuario": "vitrine", "email": "vitrine@l.dev", "senha": "senha123"},
    ).get_json()
    corpo = cliente.get(
        "/api/v1/telas/vitrine",
        headers={"Authorization": f"Bearer {entrada['token_acesso']}"},
    ).get_json()
    assert corpo == {"itens": [], "fonte": ""}
