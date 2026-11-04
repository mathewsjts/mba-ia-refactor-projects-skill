class UserModel {
  // O UNIQUE de users.email decide a corrida: requisições paralelas com o mesmo e-mail
  // novo inserem uma vez e as demais reaproveitam o registro. Conta existente nunca
  // tem nome nem senha sobrescritos.
  async findOrCreate(tx, { name, email, passwordHash }) {
    await tx.run(
      'INSERT INTO users (name, email, pass) VALUES (?, ?, ?) ON CONFLICT(email) DO NOTHING',
      [name, email, passwordHash],
    );
    const user = await tx.get('SELECT id FROM users WHERE email = ?', [email]);
    return user.id;
  }

  // Dependentes primeiro: as FOREIGN KEY do schema recusam deixar órfãos.
  async deleteById(tx, userId) {
    await tx.run(
      'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
      [userId],
    );
    await tx.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
    const { changes } = await tx.run('DELETE FROM users WHERE id = ?', [userId]);
    return changes;
  }
}

module.exports = UserModel;
