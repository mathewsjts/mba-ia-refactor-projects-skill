from flask import jsonify, request

from src.controllers.validators import validar_filtros_busca, validar_paginacao, validar_produto
from src.views.serializers import serialize_produto, serialize_produtos


class ProdutoController:
    def __init__(self, produto_service):
        self._service = produto_service

    def listar(self):
        limit, offset = validar_paginacao(request.args)
        produtos = self._service.listar(limit, offset)
        return jsonify({"dados": serialize_produtos(produtos), "sucesso": True}), 200

    def mostrar(self, produto_id):
        produto = self._service.obter(produto_id)
        return jsonify({"dados": serialize_produto(produto), "sucesso": True}), 200

    def buscar(self):
        resultados = self._service.buscar(*validar_filtros_busca(request.args))
        return jsonify({
            "dados": serialize_produtos(resultados),
            "total": len(resultados),
            "sucesso": True,
        }), 200

    def criar(self):
        produto = validar_produto(request.get_json(silent=True))
        produto_id = self._service.criar(produto)
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, produto_id):
        # Ordem do original: produto inexistente (404) antes de corpo inválido (400).
        self._service.garantir_existe(produto_id)
        produto = validar_produto(request.get_json(silent=True))
        self._service.atualizar(produto_id, produto)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def remover(self, produto_id):
        self._service.remover(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
