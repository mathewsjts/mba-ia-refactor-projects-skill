const { parseCheckout } = require('./validators');

// Controller fino (T04): extrai e valida a entrada, chama o service e monta a resposta.
class CheckoutController {
    constructor(checkoutService) {
        this.checkoutService = checkoutService;
    }

    checkout = async (req, res) => {
        const input = parseCheckout(req.body);
        const enrollmentId = await this.checkoutService.checkout(input);
        res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    };
}

module.exports = CheckoutController;
