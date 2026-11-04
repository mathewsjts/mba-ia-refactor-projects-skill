class CourseModel {
  constructor(database) {
    this.database = database;
  }

  findActiveById(courseId) {
    return this.database.get(
      'SELECT id, title, price FROM courses WHERE id = ? AND active = 1',
      [courseId],
    );
  }
}

module.exports = CourseModel;
