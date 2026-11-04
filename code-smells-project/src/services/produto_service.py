import logging

from src.errors import NotFoundError

logger = logging.getLogger(__name__)


class ProdutoService:
    def __init__(self, produto_model):
        self._produtos = produto_model

    def listar(self, limit=None, offset=0):
        produtos = self._produtos.listar(limit, offset)
        logger.info("Listando %d produtos", len(produtos))
        return produtos

    def obter(self, produto_id):
        produto = self._produtos.buscar_por_id(produto_id)
        if produto is None:
            raise NotFoundError("Produto não encontrado", incluir_sucesso=True)
        return produto

    def garantir_existe(self, produto_id):
        if self._produtos.buscar_por_id(produto_id) is None:
            raise NotFoundError("Produto não encontrado")

    def buscar(self, termo, categoria, preco_min, preco_max):
        return self._produtos.buscar(termo, categoria, preco_min, preco_max)

    def criar(self, produto):
        produto_id = self._produtos.criar(**produto)
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, produto):
        self._produtos.atualizar(produto_id, **produto)

    def remover(self, produto_id):
        self.garantir_existe(produto_id)
        if self._produtos.remover(produto_id) == 0:
            # Removido por outra requisição entre a checagem e a escrita.
            raise NotFoundError("Produto não encontrado")
        logger.info("Produto %s removido", produto_id)
