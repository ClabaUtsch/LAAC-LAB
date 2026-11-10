Api.aoCarregar(() => {
  const form = document.getElementById("form-redefinir");
  const erro = document.getElementById("erro-geral");
  const ok = document.getElementById("ok");
  const token = new URLSearchParams(location.search).get("token") || "";

  if (!token) {
    erro.textContent = "Link inválido. Solicite uma nova recuperação de senha.";
    erro.hidden = false;
    form.hidden = true;
    return;
  }

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    erro.hidden = true;
    ok.hidden = true;
    try {
      const dados = await Api.pedir("/api/auth/redefinir-senha", {
        metodo: "POST",
        corpo: {
          token,
          senha_nova: document.getElementById("senha_nova").value,
        },
        autenticar: false,
      });
      ok.textContent = dados.mensagem || "Senha redefinida.";
      ok.hidden = false;
      form.hidden = true;
    } catch (e) {
      if (Api.ehSessaoExpirada(e)) return;
      if (!(e instanceof ErroApi)) throw e;
      erro.textContent = e.message;
      erro.hidden = false;
    }
  });
});
