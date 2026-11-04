# (faturamento acima de, taxa de desconto), da maior faixa para a menor.
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))


class RelatorioService:
    def __init__(self, pedido_model):
        self._pedidos = pedido_model

    def vendas(self):
        totais = self._pedidos.totais()
        total_pedidos = totais["total_pedidos"]
        faturamento = totais["faturamento"]
        taxa = next((taxa for limite, taxa in FAIXAS_DESCONTO if faturamento > limite), 0)
        desconto = faturamento * taxa
        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": totais["pendentes"],
            "pedidos_aprovados": totais["aprovados"],
            "pedidos_cancelados": totais["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
