/* Comunidade: praças por jogo, busca na biblioteca, entrada no fórum,
   thread com respostas e exclusão de comentários. */

const ALVO = "co-topicos";

function formatarMilhar(numero) {
  return Number(numero).toLocaleString("pt-BR");
}

function slugSelecionado() {
  return new URLSearchParams(location.search).get("jogo") || "";
}

function selecionarPraca(slug) {
  const params = new URLSearchParams(location.search);
  if (slug) params.set("jogo", slug);
  else params.delete("jogo");
  const busca = document.getElementById("co-busca");
  if (busca && busca.value.trim()) params.set("busca", busca.value.trim());
  else params.delete("busca");
  const soBib = document.getElementById("co-bib");
  if (soBib && soBib.checked) params.set("biblioteca", "1");
  else params.delete("biblioteca");
  location.search = params.toString() ? "?" + params.toString() : "";
}

function cartaoDePraca(praca, ativa) {
  const capa = Api.capa(praca);
  return Api.criar(
    "div",
    {
      class: "game-tile" + (ativa ? " is-active" : ""),
      style: "cursor:pointer",
      onclick: () => selecionarPraca(praca.slug),
    },
    capa,
    Api.criar("div", { class: "t-name" }, praca.nome),
    Api.criar(
      "div",
      { class: "t-count" },
      formatarMilhar(praca.total_topicos) +
        " tópicos · " +
        formatarMilhar(praca.membros || 0) +
        " membros" +
        (praca.membro ? " · você participa" : "")
    )
  );
}

function linhaDeTopico(topico) {
  return Api.criar(
    "div",
    {
      class: "topic",
      style: "cursor:pointer",
      onclick: () => abrirTopico(topico.id),
    },
    Api.criar("div", { class: "avatar" }, Api.iniciaisDe(topico.autor)),
    Api.criar(
      "div",
      { class: "t-body" },
      Api.criar("div", { class: "t-title" }, topico.titulo),
      Api.criar(
        "div",
        { class: "t-meta" },
        "Iniciado por " + topico.autor + "   " + topico.quando
      ),
      Api.criar("div", { class: "t-excerpt" }, topico.resumo)
    ),
    Api.badge(topico.tipo_rotulo, topico.nivel)
  );
}

const LINHAS_ESTATISTICA = [
  ["Total de membros", "membros"],
  ["Tópicos criados", "topicos"],
  ["Mensagens", "mensagens"],
  ["Jogos ativos", "jogos_ativos"],
];

function linhaDeEstatistica(estatisticas, rotulo, chave) {
  return Api.criar(
    "div",
    { class: "stat-row" },
    Api.criar("span", { class: "s-label" }, rotulo),
    Api.criar("span", { class: "s-value" }, formatarMilhar(estatisticas[chave]))
  );
}

async function publicarTopico(selecionado) {
  const titulo = document.getElementById("co-titulo");
  const tipo = document.getElementById("co-tipo");
  const corpo = document.getElementById("co-corpo");
  const erro = document.getElementById("co-composer-erro");
  const botao = document.getElementById("co-publicar");

  erro.style.display = "none";
  if (!titulo.value.trim()) {
    titulo.focus();
    return;
  }

  botao.disabled = true;
  try {
    await Api.pedir("/api/v1/topicos", {
      metodo: "POST",
      corpo: {
        titulo: titulo.value.trim(),
        tipo: tipo.value,
        corpo: corpo.value.trim(),
        jogo_id: selecionado.id,
      },
    });
    location.reload();
  } catch (e) {
    if (Api.ehSessaoExpirada(e)) return;
    erro.textContent = e instanceof ErroApi ? e.message : "Não foi possível publicar.";
    erro.style.display = "block";
    botao.disabled = false;
  }
}

async function entrarNaPraca(selecionado) {
  await Api.pedir(`/api/v1/comunidade/pracas/${selecionado.id}/entrar`, {
    metodo: "POST",
    corpo: {},
  });
  location.reload();
}

async function sairDaPraca(selecionado) {
  await Api.pedir(`/api/v1/comunidade/pracas/${selecionado.id}/sair`, {
    metodo: "POST",
    corpo: {},
  });
  location.reload();
}

