const { parsePagination } = require('./validators');
const { serializeFinancialReport } = require('../views/serializers');

class ReportController {
  constructor(reportService) {
    this.reportService = reportService;
  }

  financialReport = async (req, res) => {
    const report = await this.reportService.financialReport(parsePagination(req.query));
    res.status(200).json(serializeFinancialReport(report));
  };
}

module.exports = ReportController;
