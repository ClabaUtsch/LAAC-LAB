/* Perfil próprio: progresso, conquistas, amizades e perfis alheios. */

function cartaoPessoa(item, acoes) {
  const u = item.usuario || item;
  const avatar = Api.criar(
    "a",
    {
      class: "avatar",
      href: "/perfil/" + u.id,
      style: u.avatar_url
        ? `background-image:url(${u.avatar_url});background-size:cover`
        : `background:${u.cor_avatar || "#6b7cff"}`,
    },
    u.avatar_url ? "" : Api.iniciaisDe(u.nome_usuario || u.apelido || "?")
  );
  return Api.criar(
    "div",
    { class: "row between", style: "gap:12px;padding:10px 0;border-bottom:1px solid var(--border)" },
    Api.criar(
      "div",
      { class: "row", style: "gap:10px;align-items:center" },
      avatar,
      Api.criar(
        "div",
        null,
        Api.criar("a", { href: "/perfil/" + u.id, style: "font-weight:700;color:inherit" }, u.apelido || u.nome_usuario),
        Api.criar("div", { class: "dim", style: "font-size:12px" }, "Nível " + (u.nivel || 1))
      )
    ),
    acoes || ""
  );
}

async function iniciarPerfil() {
  const alvoAtividade = "pf-activity";
  Api.carregando(alvoAtividade, "Carregando…");

  try {
    const dados = await Api.pedir("/api/v1/telas/perfil");
    const u = dados.usuario;

    const avatar = document.getElementById("pf-avatar");
    if (u.avatar_url) {
      avatar.textContent = "";
      avatar.style.backgroundImage = `url(${u.avatar_url})`;
      avatar.style.backgroundSize = "cover";
    } else {
      avatar.textContent = Api.iniciaisDe(u.nome_usuario);
      avatar.style.background = u.cor_avatar;
    }

    document.getElementById("pf-name").textContent = u.nome_usuario;
    document.getElementById("pf-level").textContent = "Nível " + u.nivel;
    const porcentagemXp = Math.round((u.xp / u.xp_max) * 100);
    document.getElementById("pf-xp-bar").style.width = porcentagemXp + "%";
    document.getElementById("pf-xp").textContent = `${u.xp} / ${u.xp_max} XP`;
    document.getElementById("pf-bio").textContent = `"${u.bio || ""}"`;

    document.getElementById("pf-achievements").textContent = u.conquistas;
    document.getElementById("pf-friends").textContent = u.amigos;
    document.getElementById("pf-days").textContent = u.dias_ativo;

    const activity = document.getElementById(alvoAtividade);
    if (dados.jogos_recentes.length === 0) {
      Api.vazio(alvoAtividade, "Nenhum jogo recente.");
    } else {
      activity.replaceChildren();
      dados.jogos_recentes.forEach((g) => {
        activity.append(
          Api.criar(
            "a",
            { class: "profile-recent", href: "/jogo/" + g.jogo_slug },
            Api.criar(
              "div",
              {
                class: "cover",
                style:
                  "background: linear-gradient(135deg, " +
                  Api.coresDoCartao(g.capa)[0] +
                  ", " +
                  Api.coresDoCartao(g.capa)[1] +
                  ");width:64px;height:40px;font-size:9px",
              },
              Api.iniciaisDe(g.jogo)
            ),
            Api.criar(
              "div",
              { style: "flex:1;min-width:0" },
              Api.criar("div", { style: "font-weight:700;font-size:13px" }, g.jogo),
              Api.criar("div", { class: "dim", style: "font-size:12px" }, g.duracao),
              Api.criar(
                "div",
                { class: "row", style: "gap:8px;margin-top:6px" },
                Api.criar(
                  "div",
                  { class: "progress", style: "flex:1" },
                  Api.criar("span", { style: "width:" + g.porcentagem + "%" })
                ),
                Api.criar("span", { style: "font-size:11px;font-weight:700" }, g.porcentagem + "%")
              )
            )
          )
        );
      });
    }

    const conquistas = document.getElementById("pf-conquistas");
    if (conquistas) {
      conquistas.replaceChildren();
      const lista = dados.conquistas_lista || [];
      if (!lista.length) {
        conquistas.append(Api.criar("div", { class: "muted" }, "Complete ações na plataforma para desbloquear."));
      } else {
        lista.forEach((c) =>
          conquistas.append(
            Api.criar("div", { style: "padding:8px 0;border-bottom:1px solid var(--border)" }, c.nome)
          )
        );
      }
    }

    const amizades = dados.amizades || { amigos: [], pendentes: [], enviadas: [] };
    const pintarLista = (id, itens, comAcoes) => {
      const box = document.getElementById(id);
      if (!box) return;
      box.replaceChildren();
      if (!itens.length) {
        box.append(Api.criar("div", { class: "muted" }, "Nada por aqui."));
        return;
      }
      itens.forEach((item) => {
        let acoes = "";
        if (comAcoes && item.status === "pendente") {
          const aceitar = Api.criar("button", { class: "btn btn--primary", type: "button", style: "padding:4px 10px" }, "Aceitar");
          const recusar = Api.criar("button", { class: "btn btn--outline", type: "button", style: "padding:4px 10px" }, "Recusar");
          aceitar.onclick = async () => {
            await Api.pedir(`/api/v1/social/amizades/${item.amizade_id}/responder`, {
              metodo: "POST",
              corpo: { aceitar: true },
            });
            location.reload();
          };
          recusar.onclick = async () => {
            await Api.pedir(`/api/v1/social/amizades/${item.amizade_id}/responder`, {
              metodo: "POST",
              corpo: { aceitar: false },
            });
            location.reload();
          };
          acoes = Api.criar("div", { class: "row", style: "gap:6px" }, aceitar, recusar);
        }
        box.append(cartaoPessoa(item, acoes));
      });
    };
    pintarLista("pf-amigos", amizades.amigos || []);
    pintarLista("pf-pendentes", amizades.pendentes || [], true);
    pintarLista("pf-enviadas", amizades.enviadas || []);

    const busca = document.getElementById("pf-busca-amigos");
    const resultados = document.getElementById("pf-resultados-amigos");
    if (busca && resultados) {
      let timer = null;
      busca.addEventListener("input", () => {
        clearTimeout(timer);
        timer = setTimeout(async () => {
          const q = busca.value.trim();
          if (q.length < 2) {
            resultados.replaceChildren();
            return;
          }
          const resp = await Api.pedir("/api/v1/social/pessoas?busca=" + encodeURIComponent(q));
          resultados.replaceChildren();
          (resp.itens || []).forEach((p) => {
            const btn = Api.criar("button", { class: "btn btn--primary", type: "button", style: "padding:4px 10px" }, "Adicionar");
            if (p.relacao === "amigos") btn.textContent = "Amigos";
            if (p.relacao === "enviada" || p.relacao === "pendente") btn.textContent = "Pendente";
            btn.disabled = p.relacao !== "nenhuma" && p.relacao !== "recusada";
            btn.onclick = async () => {
              await Api.pedir("/api/v1/social/amizades", {
                metodo: "POST",
                corpo: { destinatario_id: p.id },
              });
              location.reload();
            };
            resultados.append(cartaoPessoa(p, btn));
          });
        }, 300);
      });
    }

    document.querySelectorAll("[data-aba-amizade]").forEach((tab) => {
      tab.addEventListener("click", () => {
        document.querySelectorAll("[data-aba-amizade]").forEach((t) => t.classList.remove("is-active"));
        document.querySelectorAll("[data-painel-amizade]").forEach((p) => (p.style.display = "none"));
        tab.classList.add("is-active");
        const painel = document.querySelector(`[data-painel-amizade="${tab.dataset.abaAmizade}"]`);
        if (painel) painel.style.display = "";
      });
    });
  } catch (erro) {
    if (!Api.ehSessaoExpirada(erro)) {
      Api.erro("pf-usuario", "Não foi possível carregar o perfil.");
      Api.erro(alvoAtividade, "Não foi possível carregar a atividade recente.");
      console.error(erro);
    }
  }
}

Api.aoCarregar(iniciarPerfil);
