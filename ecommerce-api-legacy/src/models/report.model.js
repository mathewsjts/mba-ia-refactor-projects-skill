// Uma consulta para o relatório inteiro (antes: 1 + cursos + 2 × matrículas).
// O pagamento é o primeiro da matrícula, como o `db.get` do original.
const FINANCIAL_ROWS = `
  SELECT c.id AS course_id, c.title, e.id AS enrollment_id,
         COALESCE(u.name, 'Unknown') AS student,
         p.id AS payment_id, p.amount, p.status
  FROM %COURSES% c
  LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u ON u.id = e.user_id
  LEFT JOIN payments p ON p.id = (SELECT MIN(id) FROM payments WHERE enrollment_id = e.id)
  ORDER BY c.id, e.id
`;

const ALL_COURSES = FINANCIAL_ROWS.replace('%COURSES%', 'courses');
const PAGE_OF_COURSES = FINANCIAL_ROWS.replace(
  '%COURSES%',
  '(SELECT id, title FROM courses ORDER BY id LIMIT ? OFFSET ?)',
);

class ReportModel {
  constructor(database) {
    this.db = database.connection;
  }

  // Paginação opcional por curso: sem `limit`, todos os cursos, como no original.
  financialRows({ limit, offset = 0 } = {}) {
    if (limit === undefined) return this.db.prepare(ALL_COURSES).all();
    return this.db.prepare(PAGE_OF_COURSES).all(limit, offset);
  }
}

module.exports = ReportModel;
