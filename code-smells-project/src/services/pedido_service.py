"""Regras de negócio de pedidos — validação de estoque, total e notificação (T04/T07)."""
from src.errors import ValidationError


class PedidoService:
    def __init__(self, pedido_model, produto_model, notificacao_service):
        self._pedidos = pedido_model
        self._produtos = produto_model
        self._notificador = notificacao_service

    def criar(self, usuario_id, itens):
        # Valida tudo ANTES de qualquer escrita (T07); erros de negócio trazem
        # `sucesso: false` no corpo do 400 (contrato original).
        total = 0
        resolvidos = []
        for item in itens:
            produto = self._produtos.buscar_por_id(item["produto_id"])
            if produto is None:
                raise ValidationError(
                    f"Produto {item['produto_id']} não encontrado", sucesso=False
                )
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError(
                    f"Estoque insuficiente para {produto['nome']}", sucesso=False
                )
            total += produto["preco"] * item["quantidade"]
            resolvidos.append({
                "produto_id": item["produto_id"],
                "quantidade": item["quantidade"],
                "preco_unitario": produto["preco"],
            })

        resultado = self._pedidos.criar(usuario_id, resolvidos, total)
        self._notificador.pedido_criado(resultado["pedido_id"], usuario_id)
        return resultado

    def listar_por_usuario(self, usuario_id):
        return self._pedidos.listar_por_usuario(usuario_id)

    def listar_todos(self):
        return self._pedidos.listar_todos()

    def atualizar_status(self, pedido_id, novo_status):
        self._pedidos.atualizar_status(pedido_id, novo_status)
        self._notificador.status_alterado(pedido_id, novo_status)
