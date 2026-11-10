"""Amizades e perfis públicos."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.controllers.autenticacao import obter_usuario_atual


def criar_blueprint_social(servico_social, servico_auth, servico_progressao=None) -> Blueprint:
    bp = Blueprint("social", __name__, url_prefix="/api/v1/social")

    @bp.get("/amizades")
    @jwt_required()
    def amizades():
        usuario = obter_usuario_atual(servico_auth)
        return jsonify(servico_social.listar_amigos(usuario.id)), 200

    @bp.get("/pessoas")
    @jwt_required()
    def pessoas():
        usuario = obter_usuario_atual(servico_auth)
        return jsonify(
            {
                "itens": servico_social.buscar_pessoas(
                    request.args.get("busca", ""), usuario.id
                )
            }
        ), 200

    @bp.post("/amizades")
    @jwt_required()
    def pedir():
        usuario = obter_usuario_atual(servico_auth)
        corpo = request.get_json(silent=True) or {}
        destino = int(corpo.get("destinatario_id") or 0)
        return jsonify(servico_social.solicitar(usuario.id, destino)), 201

    @bp.post("/amizades/<int:amizade_id>/responder")
    @jwt_required()
    def responder(amizade_id: int):
        usuario = obter_usuario_atual(servico_auth)
        corpo = request.get_json(silent=True) or {}
        aceitar = bool(corpo.get("aceitar"))
        return jsonify(servico_social.responder(usuario.id, amizade_id, aceitar)), 200

    @bp.get("/perfis/<int:usuario_id>")
    @jwt_required()
    def perfil(usuario_id: int):
        visitante = obter_usuario_atual(servico_auth)
        return jsonify(servico_social.perfil_publico(usuario_id, visitante.id)), 200

    @bp.post("/avatar")
    @jwt_required()
    def avatar():
        usuario = obter_usuario_atual(servico_auth)
        corpo = request.get_json(silent=True) or {}
        url = (corpo.get("avatar_url") or "").strip()
        if not url:
            from app.errors import DadosInvalidos

            raise DadosInvalidos("Envie avatar_url (URL ou data URL da foto).")
        if len(url) > 600_000:
            from app.errors import DadosInvalidos

            raise DadosInvalidos("Imagem grande demais. Use uma foto menor.")
        if servico_progressao is None:
            from app.errors import DadosInvalidos

            raise DadosInvalidos("Upload de avatar indisponível.")
        return jsonify(
            servico_progressao.salvar_avatar(
                usuario.id, url, cor_avatar=corpo.get("cor_avatar")
            )
        ), 200

    return bp
