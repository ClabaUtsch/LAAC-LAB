Api.aoCarregar(async () => {
  const alvo = document.getElementById("lista-ranking");

  try {
    const usuarios = await Api.pedir("/api/usuarios/ranking");
    alvo.innerHTML = "";

    if (!usuarios || usuarios.length === 0) {
      alvo.innerHTML =
        "<p style='color: #8b92a5;'>O ranking ainda está vazio! Seja o primeiro a ganhar XP.</p>";
      return;
    }

    usuarios.forEach((user, index) => {
      const posicao = index + 1;
      const nome = user.nome_usuario || "Sem Nome";
      const nivel = user.nivel || 1;
      const xp = user.xp || 0;

      const div = document.createElement("div");
      div.className = "ranking-card";
      div.innerHTML = `
                <div class="rk-pos">${posicao}º</div>
                <div class="rk-info">
                    <div class="rk-nome">${nome}</div>
                    <div style="font-size: 13px; color: #8b92a5;">Nível ${nivel}</div>
                </div>
                <div class="rk-xp">${xp} XP</div>
            `;
      alvo.appendChild(div);
    });
  } catch (erro) {
    if (Api.ehSessaoExpirada(erro)) return;
    alvo.innerHTML = "<p style='color: #ff4757;'>Erro ao carregar o ranking.</p>";
    console.error(erro);
  }
});
