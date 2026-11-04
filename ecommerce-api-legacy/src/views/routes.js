const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

function buildRoutes({ checkoutController, reportController, userController, requireAdmin }) {
  const router = express.Router();

  router.post('/api/checkout', asyncHandler(checkoutController.checkout));
  router.get(
    '/api/admin/financial-report',
    requireAdmin,
    asyncHandler(reportController.financialReport),
  );
  router.delete('/api/users/:id', requireAdmin, asyncHandler(userController.remove));

  return router;
}

module.exports = buildRoutes;
