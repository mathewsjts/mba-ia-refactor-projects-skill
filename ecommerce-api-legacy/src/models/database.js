const BetterSqlite3 = require('better-sqlite3');
const { PAYMENT_STATUS } = require('./payment.model');

// Adaptador de Promises sobre o driver, usado só dentro da fila: models e services
// não dependem de o driver ser síncrono.
function executor(raw) {
  return Object.freeze({
    async run(sql, params = []) {
      const { lastInsertRowid, changes } = raw.prepare(sql).run(...params);
      return { lastID: Number(lastInsertRowid), changes };
    },
    async get(sql, params = []) {
      return raw.prepare(sql).get(...params);
    },
    async all(sql, params = []) {
      return raw.prepare(sql).all(...params);
    },
    async exec(sql) {
      raw.exec(sql);
    },
    inTransaction() {
      return raw.inTransaction;
    },
  });
}

class Database {
  #ops;

  #queue;

  constructor(raw) {
    this.#ops = executor(raw);
    this.#queue = Promise.resolve();
  }

  static async open(filename, { verbose = false, logger } = {}) {
    const raw = new BetterSqlite3(filename, verbose ? { verbose: (sql) => logger.debug(sql) } : {});
    const database = new Database(raw);
    // foreign_keys vale por conexão; esta é a única conexão da aplicação.
    await database.exec('PRAGMA foreign_keys = ON');
    return database;
  }

  // Uma única conexão é compartilhada por todas as requisições. Toda instrução passa
  // por esta fila, então nada de outra requisição cai dentro de uma transação aberta.
  enqueue(task) {
    const result = this.#queue.then(task);
    this.#queue = result.catch(() => {});
    return result;
  }

  get(sql, params) {
    return this.enqueue(() => this.#ops.get(sql, params));
  }

  all(sql, params) {
    return this.enqueue(() => this.#ops.all(sql, params));
  }

  exec(sql) {
    return this.enqueue(() => this.#ops.exec(sql));
  }

  // O Database não expõe `run`: INSERT/UPDATE/DELETE só rodam pelo executor que
  // `work` recebe aqui, com COMMIT ao terminar e ROLLBACK se qualquer passo lançar.
  transaction(work) {
    return this.enqueue(async () => {
      await this.#ops.run('BEGIN IMMEDIATE');
      try {
        const value = await work(this.#ops);
        await this.#ops.run('COMMIT');
        return value;
      } catch (err) {
        // O SQLite já desfaz a transação sozinho em alguns erros; só desfaz se ainda aberta.
        if (this.#ops.inTransaction()) await this.#ops.run('ROLLBACK');
        throw err;
      }
    });
  }
}

const SCHEMA = `
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT NOT NULL UNIQUE,
    pass TEXT
  );
  CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY,
    title TEXT,
    price REAL,
    active INTEGER
  );
  CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    course_id INTEGER NOT NULL REFERENCES courses(id)
  );
  CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    enrollment_id INTEGER NOT NULL REFERENCES enrollments(id),
    amount REAL,
    status TEXT
  );
  CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY,
    action TEXT,
    created_at DATETIME
  );
  CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique ON users(email);
`;

function initSchema(database) {
  return database.exec(SCHEMA);
}

// Popula o banco no boot, como o original; num banco em arquivo, só na primeira vez.
async function seed(database, { hashPassword, seedUserPassword }) {
  const { total } = await database.get('SELECT COUNT(*) AS total FROM courses');
  if (total > 0) return;

  const passwordHash = seedUserPassword ? await hashPassword(seedUserPassword) : null;
  await database.transaction(async (tx) => {
    await tx.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
      'Leonan',
      'leonan@fullcycle.com.br',
      passwordHash,
    ]);
    await tx.run(
      'INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)',
      ['Clean Architecture', 997.0, 'Docker', 497.0],
    );
    await tx.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
    await tx.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [
      1,
      997.0,
      PAYMENT_STATUS.PAID,
    ]);
  });
}

module.exports = { Database, initSchema, seed };
