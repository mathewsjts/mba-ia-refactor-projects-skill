const { ValidationError } = require('../errors');

const MAX_PAGE_SIZE = 100;
const DIGITS = /^\d+$/;

const isText = (value) => typeof value === 'string';
const isMissing = (value) => value === undefined || value === null;

// Id numérico positivo, em número ou texto; qualquer outro valor não identifica registro (null).
function toId(value) {
  const id = isText(value) && DIGITS.test(value) ? Number(value) : value;
  return Number.isSafeInteger(id) && id > 0 ? id : null;
}

// Traduz as chaves públicas (contrato) para nomes internos num único lugar.
function parseCheckout(body) {
  const input = body && typeof body === 'object' && !Array.isArray(body) ? body : {};
  const { usr, eml, pwd, c_id: courseId, card } = input;

  // Mesma regra e mesma mensagem do original: obrigatórios presentes...
  if (!usr || !eml || !courseId || !card) throw new ValidationError('Bad Request');
  // ...e com o tipo esperado (BC-04): texto onde o fluxo usa texto, id em número ou texto.
  if (!isText(usr) || !isText(eml) || !isText(card)) throw new ValidationError('Bad Request');
  if (!isMissing(pwd) && !isText(pwd)) throw new ValidationError('Bad Request');
  if (typeof courseId !== 'number' && !isText(courseId)) throw new ValidationError('Bad Request');

  return { name: usr, email: eml, password: pwd || null, courseId: toId(courseId), card };
}

function parseUserId(params) {
  return toId(params.id);
}

// Paginação opcional: sem `limit`, devolve tudo, como o original.
function parsePagination(query) {
  const { limit, offset = '0' } = query;
  if (limit === undefined) return {};
  if (!isText(limit) || !DIGITS.test(limit) || !isText(offset) || !DIGITS.test(offset)) {
    throw new ValidationError('Bad Request');
  }
  return { limit: Math.min(Number(limit), MAX_PAGE_SIZE), offset: Math.min(Number(offset), Number.MAX_SAFE_INTEGER) };
}

module.exports = { parseCheckout, parseUserId, parsePagination };
