"""Blueprint de autenticação: registro, login e perfil do usuário logado."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models import Usuario
from app.schemas import LoginSchema, RegisterSchema, UsuarioSchema

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

_usuario_schema = UsuarioSchema()
_register_schema = RegisterSchema()
_login_schema = LoginSchema()


@auth_bp.post("/register")
def register():
    try:
        data = _register_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"erros": err.messages}), 422

    # Unicidade
    if Usuario.query.filter_by(nome_usuario=data["nome_usuario"]).first():
        return jsonify({"erro": "nome_usuario já está em uso"}), 409
    if Usuario.query.filter_by(email=data["email"]).first():
        return jsonify({"erro": "email já está em uso"}), 409

    usuario = Usuario(
        nome_usuario=data["nome_usuario"],
        email=data["email"],
        idade=data.get("idade"),
        avatar_url=data.get("avatar_url"),
        bio=data.get("bio"),
    )
    usuario.set_senha(data["senha"])
    db.session.add(usuario)
    db.session.commit()

    token = create_access_token(identity=str(usuario.id))
    return (
        jsonify({"usuario": _usuario_schema.dump(usuario), "access_token": token}),
        201,
    )


@auth_bp.post("/login")
def login():
    try:
        data = _login_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"erros": err.messages}), 422

    ident = data["identificador"]
    usuario = (
        Usuario.query.filter(
            (Usuario.nome_usuario == ident) | (Usuario.email == ident)
        ).first()
    )

    if usuario is None or not usuario.checar_senha(data["senha"]):
        return jsonify({"erro": "credenciais inválidas"}), 401

    token = create_access_token(identity=str(usuario.id))
    return jsonify(
        {"usuario": _usuario_schema.dump(usuario), "access_token": token}
    )


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    usuario = db.session.get(Usuario, int(user_id))
    if usuario is None:
        return jsonify({"erro": "usuário não encontrado"}), 404
    return jsonify(_usuario_schema.dump(usuario))
