// Acesso a dados de cursos (queries parametrizadas — T01).
class CourseModel {
    constructor(db) {
        this.db = db;
    }

    findActiveById(id) {
        return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
    }
}

module.exports = CourseModel;
