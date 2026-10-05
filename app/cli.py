"""Comandos de linha de comando.

O bootstrap do primeiro administrador não pode ser uma rota: qualquer
rota capaz de conceder privilégio é uma rota capaz de ser abusada. Aqui
exige acesso ao servidor, que é a credencial certa para esta operação.
"""

import click
from flask.cli import with_appcontext

def registrar_comandos(app):
    app.cli.add_command(promover)
    app.cli.add_command(seed_db)
    app.cli.add_command(importar_rawg)

@click.command("promover")
@click.argument("nome_usuario")
@with_appcontext
def promover(nome_usuario):
    """Torna um usuário existente administrador."""
    from app.extensions import db
    from app.models import Usuario

    usuario = db.session.execute(
        db.select(Usuario).where(Usuario.nome_usuario == nome_usuario)
    ).scalars().first()

    if usuario is None:
        raise click.ClickException(f"Usuário '{nome_usuario}' não existe.")

    usuario.is_admin = True
    db.session.commit()

    click.echo(f"'{nome_usuario}' agora é administrador.")

@click.command("seed-db")
@with_appcontext
def seed_db():
    """Popula o banco com conteúdo de demonstração."""
    from app.seed import semear

    click.echo("Semeando o banco...")
    semear()
    click.echo("Pronto.")

@click.command("importar-rawg")
@click.option(
    "--quantidade",
    default=20,
    show_default=True,
    type=click.IntRange(min=1, max=500),
    help="Quantidade máxima de jogos a analisar/importar.",
)
@click.option(
    "--ordenacao",
    default="-added",
    show_default=True,
    help=(
        "Ordenação enviada à RAWG. Exemplos: "
        "-added, -rating, -metacritic, released."
    ),
)
@click.option(
    "--busca",
    default=None,
    help="Opcional: importa resultados de uma busca específica.",
)
@click.option(
    "--sem-detalhes",
    is_flag=True,
    help=(
        "Não consulta /games/<id>. Importa mais rápido, "
        "mas sem descrição, desenvolvedora e publicadora."
    ),
)
@with_appcontext
def importar_rawg(quantidade, ordenacao, busca, sem_detalhes):
    """Importa jogos da RAWG para o banco local."""
    from app.services.rawg_import_service import RawgImportService
    from app.services.rawg_service import RawgErro

    click.echo(f"Consultando RAWG para até {quantidade} jogo(s)...")

    try:
        resultado = RawgImportService().importar(
            quantidade=quantidade,
            detalhes=not sem_detalhes,
            ordenacao=ordenacao,
            busca=busca,
        )
    except RawgErro as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo("")
    click.echo("Resultado da importação:")
    click.echo(f"  Solicitados: {resultado['solicitados']}")
    click.echo(f"  Encontrados: {resultado['encontrados']}")
    click.echo(f"  Importados: {resultado['importados']}")
    click.echo(f"  Ignorados: {resultado['ignorados']}")

    erros = resultado["erros"]

    if erros:
        click.echo(f"  Erros: {len(erros)}")

        for erro in erros[:20]:
            click.echo(f"    - {erro}")

        if len(erros) > 20:
            click.echo(f"    ... e mais {len(erros) - 20} erro(s).")
    else:
        click.echo("  Erros: 0")
