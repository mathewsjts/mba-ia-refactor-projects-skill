// Express 4 não repassa rejeições de handlers async ao middleware de erro.
module.exports = (handler) => (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);
