// Controller do relatório financeiro (T04).
class ReportController {
    constructor(reportService) {
        this.reportService = reportService;
    }

    financialReport = async (req, res) => {
        const report = await this.reportService.financialReport();
        res.status(200).json(report);
    };
}

module.exports = ReportController;
