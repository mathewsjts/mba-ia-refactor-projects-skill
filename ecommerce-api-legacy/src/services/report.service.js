const { buildFinancialReport } = require('../views/serializers');

// Regra do relatório financeiro (T04): agrega as linhas do JOIN em memória,
// reproduzindo a estrutura de resposta do original.
class ReportService {
    constructor({ reportModel }) {
        this.reportModel = reportModel;
    }

    async financialReport() {
        const rows = await this.reportModel.financialRows();
        return buildFinancialReport(rows);
    }
}

module.exports = ReportService;
