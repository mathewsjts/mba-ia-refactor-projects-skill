const { parseCheckout } = require('./validators');
const { serializeCheckout } = require('../views/serializers');

class CheckoutController {
  constructor(checkoutService) {
    this.checkoutService = checkoutService;
  }

  checkout = async (req, res) => {
    const input = parseCheckout(req.body);
    const { enrollmentId } = await this.checkoutService.checkout(input);
    res.status(200).json(serializeCheckout(enrollmentId));
  };
}

module.exports = CheckoutController;
