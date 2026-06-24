"""Application factory do LaaC_lab API."""
from flask import Flask, jsonify

from app.extensions import db, jwt, ma, migrate


def create_app(config_object=None):
    app = Flask(__name__)

    if config_object is None:
        from config import get_config

        config_object = get_config()
    app.config.from_object(config_object)

    # Extensões
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    # Garante que os models sejam importados (necessário p/ create_all/migrate)
    from app import models  # noqa: F401

    # Blueprints
    from app.routes import register_blueprints

    register_blueprints(app)

    _register_handlers(app)
    _register_cli(app)

    @app.get("/")
    def index():
        return jsonify(
            {
                "api": "LaaC_lab — Bugômetro",
                "status": "online",
                "docs": "veja README.md para a lista de endpoints",
            }
        )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app


def _register_handlers(app):
    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"erro": "recurso não encontrado"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return jsonify({"erro": "método não permitido"}), 405

    @app.errorhandler(500)
    def server_error(_e):
        db.session.rollback()
        return jsonify({"erro": "erro interno do servidor"}), 500

    # --- JWT ---
    @jwt.expired_token_loader
    def expired_token(_h, _p):
        return jsonify({"erro": "token expirado"}), 401

    @jwt.invalid_token_loader
    def invalid_token(_reason):
        return jsonify({"erro": "token inválido"}), 401

    @jwt.unauthorized_loader
    def missing_token(_reason):
        return jsonify({"erro": "token de autenticação ausente"}), 401


def _register_cli(app):
    """Comandos de linha de comando: flask init-db, flask seed-db."""
    from app.seed import init_db_command, seed_db_command

    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command)
