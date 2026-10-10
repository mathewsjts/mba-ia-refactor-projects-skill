// Controller de usuários (T04).
class UserController {
    constructor(userService) {
        this.userService = userService;
    }

    remove = async (req, res) => {
        await this.userService.delete(req.params.id);
        // Status e tipo de corpo (texto 200) preservados; a mensagem agora
        // reflete a remoção íntegra em cascata (F-17), não os dados órfãos.
        res.status(200).send('Usuário removido com matrículas e pagamentos associados.');
    };
}

module.exports = UserController;
