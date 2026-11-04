const { STATUS_CODES } = require('node:http');
const { AppError } = require('../errors');

const INTERNAL_ERROR_MESSAGE = 'Erro interno do servidor';

// Express reconhece middleware de erro pelos 4 parâmetros. Respostas de erro
// continuam em texto puro, como no original.
module.exports = (logger) => function errorHandler(err, req, res, next) {
  if (res.headersSent) return next(err);
  if (err instanceof AppError) return res.status(err.statusCode).send(err.message);

  // Erros do próprio Express, como JSON malformado (400) ou corpo grande demais (413).
  const status = err.statusCode || err.status;
  if (status >= 400 && status < 500) return res.status(status).send(STATUS_CODES[status]);

  logger.error('Erro não tratado', { method: req.method, path: req.path, error: err.stack });
  return res.status(500).send(INTERNAL_ERROR_MESSAGE);
};
