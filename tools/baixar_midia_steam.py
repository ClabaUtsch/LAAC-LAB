"""Gera dados/midia_jogos.json a partir da API pública da Steam.

Uso: python tools/baixar_midia_steam.py
Não entra no ciclo HTTP da aplicação — só materializa o JSON de mídia.
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from app.services.jogo_service import gerar_slug

CATALOGO = RAIZ / "dados" / "jogos_steam.json"
SAIDA = RAIZ / "dados" / "midia_jogos.json"
UA = "Mozilla/5.0 (compatible; LaaCLabMidia/1.0)"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as resp:
        return resp.read()


def _head_ok(url: str) -> bool:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return 200 <= resp.status < 400
    except urllib.error.HTTPError as err:
        return err.code == 200
    except OSError:
        return False


def _texto(html_bruto: str) -> str:
    texto = html_bruto or ""
    texto = re.sub(r"(?i)<br\s*/?>", "\n", texto)
    texto = re.sub(r"(?i)</(p|li|h[1-6]|div)>", "\n", texto)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = html.unescape(texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n[ \t]+", "\n", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _linhas_req(bloco: str) -> list[str]:
    linhas = []
    for bruta in _texto(bloco).split("\n"):
        linha = bruta.strip(" -\t")
        if not linha:
            continue
        if re.fullmatch(r"(?i)(minimum|recommended|mínimo|mínimos|recomendado|recomendados):?", linha):
            continue
        linhas.append(linha)
    return linhas[:12]


def _trailer(movies: list) -> dict | None:
    if not movies:
        return None
    escolhido = next((m for m in movies if m.get("highlight")), movies[0])
    mid = escolhido.get("id")
    dados = {
        "titulo": escolhido.get("name") or "Trailer",
        "thumb": escolhido.get("thumbnail") or "",
    }
    if mid:
        for nome in ("movie_max.mp4", "movie480.mp4"):
            url = f"https://cdn.akamai.steamstatic.com/steam/apps/{mid}/{nome}"
            if _head_ok(url):
                dados["mp4"] = url
                return dados
    hls = escolhido.get("hls_h264") or ""
    if hls:
        dados["hls"] = hls
        return dados
    return None


def _detalhe(appid: int) -> dict | None:
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=brazilian&cc=BR"
    try:
        bruto = json.loads(_get(url).decode("utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    no = bruto.get(str(appid)) or {}
    if not no.get("success"):
        return None
    return no.get("data") or {}


def montar() -> dict:
    jogos = json.loads(CATALOGO.read_text(encoding="utf-8"))
    saida = {}
    for jogo in jogos:
        slug = jogo.get("slug") or gerar_slug(jogo["name"])
        appid = jogo.get("steam_appid")
        print(f"→ {jogo['name']} ({appid}) [{slug}]", flush=True)
        steam = _detalhe(int(appid)) if appid else None
        time.sleep(0.35)
        trailer = _trailer((steam or {}).get("movies") or [])
        imagens = []
        for shot in ((steam or {}).get("screenshots") or [])[:6]:
            src = shot.get("path_full") or ""
            thumb = shot.get("path_thumbnail") or src
            if src:
                imagens.append({"src": src, "thumb": thumb})
        if not imagens and jogo.get("cover_image"):
            imagens.append({"src": jogo["cover_image"], "thumb": jogo["cover_image"]})
        if slug == "fortnite":
            trailer = {
                "titulo": "Trailer oficial Fortnite",
                "embed": "https://www.youtube.com/embed/5uE0XFJSVZA",
                "thumb": "https://i.ytimg.com/vi/5uE0XFJSVZA/hqdefault.jpg",
            }
            imagens = [
                {"src": "https://i.ytimg.com/vi/5uE0XFJSVZA/hqdefault.jpg", "thumb": "https://i.ytimg.com/vi/5uE0XFJSVZA/hqdefault.jpg"},
                {"src": "https://i.ytimg.com/vi/YUbGFGltS0s/hqdefault.jpg", "thumb": "https://i.ytimg.com/vi/YUbGFGltS0s/hqdefault.jpg"},
                {
                    "src": "https://upload.wikimedia.org/wikipedia/commons/b/bb/Fortnite_Pro-Am_stadium_at_E3_2018_3.jpg",
                    "thumb": "https://upload.wikimedia.org/wikipedia/commons/b/bb/Fortnite_Pro-Am_stadium_at_E3_2018_3.jpg",
                },
            ]
        if slug == "valorant":
            stills = [
                "e_E9W2vsRbQ",
                "IhhjcB2ZjIM",
                "hhlgphVf-1g",
                "-M_r8MKQ3mo",
                "ua-iIRQDY8g",
                "C3QTyMXi-WE",
            ]
            trailer = {
                "titulo": "VALORANT | Official Launch Cinematic Trailer",
                "embed": "https://www.youtube.com/embed/e_E9W2vsRbQ",
                "thumb": "https://i.ytimg.com/vi/e_E9W2vsRbQ/maxresdefault.jpg",
            }
            imagens = [
                {
                    "src": f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg",
                    "thumb": f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg",
                }
                for vid in stills[1:]
            ]
        pc = (steam or {}).get("pc_requirements") or {}
        saida[slug] = {
            "legenda": _texto((steam or {}).get("short_description") or jogo.get("short_description") or ""),
            "historia": _texto((steam or {}).get("about_the_game") or jogo.get("about") or "")[:1800],
            "tempo_medio": "40h" if slug == "palworld" else "",
            "tags": list(jogo.get("genres") or []),
            "trailer": trailer,
            "imagens": imagens,
            "requisitos": {
                "minimo": _linhas_req(pc.get("minimum") or ""),
                "recomendado": _linhas_req(pc.get("recommended") or ""),
            },
        }
        if slug == "palworld":
            extra = saida[slug]
            extra["tags"] = extra["tags"] or [
                "Mundo aberto", "Sobrevivência", "Criaturas", "Cooperativo", "Crafting"
            ]
            if extra["trailer"] is None:
                extra["trailer"] = {
                    "titulo": "Trailer oficial Palworld 1.0",
                    "embed": "https://www.youtube.com/embed/1fpGg9wNM9A",
                    "thumb": "",
                }
            else:
                extra["trailer"]["embed"] = "https://www.youtube.com/embed/1fpGg9wNM9A"
        print(
            f"   trailer={'sim' if saida[slug]['trailer'] else 'não'} "
            f"fotos={len(saida[slug]['imagens'])}",
            flush=True,
        )
    return saida


if __name__ == "__main__":
    catalogo = montar()
    SAIDA.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Gravado {SAIDA} ({len(catalogo)} jogos)")
