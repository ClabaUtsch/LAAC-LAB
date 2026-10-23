/* Biblioteca + Detalhes: tela com grid de todos os jogos na biblioteca.
   Alterna para exibir a página completa do jogo (estilo SPA) sem sair da aba. */

let todosOsJogos = [];
let filtroAtual = 'todos'; 

// ========================== LÓGICA DA GRADE (BIBLIOTECA) ==========================

async function iniciarBiblioteca() {
  const alvo = "lib-grid";
  Api.carregando(alvo, "Carregando…");

  try {
    const dados = await Api.pedir("/api/v1/telas/biblioteca");
    todosOsJogos = dados.jogos || [];

    renderizarFiltros();
    renderizarGrid();
  } catch (erro) {
    if (!Api.ehSessaoExpirada(erro)) {
      Api.erro(alvo, "Não foi possível carregar a biblioteca.");
      console.error(erro);
    }
  }
}

function renderizarFiltros() {
  const filtros = document.getElementById("lib-filters");
  if (!filtros) return;

  const totalTodos = todosOsJogos.length;
  const totalFavoritos = todosOsJogos.filter(j => j.favorito).length;
  const estiloAtivo = "cursor: pointer;";
  const estiloInativo = "cursor: pointer; background: transparent; border: 1px solid var(--border-soft, #2a2d3e); color: var(--text-dim, #8b92a5);";

  const chipTodos = Api.criar("span", {
    class: "chip", style: filtroAtual === 'todos' ? estiloAtivo : estiloInativo,
    onclick: () => { filtroAtual = 'todos'; renderizarFiltros(); renderizarGrid(); }
  }, `Todos (${totalTodos})`);

  const chipFavoritos = Api.criar("span", {
    class: "chip", style: (filtroAtual === 'favoritos' ? estiloAtivo : estiloInativo) + " margin-left: 8px;",
    onclick: () => { filtroAtual = 'favoritos'; renderizarFiltros(); renderizarGrid(); }
  }, `Favoritos (${totalFavoritos})`);

  filtros.replaceChildren(chipTodos, chipFavoritos);
}

function renderizarGrid() {
  const alvo = "lib-grid";
  const grid = document.getElementById(alvo);
  if (!grid) return;

  grid.replaceChildren();

  const jogosFiltrados = filtroAtual === 'favoritos' ? todosOsJogos.filter(j => j.favorito) : todosOsJogos;

  if (jogosFiltrados.length === 0) {
    const msg = filtroAtual === 'favoritos' ? "Você ainda não tem nenhum jogo favorito." : "Sua biblioteca está vazia.";
    Api.vazio(alvo, msg);
    return;
  }

  jogosFiltrados.forEach((jogo) => {
    const cartao = Api.criar("div", { 
      class: "game-card", 
      style: "cursor: pointer; transition: transform 0.2s;",
      onclick: () => abrirDetalhesJogo(jogo.slug)
    },
      Api.capa(jogo),
      Api.criar("div", { class: "g-name" }, jogo.nome),
      Api.criar("div", { class: "row", style: "gap:8px" },
        Api.chipPontuacao(jogo.pontuacao, jogo.status),
        criarBotaoFavoritar(jogo)
      )
    );
    grid.append(cartao);
  });
}

function criarBotaoFavoritar(jogo) {
  const botao = Api.criar("button", {
    class: "btn btn--outline",
    style: "margin-top: 8px;",
    onclick: async (evento) => {
      evento.preventDefault();
      evento.stopPropagation();
      
      const txt = botao.textContent;
      botao.textContent = "...";
      botao.disabled = true;
      try {
        await Api.pedir(`/api/v1/biblioteca/${jogo.entrada_id}`, {
          metodo: "PATCH", corpo: { favorito: !jogo.favorito },
        });
        
        jogo.favorito = !jogo.favorito;
        botao.textContent = jogo.favorito ? "★ Favorito" : "☆ Favoritar";
        botao.disabled = false;
        
        if (filtroAtual === 'favoritos' && !jogo.favorito) {
           renderizarGrid();
           renderizarFiltros();
        }
      } catch (e) {
        botao.textContent = txt;
        botao.disabled = false;
      }
    }
  }, jogo.favorito ? "★ Favorito" : "☆ Favoritar");
  return botao;
}