function pintarPosts(lista, posts) {
  lista.replaceChildren();
  if (!posts.length) {
    lista.append(
      Api.criar("div", { class: "muted" }, "Nenhuma resposta ainda. Seja o primeiro.")
    );
    return;
  }
  posts.forEach((post) => {
    const acoes = Api.criar("div", { class: "row", style: "gap:8px;margin-top:6px" });
    if (post.pode_apagar) {
      const btn = Api.criar(
        "button",
        { class: "btn btn--outline", type: "button", style: "padding:4px 10px;font-size:12px" },
        "Apagar"
      );
      btn.addEventListener("click", async () => {
        if (!confirm("Apagar este comentário?")) return;
        try {
          await Api.pedir(`/api/v1/comunidade/posts/${post.id}`, { metodo: "DELETE" });
          await abrirTopico(Number(document.getElementById("co-thread").dataset.topicoId));
        } catch (e) {
          if (Api.ehSessaoExpirada(e)) return;
          alert(e instanceof ErroApi ? e.message : "Não foi possível apagar.");
        }
      });
      acoes.append(btn);
    }
    const responder = Api.criar(
      "button",
      { class: "btn btn--outline", type: "button", style: "padding:4px 10px;font-size:12px" },
      "Responder"
    );
    responder.addEventListener("click", () => {
      const campo = document.getElementById("co-resposta");
      campo.dataset.parentId = String(post.id);
      campo.placeholder = "Respondendo a " + post.autor + "…";
      campo.focus();
    });
    acoes.append(responder);

    lista.append(
      Api.criar(
        "div",
        {
          class: "topic",
          style: post.parent_id ? "margin-left:28px;border-left:2px solid var(--border)" : "",
        },
        Api.criar(
          "a",
          {
            class: "avatar",
            href: "/perfil/" + post.autor_id,
            style: post.avatar_url
              ? `background-image:url(${post.avatar_url});background-size:cover`
              : `background:${post.cor_avatar}`,
          },
          post.avatar_url ? "" : Api.iniciaisDe(post.autor)
        ),
        Api.criar(
          "div",
          { class: "t-body" },
          Api.criar("div", { class: "t-title" }, post.autor),
          Api.criar("div", { class: "t-meta" }, post.quando),
          Api.criar("div", { class: "t-excerpt" }, post.conteudo),
          acoes
        )
      )
    );
  });
}

