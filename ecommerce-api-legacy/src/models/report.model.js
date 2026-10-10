// Relatório financeiro numa única consulta com JOIN, eliminando o N+1 original (T08).
class ReportModel {
    constructor(db) {
        this.db = db;
    }

    async financialRows() {
        return this.db.all(`
            SELECT c.id AS course_id, c.title, e.id AS enrollment_id,
                   u.name AS student, p.amount, p.status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u ON u.id = e.user_id
            LEFT JOIN payments p ON p.enrollment_id = e.id
            ORDER BY c.id, e.id
        `);
    }
}

module.exports = ReportModel;
