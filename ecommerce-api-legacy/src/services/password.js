const crypto = require('node:crypto');
const { promisify } = require('node:util');

const scrypt = promisify(crypto.scrypt);
const KEY_LENGTH = 64;
const SALT_LENGTH = 16;

// KDF com salt aleatório por senha; formato `scrypt$<salt>$<chave>`.
async function hashPassword(plain) {
  const salt = crypto.randomBytes(SALT_LENGTH);
  const key = await scrypt(plain, salt, KEY_LENGTH);
  return `scrypt$${salt.toString('hex')}$${key.toString('hex')}`;
}

module.exports = { hashPassword };
