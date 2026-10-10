// Hash de senha com KDF e salt (T05), usando crypto nativo — sem dependência nova.
const crypto = require('node:crypto');
const { promisify } = require('node:util');

const scrypt = promisify(crypto.scrypt);
const KEY_LENGTH = 64;

async function hashPassword(plain) {
    const salt = crypto.randomBytes(16);
    const key = await scrypt(plain, salt, KEY_LENGTH);
    return `scrypt$${salt.toString('hex')}$${key.toString('hex')}`;
}

async function verifyPassword(stored, plain) {
    const [scheme, saltHex, keyHex] = String(stored).split('$');
    if (scheme !== 'scrypt' || !saltHex || !keyHex) return false;
    const expected = Buffer.from(keyHex, 'hex');
    const actual = await scrypt(plain, Buffer.from(saltHex, 'hex'), expected.length);
    return expected.length === actual.length && crypto.timingSafeEqual(expected, actual);
}

module.exports = { hashPassword, verifyPassword };
