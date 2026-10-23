/* Explorar: catálogo paginado (busca/gênero/ordenação) + adicionar à
   biblioteca.

   Convertido de view/herdado/explorar.js: a paginação nova é
   {itens, proxima}, não {results, next} do DRF. `proxima` já é um
   caminho relativo com TODOS os parâmetros da consulta preservados —
   basta usá-lo como está para "Carregar mais"; remontar a query a
   partir dos filtros da tela faria a página 2 voltar à ordenação
   padrão e misturar resultados fora de ordem. */

const ATRASO_BUSCA_MS = 400;

let proximoCaminho = null;
const comparados = [];
let generosPreenchidos = false;
let temporizadorBusca = null;

/* Monta o caminho da primeira página a partir dos três filtros da
   tela. Usado só para pedidos "do zero" (reset); seguir "Carregar
   mais" nunca passa por aqui — usa `proximoCaminho` puro. */
function montarCaminhoDaBusca() {
  const parametros = new URLSearchParams();
  const busca = document.getElementById("ex-busca").value.trim();
  const genero = document.getElementById("ex-genero").value;
  const ordenar = document.getElementById("ex-ordem").value;
  if (busca) parametros.set("busca", busca);
  if (genero) parametros.set("genero", genero);
  if (ordenar) parametros.set("ordenar_por", ordenar);
  parametros.set("pagina", "1");
  return "/api/v1/telas/explorar?" + parametros.toString();
}

/* Cartão canônico (Api.cartaoDeJogo) + botão de adicionar à
   biblioteca, que usa o `id` do jogo — não o slug. */
function montarCartao(jogo) {
  const botao = Api.criar(
    "button",
    {
      class: "btn btn--primary",
      style: "margin-top:8px;width:100%;justify-content:center",
      onclick: async (evento) => {
        evento.preventDefault();
        evento.stopPropagation();
        botao.disabled = true;
        try {
          await Api.pedir("/api/v1/biblioteca", {
            metodo: "POST",
            corpo: { jogo_id: jogo.id },
          });
          botao.textContent = "Na biblioteca ✓";
        } catch (erro) {
          if (Api.ehSessaoExpirada(erro)) return;
          if (erro.status === 409) {
            // Já estava na biblioteca: sucesso idempotente, sem pintar erro.
            botao.textContent = "Na biblioteca ✓";
            return;
          }
          botao.textContent = "Erro";
          botao.disabled = false;
        }
      },
    },
    jogo.na_biblioteca ? "Na biblioteca ✓" : "Adicionar"
  );
  if (jogo.na_biblioteca) botao.disabled = true;

  const quero = Api.criar(
    "button",
    {
      type: "button",
      class: "btn btn--outline",
      style: "margin-top:8px;width:100%;justify-content:center",
      onclick: (evento) => {
        evento.preventDefault();
        evento.stopPropagation();
        const ligado = Api.filaTeste.alternar(jogo);
        quero.textContent = ligado ? "Na fila de teste ✓" : "Quero testar";
      },
    },
    Api.filaTeste.tem(jogo.slug) ? "Na fila de teste ✓" : "Quero testar"
  );

  const noComparar = comparados.some((item) => item.slug === jogo.slug);
  const comparar = Api.criar(
    "button",
    {
      type: "button",
      class: "btn btn--outline",
      style: "margin-top:8px;width:100%;justify-content:center",
      onclick: (evento) => {
        evento.preventDefault();
        evento.stopPropagation();
        alternarComparacao(jogo);
      },
    },
    noComparar ? "Na comparação ✓" : "Comparar saúde"
  );

  const pecas = [
    Api.criar("span", { class: "store-chip" }, "Abrir vitrine"),
    botao,
    quero,
    comparar,
  ];
  const cartao = Api.cartaoDeJogo(jogo, Api.criar("div", {}, ...pecas));
  cartao.classList.add("game-card--vitrine");
  const capa = cartao.querySelector(".cover");
  if (capa && jogo.tem_trailer) {
    capa.style.position = "relative";
    capa.append(Api.criar("span", { class: "store-thumb-play" }, "▶ Trailer"));
  }
  return cartao;
}

function alternarComparacao(jogo) {
  const indice = comparados.findIndex((item) => item.slug === jogo.slug);
  if (indice >= 0) comparados.splice(indice, 1);
  else {
    if (comparados.length >= 2) comparados.shift();
    comparados.push({
      slug: jogo.slug,
      nome: jogo.nome,
      pontuacao: jogo.pontuacao,
      rotulo: (jogo.status && jogo.status.rotulo) || "",
    });
  }
  pintarComparacao();
  document.querySelectorAll("#ex-grade .game-card").forEach((cartao) => {
    const href = cartao.getAttribute("href") || "";
    const slug = href.split("/").pop();
    const botao = [...cartao.querySelectorAll("button")].find((el) =>
      el.textContent.indexOf("ompara") >= 0 || el.textContent.indexOf("comparação") >= 0
    );
    if (!botao) return;
    const ligado = comparados.some((item) => item.slug === slug);
    botao.textContent = ligado ? "Na comparação ✓" : "Comparar saúde";
  });
}

