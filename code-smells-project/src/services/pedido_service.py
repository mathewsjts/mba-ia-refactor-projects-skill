from src.errors import RegraNegocioError

STATUS_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")


class PedidoService:
    def __init__(self, pedido_model, produto_model, usuario_service, notificador):
        self._pedidos = pedido_model
        self._produtos = produto_model
        self._usuarios = usuario_service
        self._notificador = notificador

    def criar(self, usuario_id, itens):
        if not self._usuarios.existe(usuario_id):
            raise RegraNegocioError("Usuário não encontrado")

        # Checagem completa antes da primeira escrita; mensagens e ordem do original.
        itens_validados = []
        total = 0
        for item in itens:
            produto = self._produtos.buscar_por_id(item["produto_id"])
            if produto is None:
                raise RegraNegocioError("Produto " + str(item["produto_id"]) + " não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise RegraNegocioError("Estoque insuficiente para " + produto["nome"])
            total = total + (produto["preco"] * item["quantidade"])
            itens_validados.append({
                "produto_id": item["produto_id"],
                "quantidade": item["quantidade"],
                "preco_unitario": produto["preco"],
                "nome": produto["nome"],
            })

        pedido_id = self._pedidos.criar(usuario_id, itens_validados, total)
        self._notificador.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar(self, limit=None, offset=0):
        return self._pedidos.listar(limit, offset)

    def listar_por_usuario(self, usuario_id):
        return self._pedidos.listar_por_usuario(usuario_id)

    def atualizar_status(self, pedido_id, status):
        # Como no original, pedido inexistente não é erro: nenhuma linha muda e a resposta é 200.
        self._pedidos.atualizar_status(pedido_id, status)
        self._notificador.status_alterado(pedido_id, status)
