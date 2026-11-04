# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Organizada em MVC com camada de serviços: `config/` (ambiente), `models/` (entidades e repositórios), `services/` (regras), `controllers/` (requisição → serviço → resposta), `routes/` (views: rotas e serializers) e `middlewares/` (autenticação e erros), montados em `app.py`.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo. **Rode-o antes do primeiro boot**; sem ele, os endpoints devolvem listas vazias.

## Configuração

Variáveis lidas do ambiente ou de um arquivo `.env` (veja `.env.example`):

| Variável | Padrão | Uso |
|---|---|---|
| `PORT` | `5000` | Porta do `python app.py` |
| `APP_HOST` | `127.0.0.1` | Interface de rede; use `0.0.0.0` para aceitar conexões de outras máquinas |
| `APP_DEBUG` | `false` | Debugger do Werkzeug; nunca ligue em produção |
| `APP_ENV` | `development` | `production` exige `SECRET_KEY` e bloqueia CORS sem `CORS_ORIGINS` |
| `SECRET_KEY` | aleatória por boot | Assina os tokens de login. Sem ela, os tokens deixam de valer a cada restart |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI do SQLAlchemy |
| `CORS_ORIGINS` | `*` fora de produção | Origens permitidas, separadas por vírgula |
| `TOKEN_MAX_AGE` | `86400` | Validade do token em segundos |
| `LOG_LEVEL` | `INFO` | Nível do `logging` |

## Autenticação

`POST /login` devolve `token`. Envie-o como `Authorization: Bearer <token>` em:

- `DELETE /tasks/<id>`, `DELETE /categories/<id>`, `DELETE /users/<id>`;
- `PUT /users/<id>`: só o próprio usuário altera a própria conta. Perfil (`role`), estado (`active`) e contas de outras pessoas exigem admin;
- `GET /users`, `GET /users/<id>`, `GET /reports/user/<id>`, que devolvem e-mails.

`POST /users` continua público e grava o perfil `user`; o `role` enviado só vale quando quem chama é admin autenticado.

Primeiro admin sem o seed (produção):

```bash
flask --app app create-admin --name "Admin" --email admin@exemplo.com
```

A paginação é opcional em `GET /tasks`, `/tasks/search`, `/users` e `/categories`: use `?limit=<n>&offset=<n>`, com até 100 itens por página. Sem `limit`, a lista vem completa.
