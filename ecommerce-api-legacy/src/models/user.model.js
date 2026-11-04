class UserModel {
  constructor(database) {
    this.database = database;
    this.db = database.connection;
  }

  findByEmail(email) {
    return this.db.prepare('SELECT id FROM users WHERE email = ?').get(email);
  }

  // Unicidade garantida pelo UNIQUE de users.email: insere só se o e-mail não existe
  // e devolve o id do registro, novo ou já existente. Sem hash, não cria conta.
  findOrCreate({ name, email, passwordHash }) {
    if (passwordHash) {
      this.db
        .prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?) ON CONFLICT(email) DO NOTHING')
        .run(name, email, passwordHash);
    }
    const row = this.findByEmail(email);
    return row ? row.id : undefined;
  }

  // Remove o usuário com matrículas e pagamentos, filhas antes das mães, numa transação.
  deleteWithDependents(userId) {
    return this.database.transaction(() => {
      this.db
        .prepare('DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)')
        .run(userId);
      this.db.prepare('DELETE FROM enrollments WHERE user_id = ?').run(userId);
      return this.db.prepare('DELETE FROM users WHERE id = ?').run(userId).changes;
    });
  }
}

module.exports = UserModel;
