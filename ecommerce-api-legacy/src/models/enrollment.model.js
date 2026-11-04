class EnrollmentModel {
  async create(tx, { userId, courseId }) {
    const { lastID } = await tx.run(
      'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
      [userId, courseId],
    );
    return lastID;
  }
}

module.exports = EnrollmentModel;
