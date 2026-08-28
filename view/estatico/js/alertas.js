/* Alertas: lista filtrável, resumo clicável, favoritos e notificações. */

const ALERT_ICONS = {
  wifi: '<path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><path d="M12 20h.01"/>',
  alert: '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/><path d="M12 9v4M12 17h.01"/>',
  check: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m22 4-10 10.01L9 11"/>',
};

const LEVEL_ICON = { critical: "wifi", warning: "alert", stable: "check" };
const CHAVE_INSCRITOS = "laac.alertas.inscritos";

let todosAlertas = [];
let filtroNivel = "todos";
let buscaTexto = "";

function glyphSvg(icon, size) {
  const body = ALERT_ICONS[icon] || ALERT_ICONS.alert;
  return '<svg viewBox="0 0 24 24" width="' + size + '" height="' + size +
    '" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
    body + "</svg>";
}

function inscritos() {
  try {
    return JSON.parse(localStorage.getItem(CHAVE_INSCRITOS) || "[]");
  } catch (_erro) {
    return [];
  }
}

function salvarInscritos(ids) {
  localStorage.setItem(CHAVE_INSCRITOS, JSON.stringify(ids));
}

function estaInscrito(id) {
  return inscritos().map(String).includes(String(id));
}

function alternarInscricao(id) {
  const atual = inscritos().map(String);
  const chave = String(id);
  const proximo = atual.includes(chave)
    ? atual.filter((item) => item !== chave)
    : atual.concat(chave);
  salvarInscritos(proximo);
  return proximo.includes(chave);
}

function renderAlert(alerta) {
  const capa = Api.capa({
    nome: alerta.jogo,
    capa: alerta.capa,
    imagem_capa: alerta.imagem_capa,
    arquivo_capa: alerta.arquivo_capa,
  });
  const detalhes = Api.criar(
    "a",
    {
      class: "btn btn--outline",
      href: alerta.jogo_slug ? "/jogo/" + alerta.jogo_slug + "?de=alertas" : "/alertas",
      style: "padding:6px 14px;font-size:12px",
    },
    "Ver detalhes"
  );
  const inscrever = Api.criar(
    "button",
    {
      type: "button",
      class: "btn btn--outline",
      style: "padding:6px 14px;font-size:12px",
    },
    estaInscrito(alerta.id) ? "Notificando" : "Notificar"
  );
  inscrever.addEventListener("click", (evento) => {
    evento.preventDefault();
    const ligado = alternarInscricao(alerta.id);
    inscrever.textContent = ligado ? "Notificando" : "Notificar";
  });

  const linha = Api.criar(
    "div",
    { class: "alert-row", id: "alerta-" + alerta.id },
    capa,
    Api.criar(
      "div",
      { class: "a-body" },
      Api.badge(alerta.severidade_rotulo, alerta.nivel),
      Api.criar("div", { class: "a-title" }, alerta.jogo),
      Api.criar("div", { class: "a-text" }, alerta.texto),
      Api.criar("div", { class: "a-when" }, alerta.quando || "")
    ),
    Api.criar(
      "div",
      { class: "a-status" },
      Api.criar("div", { class: "status-glyph " + alerta.nivel, html: glyphSvg(alerta.icone, 28) }),
      detalhes,
      inscrever
    )
  );
  return linha;
}

function renderSummaryRow(resumo) {
  const linha = Api.criar(
    "button",
    {
      type: "button",
      class: "summary-row" + (filtroNivel === resumo.nivel ? " is-on" : ""),
      "data-nivel": resumo.nivel,
    },
    Api.criar("span", {
      style: "color:var(--" + resumo.nivel + ");display:grid;place-items:center",
      html: glyphSvg(LEVEL_ICON[resumo.nivel] || "alert", 22),
    }),
    Api.criar("span", { class: "n", style: "font-size:20px" }, String(resumo.contagem)),
    Api.criar("span", {}, resumo.rotulo)
  );
  linha.addEventListener("click", () => {
    filtroNivel = filtroNivel === resumo.nivel ? "todos" : resumo.nivel;
    marcarChips();
    document.querySelectorAll("#al-summary .summary-row").forEach((no) => {
      no.classList.toggle("is-on", no.dataset.nivel === filtroNivel);
    });
    pintarLista();
  });
  return linha;
}

