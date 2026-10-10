const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const requireAdmin = require('../middlewares/requireAdmin');

// Mapeamento rota → controller (View). Paths e métodos idênticos ao original.
function buildRoutes({ checkoutController, reportController, userController, adminToken }) {
    const router = express.Router();
    const admin = requireAdmin(adminToken);

    router.post('/api/checkout', asyncHandler(checkoutController.checkout));
    // Rotas administrativa e destrutiva protegidas por token (BC-01, BC-02).
    router.get('/api/admin/financial-report', admin, asyncHandler(reportController.financialReport));
    router.delete('/api/users/:id', admin, asyncHandler(userController.remove));

    return router;
}

module.exports = buildRoutes;
