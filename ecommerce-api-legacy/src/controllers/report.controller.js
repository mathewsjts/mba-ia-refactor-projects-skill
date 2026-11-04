const { parsePagination } = require('./validators');
const { serializeFinancialReport } = require('../views/serializers');

class ReportController {
  constructor({ reportService }) {
    this.reportService = reportService;
  }

  financialReport = async (req, res) => {
    const report = this.reportService.financialReport(parsePagination(req.query));
    res.json(serializeFinancialReport(report));
  };
}

module.exports = ReportController;
