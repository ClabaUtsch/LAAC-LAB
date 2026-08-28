/* Detalhe do jogo: barra (nome + última atualização) + hero + sobre +
   estatísticas + bugs reportados + comentários.

   O slug não chega mais por `data-slug` (o template Django injetava; o
   mecanismo morreu com ele). A rota `/jogo/<slug>` serve o MESMO
   `jogo.html` para qualquer slug, então quem sabe qual jogo é este é o
   último segmento de `location.pathname`. */

/* "1284" -> "1.284" (formato pt-BR). Unifica com a tela de comunidade:
   o servidor manda o inteiro cru, o cliente formata. */
function fmt(n) {
  return Number(n).toLocaleString("pt-BR");
}

/* severidade (baixa/media/alta/critica) -> nível de badge/score-chip. */
function nivelDeSeveridade(severidade) {
  if (severidade === "critica") return "critical";
  if (severidade === "alta" || severidade === "media") return "warning";
  return "stable";
}

const ESTILO_CAMPO =
  "width:100%;background:var(--surface-2);border:1px solid var(--border);" +
  "border-radius:10px;padding:10px 12px;color:var(--text);font:inherit";

/* Mini-formulário "Reportar um bug": só título é obrigatório além do
   jogo_id — categoria e severidade têm default no servidor. */
function construirFormularioDeBug(jogoId) {
  const titulo = Api.criar("input", {
    type: "text",
    placeholder: "Título do bug…",
    style: ESTILO_CAMPO + ";margin-top:8px",
  });
  const erro = Api.criar("div", {
    style: "color:var(--critical);font-size:12px;margin-top:6px;display:none",
  });

  const botao = Api.criar(
    "button",
    {
      class: "btn btn--primary",
      style: "width:100%;justify-content:center;margin-top:8px",
      onclick: async () => {
        if (!titulo.value.trim()) return;
        botao.disabled = true;
        erro.style.display = "none";
        try {
          await Api.pedir("/api/v1/relatos-bug", {
            metodo: "POST",
            corpo: { jogo_id: jogoId, titulo: titulo.value.trim() },
          });
          location.reload();
        } catch (e) {
          if (Api.ehSessaoExpirada(e)) return;
          // 422 -> {"erros": {campo: [msg]}}, não {"erro": msg}: usar
          // e.message aqui sempre caía no genérico "Não foi possível
          // completar a operação.", desperdiçando o campo que a API
          // já apontou (o bugômetro já faz isto certo).
          erro.textContent = e.erros
            ? Object.values(e.erros).flat().join(" ")
            : "Não foi possível reportar o bug. " + e.message;
          erro.style.display = "block";
          botao.disabled = false;
        }
      },
    },
    "🐞 Reportar um bug"
  );

  return Api.criar("div", { style: "margin-top:12px" }, titulo, botao, erro);
}

/* Compositor de comentário: publica em /api/v1/avaliacoes e recarrega a
   tela (a resposta do POST não traz o nome do autor, só usuario_id — o
   jeito simples e confiável de mostrar o comentário certo é recarregar,
   igual ao botão de favoritar da biblioteca). */
function construirComposerDeComentario(jogoId) {
  const texto = Api.criar("textarea", {
    placeholder: "Escreva um comentário…",
    rows: "2",
    style: ESTILO_CAMPO,
  });
  const erro = Api.criar("div", {
    style: "color:var(--critical);font-size:12px;margin-top:6px;display:none",
  });

  const botao = Api.criar(
    "button",
    {
      class: "btn btn--primary",
      style: "margin-top:8px;width:100%;justify-content:center",
      onclick: async () => {
        if (!texto.value.trim()) return;
        botao.disabled = true;
        erro.style.display = "none";
        try {
          await Api.pedir("/api/v1/avaliacoes", {
            metodo: "POST",
            corpo: { jogo_id: jogoId, comentario: texto.value.trim() },
          });
          location.reload();
        } catch (e) {
          if (Api.ehSessaoExpirada(e)) return;
          erro.textContent = "Não foi possível comentar. " + e.message;
          erro.style.display = "block";
          botao.disabled = false;
        }
      },
    },
    "Comentar"
  );

  return Api.criar("div", { style: "margin-bottom:14px" }, texto, botao, erro);
}

