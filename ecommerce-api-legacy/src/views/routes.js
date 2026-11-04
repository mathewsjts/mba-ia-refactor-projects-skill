const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

// `requireAdmin` protege as rotas administrativas (T14); o checkout é o fluxo público de visitante.
function buildRoutes({ checkoutController, reportController, userController, requireAdmin }) {
  const router = express.Router();
  router.post('/api/checkout', asyncHandler(checkoutController.checkout));
  router.get('/api/admin/financial-report', requireAdmin, asyncHandler(reportController.financialReport));
  router.delete('/api/users/:id', requireAdmin, asyncHandler(userController.delete));
  return router;
}

module.exports = buildRoutes;
