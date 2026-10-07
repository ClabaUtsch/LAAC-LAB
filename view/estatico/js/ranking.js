Api.aoCarregar(async () => {
    const alvo = document.getElementById("lista-ranking");

    try {
        // Usando o Api.pedir da tua equipa! É mais seguro e envia o token.
        const usuarios = await Api.pedir("/api/usuarios/ranking");

        alvo.innerHTML = ""; // Limpa a mensagem "A carregar..."

        if (!usuarios || usuarios.length === 0) {
            alvo.innerHTML = "<p style='color: #8b92a5;'>O ranking ainda está vazio! Seja o primeiro a ganhar XP.</p>";
            return;
        }

        // Desenha o cartão para cada utilizador
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
        alvo.innerHTML = "<p style='color: #ff4757;'>Erro ao carregar o ranking.</p>";
        console.error(erro);
    }
});