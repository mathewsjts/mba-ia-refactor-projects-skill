const { parseUserId } = require('./validators');

class UserController {
  constructor({ userService }) {
    this.userService = userService;
  }

  // 200 também para id inexistente, como no original.
  delete = async (req, res) => {
    this.userService.delete(parseUserId(req.params));
    res.send('Usuário deletado');
  };
}

module.exports = UserController;
