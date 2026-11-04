class UserService {
  constructor({ database, userModel }) {
    this.database = database;
    this.userModel = userModel;
  }

  // Pagamentos, matrículas e o usuário saem juntos; uma falha não responde sucesso.
  deleteUser(userId) {
    return this.database.transaction((tx) => this.userModel.deleteById(tx, userId));
  }
}

module.exports = UserService;
