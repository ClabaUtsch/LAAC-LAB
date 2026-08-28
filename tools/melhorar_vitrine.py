"""Baixa capturas em resolução maior para `view/estatico/vitrine/`.

Prioridade: screenshot full da Steam; senão still `maxresdefault` do YouTube.
Uso: python tools/melhorar_vitrine.py
"""
from __future__ import annotations

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
MIDIA = RAIZ / "dados" / "midia_jogos.json"
VITRINE = RAIZ / "view" / "estatico" / "vitrine"
UA = "Mozilla/5.0 (compatible; LaaCLabMidia/1.0)"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read()


def _id_youtube(embed: str) -> str:
    achado = re.search(r"(?:embed/|youtu\.be/)([\w-]{6,})", embed or "")
    return achado.group(1) if achado else ""


def _gravar(caminho: Path, bruto: bytes) -> bool:
    if len(bruto) < 8000:
        return False
    atual = caminho.read_bytes() if caminho.exists() else b""
    if len(bruto) <= len(atual) + 2048 and caminho.exists():
        return False
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(bruto)
    return True


def _steam(appid: int) -> dict | None:
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=brazilian&cc=BR"
    try:
        bruto = json.loads(_get(url).decode("utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    no = bruto.get(str(appid)) or {}
    if not no.get("success"):
        return None
    return no.get("data") or {}


def _youtube_stills(video_id: str) -> list[bytes]:
    if not video_id:
        return []
    for nome in ("maxresdefault.jpg", "sddefault.jpg", "hqdefault.jpg"):
        url = f"https://i.ytimg.com/vi/{video_id}/{nome}"
        try:
            bruto = _get(url)
        except (OSError, urllib.error.HTTPError):
            continue
        if len(bruto) >= 8000:
            return [bruto]
    return []


def main() -> int:
    jogos = json.loads(CATALOGO.read_text(encoding="utf-8"))
    midia = json.loads(MIDIA.read_text(encoding="utf-8"))
    for jogo in jogos:
        slug_json = jogo.get("slug") or gerar_slug(jogo["name"])
        extras = midia.get(slug_json) or {}
        pasta_nome = slug_json
        if not extras:
            from app.services.midia_catalogo import slug_sem_marca

            alvo = slug_sem_marca(slug_json)
            for chave, valor in midia.items():
                if slug_sem_marca(chave) == alvo:
                    extras = valor
                    pasta_nome = chave
                    break
        slug = pasta_nome
        pasta = VITRINE / slug
        urls: list[str] = []
        appid = jogo.get("steam_appid")
        if appid:
            print(f"Steam {slug} ({appid})…", flush=True)
            steam = _steam(int(appid))
            time.sleep(0.3)
            for shot in ((steam or {}).get("screenshots") or [])[:6]:
                src = shot.get("path_full") or shot.get("path_thumbnail") or ""
                if src:
                    urls.append(src)
        yt = _id_youtube(((extras.get("trailer") or {}).get("embed") or ""))
        baixados = 0
        for i, url in enumerate(urls, start=1):
            destino = pasta / f"{i:02d}.jpg"
            try:
                bruto = _get(url)
            except (OSError, urllib.error.HTTPError) as erro:
                print(f"  falhou {url}: {erro}", flush=True)
                continue
            if _gravar(destino, bruto):
                baixados += 1
                print(f"  {destino.name} {len(bruto)} bytes", flush=True)
        if baixados == 0:
            stills = _youtube_stills(yt)
            if stills:
                destino = pasta / "01.jpg"
                if _gravar(destino, stills[0]):
                    baixados += 1
                    print(f"  YouTube {destino.name} {len(stills[0])} bytes", flush=True)
        if baixados == 0:
            print(f"  sem ganho em {slug}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