function montarStats(dados) {
  const ttz = dados.tempo_para_zerar || {};

  document.getElementById("jg-stats").replaceChildren(
    Api.criar(
      "div",
      { class: "store-kpi" },
      Api.criar("div", { class: "store-kpi-n" }, fmt(dados.conquistas)),
      Api.criar("div", { class: "store-kpi-l" }, "Conquistas")
    ),
    Api.criar(
      "div",
      { class: "store-kpi" },
      Api.criar("div", { class: "store-kpi-n" }, ttz.medio || "—"),
      Api.criar("div", { class: "store-kpi-l" }, "Tempo médio para zerar")
    ),
    Api.criar(
      "div",
      { class: "row", style: "gap:16px;margin-top:8px" },
      Api.criar("span", { class: "vote up" }, "👍 " + fmt(dados.curtidas)),
      Api.criar("span", { class: "vote down" }, "👎 " + fmt(dados.descurtidas))
    )
  );
}

let indiceMidia = 0;
let itensMidia = [];
let playerHls = null;

function mostrarMidia(indice) {
  if (!itensMidia.length) return;
  indiceMidia = (indice + itensMidia.length) % itensMidia.length;
  const item = itensMidia[indiceMidia];
  const stage = document.getElementById("jg-stage");
  if (playerHls) {
    playerHls.destroy();
    playerHls = null;
  }
  if (item.tipo === "trailer") {
    if (/youtube\.com|youtu\.be/.test(item.src)) {
      stage.replaceChildren(
        Api.criar("iframe", {
          class: "store-frame",
          src: item.src.replace("www.youtube.com", "www.youtube-nocookie.com") + (item.src.includes("?") ? "&" : "?") + "rel=0&modestbranding=1",
          title: item.titulo || "Trailer",
          allow: "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture",
          allowfullscreen: "true",
        })
      );
    } else {
      const video = Api.criar("video", {
        class: "store-frame",
        controls: "true",
        playsinline: "true",
        poster: item.thumb || "",
        src: item.src,
        onerror: () => {
          if (itensMidia.length > 1) mostrarMidia(indiceMidia + 1);
        },
      });
      stage.replaceChildren(video);
      if (/\.m3u8(\?|$)/.test(item.src) && window.Hls && Hls.isSupported()) {
        playerHls = new Hls();
        playerHls.loadSource(item.src);
        playerHls.attachMedia(video);
      }
    }
  } else {
    stage.replaceChildren(
      Api.criar("img", {
        class: "store-shot",
        src: item.src,
        alt: item.titulo || "",
      })
    );
  }
  document.querySelectorAll("#jg-thumbs .store-thumb").forEach((el, i) => {
    el.classList.toggle("is-on", i === indiceMidia);
  });
}

function montarGaleria(dados) {
  itensMidia = dados.galeria || [];
  const thumbs = document.getElementById("jg-thumbs");
  const prev = document.getElementById("jg-prev");
  const next = document.getElementById("jg-next");
  if (itensMidia.length === 0) {
    document.getElementById("jg-stage").replaceChildren(
      Api.criar("div", { class: "store-shot store-shot--empty" }, "Sem mídia cadastrada.")
    );
    thumbs.replaceChildren();
    prev.hidden = true;
    next.hidden = true;
    return;
  }
  prev.hidden = itensMidia.length < 2;
  next.hidden = itensMidia.length < 2;
  thumbs.replaceChildren(
    ...itensMidia.map((item, i) => {
      const thumb = Api.criar(
        "button",
        {
          type: "button",
          class: "store-thumb" + (i === 0 ? " is-on" : ""),
          onclick: () => mostrarMidia(i),
        },
        item.thumb
          ? Api.criar("img", { src: item.thumb, alt: item.titulo || "" })
          : Api.criar("span", { class: "store-thumb-play" }, "▶")
      );
      if (item.tipo === "trailer") {
        thumb.append(Api.criar("span", { class: "store-thumb-play" }, "▶"));
      }
      return thumb;
    })
  );
  prev.onclick = () => mostrarMidia(indiceMidia - 1);
  next.onclick = () => mostrarMidia(indiceMidia + 1);
  mostrarMidia(0);
}

