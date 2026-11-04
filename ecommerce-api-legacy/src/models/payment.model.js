const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

class PaymentModel {
  constructor(database) {
    this.db = database.connection;
  }

  create({ enrollmentId, amount, status }) {
    this.db
      .prepare('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)')
      .run(enrollmentId, amount, status);
  }
}

module.exports = { PaymentModel, PAYMENT_STATUS };
