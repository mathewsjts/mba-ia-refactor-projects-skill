const { AppError } = require('../errors');
const logger = require('../config/logger');

// Tratamento de erro central (T10). Erros de domínio viram a resposta de texto
// que o contrato já usava; inesperados viram 500 genérico, sem vazar detalhes.
// Express reconhece o middleware de erro pelos 4 parâmetros.
module.exports = function errorHandler(err, req, res, next) {
    if (res.headersSent) return next(err);
    if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
    const status = err.statusCode || err.status; // ex.: JSON malformado no express.json() → 400
    if (status && status < 500) return res.status(status).send(err.message);
    logger.error('Erro não tratado', { error: err.message });
    return res.status(500).send('Erro interno do servidor');
};