function pintarComparacao() {
  const barra = document.getElementById("ex-comparar");
  if (!barra) return;
  if (comparados.length === 0) {
    barra.hidden = true;
    barra.replaceChildren();
    return;
  }
  barra.hidden = false;
  if (comparados.length === 1) {
    barra.replaceChildren(
      Api.criar("p", { class: "muted" }, "Escolha mais um jogo para comparar a saúde.")
    );
    return;
  }
  const [a, b] = comparados;
  const pa = Number(a.pontuacao) || 0;
  const pb = Number(b.pontuacao) || 0;
  let leitura = "Empate de instabilidade no bugômetro.";
  if (pa !== pb) {
    leitura = (pa > pb ? a.nome : b.nome) + " está mais instável.";
  }
  const coluna = (jogo) =>
    Api.criar(
      "a",
      { class: "compare-col", href: "/jogo/" + jogo.slug },
      Api.criar("div", { class: "compare-nome" }, jogo.nome),
      Api.criar("div", { class: "compare-nota" }, String(jogo.pontuacao ?? "—")),
      Api.criar("div", { class: "muted" }, jogo.rotulo || "Bugômetro")
    );
  barra.replaceChildren(
    Api.criar("div", { class: "compare-grid" }, coluna(a), coluna(b)),
    Api.criar("p", { class: "compare-leitura" }, leitura)
  );
}

function montarVitrine(jogos) {
  const bloco = document.getElementById("ex-vitrine");
  const lista = Array.isArray(jogos) ? jogos : jogos ? [jogos] : [];
  if (!lista.length) {
    bloco.hidden = true;
    bloco.replaceChildren();
    return;
  }
  bloco.hidden = false;
  bloco.replaceChildren(
    ...lista.map((jogo) => {
      const arte = jogo.foto_vitrine || jogo.arquivo_capa || jogo.imagem_capa || "";
      return Api.criar(
        "a",
        { class: "ex-vitrine-card", href: "/jogo/" + jogo.slug },
        arte
          ? Api.criar("img", {
              class: "ex-vitrine-art",
              src: arte,
              alt: jogo.nome,
            })
          : Api.criar("div", { class: "ex-vitrine-art" }),
        Api.criar(
          "div",
          { class: "ex-vitrine-copy" },
          Api.criar("div", { class: "ex-vitrine-kicker" }, jogo.tem_trailer ? "Trailer + fotos" : "Vitrine"),
          Api.criar("h2", {}, jogo.nome),
          Api.criar(
            "p",
            {},
            jogo.descricao_curta || "Abra a página da loja: trailer, capturas e requisitos."
          ),
          Api.criar("span", { class: "btn btn--primary" }, "Abrir vitrine")
        )
      );
    })
  );
}

/* Os gêneros vêm dentro do próprio envelope de /telas/explorar, então
   só precisam ser lidos uma vez — repopular a cada busca perderia a
   seleção atual do filtro sem necessidade. */
function preencherGeneros(generos) {
  if (generosPreenchidos) return;
  generosPreenchidos = true;
  const select = document.getElementById("ex-genero");
  select.append(Api.criar("option", { value: "" }, "Todos os gêneros"));
  (generos || []).forEach((genero) => {
    select.append(Api.criar("option", { value: genero.slug }, genero.nome));
  });
}

async function carregar(caminho, reset) {
  const grade = document.getElementById("ex-grade");
  const botaoMais = document.getElementById("ex-mais");
  const erroMais = document.getElementById("ex-erro-mais");

  if (reset) Api.carregando("ex-grade", "Carregando…");
  erroMais.replaceChildren();
  botaoMais.disabled = true;

  let dados;
  try {
    dados = await Api.pedir(caminho);
  } catch (erro) {
    if (Api.ehSessaoExpirada(erro)) return;
    if (reset) {
      // Carregamento INICIAL: a grade não tem nada a preservar, então
      // substituí-la pelo estado de erro é a resposta certa.
      Api.erro("ex-grade", "Não foi possível carregar os jogos.");
      botaoMais.style.display = "none";
    } else {
      // "Carregar mais": a grade já tem itens na tela (defeito 7 da
      // revisão). Api.erro("ex-grade", ...) faz replaceChildren e
      // apagaria tudo por causa de uma oscilação de rede no incremental
      // — o erro vai perto do botão, que continua visível e clicável
      // para nova tentativa, em vez de escondido.
      Api.erro("ex-erro-mais", "Não foi possível carregar mais jogos.");
      botaoMais.disabled = false;
    }
    return;
  }

  preencherGeneros(dados.generos);

  if (reset) montarVitrine(dados.vitrines);

  // Busca sem resultado é caso comum, não erro.
  if (reset && dados.itens.length === 0) {
    Api.vazio("ex-grade", "Nenhum jogo encontrado.");
    proximoCaminho = null;
    botaoMais.style.display = "none";
    return;
  }

  if (reset) grade.replaceChildren();
  dados.itens.forEach((jogo) => grade.append(montarCartao(jogo)));

  proximoCaminho = dados.proxima;
  botaoMais.style.display = proximoCaminho ? "" : "none";
  botaoMais.disabled = false;
}

function recarregarDoZero() {
  carregar(montarCaminhoDaBusca(), true).catch((erro) => {
    if (!Api.ehSessaoExpirada(erro)) console.error(erro);
  });
}

/* Sem isto, cada tecla digitada na busca dispara um pedido — a tela
   afogaria a API numa consulta por letra. */
function buscarComAtraso() {
  clearTimeout(temporizadorBusca);
  temporizadorBusca = setTimeout(recarregarDoZero, ATRASO_BUSCA_MS);
}

async function iniciarExplorar() {
  const inicial = new URLSearchParams(location.search).get("busca");
  if (inicial) document.getElementById("ex-busca").value = inicial;
  document.getElementById("ex-busca").addEventListener("input", buscarComAtraso);
  document.getElementById("ex-genero").addEventListener("change", recarregarDoZero);
  document.getElementById("ex-ordem").addEventListener("change", recarregarDoZero);
  document.getElementById("ex-mais").addEventListener("click", () => {
    if (proximoCaminho) carregar(proximoCaminho, false);
  });

  await carregar(montarCaminhoDaBusca(), true);
}

Api.aoCarregar(iniciarExplorar);
