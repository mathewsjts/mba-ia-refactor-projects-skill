# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Configuração

Variáveis de ambiente (nomes em `.env.example`):

| Variável | Uso | Padrão |
|---|---|---|
| `PORT` | Porta HTTP | `3000` |
| `ADMIN_TOKEN` | Valor exigido no header `X-Admin-Token` pelas rotas administrativas | vazio: as rotas administrativas respondem `401` |
| `PAYMENT_GATEWAY_KEY` | Chave do gateway de pagamento | obrigatória com `NODE_ENV=production`; em desenvolvimento, chave efêmera |
| `DATABASE_FILE` | Arquivo SQLite | `:memory:` |
| `SEED_USER_PASSWORD` | Senha do usuário de exemplo do seed (gravada com hash) | vazio: usuário criado sem senha |
| `SQLITE_VERBOSE` | Registra cada instrução SQL no log de nível `debug` (`true`) | desligado |
| `LOG_LEVEL` | `error`, `warn`, `info` ou `debug` | `info` |

Exemplo:

```bash
ADMIN_TOKEN=troque-este-valor npm start
```

## Rotas administrativas

`GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem o header `X-Admin-Token` com o valor de `ADMIN_TOKEN`. O relatório aceita paginação opcional por cursos com `?limit=&offset=`; sem esses parâmetros, retorna todos os cursos.
