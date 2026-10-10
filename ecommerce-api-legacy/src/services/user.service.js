// Regra de remoção de usuário (T04). Delega a remoção transacional ao model.
class UserService {
    constructor({ userModel }) {
        this.userModel = userModel;
    }

    async delete(id) {
        return this.userModel.deleteById(id);
    }
}

module.exports = UserService;
