"""RAWG: cliente, associação, preenchimento, importação, proxy e telas.
Nenhum teste faz chamada de rede: a RAWG é simulada."""
import pytest
import requests

from app.extensions import db
from app.models import Jogo
from app.importacao.rawg_imagem_service import (
    RawgImagemService,
    chave_nome,
    escolher_candidato,
)
from app.importacao.rawg_import_service import RawgImportService
from app.services.rawg_service import (
    RawgChaveInvalida,
    RawgIndisponivel,
    RawgLimite,
    RawgNaoConfigurada,
    RawgService,
    imagem_principal,
)

IMG = "https://media.rawg.io/media/games/aaa/aaa111.jpg"
IMG2 = "https://media.rawg.io/media/games/bbb/bbb222.jpg"


class Resposta:
    def __init__(self, status=200, corpo=None, json_invalido=False):
        self.status_code = status
        self._corpo = {} if corpo is None else corpo
        self._invalido = json_invalido

    def json(self):
        if self._invalido:
            raise ValueError("x")
        return self._corpo


class SessaoFalsa:
    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.headers = {}
        self.chamadas = []

    def get(self, url, params=None, timeout=None):
        self.chamadas.append((url, dict(params or {}), timeout))
        item = self.respostas.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def servico(*respostas, tentativas=2):
    sessao = SessaoFalsa(*respostas)
    return RawgService(api_key="SEGREDO123", sessao=sessao, tentativas=tentativas,
                       espera_entre_tentativas=0), sessao


class RawgFalsa:
    """Dublê de RawgService com catálogo em memória."""

    def __init__(self, catalogo, erro=None):
        self.catalogo = catalogo
        self.buscas = []
        self.detalhes = []
        self.erro = erro

    def buscar_por_nome(self, nome, quantidade=10):
        self.buscas.append(nome)
        if self.erro:
            raise self.erro
        return [r for r in self.catalogo if nome.lower().split()[0] in r["name"].lower()]

    def obter_jogo(self, rawg_id):
        self.detalhes.append(rawg_id)
        if self.erro:
            raise self.erro
        return next(r for r in self.catalogo if r["id"] == rawg_id)

    def listar_jogos(self, **kw):
        return {"results": self.catalogo, "next": None}


def novo_jogo(nome, slug, **extra):
    jogo = Jogo(nome=nome, slug=slug, nome_busca=nome.lower(), **extra)
    db.session.add(jogo)
    db.session.commit()
    return jogo


# ---------------------------------------------------------------- cliente
def test_sem_chave_recusa_subir(monkeypatch):
    monkeypatch.delenv("RAWG_API_KEY", raising=False)
    with pytest.raises(RawgNaoConfigurada):
        RawgService()


@pytest.mark.parametrize("status,exc", [(401, RawgChaveInvalida), (403, RawgChaveInvalida),
                                        (429, RawgLimite)])
def test_status_de_erro_vira_excecao_propria(status, exc):
    s, _ = servico(Resposta(status))
    with pytest.raises(exc) as e:
        s.obter_jogo(1)
    assert "SEGREDO123" not in str(e.value)


def test_timeout_tenta_de_novo_e_depois_desiste():
    s, sessao = servico(requests.Timeout("key=SEGREDO123"), requests.Timeout("key=SEGREDO123"))
    with pytest.raises(RawgIndisponivel) as e:
        s.obter_jogo(1)
    assert len(sessao.chamadas) == 2
    assert "SEGREDO123" not in str(e.value) and e.value.__cause__ is None


def test_erro_5xx_e_recuperavel_na_segunda_tentativa():
    s, _ = servico(Resposta(503), Resposta(200, {"id": 7}))
    assert s.obter_jogo(7) == {"id": 7}


def test_json_invalido_e_formato_inesperado():
    s, _ = servico(Resposta(200, json_invalido=True))
    with pytest.raises(Exception, match="JSON"):
        s.obter_jogo(1)
    s, _ = servico(Resposta(200, [1, 2]))
    with pytest.raises(Exception, match="inesperado"):
        s.obter_jogo(1)


