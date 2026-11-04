const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

class PaymentModel {
  async create(tx, { enrollmentId, amount, status }) {
    const { lastID } = await tx.run(
      'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
      [enrollmentId, amount, status],
    );
    return lastID;
  }
}

module.exports = { PaymentModel, PAYMENT_STATUS };
