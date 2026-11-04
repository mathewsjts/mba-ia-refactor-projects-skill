class EnrollmentModel {
  constructor(database) {
    this.db = database.connection;
  }

  create({ userId, courseId }) {
    const { lastInsertRowid } = this.db
      .prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)')
      .run(userId, courseId);
    return Number(lastInsertRowid);
  }
}

module.exports = EnrollmentModel;
