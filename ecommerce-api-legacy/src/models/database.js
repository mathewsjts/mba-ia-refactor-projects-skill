const sqlite3 = require('sqlite3');
const { hashPassword } = require('./passwords');

// Adaptador que expõe o driver de callbacks do sqlite3 como Promises (T06),
// achatando o callback hell do código original.
function openDatabase(filename) {
    const raw = new sqlite3.Database(filename);
    return {
        run(sql, params = []) {
            return new Promise((resolve, reject) => {
                raw.run(sql, params, function onRun(err) {
                    if (err) return reject(err);
                    resolve({ lastID: this.lastID, changes: this.changes });
                });
            });
        },
        get(sql, params = []) {
            return new Promise((resolve, reject) => {
                raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
            });
        },
        all(sql, params = []) {
            return new Promise((resolve, reject) => {
                raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
            });
        },
        exec(sql) {
            return new Promise((resolve, reject) => {
                raw.exec(sql, (err) => (err ? reject(err) : resolve()));
            });
        },
        close() {
            return new Promise((resolve, reject) => {
                raw.close((err) => (err ? reject(err) : resolve()));
            });
        },
    };
}

// Serializa transações numa fila única, já que a conexão sqlite3 é compartilhada (T07).
function createTransactionRunner(db) {
    let queue = Promise.resolve();

    return function withTransaction(work) {
        const result = queue.then(async () => {
            await db.run('BEGIN IMMEDIATE');
            try {
                const value = await work(db);
                await db.run('COMMIT');
                return value;
            } catch (err) {
                await db.run('ROLLBACK');
                throw err;
            }
        });
        queue = result.catch(() => {});
        return result;
    };
}

// Schema com FOREIGN KEY e ON DELETE CASCADE para garantir integridade (T15).
async function initSchema(db) {
    await db.exec('PRAGMA foreign_keys = ON');
    await db.exec(`
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
        CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
        CREATE TABLE enrollments (
            id INTEGER PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE
        );
        CREATE TABLE payments (
            id INTEGER PRIMARY KEY,
            enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE CASCADE,
            amount REAL,
            status TEXT
        );
        CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
    `);
}

// Seed automático no boot, idêntico ao original — mas com a senha hasheada (T05).
async function seed(db) {
    const leonanPass = await hashPassword('123');
    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
        'Leonan',
        'leonan@fullcycle.com.br',
        leonanPass,
    ]);
    await db.run(
        "INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)",
    );
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
}

async function initializeDatabase(filename) {
    const db = openDatabase(filename);
    await initSchema(db);
    await seed(db);
    return db;
}

module.exports = { openDatabase, createTransactionRunner, initializeDatabase };
