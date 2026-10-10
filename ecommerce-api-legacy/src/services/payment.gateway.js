// Gateway de pagamento atrás de uma interface injetável (T11).
// A simulação do original (cartão começando com "4" é aprovado) vira uma
// implementação substituível, isolada da regra de negócio.
const APPROVED_CARD_PREFIX = '4';

class FakePaymentGateway {
    constructor({ apiKey } = {}) {
        // A chave viria da configuração; uma implementação real a usaria aqui.
        this.apiKey = apiKey;
    }

    async charge({ card }) {
        return typeof card === 'string' && card.startsWith(APPROVED_CARD_PREFIX);
    }
}

module.exports = FakePaymentGateway;
