"""Relatório de vendas (T04): a regra de desconto sai do model.
Limiares e taxas viram constantes nomeadas (T16, AP-21)."""

# (limiar de faturamento, taxa de desconto) em ordem decrescente de limiar.
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))


class RelatorioService:
    def __init__(self, pedido_model):
        self._pedidos = pedido_model

    def vendas(self):
        resumo = self._pedidos.resumo_vendas()
        faturamento = resumo["faturamento"]
        total_pedidos = resumo["total_pedidos"]

        taxa = next((t for limite, t in FAIXAS_DESCONTO if faturamento > limite), 0)
        desconto = faturamento * taxa

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": resumo["pendentes"],
            "pedidos_aprovados": resumo["aprovados"],
            "pedidos_cancelados": resumo["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
