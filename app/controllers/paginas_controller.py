"""Arquivos servidos diretamente, fora da API."""
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import Blueprint, Response, abort, request, send_from_directory, stream_with_context

PASTA_MIDIA = Path(__file__).resolve().parents[2] / "media"

HOSTS_PERMITIDOS = (
    "shared.akamai.steamstatic.com",
    "cdn.akamai.steamstatic.com",
    "cdn.cloudflare.steamstatic.com",
    "video.akamai.steamstatic.com",
    "i.ytimg.com",
    "upload.wikimedia.org",
    # background_image da RAWG (host exato; nada de subdomínios).
    "media.rawg.io",
    # mp4 dos trailers que a RAWG devolve (host exato).
    "steamcdn-a.akamaihd.net",
)

UA = "Mozilla/5.0 (compatible; LaaCLab/1.0)"


def _host_permitido(hostname: str | None) -> bool:
    if not hostname:
        return False
    host = hostname.lower()
    if host in HOSTS_PERMITIDOS:
        return True
    return host.endswith(".steamstatic.com") or host.endswith(".steampowered.com")


def criar_blueprint_midia() -> Blueprint:
    """Serve `/media/`. Sem esta rota, capa local some sem erro nenhum:
    o `onerror` do JS remove a imagem e mostra o gradiente."""
    bp = Blueprint("midia", __name__)

    @bp.get("/media/origem")
    def origem():
        """Repassa captura/trailer da Steam na mesma origem da app.

        O preview do navegador bloqueia o CDN externo; o Flask busca
        o arquivo e devolve em `/media/origem?u=...`."""
        bruto = request.args.get("u") or ""
        alvo = urlparse(bruto)
        if alvo.scheme != "https" or not _host_permitido(alvo.hostname):
            abort(400)
        cabecalhos = {"User-Agent": UA}
        if alvo.hostname.lower() != "media.rawg.io":
            cabecalhos["Referer"] = "https://store.steampowered.com/"
        faixa = request.headers.get("Range")
        if faixa:
            cabecalhos["Range"] = faixa
        pedido = Request(bruto, headers=cabecalhos)
        try:
            remoto = urlopen(pedido, timeout=25)
        except Exception:
            abort(502)
        status = getattr(remoto, "status", 200)
        tipo = remoto.headers.get("Content-Type", "application/octet-stream")
        comprimento = remoto.headers.get("Content-Length")
        aceita_faixa = remoto.headers.get("Accept-Ranges", "bytes")
        content_range = remoto.headers.get("Content-Range")

        def gerar():
            try:
                while True:
                    pedaco = remoto.read(64 * 1024)
                    if not pedaco:
                        break
                    yield pedaco
            finally:
                remoto.close()

        resposta = Response(
            stream_with_context(gerar()),
            status=status,
            mimetype=tipo,
        )
        if comprimento:
            resposta.headers["Content-Length"] = comprimento
        resposta.headers["Accept-Ranges"] = aceita_faixa
        if content_range:
            resposta.headers["Content-Range"] = content_range
        resposta.headers["Cache-Control"] = "public, max-age=86400"
        return resposta

    @bp.get("/media/<path:caminho>")
    def midia(caminho):
        return send_from_directory(PASTA_MIDIA, caminho)

    return bp
