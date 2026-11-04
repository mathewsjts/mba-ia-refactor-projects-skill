const Database = require('better-sqlite3');

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
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(id)
  );
  CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE CASCADE,
    amount REAL,
    status TEXT
  );
  CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY,
    action TEXT,
    created_at DATETIME
  );
  CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique ON users (email);
`;

// Conexão única criada pelo composition root e injetada nos models.
function openDatabase(filename) {
  const connection = new Database(filename);
  connection.pragma('foreign_keys = ON');
  return {
    connection,
    // Executa `work` numa transação: COMMIT ao retornar, ROLLBACK se lançar.
    // O driver é síncrono, então nenhuma instrução de outra requisição entra no meio.
    transaction: (work) => connection.transaction(work)(),
    close: () => connection.close(),
  };
}

function initSchema(database) {
  database.connection.exec(SCHEMA);
}

// Mesmo seed do original, gravado uma única vez (banco em arquivo não é repopulado).
function seedDatabase(database, { seedUserPasswordHash }) {
  const { connection } = database;
  const { count } = connection.prepare('SELECT COUNT(*) AS count FROM courses').get();
  if (count > 0) return;

  database.transaction(() => {
    connection
      .prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)')
      .run('Leonan', 'leonan@fullcycle.com.br', seedUserPasswordHash);
    const insertCourse = connection.prepare('INSERT INTO courses (title, price, active) VALUES (?, ?, 1)');
    insertCourse.run('Clean Architecture', 997.0);
    insertCourse.run('Docker', 497.0);
    connection.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)').run();
    connection.prepare("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')").run();
  });
}

module.exports = { openDatabase, initSchema, seedDatabase };
