// LAAC_LAB — main.js

document.addEventListener('DOMContentLoaded', function () {
    // Toggle de visibilidade de senha
    document.querySelectorAll('.toggle-pass').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var input = document.getElementById(btn.dataset.target);
            if (!input) return;
            var show = input.type === 'password';
            input.type = show ? 'text' : 'password';
            btn.textContent = show ? '🙈' : '👁';
        });
    });

    // Aplica a capa do jogo via JS (evita montar CSS a partir de texto do usuário no HTML)
    document.querySelectorAll('[data-cover-url]').forEach(function (el) {
        var url = el.dataset.coverUrl;
        if (url) {
            el.style.backgroundImage = 'url(' + JSON.stringify(url) + ')';
        }
    });

    // Confirmação antes de submeter formulários destrutivos (exclusão)
    document.querySelectorAll('.js-confirm-form').forEach(function (form) {
        form.addEventListener('submit', function (evt) {
            var mensagem = form.dataset.confirmMessage || 'Tem certeza?';
            if (!window.confirm(mensagem)) {
                evt.preventDefault();
            }
        });
    });

    // Auto-fechar mensagens flash após 5s
    var flashes = document.querySelectorAll('.flash');
    if (flashes.length) {
        setTimeout(function () {
            flashes.forEach(function (el) {
                el.style.transition = 'opacity .3s ease, transform .3s ease';
                el.style.opacity = '0';
                el.style.transform = 'translateY(-6px)';
                setTimeout(function () { el.remove(); }, 300);
            });
        }, 5000);
    }
});
