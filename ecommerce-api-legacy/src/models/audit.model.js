class AuditModel {
  constructor(database) {
    this.db = database.connection;
  }

  log(action) {
    this.db.prepare("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))").run(action);
  }
}

module.exports = AuditModel;