function renderFavorite(jogo) {
  return Api.cartaoDeJogo(jogo);
}

function alertasFiltrados() {
  const termo = buscaTexto.trim().toLowerCase();
  return todosAlertas.filter((alerta) => {
    if (filtroNivel !== "todos" && alerta.nivel !== filtroNivel) return false;
    if (!termo) return true;
    const blob = [alerta.jogo, alerta.texto, alerta.severidade_rotulo].join(" ").toLowerCase();
    return blob.includes(termo);
  });
}

function pintarLista() {
  const list = document.getElementById("al-list");
  const filtrados = alertasFiltrados();
  if (todosAlertas.length === 0) {
    Api.vazio("al-list", "Nenhum alerta no momento.");
    return;
  }
  if (filtrados.length === 0) {
    Api.vazio("al-list", "Nenhum alerta combina com esse filtro.");
    return;
  }
  list.replaceChildren();
  filtrados.forEach((a) => list.append(renderAlert(a)));
}

function marcarChips() {
  document.querySelectorAll("#al-filtros .chip").forEach((chip) => {
    const nivel = chip.dataset.nivel;
    chip.classList.toggle("is-off", nivel !== filtroNivel);
  });
  document.querySelectorAll("#al-summary .summary-row").forEach((no) => {
    no.classList.toggle("is-on", no.dataset.nivel === filtroNivel);
  });
}

function ligarFiltros() {
  const busca = document.getElementById("al-busca");
  if (busca) {
    busca.addEventListener("input", () => {
      buscaTexto = busca.value;
      pintarLista();
    });
  }
  document.querySelectorAll("#al-filtros .chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      filtroNivel = chip.dataset.nivel || "todos";
      marcarChips();
      pintarLista();
    });
  });
}

function ligarCtaNotificacoes() {
  const botao = document.getElementById("al-ativar-notificacoes");
  if (!botao) return;

  const pintar = () => {
    botao.textContent = notificacoesLigadas()
      ? "Notificações ativas"
      : "Ativar notificações";
  };
  pintar();

  botao.addEventListener("click", async () => {
    const ligar = !notificacoesLigadas();
    if (ligar && typeof Notification !== "undefined" && Notification.permission === "default") {
      try {
        await Notification.requestPermission();
      } catch (_erro) {
        /* o painel do sino continua funcionando sem permissão do navegador */
      }
    }
    definirNotificacoesLigadas(ligar);
    if (ligar && todosAlertas.length) {
      salvarInscritos(todosAlertas.map((a) => String(a.id)));
      pintarLista();
    }
    pintar();
    const sino = document.getElementById("casca-sino");
    if (sino && ligar) sino.click();
  });
}

async function initAlerts() {
  const data = await Api.pedir("/api/v1/telas/alertas");
  todosAlertas = data.alertas || [];
  ligarFiltros();
  ligarCtaNotificacoes();
  pintarLista();

  const summary = document.getElementById("al-summary");
  summary.replaceChildren();
  if (data.resumo.length === 0) {
    Api.vazio("al-summary");
  } else {
    data.resumo.forEach((s) => summary.append(renderSummaryRow(s)));
  }

  const favorites = document.getElementById("al-favorites");
  favorites.replaceChildren();
  if (data.favoritos.length === 0) {
    Api.vazio("al-favorites");
  } else {
    data.favoritos.forEach((f) => favorites.append(renderFavorite(f)));
  }

  const ancora = location.hash.replace("#", "");
  if (ancora) {
    const alvo = document.getElementById(ancora);
    if (alvo) alvo.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

Api.aoCarregar(() => {
  Api.carregando("al-list");
  initAlerts().catch((e) => {
    if (Api.ehSessaoExpirada(e)) return;
    if (!(e instanceof ErroApi)) {
      console.error(e);
    }
    Api.erro("al-list");
  });
});
