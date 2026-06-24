"""Configuração da aplicação.

O banco é escolhido pela variável de ambiente ``FLASK_ENV``:
    - ``development`` (padrão)  -> SQLite
    - ``production``            -> MySQL (PyMySQL)
"""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Carrega o .env da raiz do projeto
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_HOURS", "12"))
    )

    JSON_SORT_KEYS = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    _sqlite_path = os.getenv("SQLITE_PATH", "laac_lab.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{(BASE_DIR / _sqlite_path).as_posix()}"


class ProductionConfig(BaseConfig):
    DEBUG = False

    _user = os.getenv("MYSQL_USER", "root")
    _password = os.getenv("MYSQL_PASSWORD", "")
    _host = os.getenv("MYSQL_HOST", "localhost")
    _port = os.getenv("MYSQL_PORT", "3306")
    _db = os.getenv("MYSQL_DB", "LaaC_lab")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{_user}:{_password}@{_host}:{_port}/{_db}?charset=utf8mb4"
    )


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


_CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    """Retorna a classe de config conforme ``FLASK_ENV``."""
    env = os.getenv("FLASK_ENV", "development").lower()
    return _CONFIG_MAP.get(env, DevelopmentConfig)
