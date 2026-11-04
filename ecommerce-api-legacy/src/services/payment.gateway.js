const { PAYMENT_STATUS } = require('../models/payment.model');

const APPROVED_CARD_PREFIX = '4';

// Gateway simulado, substituível por uma integração real com a mesma interface.
class FakePaymentGateway {
  constructor({ apiKey, logger }) {
    this.apiKey = apiKey;
    this.logger = logger;
  }

  async charge({ card, amount }) {
    const status = card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    // Nunca o número do cartão nem a chave: só os 4 últimos dígitos.
    this.logger.info('Pagamento processado', { cardLast4: card.slice(-4), amount, status });
    return status;
  }
}

module.exports = FakePaymentGateway;
