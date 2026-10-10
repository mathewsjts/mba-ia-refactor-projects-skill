const { ValidationError } = require('../errors');

// Traduz as chaves públicas do contrato (usr/eml/pwd/c_id/card) para nomes
// internos num único ponto (T09). As chaves públicas NÃO são renomeadas (contrato).
function parseCheckout(body = {}) {
    const input = {
        name: body.usr,
        email: body.eml,
        password: body.pwd,
        courseId: body.c_id,
        card: body.card,
    };
    // Mesma regra do original: pwd não é obrigatório.
    if (!input.name || !input.email || !input.courseId || !input.card) {
        throw new ValidationError('Bad Request');
    }
    return input;
}

module.exports = { parseCheckout };
