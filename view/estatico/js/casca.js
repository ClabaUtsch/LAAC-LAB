/* Comportamento da casca: tema, item ativo, avatar e card de nível.

   O markup da casca é copiado em cada página; só o comportamento é
   compartilhado. O item ativo vem de <body data-tela="..."> e não do
   HTML, para que as cópias possam ser byte a byte idênticas. */

function aplicarTema() {
  const raiz = document.documentElement;
  if (localStorage.getItem("tema") === "claro") raiz.classList.add("light");
  const botao = document.getElementById("alternar-tema");
  if (!botao) return;
  botao.addEventListener("click", () => {
    raiz.classList.toggle("light");
    localStorage.setItem("tema", raiz.classList.contains("light") ? "claro" : "escuro");
  });
}

function marcarItemAtivo() {
  const tela = document.body.dataset.tela;
  if (!tela) return;
  const item = document.querySelector(`.nav-item[data-tela="${tela}"]`);
  if (item) item.classList.add("is-active");
}

async function preencherUsuario() {
  const eu = await Api.pedir("/api/v1/eu");
  const nome = document.getElementById("sb-nome");
  if (nome) nome.textContent = eu.apelido || eu.nome_usuario;
  const nivel = document.getElementById("sb-nivel");
  if (nivel) nivel.textContent = "Nível " + eu.nivel;
  const xp = document.getElementById("sb-xp");
  if (xp) xp.textContent = `${eu.xp} / ${eu.xp_max} XP`;
  const barra = document.getElementById("sb-xp-barra");
  if (barra && eu.xp_max) {
    barra.style.width = Math.round((eu.xp / eu.xp_max) * 100) + "%";
  }
  document.querySelectorAll(".js-avatar").forEach((a) => {
    a.textContent = Api.iniciaisDe(eu.nome_usuario);
    a.style.background = eu.cor_avatar;
  });
}

function irParaResultadosDaBusca(texto) {
  const q = (texto || "").trim();
  if (!q) return;
  const destino = "/explorar?busca=" + encodeURIComponent(q);
  if (document.body.dataset.tela === "explorar") {
    const campoPagina = document.getElementById("ex-busca");
    if (campoPagina) {
      campoPagina.value = q;
      history.replaceState(null, "", destino);
      campoPagina.dispatchEvent(new Event("input"));
    } else {
      location.href = destino;
    }
    return;
  }
  location.href = destino;
}

function fecharSugestoes(painel) {
  if (!painel) return;
  painel.hidden = true;
  painel.replaceChildren();
}

function pintarSugestoes(painel, jogos, consulta) {
  if (!jogos.length) {
    painel.hidden = false;
    painel.replaceChildren(
      Api.criar("div", { class: "search-sugestao search-sugestao--vazia" },
        "Nenhum jogo com “" + consulta + "”.")
    );
    return;
  }
  painel.hidden = false;
  painel.replaceChildren(
    ...jogos.map((jogo) =>
      Api.criar(
        "a",
        { class: "search-sugestao", href: "/jogo/" + jogo.slug, role: "option" },
        Api.criar("span", { class: "search-sugestao-nome" }, jogo.nome),
        Api.criar("span", { class: "search-sugestao-ir" }, "Abrir vitrine")
      )
    )
  );
}

function ligarBuscaDoTopo() {
  const campo = document.getElementById("casca-busca");
  const painel = document.getElementById("casca-busca-sugestoes");
  if (!campo || !painel) return;

  const inicial = new URLSearchParams(location.search).get("busca");
  if (inicial && !campo.value) campo.value = inicial;

  let temporizador = null;
  let pedido = 0;

  campo.addEventListener("input", () => {
    const texto = campo.value.trim();
    clearTimeout(temporizador);
    if (!texto) {
      fecharSugestoes(painel);
      return;
    }
    temporizador = setTimeout(async () => {
      const sequencia = ++pedido;
      try {
        const dados = await Api.pedir(
          "/api/v1/telas/explorar?busca=" + encodeURIComponent(texto) + "&por_pagina=8"
        );
        if (sequencia !== pedido) return;
        pintarSugestoes(painel, dados.itens || [], texto);
      } catch (erro) {
        if (Api.ehSessaoExpirada(erro)) return;
        if (sequencia !== pedido) return;
        painel.hidden = false;
        painel.replaceChildren(
          Api.criar("div", { class: "search-sugestao search-sugestao--vazia" },
            "Não foi possível buscar agora.")
        );
      }
    }, 280);
  });

  campo.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape") {
      fecharSugestoes(painel);
      return;
    }
    if (evento.key === "Enter") {
      evento.preventDefault();
      fecharSugestoes(painel);
      irParaResultadosDaBusca(campo.value);
    }
  });

  document.addEventListener("click", (evento) => {
    if (!evento.target.closest(".search")) fecharSugestoes(painel);
  });
}

