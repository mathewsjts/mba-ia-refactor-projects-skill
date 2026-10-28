"""Controller de produtos — fino: extrai entrada, valida, delega, responde."""
from flask import jsonify, request

from src.controllers.validators import parse_paginacao, validar_produto
from src.errors import ValidationError
from src.views.serializers import serialize_produto, serialize_produtos


class ProdutoController:
    def __init__(self, produto_service):
        self._service = produto_service

    def listar(self):
        limit, offset = parse_paginacao(request.args)
        produtos = self._service.listar(limit, offset)
        return jsonify({"dados": serialize_produtos(produtos), "sucesso": True}), 200

    def buscar(self, produto_id):
        produto = self._service.buscar(produto_id)
        return jsonify({"dados": serialize_produto(produto), "sucesso": True}), 200

    def criar(self):
        campos = validar_produto(request.get_json(silent=True), completo=True)
        novo_id = self._service.criar(campos)
        return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, produto_id):
        dados = request.get_json(silent=True)
        # Ordem do original: existência (404) antes da validação (400).
        self._service.garantir_existe(produto_id)
        campos = validar_produto(dados, completo=False)
        self._service.atualizar(produto_id, campos)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, produto_id):
        self._service.garantir_existe(produto_id)
        self._service.deletar(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    def buscar_catalogo(self):
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", None)
        preco_max = request.args.get("preco_max", None)
        try:
            # Preserva a semântica original: `if preco_min:` ignora string vazia e 0.
            if preco_min:
                preco_min = float(preco_min)
            if preco_max:
                preco_max = float(preco_max)
        except ValueError:
            raise ValidationError("Parâmetro de preço inválido")
        resultados = self._service.buscar_catalogo(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": serialize_produtos(resultados), "total": len(resultados), "sucesso": True}), 200
