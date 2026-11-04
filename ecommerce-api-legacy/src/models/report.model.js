class ReportModel {
  constructor(database) {
    this.database = database;
  }

  // Uma consulta para o relatório inteiro; a paginação, quando pedida, vale para cursos.
  financialRows({ limit, offset = 0 } = {}) {
    const courses = limit === undefined
      ? 'SELECT id, title FROM courses'
      : 'SELECT id, title FROM courses ORDER BY id LIMIT ? OFFSET ?';
    const params = limit === undefined ? [] : [limit, offset];

    return this.database.all(
      `SELECT c.id AS course_id, c.title, e.id AS enrollment_id,
              u.name AS student, p.amount, p.status
       FROM (${courses}) c
       LEFT JOIN enrollments e ON e.course_id = c.id
       LEFT JOIN users u ON u.id = e.user_id
       LEFT JOIN payments p ON p.enrollment_id = e.id
       ORDER BY c.id, e.id`,
      params,
    );
  }
}

module.exports = ReportModel;