def test_chave_vai_como_parametro_e_nao_aparece_no_repr():
    s, sessao = servico(Resposta(200, {"results": []}))
    s.buscar_por_nome("Portal")
    assert sessao.chamadas[0][1]["key"] == "SEGREDO123"
    assert sessao.chamadas[0][2] == s.timeout
    assert "SEGREDO123" not in repr(s)


def test_imagem_principal_so_aceita_https():
    assert imagem_principal({"background_image": IMG}) == IMG
    assert imagem_principal({"background_image": "http://x/y.jpg"}) == ""
    assert imagem_principal({"background_image": None}) == ""
    assert imagem_principal(None) == ""


# ------------------------------------------------------- correspondência
def test_chave_nome_ignora_marca_acento_e_pontuacao():
    assert chave_nome("HELLDIVERS™ 2") == chave_nome("Helldivers 2")
    assert chave_nome("Pokémon: Edição") == "pokemon edicao"


def test_escolhe_so_correspondencia_exata_nunca_o_primeiro(app):
    jogo = novo_jogo("Portal", "portal")
    candidatos = [{"id": 1, "name": "Portal 2", "slug": "portal-2"},
                  {"id": 2, "name": "Portal", "slug": "portal"}]
    escolhido, motivo = escolher_candidato(jogo, candidatos)
    assert escolhido["id"] == 2 and motivo == "ok"


def test_sem_correspondencia_nao_escolhe_nada(app):
    jogo = novo_jogo("Jogo Inexistente", "jogo-inexistente")
    assert escolher_candidato(jogo, [{"id": 1, "name": "Outra Coisa", "slug": "x"}]) == (
        None, "sem_correspondencia")


def test_ambiguo_resolve_por_ano_ou_fica_sem_vinculo(app):
    jogo = novo_jogo("Doom", "doom-local", data_lancamento="2016-05-13")
    cand = [{"id": 1, "name": "DOOM", "slug": "doom-2016", "released": "2016-05-13"},
            {"id": 2, "name": "Doom", "slug": "doom-1993", "released": "1993-12-10"}]
    assert escolher_candidato(jogo, cand)[0]["id"] == 1
    sem_ano = novo_jogo("Doom", "doom-outro")
    assert escolher_candidato(sem_ano, cand) == (None, "ambiguo")


# ------------------------------------------------------- preenchimento
def catalogo():
    return [{"id": 10, "name": "Portal", "slug": "portal", "background_image": IMG},
            {"id": 11, "name": "Portal 2", "slug": "portal-2", "background_image": IMG2},
            {"id": 12, "name": "Semfoto", "slug": "semfoto", "background_image": None}]


def test_preenche_apenas_jogo_sem_imagem_e_grava_vinculo(app):
    sem = novo_jogo("Portal", "portal")
    manual = novo_jogo("Portal 2", "portal-2", capa_url="https://meu.site/capa.jpg")
    local = novo_jogo("Portal Local", "portal-local", arquivo_capa="/media/capas/x.jpg")
    rawg = RawgFalsa(catalogo())
    resumo = RawgImagemService(rawg, pausa=0).preencher()
    assert resumo.analisados == 1 and resumo.atualizados == 1
    db.session.expire_all()
    assert (sem.capa_url, sem.rawg_id) == (IMG, 10)
    assert manual.capa_url == "https://meu.site/capa.jpg" and manual.rawg_id is None
    assert local.arquivo_capa == "/media/capas/x.jpg" and not local.capa_url
    assert rawg.buscas == ["Portal"]  # só o jogo sem imagem gerou consulta


def test_reexecutar_nao_consulta_nem_duplica(app):
    novo_jogo("Portal", "portal")
    servico_ = RawgImagemService(RawgFalsa(catalogo()), pausa=0)
    servico_.preencher()
    rawg2 = RawgFalsa(catalogo())
    resumo = RawgImagemService(rawg2, pausa=0).preencher()
    assert resumo.analisados == 0 and rawg2.buscas == [] and rawg2.detalhes == []
    assert db.session.query(Jogo).count() == 1


