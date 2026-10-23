"""Vitrine ao vivo: lançamentos, em breve, ofertas e notícias.

A Steam Store (`featuredcategories` + `ISteamNews`) não exige chave e
já é a origem da mídia do catálogo. Se `RAWG_API_KEY` existir, a RAWG
entra no lugar dos destaques da loja — a notícia continua sendo texto
limpo, nunca HTML.

O resultado fica em memória por 15 minutos. A home não pode esperar a
rede a cada abertura, e um único payload cabe num dicionário: não há
lista que cresça com o tempo.
"""
import html
import json
import logging
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from app.services.formatacao import tempo_relativo
from app.services.jogo_service import CAPA_PADRAO

_LOG = logging.getLogger("laac.vitrine")
_TRAVA = threading.Lock()
_CACHE = {"ate": 0.0, "corpo": {"itens": [], "fonte": ""}}

TTL_SEGUNDOS = 15 * 60
_TIMEOUT = 4.0
_LIMITE = 8

_URL_DESTAQUES = (
    "https://store.steampowered.com/api/featuredcategories?cc=br&l=brazilian"
)
_URL_NOTICIAS = (
    "https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/"
    "?appid={appid}&count=2&maxlength=240&format=json"
)

_GRUPOS_STEAM = (
    ("new_releases", "lancamento", "Lançamento", "Acabou de sair na Steam"),
    ("coming_soon", "embreve", "Em breve", "Lançamento previsto na Steam"),
    ("specials", "oferta", "Oferta", "Promoção na Steam"),
)

_SUFIXOS_IMAGEM = ("steamstatic.com", "akamaihd.net", "steampowered.com", "rawg.io")
_SUFIXOS_LINK = ("steampowered.com", "steamcommunity.com", "rawg.io")


def obter_vitrine(limite: int = _LIMITE, buscar=None, habilitado: bool = True,
                  relogio=None, cache=None) -> dict:
    """Envelope `{itens, fonte}`. Falha de rede devolve o cache ou vazio.

    `buscar` e `cache` existem para o teste não abrir socket. Em produção
    os dois ficam vazios e vale o cache do módulo.
    """
    if not habilitado:
        return {"itens": [], "fonte": ""}
    if cache is None:
        with _TRAVA:
            return _resolver(limite, buscar, relogio, _CACHE)
    return _resolver(limite, buscar, relogio, cache)


def _resolver(limite, buscar, relogio, memoria) -> dict:
    agora = relogio() if relogio else time.monotonic()
    guardado = memoria.get("corpo") or {"itens": [], "fonte": ""}
    if agora < float(memoria.get("ate") or 0) and guardado.get("itens"):
        return _recortar(guardado, limite)

    baixar = buscar or _baixar_json
    try:
        corpo = _montar(baixar)
    except Exception:
        # Sem exc_info: a URL da RAWG carrega a chave, e a mensagem
        # padrão do urllib repete essa URL.
        _LOG.warning("vitrine externa indisponivel")
        return _recortar(guardado, limite)

    if corpo["itens"]:
        memoria["ate"] = agora + TTL_SEGUNDOS
        memoria["corpo"] = corpo
    return _recortar(corpo, limite)


def _montar(buscar) -> dict:
    chave = os.getenv("RAWG_API_KEY", "").strip()
    if chave:
        return {"itens": _itens_rawg(buscar, chave), "fonte": "RAWG"}
    return {"itens": _itens_steam(buscar), "fonte": "Steam"}


def _recortar(corpo: dict, limite: int) -> dict:
    itens = corpo.get("itens") if isinstance(corpo, dict) else None
    if not isinstance(itens, list):
        itens = []
    return {"itens": itens[: max(0, limite)], "fonte": (corpo or {}).get("fonte") or ""}


def _baixar_json(url: str) -> dict:
    pedido = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LaaCLab/1.0)",
            "Accept": "application/json",
            "Accept-Language": "pt-BR,pt;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(pedido, timeout=_TIMEOUT) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeError) as erro:
        raise RuntimeError("fonte externa") from erro


