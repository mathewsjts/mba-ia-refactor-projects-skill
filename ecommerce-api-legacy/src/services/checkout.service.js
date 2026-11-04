const { NotFoundError, ValidationError } = require('../errors');
const { PAYMENT_STATUS } = require('../models/payment.model');

class CheckoutService {
  constructor({ transaction, userModel, courseModel, enrollmentModel, paymentModel, auditModel, paymentGateway, cache, hashPassword }) {
    this.transaction = transaction;
    this.userModel = userModel;
    this.courseModel = courseModel;
    this.enrollmentModel = enrollmentModel;
    this.paymentModel = paymentModel;
    this.auditModel = auditModel;
    this.paymentGateway = paymentGateway;
    this.cache = cache;
    this.hashPassword = hashPassword;
  }

  async checkout({ name, email, password, courseId, card }) {
    // 1. Validações, na ordem do original, antes de qualquer efeito.
    const course = courseId === null ? undefined : this.courseModel.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    const existingUser = this.userModel.findByEmail(email);
    if (!existingUser && !password) throw new ValidationError('Bad Request');
    const passwordHash = existingUser ? null : await this.hashPassword(password);

    // 2. Efeito externo só depois de validar tudo.
    const status = await this.paymentGateway.charge({ card, amount: course.price });
    if (status === PAYMENT_STATUS.DENIED) throw new ValidationError('Pagamento recusado');

    // 3. Todas as escritas numa transação; qualquer exceção desfaz as anteriores.
    const { userId, enrollmentId } = this.transaction(() => {
      // Usuário criado por outra requisição entre a busca e aqui é reaproveitado (UNIQUE + ON CONFLICT);
      // usuário removido nesse intervalo, sem senha para recriá-lo, cai na mesma regra da busca.
      const ownerId = this.userModel.findOrCreate({ name, email, passwordHash });
      if (ownerId === undefined) throw new ValidationError('Bad Request');
      const newEnrollmentId = this.enrollmentModel.create({ userId: ownerId, courseId: course.id });
      this.paymentModel.create({ enrollmentId: newEnrollmentId, amount: course.price, status });
      this.auditModel.log(`Checkout curso ${course.id} por ${ownerId}`);
      return { userId: ownerId, enrollmentId: newEnrollmentId };
    });

    this.cache.set(`last_checkout_${userId}`, course.title);
    return enrollmentId;
  }
}

module.exports = CheckoutService;