def test_substituir_exige_opcao_explicita_e_preserva_arquivo_capa(app):
    jogo = novo_jogo("Portal", "portal", capa_url="https://velho/x.jpg",
                     arquivo_capa="/media/capas/portal.jpg")
    RawgImagemService(RawgFalsa(catalogo()), pausa=0).preencher()
    db.session.expire_all()
    assert jogo.capa_url == "https://velho/x.jpg"
    RawgImagemService(RawgFalsa(catalogo()), pausa=0).preencher(substituir=True)
    db.session.expire_all()
    assert jogo.capa_url == IMG and jogo.arquivo_capa == "/media/capas/portal.jpg"


def test_jogo_ja_vinculado_usa_id_sem_buscar(app):
    jogo = novo_jogo("Portal", "portal", rawg_id=10)
    rawg = RawgFalsa(catalogo())
    RawgImagemService(rawg, pausa=0).preencher()
    assert rawg.buscas == [] and rawg.detalhes == [10]
    assert jogo.capa_url == IMG


def test_dry_run_nao_grava(app):
    jogo = novo_jogo("Portal", "portal")
    resumo = RawgImagemService(RawgFalsa(catalogo()), pausa=0).preencher(dry_run=True)
    db.session.expire_all()
    assert resumo.atualizados == 1 and not jogo.capa_url and jogo.rawg_id is None


def test_registro_rawg_sem_imagem_vincula_mas_mantem_fallback(app):
    jogo = novo_jogo("Semfoto", "semfoto")
    resumo = RawgImagemService(RawgFalsa(catalogo()), pausa=0).preencher()
    db.session.expire_all()
    assert resumo.vinculados_sem_imagem == 1 and not jogo.capa_url and jogo.rawg_id == 12


def test_conflito_de_vinculo_nao_duplica_registro_rawg(app):
    novo_jogo("Portal Original", "portal-original", rawg_id=10)
    outro = novo_jogo("Portal", "portal")
    resumo = RawgImagemService(RawgFalsa(catalogo()), pausa=0).preencher()
    db.session.expire_all()
    assert len(resumo.conflitos) == 1 and outro.rawg_id is None and not outro.capa_url


def test_ambiguo_e_sem_correspondencia_sao_relatados_sem_alterar(app):
    a = novo_jogo("Doom", "doom")
    b = novo_jogo("Nada Parecido", "nada")
    cat = [{"id": 1, "name": "Doom", "slug": "d1", "background_image": IMG},
           {"id": 2, "name": "DOOM", "slug": "d2", "background_image": IMG2},
           {"id": 3, "name": "Nada Parecido Mesmo", "slug": "n", "background_image": IMG}]
    resumo = RawgImagemService(RawgFalsa(cat), pausa=0).preencher()
    db.session.expire_all()
    assert resumo.ambiguos and resumo.sem_correspondencia
    assert not a.capa_url and not b.capa_url


@pytest.mark.parametrize("erro", [RawgChaveInvalida("x"), RawgLimite("x")])
def test_chave_invalida_ou_limite_interrompem_o_lote(app, erro):
    novo_jogo("Portal", "portal")
    novo_jogo("Doom", "doom")
    rawg = RawgFalsa(catalogo(), erro=erro)
    resumo = RawgImagemService(rawg, pausa=0).preencher()
    assert resumo.abortado and len(rawg.buscas) == 1


def test_indisponibilidade_registra_erro_e_aborta_apos_falhas_seguidas(app):
    for i in range(5):
        novo_jogo(f"Portal {i}", f"portal-{i}")
    rawg = RawgFalsa(catalogo(), erro=RawgIndisponivel("fora"))
    resumo = RawgImagemService(rawg, pausa=0).preencher()
    assert len(resumo.erros) == 3 and resumo.abortado


def test_vincular_manual(app):
    jogo = novo_jogo("Doom", "doom")
    cat = [{"id": 2, "name": "DOOM", "slug": "d2", "background_image": IMG2}]
    assert RawgImagemService(RawgFalsa(cat), pausa=0).vincular(jogo, 2) == "atualizado"
    assert (jogo.rawg_id, jogo.capa_url) == (2, IMG2)


