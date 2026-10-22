"""Mídia extra da tela de detalhe (galeria, trailer, requisitos).

Não passa pelo banco: o seed do catálogo não guarda screenshots nem
trailer. O JSON em `dados/midia_jogos.json` completa o que a tela da
loja precisa, indexado pelo slug do jogo.
"""
import json
import re
from pathlib import Path
from urllib.parse import quote

_ARQUIVO = Path(__file__).resolve().parents[2] / "dados" / "midia_jogos.json"
_cache = None
_mtime = None


def _catalogo() -> dict:
    global _cache, _mtime
    stamp = _ARQUIVO.stat().st_mtime if _ARQUIVO.exists() else None
    if _cache is None or stamp != _mtime:
        if _ARQUIVO.exists():
            _cache = json.loads(_ARQUIVO.read_text(encoding="utf-8"))
        else:
            _cache = {}
        _mtime = stamp
    return _cache


_ARQUIVO_RAWG = Path(__file__).resolve().parents[2] / "dados" / "midia_rawg.json"
_cache_rawg = None
_mtime_rawg = None


def _catalogo_rawg() -> dict:
    """Mídia vinda da RAWG (`flask buscar-midia-rawg`). Complementa, nunca
    substitui, o catálogo principal."""
    global _cache_rawg, _mtime_rawg
    stamp = _ARQUIVO_RAWG.stat().st_mtime if _ARQUIVO_RAWG.exists() else None
    if _cache_rawg is None or stamp != _mtime_rawg:
        try:
            dados = json.loads(_ARQUIVO_RAWG.read_text(encoding="utf-8")) if stamp else {}
        except (OSError, ValueError):
            dados = {}
        _cache_rawg = dados if isinstance(dados, dict) else {}
        _mtime_rawg = stamp
    return _cache_rawg


def para_origem(url: str | None) -> str:
    """CDN da Steam/YouTube img via `/media/origem` — mesma origem do site."""
    texto = (url or "").strip()
    if not texto:
        return ""
    if (
        texto.startswith("/")
        or "youtube.com" in texto
        or "youtu.be" in texto
        or "ytimg.com" in texto
    ):
        return texto
    return "/media/origem?u=" + quote(texto, safe="")


def slug_sem_marca(slug: str) -> str:
    """`helldiverstm-2` e `helldivers-2` são o mesmo jogo."""
    return re.sub(r"tm(?=-|$)", "", (slug or "").strip().lower())


def extras_do_slug(slug: str) -> dict:
    catalogo = _catalogo()
    bruto = catalogo.get(slug or "") or {}
    if not bruto:
        alvo = slug_sem_marca(slug)
        for chave, valor in catalogo.items():
            if slug_sem_marca(chave) == alvo:
                bruto = valor
                break
    requisitos = bruto.get("requisitos") or {}
    rawg = _catalogo_rawg().get(slug or "") or {}
    trailer = bruto.get("trailer") or rawg.get("trailer") or None
    if trailer:
        trailer = dict(trailer)
        if trailer.get("mp4"):
            trailer["mp4"] = para_origem(trailer["mp4"])
        if trailer.get("hls"):
            trailer["hls"] = para_origem(trailer["hls"])
        if trailer.get("thumb"):
            trailer["thumb"] = para_origem(trailer["thumb"])
    imagens = []
    for foto in (bruto.get("imagens") or rawg.get("imagens") or []):
        src = para_origem(foto.get("src"))
        thumb = para_origem(foto.get("thumb") or foto.get("src"))
        if src:
            imagens.append({"src": src, "thumb": thumb})
    return {
        "legenda": bruto.get("legenda") or "",
        "historia": bruto.get("historia") or "",
        "tempo_medio": bruto.get("tempo_medio") or "",
        "tags": list(bruto.get("tags") or []),
        "trailer": trailer,
        "imagens": imagens,
        "requisitos": {
            "minimo": list(requisitos.get("minimo") or []),
            "recomendado": list(requisitos.get("recomendado") or []),
        },
    }
