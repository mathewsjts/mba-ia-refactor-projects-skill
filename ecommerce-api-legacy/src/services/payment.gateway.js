const { PAYMENT_STATUS } = require('../models/payment.model');

// Simulação do gateway: cartões iniciados por este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';
const VISIBLE_CARD_DIGITS = 4;

const maskCard = (card) => `****${card.slice(-VISIBLE_CARD_DIGITS)}`;

class FakePaymentGateway {
  constructor({ apiKey, logger }) {
    this.apiKey = apiKey;
    this.logger = logger;
  }

  async charge({ card, amount }) {
    this.logger.info('Processando pagamento', { card: maskCard(card), amount });
    return card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
  }
}

module.exports = FakePaymentGateway;
