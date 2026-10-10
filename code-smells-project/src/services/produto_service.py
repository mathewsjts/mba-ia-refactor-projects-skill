"""Regras de produto (T04). Orquestra o model; a validação de entrada fica no
validador (T09) e o formato de resposta na view (T13)."""
from src.errors import NotFoundError


class ProdutoService:
    def __init__(self, produto_model):
        self._produtos = produto_model

    def listar(self, limit=None, offset=0):
        return self._produtos.listar(limit=limit, offset=offset)

    def buscar(self, produto_id):
        produto = self._produtos.buscar_por_id(produto_id)
        if produto is None:
            # 404 do original incluía "sucesso": False nesta rota.
            raise NotFoundError("Produto não encontrado", include_sucesso=True)
        return produto

    def pesquisar(self, termo, categoria, preco_min, preco_max):
        return self._produtos.buscar(termo, categoria, preco_min, preco_max)

    def garantir_existe(self, produto_id):
        # 404 do original (em atualizar/deletar) NÃO incluía "sucesso".
        if self._produtos.buscar_por_id(produto_id) is None:
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
        self.garantir_existe(produto_id)
        self._produtos.deletar(produto_id)
