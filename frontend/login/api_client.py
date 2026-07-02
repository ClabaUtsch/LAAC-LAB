"""
Cliente HTTP para a api-flask-laaclab (Bugômetro).

Cada função representa um caso de uso do frontend (registrar, autenticar,
listar jogos, criar jogo, ...) e faz a chamada REST correspondente às rotas
CRUD já implementadas na API (app/routes.py, app/auth.py, app/usuarios.py).
Nenhum acesso a banco é feito por aqui — tudo passa pela API.
"""
import os

import requests

API_BASE_URL = os.environ.get('API_BASE_URL', 'http://127.0.0.1:5000').rstrip('/')

_TIMEOUT = 10


class ApiError(Exception):
    """Erro de comunicação com a API (erro de rede, 4xx ou 5xx)."""

    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self.payload = payload or {}
        super().__init__(self._extrair_mensagem())

    def _extrair_mensagem(self):
        if 'erro' in self.payload:
            return self.payload['erro']
        if 'erros' in self.payload:
            partes = []
            for campo, msgs in self.payload['erros'].items():
                msgs_str = ', '.join(msgs) if isinstance(msgs, list) else str(msgs)
                partes.append(f'{campo}: {msgs_str}')
            return '; '.join(partes)
        return 'Não foi possível comunicar com a API.'


def _request(method, path, token=None, **kwargs):
    url = f'{API_BASE_URL}{path}'
    headers = kwargs.pop('headers', {})
    if token:
        headers['Authorization'] = f'Bearer {token}'

    try:
        resposta = requests.request(method, url, headers=headers, timeout=_TIMEOUT, **kwargs)
    except requests.exceptions.RequestException as exc:
        raise ApiError(503, {'erro': 'Não foi possível conectar à API do LaaC_lab. Ela está rodando?'}) from exc

    if resposta.status_code >= 400:
        try:
            payload = resposta.json()
        except ValueError:
            payload = {}
        raise ApiError(resposta.status_code, payload)

    if resposta.status_code == 204 or not resposta.content:
        return None
    return resposta.json()


# ─── Autenticação ───────────────────────────────────────────────────────────

def registrar(nome_usuario, email, senha, idade=None):
    dados = {'nome_usuario': nome_usuario, 'email': email, 'senha': senha}
    if idade is not None:
        dados['idade'] = idade
    return _request('POST', '/api/auth/register', json=dados)


def autenticar(identificador, senha):
    return _request('POST', '/api/auth/login', json={'identificador': identificador, 'senha': senha})


# ─── Jogos ──────────────────────────────────────────────────────────────────

def listar_jogos(page=1, per_page=12):
    return _request('GET', '/api/jogos', params={'page': page, 'per_page': per_page})


def obter_jogo(jogo_id):
    return _request('GET', f'/api/jogos/{jogo_id}')


def criar_jogo(token, dados):
    return _request('POST', '/api/jogos', token=token, json=dados)


def atualizar_jogo(token, jogo_id, dados):
    return _request('PUT', f'/api/jogos/{jogo_id}', token=token, json=dados)


def excluir_jogo(token, jogo_id):
    return _request('DELETE', f'/api/jogos/{jogo_id}', token=token)


# ─── Usuários ───────────────────────────────────────────────────────────────

def listar_usuarios(page=1, per_page=20):
    return _request('GET', '/api/usuarios', params={'page': page, 'per_page': per_page})


def obter_usuario(usuario_id):
    return _request('GET', f'/api/usuarios/{usuario_id}')


def atualizar_usuario(token, usuario_id, dados):
    return _request('PUT', f'/api/usuarios/{usuario_id}', token=token, json=dados)


def excluir_usuario(token, usuario_id):
    return _request('DELETE', f'/api/usuarios/{usuario_id}', token=token)
