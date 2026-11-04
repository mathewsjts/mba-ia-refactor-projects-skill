const crypto = require('node:crypto');

const DEFAULT_PORT = 3000;

function parsePort(value) {
  if (value === undefined || value === '') return DEFAULT_PORT;
  const port = Number(value);
  if (!Number.isInteger(port) || port < 0 || port > 65535) {
    throw new Error(`PORT inválida: ${value}`);
  }
  return port;
}

// Segredo obrigatório em produção; em desenvolvimento, valor aleatório efêmero (nunca um literal).
function secret(environ, name, production) {
  const value = environ[name];
  if (value) return value;
  if (production) throw new Error(`Variável de ambiente obrigatória ausente: ${name}`);
  return crypto.randomBytes(32).toString('hex');
}

// Lê o ambiente uma única vez; chamado só pelo composition root.
function loadConfig(environ = process.env) {
  const env = environ.NODE_ENV || 'development';
  const production = env === 'production';

  return Object.freeze({
    env,
    port: parsePort(environ.PORT),
    databaseFile: environ.DATABASE_FILE || ':memory:',
    adminToken: secret(environ, 'ADMIN_TOKEN', production),
    adminTokenConfigured: Boolean(environ.ADMIN_TOKEN),
    paymentGatewayKey: secret(environ, 'PAYMENT_GATEWAY_KEY', production),
  });
}

module.exports = { loadConfig };
