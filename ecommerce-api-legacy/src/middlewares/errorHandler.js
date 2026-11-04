const { AppError } = require('../errors');

// Ponto único de tradução de erro → HTTP, no formato texto que o projeto já usa.
// Express reconhece middleware de erro pelos 4 parâmetros.
function buildErrorHandler({ logger }) {
  return function errorHandler(err, req, res, next) {
    if (res.headersSent) return next(err);
    if (err instanceof AppError) return res.status(err.statusCode).send(err.message);

    // Erros de cliente do próprio Express (ex.: JSON malformado no express.json() → 400).
    const status = err.statusCode || err.status;
    if (status >= 400 && status < 500) return res.status(status).send(err.expose ? err.message : 'Bad Request');

    logger.error('Erro não tratado', { method: req.method, path: req.path, error: err.message, stack: err.stack });
    return res.status(500).send('Erro interno do servidor');
  };
}

module.exports = buildErrorHandler;
