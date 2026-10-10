"""Controller de produtos: extrai entrada, chama o service, monta a resposta."""
import logging

from flask import jsonify, request

from src.controllers.validators import parse_preco, validar_produto
from src.errors import ValidationError
from src.views.serializers import serialize_produto, serialize_produtos

logger = logging.getLogger(__name__)

MAX_PAGE_SIZE = 100


class ProdutoController:
    def __init__(self, produto_service):
        self._service = produto_service

    def listar(self):
        limit, offset = self._paginacao(request.args)
        produtos = self._service.listar(limit=limit, offset=offset)
        logger.info("Listando %d produtos", len(produtos))
        return jsonify({"dados": serialize_produtos(produtos), "sucesso": True}), 200

    def buscar(self, id):
        produto = self._service.buscar(id)
        return jsonify({"dados": serialize_produto(produto), "sucesso": True}), 200

    def criar(self):
        campos = validar_produto(request.get_json(silent=True), completo=True)
        produto_id = self._service.criar(campos)
        logger.info("Produto criado com ID %s", produto_id)
        return jsonify({
            "dados": {"id": produto_id},
            "sucesso": True,
            "mensagem": "Produto criado",
        }), 201

    def atualizar(self, id):
        dados = request.get_json(silent=True)
        # Ordem do original: existência (404) antes da validação do corpo (400).
        self._service.garantir_existe(id)
        campos = validar_produto(dados, completo=False)
        self._service.atualizar(id, campos)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, id):
        self._service.deletar(id)
        logger.info("Produto %s deletado", id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    def buscar_produtos(self):
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = parse_preco(request.args.get("preco_min", None))
        preco_max = parse_preco(request.args.get("preco_max", None))
        resultados = self._service.pesquisar(termo, categoria, preco_min, preco_max)
        return jsonify({
            "dados": serialize_produtos(resultados),
            "total": len(resultados),
            "sucesso": True,
        }), 200

    @staticmethod
    def _paginacao(args):
        if "limit" not in args:
            return None, 0
        try:
            limit = min(int(args["limit"]), MAX_PAGE_SIZE)
            offset = int(args.get("offset", 0))
        except (TypeError, ValueError):
            raise ValidationError("Parâmetros de paginação inválidos")
        return limit, offset
