# code-smells-project

API de E-commerce em Python/Flask, refatorada para MVC em camadas pela skill `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (os usuários de exemplo só são criados fora de produção).

## Configuração

As variáveis de ambiente estão listadas em `.env.example`. Todas têm defaults seguros para desenvolvimento:

| Variável | Default | Uso |
|---|---|---|
| `APP_ENV` | `development` | `production` exige `SECRET_KEY`, fecha o CORS e não cria usuários de exemplo |
| `PORT` | `5000` | porta do servidor |
| `HOST` | `127.0.0.1` | use `0.0.0.0` para expor na rede |
| `DEBUG` | `false` | `1` liga o modo debug (nunca em produção) |
| `SECRET_KEY` | aleatória por processo | assina os tokens de login; obrigatória em produção |
| `CORS_ORIGINS` | `*` fora de produção | lista de origens separadas por vírgula |
| `DATABASE_PATH` | `loja.db` | arquivo SQLite |
| `TOKEN_MAX_AGE` | `86400` | validade do token de login, em segundos |

Exemplo em outra porta: `PORT=5050 python app.py`.

## Autenticação

`POST /login` devolve `dados.token`. Envie-o como `Authorization: Bearer <token>`:

- perfil `admin`: `POST/PUT/DELETE /produtos`, `GET /usuarios`, `GET /pedidos`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas`;
- o próprio usuário ou `admin`: `GET /usuarios/<id>`, `GET /pedidos/usuario/<id>`, `POST /pedidos`;
- públicas: `GET /`, `GET /health`, `GET /produtos`, `GET /produtos/<id>`, `GET /produtos/busca`, `POST /usuarios`, `POST /login`.

As listagens `GET /produtos`, `GET /usuarios` e `GET /pedidos` aceitam paginação opcional por `?limit=&offset=`.

## Comandos de administração

O reset de dados, antes exposto como rota HTTP, agora é um comando de linha (uso local):

```bash
flask --app app reset-db
```

## Estrutura

```
app.py            # entry point (create_app + run)
src/
  app.py          # composition root
  errors.py       # erros de domínio
  config/         # configuração lida do ambiente
  models/         # acesso a dados por domínio, conexão, transação, schema, seed
  services/       # regras de negócio, autenticação e notificações
  controllers/    # fluxo de requisição/resposta + validação
  views/          # rotas e serializers
  middlewares/    # tratamento de erros e autenticação
```
