"""Controladores para o recurso de Usuários."""
from flask import Blueprint, jsonify
from app.services.usuario_service import UsuarioService

# Importa o schema do arquivo correto (ajuste 'auth' para 'usuario' se necessário)
from app.schemas.usuario import UsuarioSchema 

def criar_blueprint_usuario():
    # Cria o agrupamento de rotas (Blueprint) para os utilizadores
    bp = Blueprint("usuarios", __name__)
    service = UsuarioService()

    # Define a rota que o frontend vai chamar
    @bp.get("/api/usuarios/ranking")
    def exibir_ranking():
        usuarios = service.obter_ranking_comunidade()
        
        # Converte a lista do banco de dados para JSON
        schema = UsuarioSchema(many=True)
        return jsonify(schema.dump(usuarios)), 200

    return bp