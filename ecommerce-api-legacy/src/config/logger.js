// Ponto único de logging (T16), fácil de trocar por pino/winston depois.
// Nunca registrar senha, token, cartão ou segredo (AP-03).
const logger = {
    info: (message, meta = {}) =>
        console.info(JSON.stringify({ level: 'info', message, ...meta })),
    error: (message, meta = {}) =>
        console.error(JSON.stringify({ level: 'error', message, ...meta })),
};

module.exports = logger;