def _itens_steam(buscar) -> list[dict]:
    bruto = buscar(_URL_DESTAQUES)
    if not isinstance(bruto, dict):
        return []

    vistos = set()
    grupos = []
    imagem_por_app = {}
    app_noticia = 0
    for chave, tipo, rotulo, frase in _GRUPOS_STEAM:
        bloco = bruto.get(chave) or {}
        crus = bloco.get("items") if isinstance(bloco, dict) else None
        if not isinstance(crus, list):
            continue
        grupo = []
        for cru in crus[:4]:
            if not isinstance(cru, dict):
                continue
            item = _item_de_loja(cru, tipo, rotulo, frase, vistos)
            if item is None:
                continue
            grupo.append(item)
            appid = _appid(cru.get("id"))
            if appid and item["imagem_capa"]:
                imagem_por_app[appid] = item["imagem_capa"]
            if appid and not app_noticia and tipo == "lancamento":
                app_noticia = appid
        if grupo:
            grupos.append(grupo)

    if not app_noticia and imagem_por_app:
        app_noticia = next(iter(imagem_por_app))
    noticias = _noticias_de_app(
        buscar, app_noticia, imagem_por_app.get(app_noticia, ""), vistos
    )
    if noticias:
        grupos.append(noticias)
    return _intercalar(grupos, _LIMITE)


def _item_de_loja(cru: dict, tipo: str, rotulo: str, frase: str, vistos: set):
    nome = _limpo(cru.get("name"), 120)
    if not nome:
        return None
    appid = _appid(cru.get("id"))
    imagem = ""
    for campo in ("header_image", "large_capsule_image", "small_capsule_image"):
        imagem = _url_permitida(cru.get(campo), _SUFIXOS_IMAGEM)
        if imagem:
            break
    url = ""
    if appid:
        url = _url_permitida(
            f"https://store.steampowered.com/app/{appid}", _SUFIXOS_LINK
        )
    return _montar_item(
        tipo=tipo,
        rotulo=rotulo,
        jogo=nome,
        titulo=nome,
        resumo=_resumo_preco(cru, frase),
        quando="agora",
        imagem=imagem,
        url=url,
        vistos=vistos,
    )


def _noticias_de_app(buscar, appid: int, imagem: str, vistos: set) -> list[dict]:
    if not appid:
        return []
    try:
        bruto = buscar(_URL_NOTICIAS.format(appid=appid))
    except Exception:
        return []
    noticias = (bruto or {}).get("appnews", {}).get("newsitems") if isinstance(bruto, dict) else None
    if not isinstance(noticias, list):
        return []
    grupo = []
    for cru in noticias[:2]:
        if not isinstance(cru, dict):
            continue
        titulo = _limpo(cru.get("title"), 140)
        if not titulo:
            continue
        quando = _quando_unix(cru.get("date"))
        url = _url_permitida(cru.get("url"), _SUFIXOS_LINK)
        item = _montar_item(
            tipo="noticia",
            rotulo="Notícia",
            jogo=titulo,
            titulo=titulo,
            resumo=_limpo(cru.get("contents"), 180) or "Notícia publicada na Steam.",
            quando=quando,
            imagem=imagem,
            url=url,
            vistos=vistos,
        )
        if item:
            grupo.append(item)
    return grupo


def _itens_rawg(buscar, chave: str) -> list[dict]:
    hoje = datetime.now(timezone.utc).date()
    vistos = set()
    recentes = _pagina_rawg(
        buscar, chave, hoje - timedelta(days=45), hoje, "-added", "lancamento", vistos
    )
    futuros = _pagina_rawg(
        buscar, chave, hoje, hoje + timedelta(days=150), "released", "embreve", vistos
    )
    return _intercalar([recentes, futuros], _LIMITE)


