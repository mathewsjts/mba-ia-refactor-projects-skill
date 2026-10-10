// Configuração lida do ambiente uma única vez (T02).
// Nenhum segredo literal: valores vêm de variáveis de ambiente.
const nodeEnv = process.env.NODE_ENV || 'development';
const isProduction = nodeEnv === 'production';

function secret(name) {
    const value = process.env[name];
    if (!value && isProduction) {
        throw new Error(`Variável de ambiente obrigatória ausente em produção: ${name}`);
    }
    return value || '';
}

module.exports = Object.freeze({
    nodeEnv,
    isProduction,
    // Mesmo default do original (3000) para preservar o comando documentado.
    port: Number(process.env.PORT || 3000),
    // SQLite em memória como no original; configurável para outros ambientes.
    databaseFile: process.env.DATABASE_FILE || ':memory:',
    // Token exigido pelas rotas administrativas/destrutivas (T14).
    adminToken: secret('ADMIN_TOKEN'),
    // Chave do gateway de pagamento — antes hardcoded em utils.js (F-01).
    paymentGatewayKey: secret('PAYMENT_GATEWAY_KEY'),
});
