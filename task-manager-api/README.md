# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, refatorada para MVC com camada de services.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

No macOS a porta 5000 costuma estar ocupada pelo AirPlay Receiver; use outra porta com `PORT=5055 python app.py`.

## Configuração

Lida do ambiente (ou de um arquivo `.env`; veja `.env.example`):

| Variável | Padrão | Uso |
|---|---|---|
| `APP_ENV` | `development` | em `production`, `SECRET_KEY` passa a ser obrigatória |
| `SECRET_KEY` | aleatória por processo | assina os tokens de login. **Defina em qualquer deploy**: sem ela, os tokens deixam de valer a cada restart e não valem entre workers |
| `FLASK_DEBUG` | `false` | nunca ligue fora da máquina local |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | endereço de escuta (antes era `0.0.0.0`) |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI do SQLAlchemy |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | origens liberadas para chamadas do navegador |
| `TOKEN_MAX_AGE_SECONDS` | `86400` | validade do token de login |

## Autenticação e permissões

`POST /login` devolve `token`; envie-o como `Authorization: Bearer <token>`.

| Rotas | Quem pode |
|---|---|
| `POST /login`, `POST /users` (cadastro) | público. No cadastro, `role` só é aceito quando quem chama é admin; senão, a conta nasce `user` |
| `POST/PUT/DELETE /tasks…` | token; dono da task ou admin. Criar ou transferir task para outra conta: só admin |
| `PUT /users/<id>` | token; a própria conta (nome, e-mail, senha) ou admin. `role` e `active`: só admin. Senha: só a própria conta |
| `DELETE /users/<id>` | token; a própria conta ou admin |
| `POST/PUT/DELETE /categories…` | token de admin |
| `GET /users` | token de admin |
| `GET /users/<id>`, `GET /reports/user/<id>` | token; a própria conta ou admin |
| demais `GET` | público |

Senhas novas precisam ter pelo menos 8 caracteres. As senhas antigas em MD5 são regravadas com PBKDF2 no primeiro login.

Primeiro admin em um banco sem seed:

```bash
flask --app app create-admin
```

## Paginação

`GET /tasks`, `/tasks/search`, `/users` e `/categories` aceitam `?page=<n>&per_page=<n>` (máximo de 100 por página). Sem esses parâmetros, a lista continua completa.

## Estrutura

```
app.py              composition root (create_app) e entry point
config/             configuração lida do ambiente
models/             entidades e repositórios (acesso a dados)
services/           regras de negócio e autorização
controllers/        fluxo requisição → service → resposta, validação de entrada
routes/             views: mapeamento de rotas e serializers
middlewares/        autenticação e tratamento central de erros
errors.py           erros de domínio
constants.py        constantes do domínio
```

## Riscos conhecidos

- A `SECRET_KEY` e a senha SMTP antigas continuam no histórico git: troque-as.
- Contas que nunca mais fizerem login continuam com hash MD5 até redefinirem a senha.
- Nomes de usuários continuam públicos em `GET /tasks` e `GET /reports/summary`.
- python-dotenv 1.2.1 tem a CVE-2026-28684 (em `set_key`/`unset_key`, que o projeto não usa); a correção exige Python ≥ 3.10.
- O runtime Python 3.9 está sem suporte; migre para Python ≥ 3.11.
- O token não é revogado ao trocar a senha (vale até expirar); conta apagada ou desativada perde o acesso na hora.
- O login não limita tentativas.
- Bancos criados antes da refatoração não ganham `ON DELETE` no DDL; a cascata do ORM cobre a API.
