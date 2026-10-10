// Express 4 não repassa rejeições de handlers async ao middleware de erro;
// este wrapper encaminha qualquer rejeição para next() (T10).
module.exports = (handler) => (req, res, next) =>
    Promise.resolve(handler(req, res, next)).catch(next);