function montarRequisitos(dados) {
  const req = dados.requisitos || {};
  const min = req.minimo || [];
  const rec = req.recomendado || [];
  const bloco = document.getElementById("jg-req-bloco");
  const alvo = document.getElementById("jg-requisitos");
  if (!min.length && !rec.length) {
    bloco.hidden = true;
    return;
  }
  bloco.hidden = false;
  const coluna = (titulo, linhas) =>
    Api.criar(
      "div",
      { class: "store-req-col" },
      Api.criar("div", { class: "store-req-h" }, titulo),
      ...linhas.map((l) => Api.criar("div", { class: "store-req-l" }, l))
    );
  const colunas = [];
  if (min.length) colunas.push(coluna("Mínimos", min));
  if (rec.length) colunas.push(coluna("Recomendados", rec));
  alvo.replaceChildren(...colunas);
}

function montarMeta(dados) {
  const linhas = [];
  if (dados.desenvolvedora) {
    linhas.push(["Desenvolvedora", dados.desenvolvedora]);
  }
  if (dados.publicadora) {
    linhas.push(["Publicadora", dados.publicadora]);
  }
  linhas.push(["Lançamento", dados.ultima_atualizacao || "—"]);
  document.getElementById("jg-meta").replaceChildren(
    ...linhas.map(([k, v]) =>
      Api.criar(
        "div",
        { class: "stat-row" },
        Api.criar("span", { class: "s-label" }, k),
        Api.criar("span", { class: "s-value" }, v)
      )
    )
  );
}

function rotuloConfirmar(confirmacoes, jaConfirmei) {
  return jaConfirmei ? "✓ Confirmado" : `👍 Confirmar (${confirmacoes})`;
}

/* Botão "confirmar bug": POST /api/v1/votos-bug com {relato_id}. Nasce
   desabilitado e rotulado quando `bug.ja_confirmei` já é true (chega
   pronto do backend, por relato e por usuário logado).

   Um 409 aqui não é erro: a unique (relato_id, usuario_id) do backend
   significa que o voto já existe — o estado desejado já foi alcançado
   (ex.: duplo clique). Trata como sucesso idempotente — desabilita e
   rotula como confirmado, sem incrementar a contagem e sem pintar
   mensagem de erro, que aqui seria só ruído. */
function botaoConfirmarBug(bug) {
  const botao = Api.criar(
    "button",
    { class: "btn btn--outline", type: "button" },
    rotuloConfirmar(bug.confirmacoes, bug.ja_confirmei)
  );

  const marcarConfirmado = () => {
    botao.disabled = true;
    botao.style.opacity = "0.6";
    botao.style.cursor = "default";
    botao.textContent = rotuloConfirmar(bug.confirmacoes, true);
  };
  if (bug.ja_confirmei) marcarConfirmado();

  botao.addEventListener("click", async () => {
    botao.disabled = true;
    try {
      await Api.pedir("/api/v1/votos-bug", { metodo: "POST", corpo: { relato_id: bug.id } });
      bug.confirmacoes += 1;
      marcarConfirmado();
    } catch (e) {
      if (Api.ehSessaoExpirada(e)) return;
      if (e instanceof ErroApi && e.status === 409) {
        marcarConfirmado();
        return;
      }
      botao.disabled = false;
    }
  });

  return botao;
}

