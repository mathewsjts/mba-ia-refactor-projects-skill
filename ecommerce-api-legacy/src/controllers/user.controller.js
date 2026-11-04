const { parseUserId } = require('./validators');

class UserController {
  constructor(userService) {
    this.userService = userService;
  }

  // O original respondia 200 também para id inexistente; o contrato é mantido.
  remove = async (req, res) => {
    await this.userService.deleteUser(parseUserId(req.params.id));
    res.status(200).send('Usuário deletado.');
  };
}

module.exports = UserController;
