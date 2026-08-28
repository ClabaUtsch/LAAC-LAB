/* Início (home) screen: carrossel dos jogos em destaque, cards de
   atualização com capa, trending topics e jogos favoritos. Tudo vem de
   /api/v1/telas/inicio e é renderizado com os helpers de Api.

   IMPORTANTE: a chave `jogo` na resposta é o NOME de exibição;
   o slug é sempre `jogo_slug` em banners/atualizacoes. O ranking do
   mês linka pelo `slug` do cartão. */

/* Vertical three-dots glyph shown at the end of each trending row. */
const TRENDING_GLYPH =
  '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">' +
  '<circle cx="12" cy="5" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="19" r="1.6"/></svg>';

const INTERVALO_CARROSSEL_MS = 6000;

let indiceBanner = 0;
let timerCarrossel = null;

function fonteCapa(item) {
  return item.arquivo_capa || item.imagem_capa || "";
}

function aplicarBanner(banner) {
  const hero = document.getElementById("home-hero");
  hero.style.background = `linear-gradient(135deg, ${banner.capa[0]}, ${banner.capa[1]})`;
  document.getElementById("hero-text").textContent = banner.titulo;

  const img = document.getElementById("hero-img");
  const fonte = fonteCapa(banner);
  if (fonte) {
    img.src = fonte;
    img.alt = banner.jogo || "";
    img.hidden = false;
    img.onerror = () => {
      img.hidden = true;
    };
  } else {
    img.removeAttribute("src");
    img.alt = "";
    img.hidden = true;
  }
}

function marcarPonto(indice) {
  document.querySelectorAll("#hero-dots span").forEach((ponto, i) => {
    ponto.classList.toggle("on", i === indice);
  });
}

function irParaBanner(banners, indice) {
  indiceBanner = (indice + banners.length) % banners.length;
  aplicarBanner(banners[indiceBanner]);
  marcarPonto(indiceBanner);
}

function pararCarrossel() {
  if (timerCarrossel) {
    clearInterval(timerCarrossel);
    timerCarrossel = null;
  }
}

function reiniciarTimer(banners) {
  pararCarrossel();
  if (banners.length < 2) return;
  timerCarrossel = setInterval(() => {
    irParaBanner(banners, indiceBanner + 1);
  }, INTERVALO_CARROSSEL_MS);
}

function iniciarCarrossel(banners) {
  const dots = document.getElementById("hero-dots");
  dots.replaceChildren();
  banners.forEach((banner, i) => {
    const ponto = Api.criar("span", i === 0 ? { class: "on" } : {});
    ponto.setAttribute("role", "button");
    ponto.setAttribute("tabindex", "0");
    ponto.setAttribute("aria-label", "Mostrar " + banner.jogo);
    ponto.addEventListener("click", (evento) => {
      evento.stopPropagation();
      irParaBanner(banners, i);
      reiniciarTimer(banners);
    });
    ponto.addEventListener("keydown", (evento) => {
      if (evento.key === "Enter" || evento.key === " ") {
        evento.preventDefault();
        ponto.click();
      }
    });
    dots.append(ponto);
  });

  indiceBanner = 0;
  aplicarBanner(banners[0]);

  const prev = document.getElementById("hero-prev");
  const next = document.getElementById("hero-next");
  const varios = banners.length > 1;
  prev.hidden = !varios;
  next.hidden = !varios;
  prev.onclick = (evento) => {
    evento.stopPropagation();
    irParaBanner(banners, indiceBanner - 1);
    reiniciarTimer(banners);
  };
  next.onclick = (evento) => {
    evento.stopPropagation();
    irParaBanner(banners, indiceBanner + 1);
    reiniciarTimer(banners);
  };

  const hero = document.getElementById("home-hero");
  hero.style.cursor = banners[0].jogo_slug ? "pointer" : "";
  hero.onclick = (evento) => {
    if (evento.target.closest("#hero-dots") || evento.target.closest(".hero-arrow")) return;
    const slug = banners[indiceBanner].jogo_slug;
    if (slug) location.href = "/jogo/" + slug;
  };

  if (varios) {
    reiniciarTimer(banners);
    hero.onmouseenter = pararCarrossel;
    hero.onmouseleave = () => reiniciarTimer(banners);
  }
}

