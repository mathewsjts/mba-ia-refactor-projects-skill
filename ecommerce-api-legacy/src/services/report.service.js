const { PAYMENT_STATUS } = require('../models/payment.model');

class ReportService {
  constructor({ reportModel }) {
    this.reportModel = reportModel;
  }

  // Receita conta só pagamentos PAID; `paid` mostra o valor do pagamento, ou 0 sem pagamento.
  financialReport(pagination) {
    const courses = new Map();
    for (const row of this.reportModel.financialRows(pagination)) {
      if (!courses.has(row.course_id)) {
        courses.set(row.course_id, { course: row.title, revenue: 0, students: [] });
      }
      if (row.enrollment_id === null) continue;

      const entry = courses.get(row.course_id);
      if (row.status === PAYMENT_STATUS.PAID) entry.revenue += row.amount;
      entry.students.push({ student: row.student, paid: row.payment_id === null ? 0 : row.amount });
    }
    return [...courses.values()];
  }
}

module.exports = ReportService;
