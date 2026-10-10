// Persistência da matrícula com pagamento e auditoria (T01) numa única transação (T07).
class EnrollmentModel {
    constructor({ db, withTransaction }) {
        this.db = db;
        this.withTransaction = withTransaction;
    }

    // Grava enrollment + payment + audit_log atomicamente; qualquer falha faz rollback.
    createCheckout({ userId, courseId, amount, status, auditAction }) {
        return this.withTransaction(async (db) => {
            const { lastID: enrollmentId } = await db.run(
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
                [userId, courseId],
            );
            await db.run(
                'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
                [enrollmentId, amount, status],
            );
            await db.run(
                "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
                [auditAction],
            );
            return enrollmentId;
        });
    }
}

module.exports = EnrollmentModel;
