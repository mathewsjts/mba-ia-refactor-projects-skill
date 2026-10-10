const crypto = require('node:crypto');

// Protege rotas administrativas/destrutivas (T14, BC-01/BC-02).
// Falha fechada: sem ADMIN_TOKEN configurado, recusa todas as requisições.
module.exports = (adminToken) => (req, res, next) => {
    const expected = Buffer.from(adminToken || '');
    const provided = Buffer.from(req.get('X-Admin-Token') || '');
    const valid =
        expected.length > 0 &&
        expected.length === provided.length &&
        crypto.timingSafeEqual(expected, provided);
    if (!valid) return res.status(401).send('Não autorizado');
    return next();
};
