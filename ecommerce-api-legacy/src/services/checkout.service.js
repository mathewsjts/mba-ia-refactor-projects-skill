const { NotFoundError, PaymentDeclinedError } = require('../errors');
const { PAYMENT_STATUS } = require('../models/payment.model');

class CheckoutService {
  constructor({
    database,
    courseModel,
    userModel,
    enrollmentModel,
    paymentModel,
    auditModel,
    paymentGateway,
    cache,
    hashPassword,
  }) {
    this.database = database;
    this.courseModel = courseModel;
    this.userModel = userModel;
    this.enrollmentModel = enrollmentModel;
    this.paymentModel = paymentModel;
    this.auditModel = auditModel;
    this.paymentGateway = paymentGateway;
    this.cache = cache;
    this.hashPassword = hashPassword;
  }

  async checkout({ name, email, password, courseId, card }) {
    // Tudo o que pode recusar o checkout acontece antes da primeira escrita.
    const course = await this.courseModel.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    // Sem senha, a conta nasce sem credencial — nunca com uma senha padrão.
    const passwordHash = password ? await this.hashPassword(password) : null;

    const status = await this.paymentGateway.charge({ card, amount: course.price });
    if (status !== PAYMENT_STATUS.PAID) throw new PaymentDeclinedError();

    // Usuário, matrícula, pagamento e auditoria: todos gravados ou nenhum.
    const { userId, enrollmentId } = await this.database.transaction(async (tx) => {
      const newUserId = await this.userModel.findOrCreate(tx, { name, email, passwordHash });
      const newEnrollmentId = await this.enrollmentModel.create(tx, {
        userId: newUserId,
        courseId: course.id,
      });
      await this.paymentModel.create(tx, {
        enrollmentId: newEnrollmentId,
        amount: course.price,
        status,
      });
      await this.auditModel.log(tx, `Checkout curso ${course.id} por ${newUserId}`);
      return { userId: newUserId, enrollmentId: newEnrollmentId };
    });

    this.cache.set(`last_checkout_${userId}`, course.title);
    return { enrollmentId };
  }
}

module.exports = CheckoutService;
