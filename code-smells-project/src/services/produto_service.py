"""Regras de negócio de produtos."""
from src.errors import NotFoundError


class ProdutoService:
    def __init__(self, produto_model):
        self._produtos = produto_model

    def listar(self, limit=None, offset=0):
        return self._produtos.listar(limit, offset)

    def buscar(self, produto_id):
        produto = self._produtos.buscar_por_id(produto_id)
        if produto is None:
            # GET traz `sucesso: false` no corpo do 404 (contrato original).
            raise NotFoundError("Produto não encontrado", sucesso=False)
        return produto

    def garantir_existe(self, produto_id):
        if self._produtos.buscar_por_id(produto_id) is None:
            # PUT/DELETE: 404 só com `erro` (contrato original).
            raise NotFoundError("Produto não encontrado")

    def criar(self, campos):
        return self._produtos.criar(
            campos["nome"], campos["descricao"], campos["preco"],
            campos["estoque"], campos["categoria"],
        )

    def atualizar(self, produto_id, campos):
        self._produtos.atualizar(
            produto_id, campos["nome"], campos["descricao"], campos["preco"],
            campos["estoque"], campos["categoria"],
        )

    def deletar(self, produto_id):
        self._produtos.deletar(produto_id)

    def buscar_catalogo(self, termo, categoria, preco_min, preco_max):
        return self._produtos.buscar(termo, categoria, preco_min, preco_max)