let indiceNoticia = 0;

function fonteCapaNoticia(item) {
  return item.arquivo_capa || item.imagem_capa || "";
}

function aplicarNoticia(item) {
  const bloco = document.getElementById("home-noticias");
  bloco.style.background = `linear-gradient(135deg, ${item.capa[0]}, ${item.capa[1]})`;
  document.getElementById("news-game").textContent = item.jogo || "Comunidade";
  document.getElementById("news-title").textContent = item.titulo;
  document.getElementById("news-text").textContent = item.resumo || "";
  document.getElementById("news-when").textContent = item.quando || "";
  const img = document.getElementById("news-img");
  const fonte = fonteCapaNoticia(item);
  if (fonte) {
    img.src = fonte;
    img.alt = item.titulo || "";
    img.hidden = false;
    img.onerror = () => {
      img.hidden = true;
    };
  } else {
    img.removeAttribute("src");
    img.alt = "";
    img.hidden = true;
  }
}

function marcarPontoNoticia(indice) {
  document.querySelectorAll("#news-dots span").forEach((ponto, i) => {
    ponto.classList.toggle("on", i === indice);
  });
}

function irParaNoticia(noticias, indice) {
  indiceNoticia = (indice + noticias.length) % noticias.length;
  aplicarNoticia(noticias[indiceNoticia]);
  marcarPontoNoticia(indiceNoticia);
}

function iniciarCarrosselNoticias(noticias) {
  const dots = document.getElementById("news-dots");
  dots.replaceChildren();
  noticias.forEach((item, i) => {
    const ponto = Api.criar("span", i === 0 ? { class: "on" } : {});
    ponto.setAttribute("role", "button");
    ponto.setAttribute("tabindex", "0");
    ponto.setAttribute("aria-label", "Mostrar " + item.titulo);
    ponto.addEventListener("click", (evento) => {
      evento.stopPropagation();
      irParaNoticia(noticias, i);
    });
    ponto.addEventListener("keydown", (evento) => {
      if (evento.key === "Enter" || evento.key === " ") {
        evento.preventDefault();
        ponto.click();
      }
    });
    dots.append(ponto);
  });

  indiceNoticia = 0;
  aplicarNoticia(noticias[0]);

  const prev = document.getElementById("news-prev");
  const next = document.getElementById("news-next");
  const varios = noticias.length > 1;
  prev.hidden = !varios;
  next.hidden = !varios;
  prev.onclick = (evento) => {
    evento.stopPropagation();
    irParaNoticia(noticias, indiceNoticia - 1);
  };
  next.onclick = (evento) => {
    evento.stopPropagation();
    irParaNoticia(noticias, indiceNoticia + 1);
  };

  const bloco = document.getElementById("home-noticias");
  bloco.style.cursor = noticias[0].jogo_slug ? "pointer" : "";
  bloco.onclick = (evento) => {
    if (evento.target.closest("#news-dots") || evento.target.closest(".hero-arrow")) return;
    const slug = noticias[indiceNoticia].jogo_slug;
    if (slug) location.href = "/jogo/" + slug;
  };
}

function capaDaAtualizacao(u) {
  /* atualizacoes[] usa `jogo` (nome de exibição). Api.capa espera
     `nome` e `iniciais` — montamos esse shape aqui. */
  return Api.capa({
    nome: u.jogo,
    iniciais: Api.iniciaisDe(u.jogo),
    capa: u.capa,
    imagem_capa: u.imagem_capa,
    arquivo_capa: u.arquivo_capa,
  });
}

