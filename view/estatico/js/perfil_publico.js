Api.aoCarregar(async () => {
  const id = Number(location.pathname.split("/").pop());
  if (!id) {
    Api.erro("conteudo", "Perfil inválido.");
    return;
  }
  try {
    const u = await Api.pedir(`/api/v1/social/perfis/${id}`);
    const avatar = document.getElementById("pp-avatar");
    if (u.avatar_url) {
      avatar.textContent = "";
      avatar.style.backgroundImage = `url(${u.avatar_url})`;
      avatar.style.backgroundSize = "cover";
    } else {
      avatar.textContent = Api.iniciaisDe(u.nome_usuario);
      avatar.style.background = u.cor_avatar;
    }
    document.getElementById("pp-name").textContent = u.apelido || u.nome_usuario;
    document.getElementById("pp-level").textContent = "Nível " + u.nivel;
    document.getElementById("pp-bio").textContent = u.bio || "Sem bio.";
    document.getElementById("pp-achievements").textContent = u.conquistas;
    document.getElementById("pp-friends").textContent = u.amigos;
    document.getElementById("pp-days").textContent = u.dias_ativo;
    const status = document.getElementById("pp-status");
    const btn = document.getElementById("pp-add");
    if (u.relacao === "eu") {
      btn.style.display = "none";
      status.textContent = "Este é o seu perfil.";
    } else if (u.relacao === "amigos") {
      btn.disabled = true;
      btn.textContent = "Vocês são amigos";
    } else if (u.relacao === "enviada" || u.relacao === "pendente") {
      btn.disabled = true;
      btn.textContent = "Pedido pendente";
    } else {
      btn.onclick = async () => {
        await Api.pedir("/api/v1/social/amizades", {
          metodo: "POST",
          corpo: { destinatario_id: u.id },
        });
        location.reload();
      };
    }
  } catch (e) {
    if (Api.ehSessaoExpirada(e)) return;
    Api.erro("conteudo", e instanceof ErroApi ? e.message : "Não foi possível abrir este perfil.");
  }
});
