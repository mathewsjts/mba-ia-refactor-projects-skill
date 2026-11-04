const { ValidationError } = require('../errors');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+$/;
const DIGITS_PATTERN = /^\d+$/;
const MAX_PAGE_SIZE = 100;

const isPlainObject = (value) =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

const isNonEmptyString = (value) => typeof value === 'string' && value.trim() !== '';

// Inteiro não negativo seguro, vindo como número JSON ou texto de dígitos.
function toId(value) {
  if (typeof value === 'number') return Number.isSafeInteger(value) && value >= 0 ? value : null;
  if (typeof value === 'string' && DIGITS_PATTERN.test(value)) {
    const id = Number(value);
    return Number.isSafeInteger(id) ? id : null;
  }
  return null;
}

// Traduz as chaves públicas do contrato (usr, eml, pwd, c_id, card) para nomes internos.
function parseCheckout(body) {
  if (!isPlainObject(body)) throw new ValidationError();

  const { usr: name, eml: email, pwd: password, c_id: rawCourseId, card } = body;
  const courseId = toId(rawCourseId);

  // `pwd` é opcional, como no original: ausente, nulo ou vazio cria a conta sem senha.
  const passwordValid = password === undefined || password === null || typeof password === 'string';

  if (
    !isNonEmptyString(name)
    || !isNonEmptyString(email)
    || !EMAIL_PATTERN.test(email)
    || !passwordValid
    || !courseId
    || !isNonEmptyString(card)
  ) {
    throw new ValidationError();
  }

  return { name, email, password: password || null, courseId, card };
}

function parseUserId(rawId) {
  const userId = toId(rawId);
  if (userId === null) throw new ValidationError();
  return userId;
}

// Paginação opcional: sem `limit`, o relatório vem inteiro, como antes.
function parsePagination(query = {}) {
  if (query.limit === undefined) return {};
  const limit = toId(query.limit);
  const offset = query.offset === undefined ? 0 : toId(query.offset);
  if (!limit || offset === null) throw new ValidationError();
  return { limit: Math.min(limit, MAX_PAGE_SIZE), offset };
}

module.exports = { parseCheckout, parseUserId, parsePagination };
