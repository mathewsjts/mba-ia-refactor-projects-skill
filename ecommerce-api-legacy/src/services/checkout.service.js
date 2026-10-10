const crypto = require('node:crypto');
const { NotFoundError, ValidationError } = require('../errors');
const { hashPassword } = require('../models/passwords');

const PAYMENT_STATUS_PAID = 'PAID';

// Regra de negócio do checkout (T04): orquestra models, gateway e cache,
// sem conhecer requisição nem resposta HTTP.
class CheckoutService {
    constructor({ courseModel, userModel, enrollmentModel, paymentGateway, cache }) {
        this.courseModel = courseModel;
        this.userModel = userModel;
        this.enrollmentModel = enrollmentModel;
        this.paymentGateway = paymentGateway;
        this.cache = cache;
    }

    async checkout({ name, email, password, courseId, card }) {
        // Ordem de verificação preservada: curso inexistente (404) antes de pagamento (400).
        const course = await this.courseModel.findActiveById(courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        const approved = await this.paymentGateway.charge({ card, amount: course.price });
        if (!approved) throw new ValidationError('Pagamento recusado');

        const userId = await this.resolveUserId({ name, email, password });

        const enrollmentId = await this.enrollmentModel.createCheckout({
            userId,
            courseId,
            amount: course.price,
            status: PAYMENT_STATUS_PAID,
            auditAction: `Checkout curso ${courseId} por ${userId}`,
        });

        this.cache.set(`last_checkout_${userId}`, course.title);
        return enrollmentId;
    }

    async resolveUserId({ name, email, password }) {
        const existing = await this.userModel.findByEmail(email);
        if (existing) return existing.id;

        // Sem senha, gera uma aleatória forte em vez do default previsível "123456" (F-03).
        const plain = password || crypto.randomBytes(16).toString('hex');
        const passHash = await hashPassword(plain);
        return this.userModel.create({ name, email, passHash });
    }
}

module.exports = CheckoutService;
