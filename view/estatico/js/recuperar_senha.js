Api.aoCarregar(() => {
  const form = document.getElementById("form-recuperar");
  const erro = document.getElementById("erro-geral");
  const ok = document.getElementById("ok");

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    erro.hidden = true;
    ok.hidden = true;
    try {
      const dados = await Api.pedir("/api/auth/recuperar-senha", {
        metodo: "POST",
        corpo: { email: document.getElementById("email").value.trim() },
        autenticar: false,
      });
      let msg = dados.mensagem || "Verifique seu e-mail.";
      if (dados.token_dev) {
        msg +=
          " (dev) Abra /redefinir-senha?token=" +
          encodeURIComponent(dados.token_dev);
      }
      ok.textContent = msg;
      ok.hidden = false;
    } catch (e) {
      if (Api.ehSessaoExpirada(e)) return;
      if (!(e instanceof ErroApi)) throw e;
      erro.textContent = e.message;
      erro.hidden = false;
    }
  });
});
