// Serialização pública das respostas (T13), com os mesmos campos do contrato original.

// Monta o relatório financeiro a partir das linhas do JOIN, preservando a
// estrutura e os fallbacks do handler original ('Unknown' e 0).
function buildFinancialReport(rows) {
    const report = new Map();

    for (const row of rows) {
        if (!report.has(row.course_id)) {
            report.set(row.course_id, { course: row.title, revenue: 0, students: [] });
        }
        // Curso sem matrícula (LEFT JOIN) entra com students vazio, como no original.
        if (row.enrollment_id == null) continue;

        const entry = report.get(row.course_id);
        if (row.status === 'PAID') entry.revenue += row.amount;
        entry.students.push({
            student: row.student || 'Unknown',
            paid: row.amount || 0,
        });
    }

    return [...report.values()];
}

module.exports = { buildFinancialReport };
