const crypto = require('node:crypto');

// Sem ADMIN_TOKEN configurado, nenhum valor de header é aceito (falha fechada).
module.exports = (adminToken) => (req, res, next) => {
  const expected = Buffer.from(adminToken || '');
  const provided = Buffer.from(req.get('X-Admin-Token') || '');
  const valid = expected.length > 0
    && expected.length === provided.length
    && crypto.timingSafeEqual(expected, provided);
  if (!valid) return res.status(401).send('Não autorizado');
  return next();
};
