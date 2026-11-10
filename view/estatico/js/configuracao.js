/* Configuração: perfil (sem editar idade), avatar e senha. */
Api.aoCarregar(async () => {
  const formPerfil = document.getElementById("form-perfil");
  const formSenha = document.getElementById("form-senha");
  const formAvatar = document.getElementById("form-avatar");

  const camposPerfil = {
    apelido: document.getElementById("apelido"),
    bio: document.getElementById("bio"),
  };
  const errosPerfil = {
    apelido: document.getElementById("erro-apelido"),
    bio: document.getElementById("erro-bio"),
  };
  const erroGeralPerfil = document.getElementById("cf-erro-perfil");
  const sucessoPerfil = document.getElementById("cf-sucesso-perfil");

  const camposSenha = {
    senha_atual: document.getElementById("senha_atual"),
    senha_nova: document.getElementById("senha_nova"),
  };
  const errosSenha = {
    senha_atual: document.getElementById("erro-senha_atual"),
    senha_nova: document.getElementById("erro-senha_nova"),
  };
  const erroGeralSenha = document.getElementById("cf-erro-senha");
  const sucessoSenha = document.getElementById("cf-sucesso-senha");

  let usuarioId = null;

  function limparErros(errosPorCampo, erroGeral, sucesso) {
    erroGeral.hidden = true;
    erroGeral.textContent = "";
    sucesso.hidden = true;
    sucesso.textContent = "";
    for (const alvo of Object.values(errosPorCampo)) alvo.textContent = "";
  }

  function mostrarErros(erro, errosPorCampo, erroGeral) {
    if (erro.erros) {
      for (const [campo, mensagens] of Object.entries(erro.erros)) {
        const alvo = errosPorCampo[campo];
        if (alvo) {
          alvo.textContent = mensagens.join(" ");
        } else {
          erroGeral.textContent = mensagens.join(" ");
          erroGeral.hidden = false;
        }
      }
    } else {
      erroGeral.textContent = erro.message;
      erroGeral.hidden = false;
    }
  }

  formPerfil.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparErros(errosPerfil, erroGeralPerfil, sucessoPerfil);

    if (!usuarioId) {
      erroGeralPerfil.textContent = "Não foi possível identificar sua conta. Recarregue a página.";
      erroGeralPerfil.hidden = false;
      return;
    }

    try {
      const atualizado = await Api.pedir(`/api/v1/usuarios/${usuarioId}`, {
        metodo: "PUT",
        corpo: {
          apelido: camposPerfil.apelido.value.trim(),
          bio: camposPerfil.bio.value.trim(),
        },
      });
      camposPerfil.apelido.value = atualizado.apelido || "";
      camposPerfil.bio.value = atualizado.bio || "";
      sucessoPerfil.textContent = "Perfil atualizado.";
      sucessoPerfil.hidden = false;
    } catch (e) {
      if (!(e instanceof ErroApi)) throw e;
      if (Api.ehSessaoExpirada(e)) return;
      mostrarErros(e, errosPerfil, erroGeralPerfil);
    }
  });

  formSenha.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparErros(errosSenha, erroGeralSenha, sucessoSenha);

    try {
      const resposta = await Api.pedir("/api/auth/senha", {
        metodo: "POST",
        corpo: {
          senha_atual: camposSenha.senha_atual.value,
          senha_nova: camposSenha.senha_nova.value,
        },
      });
      Api.guardarSessao(resposta);
      formSenha.reset();
      sucessoSenha.textContent = "Senha alterada.";
      sucessoSenha.hidden = false;
    } catch (e) {
      if (!(e instanceof ErroApi)) throw e;
      if (Api.ehSessaoExpirada(e)) return;
      mostrarErros(e, errosSenha, erroGeralSenha);
    }
  });

  if (formAvatar) {
    formAvatar.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const status = document.getElementById("cf-sucesso-avatar");
      const erroAvatar = document.getElementById("cf-erro-avatar");
      status.hidden = true;
      erroAvatar.hidden = true;
      const arquivo = document.getElementById("avatar_arquivo").files[0];
      const urlManual = document.getElementById("avatar_url").value.trim();
      try {
        let avatar_url = urlManual;
        if (arquivo) {
          if (arquivo.size > 400_000) {
            throw new ErroApi("Use uma imagem menor que 400 KB.", 400);
          }
          avatar_url = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(new ErroApi("Falha ao ler a imagem.", 400));
            reader.readAsDataURL(arquivo);
          });
        }
        if (!avatar_url) {
          throw new ErroApi("Selecione uma foto ou informe uma URL.", 400);
        }
        const resp = await Api.pedir("/api/v1/social/avatar", {
          metodo: "POST",
          corpo: { avatar_url },
        });
        const preview = document.getElementById("cf-avatar-preview");
        preview.style.backgroundImage = `url(${resp.avatar_url})`;
        preview.style.backgroundSize = "cover";
        preview.textContent = "";
        status.textContent = "Foto atualizada.";
        status.hidden = false;
      } catch (e) {
        if (Api.ehSessaoExpirada(e)) return;
        erroAvatar.textContent = e instanceof ErroApi ? e.message : "Falha ao salvar foto.";
        erroAvatar.hidden = false;
      }
    });
  }

  Api.carregando("cf-status", "Carregando…");
  try {
    const eu = await Api.pedir("/api/v1/eu");
    usuarioId = eu.id;
    camposPerfil.apelido.value = eu.apelido || "";
    camposPerfil.bio.value = eu.bio || "";
    const idade = document.getElementById("idade_readonly");
    if (idade) idade.value = eu.idade == null ? "Não informada" : String(eu.idade);
    const preview = document.getElementById("cf-avatar-preview");
    if (preview) {
      if (eu.avatar_url) {
        preview.style.backgroundImage = `url(${eu.avatar_url})`;
        preview.style.backgroundSize = "cover";
        preview.textContent = "";
      } else {
        preview.textContent = Api.iniciaisDe(eu.nome_usuario);
        preview.style.background = eu.cor_avatar;
      }
    }
    document.getElementById("cf-status").replaceChildren();
  } catch (erro) {
    if (Api.ehSessaoExpirada(erro)) return;
    Api.erro("cf-status", "Não foi possível carregar seus dados.");
    console.error(erro);
  }
});
