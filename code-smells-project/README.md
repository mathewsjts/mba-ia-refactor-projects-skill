# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração

A configuração vem de variáveis de ambiente (veja `.env.example`). Nenhum segredo fica no código. Principais variáveis:

- `SECRET_KEY` — obrigatória em produção (`APP_ENV=production`); em desenvolvimento é gerada automaticamente por boot.
- `ADMIN_TOKEN` — exigido no header `X-Admin-Token` pelas rotas administrativas (`/admin/reset-db`, `/admin/query`). Sem ele, essas rotas recusam toda requisição.
- `PORT` (default 5000), `APP_HOST` (default `127.0.0.1`), `APP_DEBUG` (default `false`), `DATABASE_PATH` (default `loja.db`), `CORS_ORIGINS`.

## Arquitetura

Estrutura MVC em `src/` (config, models, services, controllers, views, middlewares); `app.py` na raiz é o entry point fino que monta a aplicação via `create_app()`.