def _pagina_rawg(buscar, chave, inicio, fim, ordem, tipo_forcado, vistos) -> list[dict]:
    parametros = urllib.parse.urlencode(
        {
            "key": chave,
            "dates": f"{inicio.isoformat()},{fim.isoformat()}",
            "ordering": ordem,
            "page_size": 4,
        }
    )
    try:
        bruto = buscar("https://api.rawg.io/api/games?" + parametros)
    except Exception:
        return []
    crus = bruto.get("results") if isinstance(bruto, dict) else None
    if not isinstance(crus, list):
        return []
    hoje = datetime.now(timezone.utc).date()
    grupo = []
    for cru in crus:
        if not isinstance(cru, dict):
            continue
        nome = _limpo(cru.get("name"), 120)
        slug = cru.get("slug") if isinstance(cru.get("slug"), str) else ""
        if not re.fullmatch(r"[a-z0-9-]{1,80}", slug):
            slug = ""
        url = _url_permitida(f"https://rawg.io/games/{slug}", _SUFIXOS_LINK) if slug else ""
        tipo, rotulo = _tipo_rawg(cru.get("released"), hoje, tipo_forcado)
        nota = cru.get("metacritic")
        resumo = "RAWG"
        if isinstance(nota, int):
            resumo += f" · Metacritic {nota}"
        elif cru.get("released"):
            resumo += f" · {cru.get('released')}"
        item = _montar_item(
            tipo=tipo,
            rotulo=rotulo,
            jogo=nome,
            titulo=nome,
            resumo=resumo,
            quando=_limpo(str(cru.get("released") or "agora"), 40),
            imagem=_url_permitida(cru.get("background_image"), _SUFIXOS_IMAGEM),
            url=url,
            vistos=vistos,
        )
        if item:
            grupo.append(item)
    return grupo


def _tipo_rawg(released, hoje, forcado: str) -> tuple[str, str]:
    if forcado == "embreve":
        return "embreve", "Em breve"
    try:
        data = datetime.strptime(str(released), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return "noticia", "Novidade"
    if data > hoje:
        return "embreve", "Em breve"
    return "lancamento", "Lançamento"


def _montar_item(*, tipo, rotulo, jogo, titulo, resumo, quando, imagem, url, vistos):
    titulo = _limpo(titulo, 140)
    jogo = _limpo(jogo, 120) or titulo
    if not titulo:
        return None
    chave = (tipo, titulo.lower())
    if chave in vistos:
        return None
    vistos.add(chave)
    return {
        "tipo": tipo,
        "rotulo": rotulo,
        "jogo": jogo,
        "jogo_slug": "",
        "titulo": titulo,
        "resumo": _limpo(resumo, 180),
        "quando": quando or "agora",
        "capa": list(CAPA_PADRAO),
        "imagem_capa": imagem or "",
        "arquivo_capa": "",
        "url_externa": url or "",
    }


def _resumo_preco(cru: dict, frase: str) -> str:
    if cru.get("discounted"):
        percentual = cru.get("discount_percent")
        if isinstance(percentual, int) and 0 < percentual <= 100:
            return f"{frase} · −{percentual}%"
    return frase


def _quando_unix(valor) -> str:
    try:
        instante = datetime.fromtimestamp(int(valor), timezone.utc)
    except (TypeError, ValueError, OSError, OverflowError):
        return "agora"
    return tempo_relativo(instante)


def _appid(valor) -> int:
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return 0
    return numero if numero > 0 else 0


def _limpo(texto, limite: int) -> str:
    bruto = html.unescape(str(texto or ""))
    bruto = re.sub(r"\[/?[^\]]+\]", " ", bruto)
    bruto = re.sub(r"<[^>]+>", " ", bruto)
    bruto = re.sub(r"[\x00-\x1f]+", " ", bruto)
    bruto = re.sub(r"\s+", " ", bruto).strip()
    if len(bruto) <= limite:
        return bruto
    corte = bruto[: limite - 1].rsplit(" ", 1)[0].strip()
    return (corte or bruto[: limite - 1].strip()) + "…"


def _url_permitida(bruto, sufixos: tuple[str, ...]) -> str:
    if not isinstance(bruto, str):
        return ""
    partes = urllib.parse.urlparse(bruto.strip())
    if partes.scheme != "https" or partes.username or partes.password:
        return ""
    host = (partes.hostname or "").lower().rstrip(".")
    if not host or not any(host == sufixo or host.endswith("." + sufixo) for sufixo in sufixos):
        return ""
    return urllib.parse.urlunparse(partes)


def _intercalar(grupos: list[list[dict]], limite: int) -> list[dict]:
    filas = [list(grupo) for grupo in grupos if grupo]
    saida = []
    while filas and len(saida) < limite:
        proxima = []
        for fila in filas:
            if len(saida) >= limite:
                break
            if not fila:
                continue
            saida.append(fila.pop(0))
            if fila:
                proxima.append(fila)
        filas = proxima
    return saida
