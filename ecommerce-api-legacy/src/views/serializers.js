// Campos públicos explícitos do relatório financeiro (nenhum e-mail, senha ou id interno).
const serializeStudent = ({ student, paid }) => ({ student, paid });

const serializeCourseReport = ({ course, revenue, students }) => ({
  course,
  revenue,
  students: students.map(serializeStudent),
});

const serializeFinancialReport = (report) => report.map(serializeCourseReport);

module.exports = { serializeFinancialReport };
