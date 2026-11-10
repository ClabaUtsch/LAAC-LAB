"""Participação em praças e threads do fórum."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.controllers.autenticacao import obter_usuario_atual


def criar_blueprint_comunidade(
    servico_comunidade, servico_auth, servico_telas=None
) -> Blueprint:
    bp = Blueprint("comunidade_api", __name__, url_prefix="/api/v1/comunidade")

    @bp.post("/pracas/<int:jogo_id>/entrar")
    @jwt_required()
    def entrar(jogo_id: int):
        usuario = obter_usuario_atual(servico_auth)
        return jsonify(servico_comunidade.entrar(usuario.id, jogo_id)), 201

    @bp.post("/pracas/<int:jogo_id>/sair")
    @jwt_required()
    def sair(jogo_id: int):
        usuario = obter_usuario_atual(servico_auth)
        servico_comunidade.sair(usuario.id, jogo_id)
        return jsonify({"membro": False}), 200

    @bp.get("/topicos/<int:topico_id>")
    @jwt_required()
    def topico(topico_id: int):
        usuario = obter_usuario_atual(servico_auth)
        return jsonify(servico_comunidade.detalhe_topico(topico_id, usuario.id)), 200

    @bp.post("/topicos/<int:topico_id>/respostas")
    @jwt_required()
    def responder(topico_id: int):
        usuario = obter_usuario_atual(servico_auth)
        corpo = request.get_json(silent=True) or {}
        return jsonify(
            servico_comunidade.responder(
                usuario.id,
                topico_id,
                corpo.get("conteudo") or "",
                parent_id=corpo.get("parent_id"),
            )
        ), 201

    @bp.delete("/posts/<int:post_id>")
    @jwt_required()
    def apagar(post_id: int):
        usuario = obter_usuario_atual(servico_auth)
        servico_comunidade.apagar_post(usuario.id, post_id, is_admin=usuario.is_admin)
        return ("", 204)

    return bp