# ------------------------------------------------------------ importação
def test_importacao_grava_imagem_e_vinculo_e_nao_duplica(app):
    rawg = RawgFalsa(catalogo())
    primeira = RawgImportService(rawg, pausa=0).importar(quantidade=3, detalhes=False)
    assert primeira["importados"] == 3
    portal = db.session.execute(db.select(Jogo).where(Jogo.rawg_id == 10)).scalar_one()
    assert portal.capa_url == IMG
    segunda = RawgImportService(rawg, pausa=0).importar(quantidade=3, detalhes=False)
    assert segunda["importados"] == 0 and db.session.query(Jogo).count() == 3


def test_importacao_completa_jogo_existente_sem_sobrescrever(app):
    sem = novo_jogo("Portal", "portal")
    manual = novo_jogo("Portal 2", "portal-2", capa_url="https://meu.site/capa.jpg")
    r = RawgImportService(RawgFalsa(catalogo()), pausa=0).importar(quantidade=2, detalhes=False)
    db.session.expire_all()
    assert r["atualizados"] == 2 and r["importados"] == 0
    assert (sem.capa_url, sem.rawg_id) == (IMG, 10)
    assert manual.capa_url == "https://meu.site/capa.jpg" and manual.rawg_id == 11


# ---------------------------------------------------------- proxy / telas
def test_proxy_aceita_so_o_host_exato_da_rawg(cliente, monkeypatch):
    visto = {}

    class Fake:
        status = 200
        headers = {"Content-Type": "image/jpeg", "Content-Length": "4"}

        def read(self, n=-1):
            if getattr(self, "_f", False):
                return b""
            self._f = True
            return b"JPEG"

        def close(self):
            pass

    def fake(pedido, timeout=25):
        visto["url"] = pedido.full_url
        visto["referer"] = pedido.get_header("Referer")
        return Fake()

    monkeypatch.setattr("app.controllers.paginas_controller.urlopen", fake)
    ok = cliente.get("/media/origem?u=" + IMG)
    assert ok.status_code == 200 and ok.data == b"JPEG"
    assert visto["url"] == IMG and visto["referer"] is None
    for ruim in ("http://media.rawg.io/x.jpg", "https://evil.media.rawg.io/x.jpg",
                 "https://media.rawg.io.evil.com/x.jpg", "https://api.rawg.io/x"):
        assert cliente.get("/media/origem?u=" + ruim).status_code == 400


def test_detalhe_do_jogo_com_imagem_rawg_passa_pelo_proxy_liberado(app, cliente):
    from app.services.midia_catalogo import para_origem

    jogo = novo_jogo("Jogo Rawg", "jogo-rawg", capa_url=IMG)
    corpo = cliente.post(
        "/api/auth/registro",
        json={"nome_usuario": "gamer", "email": "gamer@l.dev", "senha": "senha123"},
    ).get_json()
    cab = {"Authorization": f"Bearer {corpo['token_acesso']}"}
    resposta = cliente.get("/api/v1/telas/jogo/jogo-rawg", headers=cab)
    assert resposta.status_code == 200
    dados = resposta.get_json()
    assert dados["imagem_capa"] == para_origem(IMG)
    assert cliente.get(dados["imagem_capa"]).status_code != 400  # host aceito pelo proxy
    assert jogo.capa_url == IMG


def test_card_carrega_imagem_persistida_sem_consultar_a_rawg(app, monkeypatch):
    from app.services.jogo_service import JogoService

    def proibido(*a, **k):
        raise AssertionError("abrir página não pode consultar a RAWG")

    monkeypatch.setattr(requests.Session, "get", proibido)
    jogo = novo_jogo("Jogo Rawg", "jogo-rawg", capa_url=IMG)
    card = JogoService.montar_card(jogo, favorito=False, na_biblioteca=False)
    assert card["imagem_capa"] == IMG


def test_card_sem_imagem_mantem_fallback_de_gradiente(app):
    from app.services.jogo_service import CAPA_PADRAO, JogoService

    card = JogoService.montar_card(novo_jogo("Sem Capa", "sem-capa"), False, False)
    assert card["imagem_capa"] == "" and card["arquivo_capa"] == ""
    assert card["capa"] == CAPA_PADRAO


def test_api_de_jogos_nao_aceita_gravar_rawg_id(app, cliente):
    from app.schemas.jogo import JogoEntradaSchema

    assert "rawg_id" in JogoEntradaSchema.Meta.dump_only
