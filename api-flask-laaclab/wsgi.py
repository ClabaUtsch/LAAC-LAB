"""Ponto de entrada da aplicação.

Desenvolvimento:  python wsgi.py
Produção (ex.):   gunicorn "wsgi:app"
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))
