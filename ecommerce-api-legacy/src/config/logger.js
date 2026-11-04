// Ponto único de log (JSON com nível), fácil de trocar por pino/winston.
function write(stream, level, message, meta) {
  stream.write(`${JSON.stringify({ level, time: new Date().toISOString(), message, ...meta })}\n`);
}

const logger = Object.freeze({
  info: (message, meta = {}) => write(process.stdout, 'info', message, meta),
  warn: (message, meta = {}) => write(process.stderr, 'warn', message, meta),
  error: (message, meta = {}) => write(process.stderr, 'error', message, meta),
});

module.exports = logger;
