const crypto = require('node:crypto');

const DEFAULT_PORT = 3000;

function parsePort(value) {
  const port = Number(value);
  if (!Number.isInteger(port) || port < 0 || port > 65535) {
    throw new Error(`PORT inválida: ${value}`);
  }
  return port;
}

// Lê o ambiente uma única vez; chamada só pelo composition root.
function loadConfig(environ = process.env) {
  const env = environ.NODE_ENV || 'development';
  const production = env === 'production';

  function required(name) {
    const value = environ[name];
    if (!value && production) {
      throw new Error(`Variável de ambiente obrigatória ausente: ${name}`);
    }
    return value || '';
  }

  return Object.freeze({
    env,
    port: parsePort(environ.PORT || DEFAULT_PORT),
    databaseFile: environ.DATABASE_FILE || ':memory:',
    sqliteVerbose: environ.SQLITE_VERBOSE === 'true',
    logLevel: environ.LOG_LEVEL || 'info',
    // Sem ADMIN_TOKEN as rotas administrativas recusam toda requisição (falha fechada).
    adminToken: required('ADMIN_TOKEN'),
    // Fora de produção, uma chave efêmera por boot; nunca um literal.
    paymentGatewayKey: required('PAYMENT_GATEWAY_KEY') || crypto.randomBytes(16).toString('hex'),
    // Senha do usuário de exemplo do seed; ausente, ele é criado sem credencial.
    seedUserPassword: environ.SEED_USER_PASSWORD || '',
  });
}

module.exports = loadConfig;
