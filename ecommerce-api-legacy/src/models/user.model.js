// Acesso a dados de usuários (T01) com remoção em cascata transacional (T15).
class UserModel {
    constructor({ db, withTransaction }) {
        this.db = db;
        this.withTransaction = withTransaction;
    }

    findByEmail(email) {
        return this.db.get('SELECT id FROM users WHERE email = ?', [email]);
    }

    async create({ name, email, passHash }) {
        const { lastID } = await this.db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passHash],
        );
        return lastID;
    }

    // Remove o usuário e seus dependentes numa única transação, sem deixar órfãos (F-17).
    deleteById(id) {
        return this.withTransaction(async (db) => {
            await db.run(
                'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
                [id],
            );
            await db.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
            const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
            return changes;
        });
    }
}

module.exports = UserModel;
