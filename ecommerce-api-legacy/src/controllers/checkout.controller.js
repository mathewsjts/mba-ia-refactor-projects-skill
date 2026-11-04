const { parseCheckout } = require('./validators');

class CheckoutController {
  constructor({ checkoutService }) {
    this.checkoutService = checkoutService;
  }

  checkout = async (req, res) => {
    const enrollmentId = await this.checkoutService.checkout(parseCheckout(req.body));
    res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
  };
}

module.exports = CheckoutController;
