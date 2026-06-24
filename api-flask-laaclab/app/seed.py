"""Comandos CLI para criar e popular o banco.

    flask init-db   -> cria todas as tabelas (db.create_all)
    flask seed-db   -> insere dados de exemplo
"""
from datetime import date

import click
from flask.cli import with_appcontext

from app.extensions import db


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Cria todas as tabelas no banco configurado."""
    db.create_all()
    click.echo("[OK] Tabelas criadas.")


@click.command("seed-db")
@with_appcontext
def seed_db_command():
    """Popula o banco com dados de exemplo (idempotente-ish)."""
    from app.models import (
        Avaliacao,
        BugometroStatus,
        Categoria,
        Jogo,
        MetricaBug,
        Plataforma,
        RelatoBug,
        Usuario,
    )

    db.create_all()

    if Usuario.query.first():
        click.echo("Banco já possui dados — seed ignorado.")
        return

    # Usuários
    admin = Usuario(nome_usuario="admin", email="admin@laac.dev", nivel=99)
    admin.set_senha("admin123")
    jogador = Usuario(nome_usuario="jogador1", email="jogador@laac.dev")
    jogador.set_senha("senha123")
    db.session.add_all([admin, jogador])

    # Plataformas
    pc = Plataforma(nome="PC")
    ps5 = Plataforma(nome="PlayStation 5")
    xbox = Plataforma(nome="Xbox Series X")
    db.session.add_all([pc, ps5, xbox])

    # Jogos
    jogo1 = Jogo(
        nome="Cyber Quest",
        descricao="RPG de ação futurista.",
        genero="RPG",
        classificacao="16",
        desenvolvedora="LaaC Studios",
        data_lancamento=date(2024, 11, 20),
    )
    jogo2 = Jogo(
        nome="Bug Hunters",
        descricao="Jogo cooperativo de caça a bugs.",
        genero="Co-op",
        classificacao="12",
        desenvolvedora="QA Games",
        data_lancamento=date(2025, 3, 10),
    )
    db.session.add_all([jogo1, jogo2])
    db.session.flush()  # garante IDs

    # Bugômetro
    db.session.add_all(
        [
            BugometroStatus(jogo_id=jogo1.id, pontuacao=72, status="instavel"),
            BugometroStatus(jogo_id=jogo2.id, pontuacao=18, status="estavel"),
            MetricaBug(
                jogo_id=jogo1.id, tipo="crash", severidade="alta", porcentagem=35
            ),
            MetricaBug(
                jogo_id=jogo1.id, tipo="fps_drop", severidade="media", porcentagem=20
            ),
            RelatoBug(
                jogo_id=jogo1.id,
                titulo="Crash ao salvar",
                descricao="O jogo fecha ao salvar na fase 3.",
                severidade="alta",
                origem="usuario",
            ),
        ]
    )

    # Categoria de fórum + avaliação
    db.session.add(Categoria(nome="Geral"))
    db.session.add(
        Avaliacao(
            usuario_id=jogador.id,
            jogo_id=jogo1.id,
            nota=4.5,
            comentario="Ótimo jogo, mas tem alguns bugs.",
        )
    )

    db.session.commit()
    click.echo("[OK] Dados de exemplo inseridos.")
    click.echo("  Login admin:   admin / admin123")
    click.echo("  Login jogador: jogador1 / senha123")
