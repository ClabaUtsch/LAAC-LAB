"""Fábrica genérica de blueprints CRUD.

Gera, para um model + schema, as rotas REST padrão:

    GET    /            -> lista (com paginação ?page=&per_page=)
    GET    /<id>        -> detalhe
    POST   /            -> cria               (requer JWT)
    PUT    /<id>        -> atualiza (parcial)  (requer JWT)
    DELETE /<id>        -> remove             (requer JWT)

Leitura é pública; escrita exige token JWT válido.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.extensions import db


def make_crud_blueprint(
    name: str,
    model,
    schema_cls,
    url_prefix: str,
    *,
    protect_write: bool = True,
):
    """Cria um Blueprint com CRUD completo para ``model``.

    :param name: nome do blueprint.
    :param model: classe do model SQLAlchemy.
    :param schema_cls: classe do schema Marshmallow.
    :param url_prefix: prefixo das rotas (ex.: ``/api/jogos``).
    :param protect_write: se ``True``, POST/PUT/DELETE exigem JWT.
    """
    bp = Blueprint(name, __name__, url_prefix=url_prefix)
    schema = schema_cls()
    schema_many = schema_cls(many=True)

    def _maybe_protect(view):
        return jwt_required()(view) if protect_write else view

    # -------- LIST --------
    @bp.get("")
    @bp.get("/")
    def listar():
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        pagination = model.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        return jsonify(
            {
                "items": schema_many.dump(pagination.items),
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
            }
        )

    # -------- DETAIL --------
    @bp.get("/<int:item_id>")
    def detalhar(item_id):
        item = db.session.get(model, item_id)
        if item is None:
            return jsonify({"erro": f"{name} {item_id} não encontrado"}), 404
        return jsonify(schema.dump(item))

    # -------- CREATE --------
    @bp.post("")
    @bp.post("/")
    @_maybe_protect
    def criar():
        json_data = request.get_json(silent=True) or {}
        try:
            data = schema.load(json_data)
        except ValidationError as err:
            return jsonify({"erros": err.messages}), 422

        item = model(**data)
        db.session.add(item)
        db.session.commit()
        return jsonify(schema.dump(item)), 201

    # -------- UPDATE (parcial) --------
    @bp.put("/<int:item_id>")
    @bp.patch("/<int:item_id>")
    @_maybe_protect
    def atualizar(item_id):
        item = db.session.get(model, item_id)
        if item is None:
            return jsonify({"erro": f"{name} {item_id} não encontrado"}), 404

        json_data = request.get_json(silent=True) or {}
        try:
            data = schema.load(json_data, partial=True)
        except ValidationError as err:
            return jsonify({"erros": err.messages}), 422

        for key, value in data.items():
            setattr(item, key, value)
        db.session.commit()
        return jsonify(schema.dump(item))

    # -------- DELETE --------
    @bp.delete("/<int:item_id>")
    @_maybe_protect
    def remover(item_id):
        item = db.session.get(model, item_id)
        if item is None:
            return jsonify({"erro": f"{name} {item_id} não encontrado"}), 404
        db.session.delete(item)
        db.session.commit()
        return "", 204

    return bp
