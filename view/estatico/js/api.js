/* Núcleo do frontend do LAAC-LAB.

   Substitui o `app.js` herdado, que falava com o Django por cookie de
   sessão e header X-CSRFToken. A API atual é JWT Bearer, então tudo que
   toca a rede passa por aqui. */

const CHAVE_ACESSO = "laaclab.acesso";
const CHAVE_RENOVACAO = "laaclab.renovacao";

class ErroApi extends Error {
  constructor(status, mensagem, erros) {
    super(mensagem);
    this.status = status;
    this.erros = erros || null; // {campo: [mensagem]}, só em 422
  }
}

const Api = {
  // ---- sessão ----------------------------------------------------------
  acesso() {
    return localStorage.getItem(CHAVE_ACESSO) || "";
  },

  renovacao() {
    return localStorage.getItem(CHAVE_RENOVACAO) || "";
  },

  autenticado() {
    return Boolean(Api.acesso());
  },

  guardarSessao(dados) {
    if (dados.token_acesso) localStorage.setItem(CHAVE_ACESSO, dados.token_acesso);
    if (dados.token_renovacao) localStorage.setItem(CHAVE_RENOVACAO, dados.token_renovacao);
  },

  limparSessao() {
    localStorage.removeItem(CHAVE_ACESSO);
    localStorage.removeItem(CHAVE_RENOVACAO);
  },

  paraLogin() {
    // Freio próprio: sem isto, uma chamada autenticada esquecida na
    // própria página de login recarrega /login indefinidamente. A
    // disciplina que evita isso hoje mora em login.js e casca.js — o
    // núcleo não deve depender de dois arquivos lembrarem dela.
    if (location.pathname === "/login") {
      Api.limparSessao();
      return;
    }
    Api.limparSessao();
    const destino = encodeURIComponent(location.pathname + location.search);
    window.location = "/login?destino=" + destino;
  },

  /* Valida `?destino=` antes de usar como próximo local após login ou
     registro. Quem escreve esse parâmetro é sempre Api.paraLogin()
     acima, que produz location.pathname + location.search —
     same-origin. Qualquer outra coisa é redirecionamento aberto (a
     tela de login real, no domínio real, manda a vítima para
     `destino=//evil.com` depois de autenticar) ou pior:
     `destino=javascript:...` roda na própria origem, DEPOIS que
     guardarSessao() já gravou o token no localStorage.

     Só aceita destino same-origin. Validar isso por regex é adivinhar
     o parser de URL do navegador, e perde-se: `/\evil.com` e um TAB
     logo depois da primeira barra viram host externo (o parser
     remove TAB/LF/CR de qualquer posição antes de resolver, e trata
     `\` como `/`). Deixar o próprio parser resolver e comparar a
     origem é o que não erra. */
  destinoSeguro(bruto) {
    if (typeof bruto !== "string" || bruto === "") return "/";
    let url;
    try {
      url = new URL(bruto, location.origin);
    } catch {
      return "/";
    }
    return url.origin === location.origin ? url.pathname + url.search + url.hash : "/";
  },

  /* Troca o refresh por um access novo. O endpoint é
     @jwt_required(refresh=True): o refresh vai no Authorization, e a
     resposta traz SÓ token_acesso — o refresh segue o mesmo até expirar. */
  async renovar() {
    const refresh = Api.renovacao();
    if (!refresh) return false;
    const resposta = await fetch("/api/auth/renovar", {
      method: "POST",
      headers: { Authorization: "Bearer " + refresh, Accept: "application/json" },
    });
    if (!resposta.ok) return false;
    const dados = await resposta.json();
    localStorage.setItem(CHAVE_ACESSO, dados.token_acesso);
    return true;
  },

  // ---- rede ------------------------------------------------------------
  /* Único caminho de acesso à API.

     Em 401 tenta renovar UMA vez e refaz a requisição. Sem isso o access
     de 30 min expulsaria a pessoa no meio de qualquer sessão longa, e o
     refresh de 7 dias nunca serviria para nada. */
  async pedir(caminho, opcoes = {}, jaRenovou = false) {
    const { metodo = "GET", corpo = null, autenticar = true } = opcoes;

    const cabecalhos = { Accept: "application/json" };
    if (corpo !== null) cabecalhos["Content-Type"] = "application/json";
    if (autenticar && Api.acesso()) cabecalhos.Authorization = "Bearer " + Api.acesso();

    const resposta = await fetch(caminho, {
      method: metodo,
      headers: cabecalhos,
      body: corpo === null ? undefined : JSON.stringify(corpo),
    });

    if (resposta.status === 401 && autenticar) {
      if (jaRenovou || !(await Api.renovar())) {
        Api.paraLogin();
        throw new ErroApi(401, "Sessão expirada.");
      }
      return Api.pedir(caminho, opcoes, true);
    }

    if (resposta.status === 204) return null;

    const dados = await resposta.json().catch(() => ({}));
    if (!resposta.ok) {
      // 401/403/404/409 -> {"erro": msg}; 422 -> {"erros": {campo: [msg]}}
      throw new ErroApi(
        resposta.status,
        dados.erro || "Não foi possível completar a operação.",
        dados.erros
      );
    }
    return dados;
  },

  // ---- DOM -------------------------------------------------------------
  /* criar("div", {class: "card"}, filho, "texto") */
  criar(tag, atributos = {}, ...filhos) {
    const no = document.createElement(tag);
    for (const [chave, valor] of Object.entries(atributos)) {
      if (chave === "class") no.className = valor;
      // `html` injeta innerHTML: NUNCA com texto vindo da API. Conteúdo
      // de fórum e comentário é escrito por outros usuários — passe como
      // filho de texto, que vai por createTextNode.
      else if (chave === "html") no.innerHTML = valor;
      else if (chave.startsWith("on") && typeof valor === "function") {
        no.addEventListener(chave.slice(2), valor);
      } else if (valor !== null && valor !== undefined) {
        no.setAttribute(chave, valor);
      }
    }
    for (const filho of filhos.flat()) {
      if (filho === null || filho === undefined) continue;
      no.append(filho.nodeType ? filho : document.createTextNode(String(filho)));
    }
    return no;
  },

  iniciaisDe(nome) {
    return (nome || "?").trim().slice(0, 2).toUpperCase();
  },

  /* Ladrilho de capa: imagem quando houver, senão gradiente + iniciais.
     `capa` é sempre um par de cores hex. Os dois campos de imagem vazios
     é o caso normal, não erro. */
  /* Só hex entra em `style`. Cor vinda da API interpolada crua
     quebra o CSS (`#fff;background:url(...)`). */
  corSegura(valor, reserva) {
    return /^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/.test(String(valor || ""))
      ? String(valor)
      : reserva;
  },

  coresDoCartao(capa, reserva) {
    const base = Array.isArray(reserva) && reserva.length >= 2
      ? reserva
      : ["#2b2d47", "#14152b"];
    const lista = Array.isArray(capa) ? capa : [];
    return [Api.corSegura(lista[0], base[0]), Api.corSegura(lista[1], base[1])];
  },

  pintarFundo(elemento, capa, reserva) {
    if (!elemento) return;
    const par = Api.coresDoCartao(capa, reserva);
    elemento.style.background = "linear-gradient(135deg, " + par[0] + ", " + par[1] + ")";
  },

  /* Caminho local (`/media/...`) ou https. Rejeita javascript:, data:
     e aspas que escapariam de url("..."). */
  urlDeMidia(bruto) {
    if (typeof bruto !== "string") return "";
    const texto = bruto.trim();
    if (!texto || texto.length > 2000 || /[\s"'<>\\]/.test(texto)) return "";
    if (/^(javascript|data|vbscript):/i.test(texto)) return "";
    if (texto.startsWith("/") && !texto.startsWith("//") && !texto.startsWith("/\\")) return texto;
    try {
      const url = new URL(texto);
      return url.protocol === "https:" ? url.href : "";
    } catch (_erro) {
      return "";
    }
  },

  pintarImagemDeFundo(elemento, bruto) {
    const segura = Api.urlDeMidia(bruto);
    if (!elemento) return segura;
    elemento.style.backgroundImage = segura ? "url(" + JSON.stringify(segura) + ")" : "none";
    return segura;
  },

  /* Link de saída da vitrine: só https nos hosts da loja/RAWG. */
  linkExternoSeguro(bruto) {
    try {
      const url = new URL(bruto);
      if (url.protocol !== "https:" || url.username || url.password) return "";
      const host = url.hostname.toLowerCase();
      const ok = host === "store.steampowered.com"
        || host === "steamcommunity.com"
        || host === "rawg.io"
        || host === "www.rawg.io";
      return ok ? url.href : "";
    } catch (_erro) {
      return "";
    }
  },

  /* Fila "Quero testar": só neste navegador, teto de 12 jogos. */
  filaTeste: {
    chave: "laac.queroTestar",
    ler() {
      try {
        const lista = JSON.parse(localStorage.getItem(Api.filaTeste.chave) || "[]");
        if (!Array.isArray(lista)) return [];
        return lista.filter((item) => item && typeof item.slug === "string" && item.slug);
      } catch (_erro) {
        return [];
      }
    },
    gravar(lista) {
      localStorage.setItem(Api.filaTeste.chave, JSON.stringify(lista.slice(0, 12)));
    },
    tem(slug) {
      return Api.filaTeste.ler().some((item) => item.slug === slug);
    },
    alternar(jogo) {
      const lista = Api.filaTeste.ler();
      const existe = lista.some((item) => item.slug === jogo.slug);
      const proxima = existe
        ? lista.filter((item) => item.slug !== jogo.slug)
        : [{
            slug: jogo.slug,
            nome: String(jogo.nome || "").slice(0, 80),
            pontuacao: Number(jogo.pontuacao) || 0,
          }, ...lista];
      Api.filaTeste.gravar(proxima);
      return !existe;
    },
    remover(slug) {
      Api.filaTeste.gravar(Api.filaTeste.ler().filter((item) => item.slug !== slug));
    },
  },

  capa(jogo, classe = "") {
    const cores = Api.coresDoCartao(jogo.capa, ["#2b2d47", "#12131f"]);
    const fundo = "background: linear-gradient(135deg, " + cores[0] + ", " + cores[1] + ");";
    const ladrilho = Api.criar(
      "div",
      { class: "cover " + classe, style: fundo },
      jogo.iniciais || Api.iniciaisDe(jogo.nome)
    );
    const fonte = Api.urlDeMidia(jogo.arquivo_capa || jogo.imagem_capa || "");
    if (fonte) {
      const img = Api.criar("img", {
        src: fonte,
        alt: jogo.nome || "",
        loading: "lazy",
        style: "width:100%;height:100%;object-fit:cover;position:absolute;inset:0",
        onerror: () => img.remove(),
      });
      ladrilho.style.position = "relative";
      ladrilho.style.overflow = "hidden";
      ladrilho.append(img);
    }
    return ladrilho;
  },

  chipPontuacao(pontuacao, status) {
    return Api.criar(
      "span",
      { class: "score-chip " + (status ? status.nivel : "stable") },
      String(pontuacao)
    );
  },

  badge(rotulo, nivel) {
    return Api.criar("span", { class: "badge badge--" + nivel }, rotulo);
  },

  /* Cartão canônico. Cinco telas recebem exatamente a mesma forma de
     jogo, então existe um renderizador só — é o que impede as telas de
     divergirem visualmente sendo escritas em paralelo. */
  cartaoDeJogo(jogo, extra = null) {
    const capa = Api.capa(jogo);
    capa.style.height = "150px";
    return Api.criar(
      "a",
      { class: "game-card", href: "/jogo/" + jogo.slug },
      capa,
      Api.criar("div", { class: "g-name" }, jogo.nome),
      Api.criar(
        "div",
        { class: "row", style: "gap:8px" },
        Api.chipPontuacao(jogo.pontuacao, jogo.status),
        Api.badge((jogo.status || {}).rotulo, (jogo.status || {}).nivel)
      ),
      extra
    );
  },

  // ---- estados ---------------------------------------------------------
  _estado(alvo, classe, mensagem) {
    const no = typeof alvo === "string" ? document.getElementById(alvo) : alvo;
    if (!no) return;
    no.replaceChildren(Api.criar("div", { class: "estado " + classe }, mensagem));
  },

  carregando(alvo, mensagem = "Carregando…") {
    Api._estado(alvo, "", mensagem);
  },

  vazio(alvo, mensagem = "Nada por aqui ainda.") {
    Api._estado(alvo, "estado--vazio", mensagem);
  },

  erro(alvo, mensagem = "Não foi possível carregar.") {
    Api._estado(alvo, "estado--erro", mensagem);
  },

  /* Um 401 já passou por Api.paraLogin(), que redirecionou. Pintar
     "Não foi possível carregar." ou "Sessão expirada." por cima disso
     é ruído durante uma navegação que já está em voo — cada tela
     tratava esse caso de um jeito (algumas pulavam, outras pintavam
     igual a qualquer outro erro); este helper é o único lugar que
     decide, para a próxima tela herdar em vez de escolher o seu. */
  ehSessaoExpirada(erro) {
    return erro instanceof ErroApi && erro.status === 401;
  },

  /* Um 401 já redirecionou e lançou: não é erro para mostrar na tela. */
  aoCarregar(fn) {
    document.addEventListener("DOMContentLoaded", () => {
      Promise.resolve(fn()).catch((e) => {
        if (Api.ehSessaoExpirada(e)) return;
        console.error(e);
      });
    });
  },
};
