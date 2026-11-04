class UserService {
  constructor({ userModel }) {
    this.userModel = userModel;
  }

  // Id inválido não corresponde a nenhum usuário: nada a remover, como um id inexistente.
  delete(userId) {
    if (userId === null) return 0;
    return this.userModel.deleteWithDependents(userId);
  }
}

module.exports = UserService;