const CHAVE_NOTIFICACOES = "laac.notificacoes.ativas";

function notificacoesLigadas() {
  return localStorage.getItem(CHAVE_NOTIFICACOES) === "1";
}

function definirNotificacoesLigadas(ligado) {
  localStorage.setItem(CHAVE_NOTIFICACOES, ligado ? "1" : "0");
}

function pintarNotificacoes(lista, dados) {
  const itens = (dados && dados.itens) || [];
  if (!itens.length) {
    lista.replaceChildren(Api.criar("p", { class: "muted" }, "Nenhuma notificação agora."));
    return;
  }
  lista.replaceChildren(
    ...itens.map((item) =>
      Api.criar(
        "a",
        { class: "notify-item", href: item.href || "#" },
        Api.criar("div", { class: "notify-item-kicker" }, item.tipo === "conta" ? "Conta" : "Alerta"),
        Api.criar("div", { class: "notify-item-title" }, item.titulo || ""),
        Api.criar("div", { class: "notify-item-text" }, item.texto || ""),
        Api.criar("div", { class: "notify-item-when" }, item.quando || "")
      )
    )
  );
}

async function carregarNotificacoes() {
  try {
    return await Api.pedir("/api/v1/eu/notificacoes");
  } catch (erro) {
    if (Api.ehSessaoExpirada(erro)) throw erro;
    const [eu, tela] = await Promise.all([
      Api.pedir("/api/v1/eu"),
      Api.pedir("/api/v1/telas/alertas"),
    ]);
    const itens = [
      {
        tipo: "conta",
        titulo: "Conta ativa",
        texto: "Você está conectado como " + (eu.apelido || eu.nome_usuario) + ".",
        quando: "agora",
        href: "/perfil",
      },
      {
        tipo: "conta",
        titulo: "Nível " + eu.nivel,
        texto: eu.xp + " XP nesta temporada. Abra o perfil para ver o progresso.",
        quando: "esta semana",
        href: "/perfil",
      },
    ];
    for (const alerta of (tela.alertas || []).slice(0, 5)) {
      itens.push({
        tipo: "alerta",
        titulo: alerta.jogo,
        texto: alerta.texto,
        quando: alerta.quando || "",
        href: "/alertas#alerta-" + alerta.id,
      });
    }
    return { itens, nao_lidas: itens.length };
  }
}

function ligarSino() {
  const botao = document.getElementById("casca-sino");
  const painel = document.getElementById("casca-notificacoes");
  const lista = document.getElementById("casca-notificacoes-lista");
  const ponto = document.getElementById("casca-sino-dot");
  if (!botao || !painel || !lista) return;

  if (ponto) ponto.hidden = false;
  let ignorarFechar = false;

  const fechar = () => {
    painel.hidden = true;
    botao.setAttribute("aria-expanded", "false");
  };

  botao.addEventListener("click", async (evento) => {
    evento.preventDefault();
    evento.stopPropagation();
    const abrir = painel.hidden;
    if (!abrir) {
      fechar();
      return;
    }
    ignorarFechar = true;
    painel.hidden = false;
    botao.setAttribute("aria-expanded", "true");
    lista.replaceChildren(Api.criar("p", { class: "muted" }, "Carregando…"));
    try {
      const dados = await carregarNotificacoes();
      pintarNotificacoes(lista, dados);
      if (ponto) ponto.hidden = true;
    } catch (erro) {
      if (Api.ehSessaoExpirada(erro)) return;
      lista.replaceChildren(
        Api.criar("p", { class: "muted" }, "Não foi possível carregar as notificações.")
      );
    } finally {
      setTimeout(() => {
        ignorarFechar = false;
      }, 0);
    }
  });

  document.addEventListener("click", (evento) => {
    if (ignorarFechar) return;
    if (!evento.target.closest(".topbar-notify")) fechar();
  });
  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape") fechar();
  });
}

Api.aoCarregar(async () => {
  aplicarTema();
  marcarItemAtivo();
  // As telas de autenticação não têm sidebar e não têm token: pedir
  // /api/v1/eu daria 401, que redirecionaria o login para o login.
  if (document.body.dataset.casca === "auth") return;
  ligarBuscaDoTopo();
  ligarSino();
  await preencherUsuario();
});
