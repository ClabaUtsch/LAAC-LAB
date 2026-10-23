"""Serviço para operações de usuários e comunidade."""
from app.repositories.usuario_repository import RepositorioUsuario
class UsuarioService:
    def __init__(self):
        self.repo = RepositorioUsuario()

    def obter_ranking_comunidade(self, limite: int = 50):
        """
        Orquestra a busca do ranking da comunidade.
        É nesta camada que as regras de negócio vivem.
        """
        usuarios = self.repo.listar_ranking_por_xp(limite)
    
        ranking_justo = [u for u in usuarios if not u.is_admin]
        
        return ranking_justo