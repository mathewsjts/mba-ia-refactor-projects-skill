const { PAYMENT_STATUS } = require('../models/payment.model');

const UNKNOWN_STUDENT = 'Unknown';

class ReportService {
  constructor({ reportModel }) {
    this.reportModel = reportModel;
  }

  // Receita por curso soma só pagamentos aprovados; cada matrícula aparece como aluno.
  async financialReport(pagination) {
    const rows = await this.reportModel.financialRows(pagination);
    const report = new Map();

    for (const row of rows) {
      if (!report.has(row.course_id)) {
        report.set(row.course_id, { course: row.title, revenue: 0, students: [] });
      }
      if (row.enrollment_id === null) continue;

      const entry = report.get(row.course_id);
      if (row.status === PAYMENT_STATUS.PAID) entry.revenue += row.amount;
      entry.students.push({ student: row.student ?? UNKNOWN_STUDENT, paid: row.amount ?? 0 });
    }

    return [...report.values()];
  }
}

module.exports = ReportService;
