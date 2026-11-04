const crypto = require('node:crypto');
const { UnauthorizedError } = require('../errors');

// Exige `X-Admin-Token` igual a ADMIN_TOKEN, em tempo constante. Falha fechada:
// sem ADMIN_TOKEN configurado, a configuração usa um valor aleatório que ninguém conhece.
function buildRequireAdmin({ adminToken }) {
  const expected = Buffer.from(adminToken || '');

  return function requireAdmin(req, res, next) {
    const provided = Buffer.from(req.get('X-Admin-Token') || '');
    const valid = expected.length > 0
      && expected.length === provided.length
      && crypto.timingSafeEqual(expected, provided);
    if (!valid) return next(new UnauthorizedError('Não autorizado'));
    return next();
  };
}

module.exports = buildRequireAdmin;
