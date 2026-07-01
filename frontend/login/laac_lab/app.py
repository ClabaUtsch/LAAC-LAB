from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

import database

app = Flask(__name__)
app.secret_key = 'laac_lab_chave_secreta_2024'
app.config['DATABASE'] = 'laac_lab.db'

database.init_app(app)

IDADE_MINIMA = 16


def calcular_idade(data_nasc_str):
    """Recebe 'YYYY-MM-DD' e retorna a idade em anos completos."""
    nascimento = date.fromisoformat(data_nasc_str)
    hoje = date.today()
    idade = hoje.year - nascimento.year - (
        (hoje.month, hoje.day) < (nascimento.month, nascimento.day)
    )
    return idade


# ─── Rotas ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'usuario_id' in session:
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
                idade = None

            if erro is None and idade is not None and idade < IDADE_MINIMA:
                erro = f'Você precisa ter pelo menos {IDADE_MINIMA} anos para criar uma conta na LAAC LAB.'

        if erro:
            flash(erro, 'danger')
            return render_template('registro.html',
                                    nome_usuario=nome_usuario,
                                    email=email,
                                    data_nascimento=data_nascimento)

        try:
            db = database.get_db()
            db.execute(
                'INSERT INTO usuario (nome_usuario, email, senha, data_nascimento) '
                'VALUES (?, ?, ?, ?)',
                (nome_usuario, email, generate_password_hash(senha), data_nascimento)
            )
            db.commit()
            flash('Conta criada com sucesso! Faça login para entrar no laboratório.', 'success')
            return redirect(url_for('login'))
        except database.sqlite3.IntegrityError:
            flash('Esse nome de usuário ou e-mail já está em uso.', 'danger')
            return render_template('registro.html', email=email, data_nascimento=data_nascimento)

    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        senha = request.form.get('senha', '')

        db = database.get_db()
        usuario = db.execute(
            'SELECT * FROM usuario WHERE email = ? OR nome_usuario = ?',
            (identificador.lower(), identificador)
        ).fetchone()

        if usuario and check_password_hash(usuario['senha'], senha):
            session['usuario_id'] = usuario['id']
            session['nome_usuario'] = usuario['nome_usuario']
            flash(f'Bem-vindo de volta, {usuario["nome_usuario"]}!', 'success')
            return redirect(url_for('dashboard'))

        flash('Usuário/e-mail ou senha incorretos.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Sessão encerrada.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        flash('Faça login para acessar o laboratório.', 'warning')
        return redirect(url_for('login'))
    return f"<h1 style='font-family:sans-serif;color:#eee;background:#0D0D19;" \
           f"min-height:100vh;margin:0;padding:40px;'>Bem-vindo, " \
           f"{session['nome_usuario']} 👋 — Dashboard em construção.</h1>"


if __name__ == '__main__':
    with app.app_context():
        database.init_db()
        database.seed_db()
    app.run(debug=True)
