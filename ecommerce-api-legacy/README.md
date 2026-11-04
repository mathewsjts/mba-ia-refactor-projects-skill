# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

Requer Node.js 22 ou superior.

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
| `DATABASE_FILE` | Arquivo SQLite; vazio usa banco em memória | `:memory:` |
| `ADMIN_TOKEN` | Valor exigido no header `X-Admin-Token` das rotas administrativas | aleatório (rotas administrativas ficam fechadas) |
| `PAYMENT_GATEWAY_KEY` | Chave do gateway de pagamento | aleatória em desenvolvimento |
| `NODE_ENV` | Com `production`, `ADMIN_TOKEN` e `PAYMENT_GATEWAY_KEY` passam a ser obrigatórias | `development` |

Exemplo: `ADMIN_TOKEN=troque-me npm start`.

## Rotas

| Método | Path | Acesso |
|---|---|---|
| `POST` | `/api/checkout` | Público (checkout de visitante). E-mail novo exige `pwd`. |
| `GET` | `/api/admin/financial-report` | Header `X-Admin-Token`. Aceita paginação opcional `?limit=&offset=` (por curso, `limit` máximo 100). |
| `DELETE` | `/api/users/:id` | Header `X-Admin-Token`. Remove também as matrículas e pagamentos do usuário. |

## Estrutura

```
src/
├── app.js          composition root e entry point
├── errors.js       erros de domínio
├── config/         configuração (ambiente) e logger
├── models/         acesso a dados, schema, seed e transações
├── services/       regras de checkout e relatório, gateway, cache, hash de senha
├── controllers/    entrada/saída HTTP e validação
├── views/          rotas e serialização
└── middlewares/    erros centralizados, autenticação administrativa
```

## Riscos conhecidos

- **Cobrança antes da gravação:** o gateway é chamado depois de todas as validações, mas antes da transação que grava a matrícula. Se a gravação falhar, a cobrança já ocorreu. Mitigação: pagamento `PENDING` antes de cobrar, ou estorno em caso de falha.
- **Checkout com e-mail existente** matricula essa conta sem provar posse dela (não há login).
- **Sem idempotência:** repetir o checkout gera nova matrícula e nova cobrança.
- **`ADMIN_TOKEN` é uma credencial estática e compartilhada:** troque-a periodicamente.
- **Estado em memória:** banco (padrão) e cache zeram a cada restart.
