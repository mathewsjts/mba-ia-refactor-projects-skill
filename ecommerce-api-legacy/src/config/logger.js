// Ponto único de log, fácil de trocar por pino/winston.
const LEVELS = Object.freeze({ error: 0, warn: 1, info: 2, debug: 3 });

function createLogger(level = 'info') {
  const threshold = LEVELS[level] ?? LEVELS.info;

  const write = (name, output) => (message, meta = {}) => {
    if (LEVELS[name] > threshold) return;
    output(JSON.stringify({ level: name, message, ...meta }));
  };

  return Object.freeze({
    error: write('error', console.error),
    warn: write('warn', console.warn),
    info: write('info', console.info),
    debug: write('debug', console.debug),
  });
}

module.exports = createLogger;