async function initHome() {
  const data = await Api.pedir("/api/v1/telas/inicio");

  // --- Carrossel: um slide por jogo em destaque (maior metacritic) ---
  // `banners` vem `[]` em banco recém-criado (nenhum jogo ainda tem
  // metacritic o bastante) — sem esta guarda, `data.banners[0]` é
  // undefined e `banner.capa[0]` explode em TypeError, não ErroApi.
  if (data.banners.length === 0) {
    // Escreve em hero-text em vez de Api.vazio("home-hero", ...):
    // home-hero é ancestral de hero-text/hero-dots, lidos por id no
    // ramo com banner logo abaixo. Api.vazio() faz replaceChildren()
    // no alvo — chamado em home-hero apagaria esses filhos, a mesma
    // armadilha que quebrava pf-usuario (achado do item 4).
    document.getElementById("hero-text").textContent = "Nenhum destaque no momento.";
    document.getElementById("hero-dots").replaceChildren();
    document.getElementById("hero-prev").hidden = true;
    document.getElementById("hero-next").hidden = true;
    document.getElementById("hero-img").hidden = true;
  } else {
    iniciarCarrossel(data.banners);
  }

  const noticias = data.noticias || [];
  if (noticias.length === 0) {
    document.getElementById("news-title").textContent = "Nenhuma notícia no momento.";
    document.getElementById("news-text").textContent = "";
    document.getElementById("news-game").textContent = "";
    document.getElementById("news-when").textContent = "";
    document.getElementById("news-dots").replaceChildren();
    document.getElementById("news-prev").hidden = true;
    document.getElementById("news-next").hidden = true;
    document.getElementById("news-img").hidden = true;
  } else {
    iniciarCarrosselNoticias(noticias);
  }

  // --- Grade de atualizações recentes (capa real quando o jogo tem) ---
  const updates = document.getElementById("home-updates");
  if (data.atualizacoes.length === 0) {
    Api.vazio("home-updates");
  } else {
    updates.replaceChildren();
    data.atualizacoes.forEach((u) => {
      updates.append(Api.criar("div", { class: "update-card" },
        capaDaAtualizacao(u),
        Api.criar("div", { class: "u-body" },
          Api.badge(u.etiqueta, u.nivel),
          Api.criar("div", { class: "u-title" }, u.titulo),
          Api.criar("div", { class: "u-text" }, u.texto),
          Api.criar("div", { class: "u-when" }, u.quando))));
    });
  }

  // --- Trending: separador de grupo (.section-title) sempre que o rótulo muda ---
  const trending = document.getElementById("home-trending");
  if (data.assuntos.length === 0) {
    Api.vazio("home-trending");
  } else {
    let lastGroup = null;
    data.assuntos.forEach((t) => {
      if (t.grupo !== lastGroup) {
        trending.append(Api.criar("div", { class: "section-title", style: "margin:12px 0 4px" }, t.grupo));
        lastGroup = t.grupo;
      }
      trending.append(Api.criar("div", { class: "trending-item" },
        Api.criar("div", { class: "t-txt" }, t.titulo),
        Api.criar("span", { class: "dim", html: TRENDING_GLYPH })));
    });
  }

  // --- Pódio: 1º, 2º e 3º lugar; só o nome do jogo é um link ---
  const favorites = document.getElementById("home-favorites");
  const ranking = (data.mais_jogados || []).slice(0, 3);
  if (ranking.length === 0) {
    Api.vazio("home-favorites", "Ainda não há ranking deste mês.");
  } else {
    const posto = ["1º lugar", "2º lugar", "3º lugar"];
    ranking.forEach((g, i) => {
      favorites.append(
        Api.criar(
          "div",
          { class: "podium-item" },
          Api.criar("div", { class: "podium-place" }, posto[i]),
          Api.criar("a", { class: "podium-name", href: "/jogo/" + g.slug }, g.nome)
        )
      );
    });
  }
}

Api.aoCarregar(() => {
  Api.carregando("home-updates");
  initHome().catch((e) => {
    // Um 401 já redirecionou: pintar "Não foi possível carregar." por
    // cima é ruído durante uma navegação que já está em voo.
    if (Api.ehSessaoExpirada(e)) return;
    if (!(e instanceof ErroApi)) {
      // Erro que não é da API (ex.: TypeError de acesso indevido a um
      // campo) não pode ficar mudo no console...
      console.error(e);
    }
    // ...nem deixar a região presa em "Carregando…" para sempre: essa
    // é a mesma regra do item 4 (nenhuma região em carregamento
    // permanente), e vale tanto para ErroApi quanto para qualquer
    // outro erro.
    Api.erro("home-updates");
  });
});