// ========================== LÓGICA DE DETALHES DO JOGO (CÓPIA DO JOGO.JS) ==========================

function fecharDetalhesJogo() {
  // Limpa o trailer/midia se estiver rodando
  if (playerHls) { playerHls.destroy(); playerHls = null; }
  document.getElementById("jg-stage").replaceChildren();
  
  // Troca de tela
  document.getElementById("area-detalhes").style.display = "none";
  document.getElementById("area-grade").style.display = "block";
  document.getElementById("jg-fundo").style.backgroundImage = "none";
  window.scrollTo(0, 0);
}

async function abrirDetalhesJogo(slug) {
  document.getElementById("area-grade").style.display = "none";
  document.getElementById("area-detalhes").style.display = "block";
  window.scrollTo(0, 0);

  Api.carregando("jg-stats", "Carregando…");
  Api.carregando("jg-bugs", "Carregando…");
  Api.carregando("jg-comentarios", "Carregando…");

  try {
    const dados = await Api.pedir(`/api/v1/telas/jogo/${slug}`);
    montarTelaDetalhes(dados);
  } catch (erro) {
    if (Api.ehSessaoExpirada(erro)) return;
    fecharDetalhesJogo();
    alert("Não foi possível carregar os detalhes do jogo.");
  }
}

// ------ FUNÇÕES AUXILIARES DA TELA DE DETALHES ------

function fmt(n) { return Number(n).toLocaleString("pt-BR"); }
function nivelDeSeveridade(severidade) {
  if (severidade === "critica") return "critical";
  if (severidade === "alta" || severidade === "media") return "warning";
  return "stable";
}
const ESTILO_CAMPO = "width:100%;background:var(--surface-2);border:1px solid var(--border);border-radius:10px;padding:10px 12px;color:var(--text);font:inherit";

function construirFormularioDeBug(jogoId) {
  const titulo = Api.criar("input", { type: "text", placeholder: "Título do bug…", style: ESTILO_CAMPO + ";margin-top:8px" });
  const erro = Api.criar("div", { style: "color:var(--critical);font-size:12px;margin-top:6px;display:none" });
  const botao = Api.criar("button", {
      class: "btn btn--primary", style: "width:100%;justify-content:center;margin-top:8px",
      onclick: async () => {
        if (!titulo.value.trim()) return;
        botao.disabled = true;
        erro.style.display = "none";
        try {
          await Api.pedir("/api/v1/relatos-bug", { metodo: "POST", corpo: { jogo_id: jogoId, titulo: titulo.value.trim() } });
          abrirDetalhesJogo(todosOsJogos.find(j => j.id === jogoId).slug); // Recarrega os detalhes localmente
        } catch (e) {
          if (Api.ehSessaoExpirada(e)) return;
          erro.textContent = e.erros ? Object.values(e.erros).flat().join(" ") : "Erro: " + e.message;
          erro.style.display = "block";
          botao.disabled = false;
        }
      },
    }, "🐞 Reportar um bug"
  );
  return Api.criar("div", { style: "margin-top:12px" }, titulo, botao, erro);
}

function construirComposerDeComentario(jogoId) {
  const texto = Api.criar("textarea", { placeholder: "Escreva um comentário…", rows: "2", style: ESTILO_CAMPO });
  const erro = Api.criar("div", { style: "color:var(--critical);font-size:12px;margin-top:6px;display:none" });
  const botao = Api.criar("button", {
      class: "btn btn--primary", style: "margin-top:8px;width:100%;justify-content:center",
      onclick: async () => {
        if (!texto.value.trim()) return;
        botao.disabled = true;
        erro.style.display = "none";
        try {
          await Api.pedir("/api/v1/avaliacoes", { metodo: "POST", corpo: { jogo_id: jogoId, comentario: texto.value.trim() } });
          abrirDetalhesJogo(todosOsJogos.find(j => j.id === jogoId).slug); // Recarrega
        } catch (e) {
          if (Api.ehSessaoExpirada(e)) return;
          erro.textContent = "Erro: " + e.message;
          erro.style.display = "block";
          botao.disabled = false;
        }
      },
    }, "Comentar"
  );
  return Api.criar("div", { style: "margin-bottom:14px" }, texto, botao, erro);
}

