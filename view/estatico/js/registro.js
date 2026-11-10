Api.aoCarregar(async () => {
  const form = document.getElementById("form-registro");
  const erroGeral = document.getElementById("erro-geral");
  const campos = {
    nome_usuario: document.getElementById("nome_usuario"),
    email: document.getElementById("email"),
    data_nascimento: document.getElementById("data_nascimento"),
    cpf: document.getElementById("cpf"),
    senha: document.getElementById("senha"),
    termos: document.getElementById("termos"),
  };

  const errosDeCampo = {
    nome_usuario: document.getElementById("erro-nome_usuario"),
    email: document.getElementById("erro-email"),
    data_nascimento: document.getElementById("erro-data_nascimento"),
    cpf: document.getElementById("erro-cpf"),
    senha: document.getElementById("erro-senha"),
    aceite_termos: document.getElementById("erro-termos"),
  };

  function limparErros() {
    erroGeral.hidden = true;
    erroGeral.textContent = "";
    for (const alvo of Object.values(errosDeCampo)) {
      if (alvo) alvo.textContent = "";
    }
  }

  function calcularIdade(dataString) {
    if (!dataString) return 0;
    const hoje = new Date();
    const [ano, mes, dia] = dataString.split("-");
    const nasc = new Date(ano, mes - 1, dia);
    let idade = hoje.getFullYear() - nasc.getFullYear();
    const diferencaMes = hoje.getMonth() - nasc.getMonth();
    if (diferencaMes < 0 || (diferencaMes === 0 && hoje.getDate() < nasc.getDate())) {
      idade--;
    }
    return idade;
  }

  function limparCpf(valor) {
    return String(valor || "").replace(/\D/g, "");
  }

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparErros();

    const dataInput = campos.data_nascimento.value;
    if (!dataInput) {
      errosDeCampo.data_nascimento.textContent = "Por favor, insira sua data de nascimento.";
      return;
    }

    const idade = calcularIdade(dataInput);
    if (idade < 16) {
      errosDeCampo.data_nascimento.textContent =
        "Cadastro bloqueado: você precisa ter pelo menos 16 anos.";
      return;
    }

    const cpf = limparCpf(campos.cpf.value);
    if (cpf.length !== 11) {
      errosDeCampo.cpf.textContent = "Informe um CPF válido com 11 dígitos.";
      return;
    }

    if (!campos.termos.checked) {
      if (errosDeCampo.aceite_termos) {
        errosDeCampo.aceite_termos.textContent =
          "Você deve aceitar os termos de uso e declarar ter 16 anos ou mais.";
      } else {
        erroGeral.textContent =
          "Você deve aceitar os termos de uso e declarar ter 16 anos ou mais.";
        erroGeral.hidden = false;
      }
      return;
    }

    try {
      const dados = await Api.pedir("/api/auth/registro", {
        metodo: "POST",
        corpo: {
          nome_usuario: campos.nome_usuario.value.trim(),
          email: campos.email.value.trim(),
          senha: campos.senha.value,
          data_nascimento: dataInput,
          cpf,
          aceite_termos: true,
        },
        autenticar: false,
      });

      Api.guardarSessao(dados);
      const destino = Api.destinoSeguro(new URLSearchParams(location.search).get("destino"));
      window.location = destino;
    } catch (e) {
      if (!(e instanceof ErroApi)) throw e;

      if (e.erros) {
        for (const [campo, mensagens] of Object.entries(e.erros)) {
          const chave = campo === "aceite_termos" ? "aceite_termos" : campo;
          const alvo = errosDeCampo[chave];
          if (alvo) {
            alvo.textContent = mensagens.join(" ");
          } else {
            erroGeral.textContent = mensagens.join(" ");
            erroGeral.hidden = false;
          }
        }
      } else {
        erroGeral.textContent = e.message;
        erroGeral.hidden = false;
      }
    }
  });
});
