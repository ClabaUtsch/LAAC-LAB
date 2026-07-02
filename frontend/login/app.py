from datetime import date
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash

import api_client
from api_client import ApiError

app = Flask(__name__)
app.secret_key = 'laac_lab_chave_secreta_2024'

IDADE_MINIMA = 16


def calcular_idade(data_nasc_str):
    """Recebe 'YYYY-MM-DD' e retorna a idade em anos completos."""
    nascimento = date.fromisoformat(data_nasc_str)
    hoje = date.today()
    idade = hoje.year - nascimento.year - (
        (hoje.month, hoje.day) < (nascimento.month, nascimento.day)
    )
    return idade


def login_required(view):
    """Exige um usuário autenticado (token JWT na sessão) para acessar a rota."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'access_token' not in session:
            flash('Faça login para acessar essa área do laboratório.', 'warning')
            return redirect(url_for('login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


def _sessao_expirada(exc):
    """Se a API recusou o token (401), derruba a sessão local e avisa o usuário."""
    if exc.status_code == 401:
        session.clear()
        flash('Sua sessão expirou. Faça login novamente.', 'warning')
        return True
    return False


# ─── Rotas de autenticação ───────────────────────────────────────────────────

@app.route('/')
def index():
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nome_usuario = request.form.get('nome_usuario', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        data_nascimento = request.form.get('data_nascimento', '')

        erro = None
        idade = None

        if not nome_usuario or not email or not senha or not data_nascimento:
            erro = 'Preencha todos os campos.'
        elif len(senha) < 6:
            erro = 'A senha deve ter no mínimo 6 caracteres.'
        elif senha != confirmar_senha:
            erro = 'As senhas não coincidem.'
        else:
            try:
                idade = calcular_idade(data_nascimento)
            except ValueError:
                erro = 'Data de nascimento inválida.'

            if erro is None and idade < IDADE_MINIMA:
                erro = f'Você precisa ter pelo menos {IDADE_MINIMA} anos para criar uma conta na LAAC LAB.'

        if erro:
            flash(erro, 'danger')
            return render_template('registro.html',
                                    nome_usuario=nome_usuario,
                                    email=email,
                                    data_nascimento=data_nascimento)

        try:
            api_client.registrar(nome_usuario, email, senha, idade)
            flash('Conta criada com sucesso! Faça login para entrar no laboratório.', 'success')
            return redirect(url_for('login'))
        except ApiError as exc:
            flash(exc.args[0] if exc.args else 'Não foi possível criar a conta.', 'danger')
            return render_template('registro.html', nome_usuario=nome_usuario,
                                    email=email, data_nascimento=data_nascimento)

    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        senha = request.form.get('senha', '')

        try:
            resultado = api_client.autenticar(identificador, senha)
            session['access_token'] = resultado['access_token']
            session['usuario'] = resultado['usuario']
            flash(f"Bem-vindo de volta, {resultado['usuario']['nome_usuario']}!", 'success')
            destino = request.args.get('next') or url_for('dashboard')
            return redirect(destino)
        except ApiError as exc:
            flash(exc.args[0] if exc.args else 'Usuário/e-mail ou senha incorretos.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Sessão encerrada.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


# ─── CRUD de Jogos ────────────────────────────────────────────────────────────

@app.route('/jogos')
def jogos_listar():
    page = request.args.get('page', 1, type=int)
    try:
        resultado = api_client.listar_jogos(page=page)
    except ApiError as exc:
        flash(exc.args[0], 'danger')
        resultado = {'items': [], 'page': 1, 'pages': 1, 'total': 0}
    return render_template('jogos_listar.html', resultado=resultado)


@app.route('/jogos/<int:jogo_id>')
def jogos_detalhar(jogo_id):
    try:
        jogo = api_client.obter_jogo(jogo_id)
    except ApiError as exc:
        flash(exc.args[0], 'danger')
        return redirect(url_for('jogos_listar'))
    return render_template('jogo_detalhe.html', jogo=jogo)


def _dados_form_jogo(form):
    dados = {
        'nome': form.get('nome', '').strip(),
        'descricao': form.get('descricao', '').strip() or None,
        'genero': form.get('genero', '').strip() or None,
        'classificacao': form.get('classificacao', '').strip() or None,
        'desenvolvedora': form.get('desenvolvedora', '').strip() or None,
        'data_lancamento': form.get('data_lancamento') or None,
        'capa_url': form.get('capa_url', '').strip() or None,
    }
    return dados


@app.route('/jogos/novo', methods=['GET', 'POST'])
@login_required
def jogos_criar():
    if request.method == 'POST':
        dados = _dados_form_jogo(request.form)
        if not dados['nome']:
            flash('O nome do jogo é obrigatório.', 'danger')
            return render_template('jogo_form.html', jogo=dados, modo='criar')

        try:
            api_client.criar_jogo(session['access_token'], dados)
            flash('Jogo cadastrado com sucesso!', 'success')
            return redirect(url_for('jogos_listar'))
        except ApiError as exc:
            if _sessao_expirada(exc):
                return redirect(url_for('login', next=request.path))
            flash(exc.args[0], 'danger')
            return render_template('jogo_form.html', jogo=dados, modo='criar')

    return render_template('jogo_form.html', jogo={}, modo='criar')


@app.route('/jogos/<int:jogo_id>/editar', methods=['GET', 'POST'])
@login_required
def jogos_editar(jogo_id):
    if request.method == 'POST':
        dados = _dados_form_jogo(request.form)
        if not dados['nome']:
            flash('O nome do jogo é obrigatório.', 'danger')
            dados['id'] = jogo_id
            return render_template('jogo_form.html', jogo=dados, modo='editar')

        try:
            api_client.atualizar_jogo(session['access_token'], jogo_id, dados)
            flash('Jogo atualizado com sucesso!', 'success')
            return redirect(url_for('jogos_detalhar', jogo_id=jogo_id))
        except ApiError as exc:
            if _sessao_expirada(exc):
                return redirect(url_for('login', next=request.path))
            flash(exc.args[0], 'danger')
            dados['id'] = jogo_id
            return render_template('jogo_form.html', jogo=dados, modo='editar')

    try:
        jogo = api_client.obter_jogo(jogo_id)
    except ApiError as exc:
        flash(exc.args[0], 'danger')
        return redirect(url_for('jogos_listar'))
    return render_template('jogo_form.html', jogo=jogo, modo='editar')


@app.route('/jogos/<int:jogo_id>/excluir', methods=['POST'])
@login_required
def jogos_excluir(jogo_id):
    try:
        api_client.excluir_jogo(session['access_token'], jogo_id)
        flash('Jogo removido do catálogo.', 'info')
    except ApiError as exc:
        if _sessao_expirada(exc):
            return redirect(url_for('login'))
        flash(exc.args[0], 'danger')
    return redirect(url_for('jogos_listar'))


# ─── Usuários (listagem pública + perfil) ────────────────────────────────────

@app.route('/usuarios')
def usuarios_listar():
    page = request.args.get('page', 1, type=int)
    try:
        resultado = api_client.listar_usuarios(page=page)
    except ApiError as exc:
        flash(exc.args[0], 'danger')
        resultado = {'items': [], 'page': 1, 'pages': 1, 'total': 0}
    return render_template('usuarios_listar.html', resultado=resultado)


@app.route('/perfil')
@login_required
def perfil():
    try:
        usuario = api_client.obter_usuario(session['usuario']['id'])
    except ApiError as exc:
        flash(exc.args[0], 'danger')
        usuario = session['usuario']
    return render_template('perfil.html', usuario=usuario)


@app.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def perfil_editar():
    usuario_id = session['usuario']['id']

    if request.method == 'POST':
        nome_usuario = request.form.get('nome_usuario', '').strip()
        email = request.form.get('email', '').strip().lower()
        idade = request.form.get('idade', '').strip()
        bio = request.form.get('bio', '').strip()
        avatar_url = request.form.get('avatar_url', '').strip()
        nova_senha = request.form.get('senha', '').strip()

        # RegisterSchema (usada no update) não aceita null explícito nesses campos,
        # então só enviamos quando preenchidos — em branco mantém o valor atual.
        dados = {'nome_usuario': nome_usuario, 'email': email}
        if bio:
            dados['bio'] = bio
        if avatar_url:
            dados['avatar_url'] = avatar_url
        if idade:
            dados['idade'] = int(idade)
        if nova_senha:
            if len(nova_senha) < 6:
                flash('A nova senha deve ter no mínimo 6 caracteres.', 'danger')
                return render_template('perfil_editar.html', usuario={**session['usuario'], **dados})
            dados['senha'] = nova_senha

        try:
            resultado = api_client.atualizar_usuario(session['access_token'], usuario_id, dados)
            session['usuario'] = resultado
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('perfil'))
        except ApiError as exc:
            if _sessao_expirada(exc):
                return redirect(url_for('login'))
            flash(exc.args[0], 'danger')
            return render_template('perfil_editar.html', usuario={**session['usuario'], **dados})

    return render_template('perfil_editar.html', usuario=session['usuario'])


@app.route('/perfil/excluir', methods=['POST'])
@login_required
def perfil_excluir():
    usuario_id = session['usuario']['id']
    try:
        api_client.excluir_usuario(session['access_token'], usuario_id)
        session.clear()
        flash('Sua conta foi removida. Sentiremos sua falta no laboratório.', 'info')
        return redirect(url_for('login'))
    except ApiError as exc:
        if _sessao_expirada(exc):
            return redirect(url_for('login'))
        flash(exc.args[0], 'danger')
        return redirect(url_for('perfil'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)
