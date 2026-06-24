"""Blueprint de usuários.

Leitura é pública; criação acontece via /api/auth/register.
Atualização e remoção exigem JWT e só o próprio usuário pode se alterar.
A senha, quando enviada num update, é re-hasheada (nunca gravada em texto puro).
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models import Usuario
from app.schemas import RegisterSchema, UsuarioSchema

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")

_schema = UsuarioSchema()
_schema_many = UsuarioSchema(many=True)
# Reaproveita validação de campos do registro, mas tudo opcional no update
_update_schema = RegisterSchema(partial=True)


@usuarios_bp.get("")
@usuarios_bp.get("/")
def listar():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    pagination = Usuario.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify(
        {
            "items": _schema_many.dump(pagination.items),
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    )


@usuarios_bp.get("/<int:user_id>")
def detalhar(user_id):
    usuario = db.session.get(Usuario, user_id)
    if usuario is None:
        return jsonify({"erro": f"usuário {user_id} não encontrado"}), 404
    return jsonify(_schema.dump(usuario))


@usuarios_bp.put("/<int:user_id>")
@usuarios_bp.patch("/<int:user_id>")
@jwt_required()
def atualizar(user_id):
    if int(get_jwt_identity()) != user_id:
        return jsonify({"erro": "você só pode alterar o próprio perfil"}), 403

    usuario = db.session.get(Usuario, user_id)
    if usuario is None:
        return jsonify({"erro": f"usuário {user_id} não encontrado"}), 404

    try:
        data = _update_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"erros": err.messages}), 422

    # Trata a senha separadamente (re-hash)
    nova_senha = data.pop("senha", None)
    if nova_senha:
        usuario.set_senha(nova_senha)

    for key, value in data.items():
        setattr(usuario, key, value)

    db.session.commit()
    return jsonify(_schema.dump(usuario))


@usuarios_bp.delete("/<int:user_id>")
@jwt_required()
def remover(user_id):
    if int(get_jwt_identity()) != user_id:
        return jsonify({"erro": "você só pode remover o próprio perfil"}), 403

    usuario = db.session.get(Usuario, user_id)
    if usuario is None:
        return jsonify({"erro": f"usuário {user_id} não encontrado"}), 404

    db.session.delete(usuario)
    db.session.commit()
    return "", 204
