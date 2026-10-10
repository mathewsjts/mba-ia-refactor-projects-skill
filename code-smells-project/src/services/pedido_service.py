"""Regra de negócio de pedidos (T04): valida estoque, calcula o total e dispara a
notificação. As escritas são atômicas no model (T07)."""
from src.errors import ValidationError


class PedidoService:
    def __init__(self, pedido_model, produto_model, notificador):
        self._pedidos = pedido_model
        self._produtos = produto_model
        self._notificador = notificador

    def criar(self, usuario_id, itens):
        # Valida TODOS os itens antes de qualquer escrita (ordem do original).
        linhas = []
        total = 0
        for item in itens:
            produto = self._produtos.buscar_por_id(item["produto_id"])
            if produto is None:
                raise ValidationError(
                    "Produto " + str(item["produto_id"]) + " não encontrado",
                    include_sucesso=True,
                )
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError(
                    "Estoque insuficiente para " + produto["nome"],
                    include_sucesso=True,
                )
            total += produto["preco"] * item["quantidade"]
            linhas.append({
                "produto_id": item["produto_id"],
                "quantidade": item["quantidade"],
                "preco_unitario": produto["preco"],
            })

        resultado = self._pedidos.criar(usuario_id, linhas, total)
        self._notificador.pedido_criado(resultado["pedido_id"], usuario_id)
        return resultado

    def listar(self, usuario_id=None):
        return self._pedidos.listar_com_itens(usuario_id=usuario_id)

    def atualizar_status(self, pedido_id, novo_status):
        self._pedidos.atualizar_status(pedido_id, novo_status)
        self._notificador.status_alterado(pedido_id, novo_status)
