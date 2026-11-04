class CourseModel {
  constructor(database) {
    this.db = database.connection;
  }

  findActiveById(courseId) {
    return this.db.prepare('SELECT id, title, price FROM courses WHERE id = ? AND active = 1').get(courseId);
  }
}

module.exports = CourseModel;
