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
    app.cli.add_command(buscar_imagens_rawg)
    app.cli.add_command(vincular_rawg)
    app.cli.add_command(buscar_midia_rawg)


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


def _rawg_ou_erro():
    from app.services.rawg_service import RawgErro, RawgService

    try:
        return RawgService()
    except RawgErro as exc:
        raise click.ClickException(str(exc)) from None


@click.command("importar-rawg")
@click.option("--quantidade", default=20, show_default=True,
              type=click.IntRange(min=1, max=1000),
              help="Quantidade máxima de jogos a analisar/importar.")
@click.option("--ordenacao", default="-added", show_default=True,
              help="Ordenação enviada à RAWG (-added, -rating, -metacritic, released).")
@click.option("--busca", default=None, help="Importa os resultados de uma busca.")
@click.option("--sem-detalhes", is_flag=True,
              help="Não consulta /games/<id>: mais rápido, sem descrição nem desenvolvedora.")
@with_appcontext
def importar_rawg(quantidade, ordenacao, busca, sem_detalhes):
    """Importa jogos da RAWG (com rawg_id e imagem principal)."""
    from app.importacao.rawg_import_service import RawgImportService
    from app.services.rawg_service import RawgErro

    servico = RawgImportService(_rawg_ou_erro())
    click.echo(f"Consultando a RAWG para até {quantidade} jogo(s)...")
    try:
        r = servico.importar(quantidade=quantidade, detalhes=not sem_detalhes,
                             ordenacao=ordenacao, busca=busca)
    except RawgErro as exc:
        raise click.ClickException(str(exc)) from None

    click.echo("\nResultado da importação:")
    for rotulo, chave in (("Solicitados", "solicitados"), ("Encontrados", "encontrados"),
                          ("Importados", "importados"), ("Completados (já existiam)", "atualizados"),
                          ("Ignorados", "ignorados")):
        click.echo(f"  {rotulo}: {r[chave]}")
    click.echo(f"  Erros: {len(r['erros'])}")
    for erro in r["erros"][:20]:
        click.echo(f"    - {erro}")


@click.command("buscar-imagens-rawg")
@click.option("--slug", default=None, help="Processa apenas o jogo com este slug.")
@click.option("--limite", type=click.IntRange(min=1), default=None,
              help="Máximo de jogos a processar nesta execução.")
@click.option("--substituir", is_flag=True,
              help="Também substitui `capa_url` já preenchida. Sem esta opção, "
                   "jogos com imagem cadastrada não são tocados. `arquivo_capa` nunca é alterado.")
@click.option("--dry-run", is_flag=True, help="Mostra o que seria feito, sem gravar.")
@with_appcontext
def buscar_imagens_rawg(slug, limite, substituir, dry_run):
    """Preenche a imagem principal (RAWG) dos jogos que estão sem imagem."""
    from app.importacao.rawg_imagem_service import RawgImagemService

    servico = RawgImagemService(_rawg_ou_erro())
    rotulos = {"atualizado": "imagem gravada", "sem_imagem": "RAWG sem imagem",
               "ja_tem_imagem": "já tem imagem", "sem_correspondencia": "sem correspondência",
               "ambiguo": "AMBÍGUO", "conflito": "conflito de vínculo"}
    if dry_run:
        click.echo("(dry-run: nada será gravado)")
    resumo = servico.preencher(
        slug=slug, limite=limite, substituir=substituir, dry_run=dry_run,
        aviso=lambda status, detalhe: click.echo(f"  [{rotulos.get(status, status)}] {detalhe}"),
    )
    click.echo("\nResultado:")
    click.echo(f"  Analisados: {resumo.analisados}")
    click.echo(f"  Imagens {'que seriam gravadas' if dry_run else 'gravadas'}: {resumo.atualizados}")
    click.echo(f"  Vinculados, mas a RAWG não tem imagem: {resumo.vinculados_sem_imagem}")
    click.echo(f"  Já tinham imagem: {resumo.ja_tinham_imagem}")
    click.echo(f"  Sem correspondência segura: {len(resumo.sem_correspondencia)}")
    click.echo(f"  Ambíguos (use vincular-rawg): {len(resumo.ambiguos)}")
    click.echo(f"  Conflitos de vínculo: {len(resumo.conflitos)}")
    click.echo(f"  Erros: {len(resumo.erros)}")
    for erro in resumo.erros[:20]:
        click.echo(f"    - {erro}")
    if resumo.abortado:
        raise click.ClickException(f"Execução interrompida: {resumo.abortado}")


@click.command("vincular-rawg")
@click.argument("slug")
@click.argument("rawg_id", type=int)
@click.option("--substituir", is_flag=True, help="Também substitui `capa_url` já preenchida.")
@with_appcontext
def vincular_rawg(slug, rawg_id, substituir):
    """Associa manualmente um jogo (SLUG) ao registro RAWG_ID e grava a imagem."""
    from app.extensions import db
    from app.models import Jogo
    from app.importacao.rawg_imagem_service import RawgImagemService
    from app.services.rawg_service import RawgErro

    jogo = db.session.execute(db.select(Jogo).where(Jogo.slug == slug)).scalars().first()
    if jogo is None:
        raise click.ClickException(f"Jogo '{slug}' não existe.")
    try:
        status = RawgImagemService(_rawg_ou_erro()).vincular(jogo, rawg_id, substituir=substituir)
    except RawgErro as exc:
        raise click.ClickException(str(exc)) from None
    if status == "conflito":
        raise click.ClickException("Vínculo recusado: o jogo ou o registro já estão associados a outro.")
    click.echo(f"'{slug}' vinculado à RAWG #{rawg_id} ({status}).")


@click.command("buscar-midia-rawg")
@click.option("--slug", default=None, help="Processa apenas este jogo.")
@click.option("--limite", type=click.IntRange(min=1), default=None)
@click.option("--substituir", is_flag=True, help="Refaz jogos que já têm mídia da RAWG.")
@click.option("--dry-run", is_flag=True, help="Mostra o que seria feito, sem gravar.")
@with_appcontext
def buscar_midia_rawg(slug, limite, substituir, dry_run):
    """Baixa a lista de capturas e trailers da RAWG (dados/midia_rawg.json)."""
    from app.importacao.rawg_midia_service import RawgMidiaService

    r = RawgMidiaService(_rawg_ou_erro()).preencher(
        slug=slug, limite=limite, substituir=substituir, dry_run=dry_run,
        aviso=lambda status, nome: click.echo(f"  [{status}] {nome}"),
    )
    click.echo("\nResultado:")
    click.echo(f"  Analisados: {r['analisados']}  |  Gravados: {r['gravados']}  |  Sem mídia na RAWG: {r['sem_midia']}")
    click.echo(f"  Já tinham mídia: {r['ja_tinham']}  |  Sem vínculo RAWG (rode buscar-imagens-rawg): {r['sem_vinculo']}")
    click.echo(f"  Erros: {len(r['erros'])}")
    for erro in r["erros"][:20]:
        click.echo(f"    - {erro}")
    if r["abortado"]:
        raise click.ClickException(f"Execução interrompida: {r['abortado']}")