async function abrirTopico(topicoId) {
  const painel = document.getElementById("co-thread");
  const lista = document.getElementById("co-thread-posts");
  painel.style.display = "";
  painel.dataset.topicoId = String(topicoId);
  Api.carregando("co-thread-posts", "Carregando discussão…");
  try {
    const dados = await Api.pedir(`/api/v1/comunidade/topicos/${topicoId}`);
    document.getElementById("co-thread-titulo").textContent = dados.titulo;
    document.getElementById("co-thread-meta").textContent =
      dados.autor + " · " + dados.quando + " · " + dados.jogo_nome;
    document.getElementById("co-thread-corpo").textContent = dados.corpo || "";
    pintarPosts(lista, dados.posts || []);
    const form = document.getElementById("co-thread-form");
    form.style.display = dados.membro ? "" : "none";
    const aviso = document.getElementById("co-thread-aviso");
    aviso.style.display = dados.membro ? "none" : "";
    painel.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (e) {
    if (Api.ehSessaoExpirada(e)) return;
    Api.erro("co-thread-posts", "Não foi possível abrir o tópico.");
  }
}

async function iniciarComunidade() {
  Api.carregando(ALVO, "Carregando…");

  const params = new URLSearchParams(location.search);
  const slug = params.get("jogo") || "";
  const busca = params.get("busca") || "";
  const bib = params.get("biblioteca") === "1";

  const campoBusca = document.getElementById("co-busca");
  const checkBib = document.getElementById("co-bib");
  if (campoBusca) campoBusca.value = busca;
  if (checkBib) checkBib.checked = bib;

  const qs = new URLSearchParams();
  if (slug) qs.set("jogo", slug);
  if (busca) qs.set("busca", busca);
  if (bib) qs.set("biblioteca", "1");
  const caminho =
    "/api/v1/telas/comunidade" + (qs.toString() ? "?" + qs.toString() : "");

  let dados;
  try {
    dados = await Api.pedir(caminho);
  } catch (erro) {
    if (Api.ehSessaoExpirada(erro)) return;
    Api.erro(ALVO, "Não foi possível carregar a comunidade.");
    console.error(erro);
    return;
  }

  const selecionado = dados.selecionado;

  const pracas = document.getElementById("co-pracas");
  if (dados.jogos.length === 0) {
    Api.vazio("co-pracas", "Nenhuma praça encontrada com esse filtro.");
  } else {
    pracas.replaceChildren();
    dados.jogos.forEach((praca) =>
      pracas.append(
        cartaoDePraca(praca, Boolean(selecionado) && praca.slug === selecionado.slug)
      )
    );
  }

  document.getElementById("co-nome").textContent = selecionado ? selecionado.nome : "—";
  document.getElementById("co-contagem").textContent = selecionado
    ? formatarMilhar(selecionado.total_topicos) +
      " tópicos · " +
      formatarMilhar(selecionado.membros || 0) +
      " membros"
    : "—";

  const composer = document.getElementById("co-composer");
  const alternarComposer = document.getElementById("co-alternar-composer");
  const btnEntrar = document.getElementById("co-entrar");
  const btnSair = document.getElementById("co-sair");

  if (!selecionado) {
    alternarComposer.style.display = "none";
    if (btnEntrar) btnEntrar.style.display = "none";
    if (btnSair) btnSair.style.display = "none";
  } else {
    const membro = Boolean(dados.membro || selecionado.membro);
    if (btnEntrar) {
      btnEntrar.style.display = membro ? "none" : "";
      btnEntrar.onclick = () =>
        entrarNaPraca(selecionado).catch((e) => {
          if (!Api.ehSessaoExpirada(e)) alert(e.message || "Falha ao entrar.");
        });
    }
    if (btnSair) {
      btnSair.style.display = membro ? "" : "none";
      btnSair.onclick = () =>
        sairDaPraca(selecionado).catch((e) => {
          if (!Api.ehSessaoExpirada(e)) alert(e.message || "Falha ao sair.");
        });
    }
    alternarComposer.style.display = membro ? "" : "none";
    alternarComposer.addEventListener("click", () => {
      composer.style.display = composer.style.display === "none" ? "" : "none";
      if (composer.style.display !== "none") document.getElementById("co-titulo").focus();
    });
    document
      .getElementById("co-publicar")
      .addEventListener("click", () => publicarTopico(selecionado));
  }

  if (dados.topicos.length === 0) {
    Api.vazio(ALVO, "Ainda não há tópicos por aqui. Entre na praça e publique.");
  } else {
    const topicos = document.getElementById(ALVO);
    topicos.replaceChildren();
    dados.topicos.forEach((topico) => topicos.append(linhaDeTopico(topico)));
  }

  const stats = document.getElementById("co-stats");
  stats.replaceChildren();
  LINHAS_ESTATISTICA.forEach(([rotulo, chave]) =>
    stats.append(linhaDeEstatistica(dados.estatisticas, rotulo, chave))
  );

  const regras = document.getElementById("co-regras");
  regras.replaceChildren();
  dados.regras.forEach((regra) =>
    regras.append(
      Api.criar("div", { class: "muted", style: "padding:6px 0;font-size:13px" }, regra)
    )
  );

  const formBusca = document.getElementById("co-form-busca");
  if (formBusca) {
    formBusca.addEventListener("submit", (ev) => {
      ev.preventDefault();
      selecionarPraca(slugSelecionado());
    });
  }

  const enviarResposta = document.getElementById("co-enviar-resposta");
  if (enviarResposta) {
    enviarResposta.addEventListener("click", async () => {
      const campo = document.getElementById("co-resposta");
      const topicoId = Number(document.getElementById("co-thread").dataset.topicoId);
      const parentId = campo.dataset.parentId ? Number(campo.dataset.parentId) : null;
      try {
        await Api.pedir(`/api/v1/comunidade/topicos/${topicoId}/respostas`, {
          metodo: "POST",
          corpo: { conteudo: campo.value, parent_id: parentId },
        });
        campo.value = "";
        delete campo.dataset.parentId;
        campo.placeholder = "Escreva sua resposta…";
        await abrirTopico(topicoId);
      } catch (e) {
        if (Api.ehSessaoExpirada(e)) return;
        alert(e instanceof ErroApi ? e.message : "Não foi possível responder.");
      }
    });
  }
}

Api.aoCarregar(iniciarComunidade);
