// Campos públicos explícitos; nada de senha, cartão ou e-mail nas respostas.
const serializeCheckout = (enrollmentId) => ({ msg: 'Sucesso', enrollment_id: enrollmentId });

const serializeStudent = ({ student, paid }) => ({ student, paid });

const serializeCourseRevenue = ({ course, revenue, students }) => ({
  course,
  revenue,
  students: students.map(serializeStudent),
});

const serializeFinancialReport = (report) => report.map(serializeCourseRevenue);

module.exports = { serializeCheckout, serializeFinancialReport };