function montarBugs(dados) {
  if (dados.bugs.length === 0) {
    Api.vazio("jg-bugs", "Nenhum bug ativo reportado.");
  } else {
    document.getElementById("jg-bugs").replaceChildren(
      ...dados.bugs.map((bug) =>
        Api.criar(
          "div",
          { class: "row between", style: "padding:6px 0;font-size:13px" },
          Api.criar(
            "div",
            { class: "row", style: "gap:8px" },
            Api.criar("span", {}, bug.titulo + " · " + bug.categoria),
            Api.badge(bug.severidade_rotulo, nivelDeSeveridade(bug.severidade))
          ),
          botaoConfirmarBug(bug)
        )
      )
    );
  }

  document.getElementById("jg-relatar").replaceChildren(construirFormularioDeBug(dados.id));
}

function montarComentarios(dados) {
  document.getElementById("jg-comentar").replaceChildren(construirComposerDeComentario(dados.id));

  if (dados.comentarios.length === 0) {
    Api.vazio("jg-comentarios", "Nenhum comentário ainda.");
    return;
  }

  document.getElementById("jg-comentarios").replaceChildren(
    ...dados.comentarios.map((c) =>
      Api.criar(
        "div",
        { class: "comment" },
        Api.criar("div", { class: "avatar" }, Api.iniciaisDe(c.autor)),
        Api.criar(
          "div",
          {},
          Api.criar("div", { class: "c-author" }, c.autor),
          Api.criar("div", { class: "c-text" }, c.texto)
        )
      )
    )
  );
}

function montarTela(dados) {
  document.title = dados.nome + " · LaaCLab";
  document.getElementById("jg-nome").textContent = dados.nome;
  document.getElementById("jg-titulo").textContent = dados.nome;
  document.getElementById("jg-atualizacao").textContent = dados.ultima_atualizacao;
  document.getElementById("jg-legenda").textContent =
    dados.descricao_curta || "Sem sinopse cadastrada.";
  const tags = dados.tags || [];
  document.getElementById("jg-tags").replaceChildren(
    ...tags.map((t) => Api.criar("span", { class: "store-chip" }, t))
  );
  document.getElementById("jg-sobre").textContent =
    dados.sobre || "Sem descrição disponível.";
  document.getElementById("jg-merch").textContent = dados.merch;

  const capa = dados.arquivo_capa || dados.imagem_capa || "";
  const cover = document.getElementById("jg-cover");
  const fundo = document.getElementById("jg-fundo");
  if (capa) {
    cover.src = capa;
    cover.alt = dados.nome;
    cover.hidden = false;
    fundo.style.backgroundImage = `url("${capa}")`;
  } else {
    cover.hidden = true;
    const [c1, c2] = dados.capa || ["#1b1d2e", "#0a0b12"];
    fundo.style.background = `linear-gradient(135deg, ${c1}, ${c2})`;
  }

  montarGaleria(dados);
  montarStats(dados);
  montarMeta(dados);
  montarRequisitos(dados);
  montarBugs(dados);
  montarComentarios(dados);
}

function veioDeAlertas() {
  if (new URLSearchParams(location.search).get("de") === "alertas") return true;
  try {
    const origem = document.referrer ? new URL(document.referrer) : null;
    return Boolean(origem && origem.origin === location.origin && origem.pathname === "/alertas");
  } catch (_erro) {
    return false;
  }
}

function aplicarVoltar() {
  const link = document.getElementById("jg-voltar");
  if (!link) return;
  if (veioDeAlertas()) {
    link.href = "/alertas";
    link.textContent = "← Alertas";
  }
}

async function iniciarJogo() {
  aplicarVoltar();
  const slug = location.pathname.split("/").pop();

  Api.carregando("jg-stats", "Carregando…");
  Api.carregando("jg-bugs", "Carregando…");
  Api.carregando("jg-comentarios", "Carregando…");

  const dados = await Api.pedir(`/api/v1/telas/jogo/${slug}`);
  montarTela(dados);
}

Api.aoCarregar(() => {
  iniciarJogo().catch((erro) => {
    if (erro instanceof ErroApi && erro.status === 404) {
      Api.erro("conteudo", "Jogo não encontrado.");
      return;
    }
    if (Api.ehSessaoExpirada(erro)) return;
    Api.erro("conteudo", "Não foi possível carregar o jogo.");
  });
});