function montarStats(dados) {
  const ttz = dados.tempo_para_zerar || {};
  document.getElementById("jg-stats").replaceChildren(
    Api.criar("div", { class: "store-kpi" }, Api.criar("div", { class: "store-kpi-n" }, fmt(dados.conquistas)), Api.criar("div", { class: "store-kpi-l" }, "Conquistas")),
    Api.criar("div", { class: "store-kpi" }, Api.criar("div", { class: "store-kpi-n" }, ttz.medio || "—"), Api.criar("div", { class: "store-kpi-l" }, "Tempo médio para zerar")),
    Api.criar("div", { class: "row", style: "gap:16px;margin-top:8px" }, Api.criar("span", { class: "vote up" }, "👍 " + fmt(dados.curtidas)), Api.criar("span", { class: "vote down" }, "👎 " + fmt(dados.descurtidas)))
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
  if (playerHls) { playerHls.destroy(); playerHls = null; }
  
  if (item.tipo === "trailer") {
    if (/youtube\.com|youtu\.be/.test(item.src)) {
      stage.replaceChildren(Api.criar("iframe", { class: "store-frame", src: item.src.replace("www.youtube.com", "www.youtube-nocookie.com") + (item.src.includes("?") ? "&" : "?") + "rel=0&modestbranding=1", title: item.titulo || "Trailer", allow: "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture", allowfullscreen: "true" }));
    } else {
      const video = Api.criar("video", { class: "store-frame", controls: "true", playsinline: "true", poster: item.thumb || "", src: item.src, onerror: () => { if (itensMidia.length > 1) mostrarMidia(indiceMidia + 1); } });
      stage.replaceChildren(video);
      if (/\.m3u8(\?|$)/.test(item.src) && window.Hls && Hls.isSupported()) {
        playerHls = new Hls(); playerHls.loadSource(item.src); playerHls.attachMedia(video);
      }
    }
  } else {
    stage.replaceChildren(Api.criar("img", { class: "store-shot", src: item.src, alt: item.titulo || "" }));
  }
  document.querySelectorAll("#jg-thumbs .store-thumb").forEach((el, i) => { el.classList.toggle("is-on", i === indiceMidia); });
}

function montarGaleria(dados) {
  itensMidia = dados.galeria || [];
  const thumbs = document.getElementById("jg-thumbs");
  const prev = document.getElementById("jg-prev");
  const next = document.getElementById("jg-next");
  if (itensMidia.length === 0) {
    document.getElementById("jg-stage").replaceChildren(Api.criar("div", { class: "store-shot store-shot--empty" }, "Sem mídia cadastrada."));
    thumbs.replaceChildren(); prev.hidden = true; next.hidden = true; return;
  }
  prev.hidden = itensMidia.length < 2; next.hidden = itensMidia.length < 2;
  thumbs.replaceChildren(...itensMidia.map((item, i) => {
      const thumb = Api.criar("button", { type: "button", class: "store-thumb" + (i === 0 ? " is-on" : ""), onclick: () => mostrarMidia(i) }, item.thumb ? Api.criar("img", { src: item.thumb, alt: item.titulo || "" }) : Api.criar("span", { class: "store-thumb-play" }, "▶"));
      if (item.tipo === "trailer") thumb.append(Api.criar("span", { class: "store-thumb-play" }, "▶"));
      return thumb;
    })
  );
  prev.onclick = () => mostrarMidia(indiceMidia - 1);
  next.onclick = () => mostrarMidia(indiceMidia + 1);
  mostrarMidia(0);
}

function montarRequisitos(dados) {
  const req = dados.requisitos || {}; const min = req.minimo || []; const rec = req.recomendado || [];
  const bloco = document.getElementById("jg-req-bloco"); const alvo = document.getElementById("jg-requisitos");
  if (!min.length && !rec.length) { bloco.hidden = true; return; }
  bloco.hidden = false;
  const coluna = (titulo, linhas) => Api.criar("div", { class: "store-req-col" }, Api.criar("div", { class: "store-req-h" }, titulo), ...linhas.map((l) => Api.criar("div", { class: "store-req-l" }, l)));
  const colunas = []; if (min.length) colunas.push(coluna("Mínimos", min)); if (rec.length) colunas.push(coluna("Recomendados", rec));
  alvo.replaceChildren(...colunas);
}

function montarMeta(dados) {
  const linhas = [];
  if (dados.desenvolvedora) linhas.push(["Desenvolvedora", dados.desenvolvedora]);
  if (dados.publicadora) linhas.push(["Publicadora", dados.publicadora]);
  linhas.push(["Lançamento", dados.ultima_atualizacao || "—"]);
  document.getElementById("jg-meta").replaceChildren(...linhas.map(([k, v]) => Api.criar("div", { class: "stat-row" }, Api.criar("span", { class: "s-label" }, k), Api.criar("span", { class: "s-value" }, v))));
}

function rotuloConfirmar(confirmacoes, jaConfirmei) { return jaConfirmei ? "✓ Confirmado" : `👍 Confirmar (${confirmacoes})`; }

function botaoConfirmarBug(bug) {
  const botao = Api.criar("button", { class: "btn btn--outline", type: "button" }, rotuloConfirmar(bug.confirmacoes, bug.ja_confirmei));
  const marcarConfirmado = () => { botao.disabled = true; botao.style.opacity = "0.6"; botao.style.cursor = "default"; botao.textContent = rotuloConfirmar(bug.confirmacoes, true); };
  if (bug.ja_confirmei) marcarConfirmado();
  botao.addEventListener("click", async () => {
    botao.disabled = true;
    try {
      await Api.pedir("/api/v1/votos-bug", { metodo: "POST", corpo: { relato_id: bug.id } });
      bug.confirmacoes += 1; marcarConfirmado();
    } catch (e) {
      if (Api.ehSessaoExpirada(e)) return;
      if (e instanceof ErroApi && e.status === 409) { marcarConfirmado(); return; }
      botao.disabled = false;
    }
  });
  return botao;
}

function montarBugs(dados) {
  if (dados.bugs.length === 0) { Api.vazio("jg-bugs", "Nenhum bug ativo reportado."); } else {
    document.getElementById("jg-bugs").replaceChildren(...dados.bugs.map((bug) => Api.criar("div", { class: "row between", style: "padding:6px 0;font-size:13px" }, Api.criar("div", { class: "row", style: "gap:8px" }, Api.criar("span", {}, bug.titulo + " · " + bug.categoria), Api.badge(bug.severidade_rotulo, nivelDeSeveridade(bug.severidade))), botaoConfirmarBug(bug))));
  }
  document.getElementById("jg-relatar").replaceChildren(construirFormularioDeBug(dados.id));
}

function montarComentarios(dados) {
  document.getElementById("jg-comentar").replaceChildren(construirComposerDeComentario(dados.id));
  if (dados.comentarios.length === 0) { Api.vazio("jg-comentarios", "Nenhum comentário ainda."); return; }
  document.getElementById("jg-comentarios").replaceChildren(...dados.comentarios.map((c) => Api.criar("div", { class: "comment" }, Api.criar("div", { class: "avatar" }, Api.iniciaisDe(c.autor)), Api.criar("div", {}, Api.criar("div", { class: "c-author" }, c.autor), Api.criar("div", { class: "c-text" }, c.texto)))));
}

function montarTelaDetalhes(dados) {
  document.getElementById("jg-nome").textContent = dados.nome;
  document.getElementById("jg-atualizacao").textContent = dados.ultima_atualizacao;
  document.getElementById("jg-legenda").textContent = dados.descricao_curta || "Sem sinopse cadastrada.";
  const tags = dados.tags || [];
  document.getElementById("jg-tags").replaceChildren(...tags.map((t) => Api.criar("span", { class: "store-chip" }, t)));
  document.getElementById("jg-sobre").textContent = dados.sobre || "Sem descrição disponível.";
  document.getElementById("jg-merch").textContent = dados.merch || "Sem merch disponível.";

  const capa = Api.urlDeMidia(dados.arquivo_capa || dados.imagem_capa || "");
  const cover = document.getElementById("jg-cover");
  const fundo = document.getElementById("jg-fundo");
  if (capa) {
    cover.src = capa; cover.alt = dados.nome; cover.hidden = false; Api.pintarImagemDeFundo(fundo, capa);
  } else {
    cover.hidden = true; Api.pintarFundo(fundo, dados.capa, ["#1b1d2e", "#0a0b12"]);
  }

  montarGaleria(dados);
  montarStats(dados);
  montarMeta(dados);
  montarRequisitos(dados);
  montarBugs(dados);
  montarComentarios(dados);
}

Api.aoCarregar(iniciarBiblioteca);