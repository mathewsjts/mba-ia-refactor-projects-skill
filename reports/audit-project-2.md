================================
RELATÓRIO DE AUDITORIA DE ARQUITETURA
================================
Projeto:  ecommerce-api-legacy
Stack:    JavaScript (Node.js v22.23.1) + Express 4.22.1
Arquivos: 3 analisados | ~180 linhas de código
Data:     2026-10-10

## Resumo
CRITICAL: 5 | HIGH: 8 | MEDIUM: 4 | LOW: 4

| # | Severidade | Anti-pattern | Local principal |
|---|---|---|---|
| F-01 | CRITICAL | Segredos e credenciais hardcoded (AP-02) | src/utils.js:2-6 |
| F-02 | CRITICAL | Exposição de dados de pagamento em log (AP-03) | src/AppManager.js:45 |
| F-03 | CRITICAL | Armazenamento inseguro de senha (AP-04) | src/utils.js:17-23 |
| F-04 | CRITICAL | Operação privilegiada sem controle de acesso (AP-05) | src/AppManager.js:80 |
| F-05 | CRITICAL | God Class / God Module (AP-06) | src/AppManager.js:4-141 |
| F-06 | HIGH | Regra de negócio na camada HTTP (AP-07) | src/AppManager.js:28-78 |
| F-07 | HIGH | Estado global mutável (AP-08) | src/utils.js:9-15 |
| F-08 | HIGH | Operação multi-passo sem transação (AP-09) | src/AppManager.js:50-62 |
| F-09 | HIGH | Configuração de execução insegura (AP-10) | src/AppManager.js:1 |
| F-10 | HIGH | Acoplamento forte sem injeção de dependência (AP-11) | src/AppManager.js:7 |
| F-11 | HIGH | Aninhamento profundo / callback hell (AP-12) | src/AppManager.js:28-78 |
| F-12 | HIGH | Tratamento de erro não centralizado (AP-15) | src/AppManager.js:131-137 |
| F-13 | HIGH | Dependência sem suporte com vulnerabilidade (AP-19) | package.json:11 |
| F-14 | MEDIUM | Query N+1 (AP-13) | src/AppManager.js:89-125 |
| F-15 | MEDIUM | Validação ausente (AP-14) | src/AppManager.js:35 |
| F-16 | MEDIUM | Listagem sem paginação (AP-17) | src/AppManager.js:83 |
| F-17 | MEDIUM | Integridade referencial não garantida (AP-18) | src/AppManager.js:131-137 |
| F-18 | LOW | Logging via console.log (AP-20) | src/utils.js:13 |
| F-19 | LOW | Magic numbers e literais duplicados (AP-21) | src/AppManager.js:46 |
| F-20 | LOW | Código morto (AP-22) | src/utils.js:10 |
| F-21 | LOW | Nomenclatura pobre (AP-23) | src/AppManager.js:29-33 |

## Findings

### F-01 [CRITICAL] Segredos e credenciais hardcoded (AP-02)
Arquivo: src/utils.js:2-6
Ocorrências: src/AppManager.js:45 (chave do gateway vazada em log) | Nenhuma adicional
Descrição: o objeto `config` guarda literais de produção: `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_****"`, `paymentGatewayKey: "pk_live_****"` (prefixo `pk_live_` de chave real) e `smtpUser`. A mesma `paymentGatewayKey` ainda é impressa em `console.log` no checkout (src/AppManager.js:45).
Impacto: qualquer pessoa com acesso ao repositório obtém credenciais de banco, gateway de pagamento e SMTP; rotacionar exige novo deploy; a chave do gateway vaza também nos logs de aplicação.
Recomendação: mover todos os segredos para variáveis de ambiente lidas numa camada de config, com `.env.example` sem valores reais, e remover o log que imprime a chave — Playbook T02.
Contrato: preservado

### F-02 [CRITICAL] Exposição de dados de pagamento em log (AP-03)
Arquivo: src/AppManager.js:45
Ocorrências: Nenhuma adicional
Descrição: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o número completo do cartão recebido (`req.body.card`) em texto claro no log, junto da chave do gateway. Violação direta de PCI-DSS.
Impacto: números de cartão (PAN) e a chave do gateway ficam persistidos nos logs, acessíveis a qualquer um com acesso ao log; vazamento de dados de pagamento.
Recomendação: nunca logar o PAN nem segredos; remover a linha. Se precisar de rastro, logar só os últimos 4 dígitos e nenhum segredo — Playbook T16 (e T02 para a chave).
Contrato: preservado

### F-03 [CRITICAL] Armazenamento inseguro de senha (AP-04)
Arquivo: src/utils.js:17-23
Ocorrências: src/AppManager.js:68 (`badCrypto(p || "123456")`), src/AppManager.js:18 (seed grava senha `'123'` em texto plano) | Nenhuma adicional
Descrição: `badCrypto()` é uma "criptografia" caseira — concatena 10.000 vezes os 2 primeiros caracteres do base64 da senha e trunca em 10 caracteres (sem salt, reversível/colidível). No checkout, quando a senha não vem, usa o default `"123456"` (src/AppManager.js:68). O seed insere a senha `'123'` em texto plano.
Impacto: com um dump do banco as senhas são triviais de recuperar ou colidir; o default silencioso cria contas com senha previsível.
Recomendação: usar hashing forte com salt (`bcrypt`/`scrypt`/`argon2`; `crypto.scrypt` da stdlib evita nova dependência), nunca aplicar default de senha e rejeitar senha ausente na validação — Playbook T05.
Contrato: preservado

### F-04 [CRITICAL] Operação privilegiada sem controle de acesso (AP-05)
Arquivo: src/AppManager.js:80
Ocorrências: src/AppManager.js:131 (DELETE /api/users/:id) | Nenhuma adicional
Descrição: `GET /api/admin/financial-report` (rota administrativa/financeira) devolve faturamento e lista de alunos por curso sem nenhuma autenticação. `DELETE /api/users/:id` apaga usuários sem autenticação. Nenhuma rota verifica token, sessão ou `req.user`.
Impacto: qualquer cliente anônimo lê o relatório financeiro completo e apaga usuários do sistema.
Recomendação: exigir um token administrativo (middleware comparando `X-Admin-Token` com `ADMIN_TOKEN` do ambiente) nas rotas administrativa e destrutiva — Playbook T14.
Contrato: exige BC-01 e BC-02

### F-05 [CRITICAL] God Class / God Module (AP-06)
Arquivo: src/AppManager.js:4-141
Ocorrências: Nenhuma adicional
Descrição: a classe `AppManager` concentra responsabilidades de todas as camadas e de todos os domínios: cria a conexão SQLite (linha 7), define o schema e o seed (`initDb`, linhas 10-23), registra as 3 rotas HTTP (`setupRoutes`, linhas 25-138), implementa regras de negócio (decisão de pagamento, agregação de receita) e simula integração de pagamento. Mistura HTTP + Dados + Regra + Integração sobre users, courses, enrollments, payments e audit_logs.
Impacto: impossível testar em isolamento; qualquer mudança tem raio de impacto global; nenhuma reutilização das regras fora do HTTP.
Recomendação: quebrar em camadas MVC — config, models (repositórios por domínio), services (regras), controllers (fluxo HTTP) e routes — com a composição no entry point — Playbook T03.
Contrato: preservado

### F-06 [HIGH] Regra de negócio na camada HTTP (AP-07)
Arquivo: src/AppManager.js:28-78
Ocorrências: src/AppManager.js:80-129 | Nenhuma adicional
Descrição: o handler de `POST /api/checkout` (linhas 28-78) executa SQL diretamente, decide o status do pagamento, cria usuário/matrícula/pagamento e grava auditoria — tudo inline. O handler de `GET /api/admin/financial-report` (linhas 80-129) faz toda a agregação de receita no próprio handler. Nenhuma regra é delegada a um serviço.
Impacto: regras não reutilizáveis fora do HTTP, impossíveis de testar sem subir o servidor; duplicação iminente quando a mesma lógica for necessária em outro contexto.
Recomendação: extrair `CheckoutService` e `ReportService`; controllers finos só extraem entrada, chamam o serviço e escolhem o status — Playbook T04.
Contrato: preservado

### F-07 [HIGH] Estado global mutável (AP-08)
Arquivo: src/utils.js:9-15
Ocorrências: src/utils.js:10,25 (`totalRevenue` exportado por valor) | Nenhuma adicional
Descrição: `globalCache = {}` é um objeto de módulo mutado em runtime por `logAndCache` (linha 14) e exportado. `totalRevenue` é um primitivo exportado por valor (linhas 10 e 25) — quem importa recebe uma cópia congelada, nunca atualizada.
Impacto: estado compartilhado mutável gera condições de corrida sob concorrência e testes que interferem entre si; o `totalRevenue` exportado é uma armadilha (sempre 0 para quem importa).
Recomendação: remover o cache global; se um cache for necessário, encapsulá-lo numa instância injetada. Remover `totalRevenue` (ver F-20) — Playbook T11.
Contrato: preservado

### F-08 [HIGH] Operação multi-passo sem transação (AP-09)
Arquivo: src/AppManager.js:50-62
Ocorrências: src/AppManager.js:69-72 (criação de usuário fora da transação do checkout) | Nenhuma adicional
Descrição: o checkout grava em sequência `enrollments` (linha 50), `payments` (linha 54) e `audit_logs` (linha 57) em callbacks aninhados, sem `BEGIN`/`COMMIT`/`ROLLBACK`. Se o INSERT de pagamento falhar, a matrícula já criada fica órfã; cada callback de erro só responde ao cliente, sem desfazer o passo anterior.
Impacto: dados inconsistentes em qualquer falha parcial — matrícula sem pagamento, pagamento sem auditoria.
Recomendação: envolver as escritas relacionadas numa transação (`BEGIN`/`COMMIT`, `ROLLBACK` em erro) dentro do service/repositório — Playbook T07.
Contrato: preservado

### F-09 [HIGH] Configuração de execução insegura (AP-10)
Arquivo: src/AppManager.js:1
Ocorrências: src/utils.js:6 (porta literal `3000` sem leitura de ambiente) | Nenhuma adicional
Descrição: `sqlite3.verbose()` (linha 1) ativa logs/stack traces detalhados do driver incondicionalmente. A porta é literal (`port: 3000` em utils.js:6), sem leitura de `process.env.PORT`, impedindo configurar ambientes sem editar código.
Impacto: ambientes não configuráveis sem editar o código; verbosidade de driver ligada em qualquer ambiente.
Recomendação: ler porta e flags de ambiente na camada de config (`process.env.PORT ?? 3000`), ativar `verbose()` só fora de produção — Playbook T02.
Contrato: preservado

### F-10 [HIGH] Acoplamento forte sem injeção de dependência (AP-11)
Arquivo: src/AppManager.js:7
Ocorrências: src/AppManager.js:46 (gateway de pagamento simulado embutido na regra) | Nenhuma adicional
Descrição: a conexão concreta é criada dentro do construtor (`new sqlite3.Database(':memory:')`, linha 7), e a "integração" de pagamento é a expressão `cc.startsWith("4") ? "PAID" : "DENIED"` embutida na regra (linha 46), sem interface de gateway.
Impacto: testes exigem banco real; trocar o banco ou o gateway significa editar a regra de negócio.
Recomendação: criar a conexão no composition root e injetá-la nos repositórios; isolar o pagamento atrás de uma interface de gateway injetada — Playbook T11.
Contrato: preservado

### F-11 [HIGH] Aninhamento profundo / callback hell (AP-12)
Arquivo: src/AppManager.js:28-78
Ocorrências: src/AppManager.js:89-125 (contadores manuais `coursesPending--`/`enrPending--`), src/AppManager.js:26 (`const self = this`) | Nenhuma adicional
Descrição: o checkout aninha 4+ níveis de callbacks (course → user → enrollment → payment → audit). O relatório financeiro usa contadores manuais para saber quando os laços assíncronos terminam, com risco de resposta dupla ou ausente. Vários callbacks ignoram o parâmetro `err` (linhas 92, 104, 106, 133).
Impacto: tratamento de erro incompleto por construção; fluxo difícil de seguir; risco de `res` chamado duas vezes ou nunca.
Recomendação: migrar o acesso a dados para Promises/async-await (`sqlite3` com wrappers `util.promisify` ou métodos próprios), achatando o fluxo — Playbook T06.
Contrato: preservado

### F-12 [HIGH] Tratamento de erro não centralizado (AP-15)
Arquivo: src/AppManager.js:131-137
Ocorrências: src/AppManager.js:38,41,51,55,70,84 (mensagens ad-hoc de erro repetidas) | Nenhuma adicional
Descrição: cada handler trata erro à sua maneira (`res.status(500).send("Erro DB")`, `"Erro Matrícula")`, etc.) e não há middleware de erro `(err, req, res, next)`. No `DELETE /api/users/:id` (linhas 131-137) o parâmetro `err` é ignorado e a rota responde 200 de sucesso mesmo que a remoção falhe — sucesso falso. Severidade escalonada para HIGH por poder retornar sucesso falso.
Impacto: bugs silenciosos, respostas inconsistentes e sucesso reportado sobre operação que pode ter falhado.
Recomendação: centralizar o tratamento num middleware de erro Express; propagar erros via `next(err)` e remover o `catch` que engole — Playbook T10.
Contrato: preservado

### F-13 [HIGH] Dependência sem suporte com vulnerabilidade (AP-19)
Arquivo: package.json:11
Ocorrências: Nenhuma adicional
Descrição: `sqlite3@5.1.7` puxa transitivamente `tar@<7` e `cacache` vulneráveis. `npm audit` reporta 14 vulnerabilidades (2 critical, 8 high), incluindo DoS e file-smuggling no `node-tar`. Severidade escalonada para HIGH pela presença de vulnerabilidades critical/high conhecidas.
Impacto: superfície de ataque via dependências transitivas sem suporte; cadeia de build/instalação vulnerável.
Recomendação: atualizar o driver (`sqlite3@6.x`, que atualiza as transitivas) **somente** se o smoke test comprovar equivalência de contrato; caso contrário manter e registrar o risco. Avaliar alternativa `node:sqlite`/`better-sqlite3` — Playbook T12. Finding pode terminar parcial se a atualização quebrar o contrato.
Contrato: preservado (atualização interna de dependência)

### F-14 [MEDIUM] Query N+1 (AP-13)
Arquivo: src/AppManager.js:89-125
Ocorrências: Nenhuma adicional
Descrição: o relatório financeiro consulta todos os cursos (linha 83) e, para cada curso, consulta `enrollments` (linha 92); para cada enrollment, consulta `users` (linha 104) e `payments` (linha 106). Um relatório com N matrículas dispara 1 + N + 2N consultas.
Impacto: tempo de resposta cresce linearmente com o volume; relatório pode ficar lento ou derrubar o servidor.
Recomendação: substituir por uma única consulta com `JOIN`/`GROUP BY` entre courses, enrollments, users e payments — Playbook T08.
Contrato: preservado

### F-15 [MEDIUM] Validação ausente (AP-14)
Arquivo: src/AppManager.js:35
Ocorrências: Nenhuma adicional
Descrição: o checkout valida apenas presença de `usr`, `eml`, `c_id`, `card` (`if (!u || !e || !cid || !cc)`), sem validar `pwd` (que então cai no default inseguro — ver F-03), tipos ou formato de e-mail/cartão. `c_id` entra direto na query sem conversão/checagem.
Impacto: entradas inválidas podem gerar comportamento inesperado e dados inconsistentes; senha ausente aceita silenciosamente.
Recomendação: centralizar a validação de entrada do checkout numa função/middleware, exigindo os campos obrigatórios e rejeitando senha ausente — Playbook T09.
Contrato: preservado

### F-16 [MEDIUM] Listagem sem paginação (AP-17)
Arquivo: src/AppManager.js:83
Ocorrências: src/AppManager.js:92 | Nenhuma adicional
Descrição: `SELECT * FROM courses` (linha 83) e `SELECT * FROM enrollments WHERE course_id = ?` (linha 92) carregam as tabelas inteiras em memória para montar o relatório, sem `LIMIT`.
Impacto: uso de memória e tempo de resposta crescem com o volume.
Recomendação: paginação é mudança de contrato; aplicar apenas de forma opcional via query params sem alterar a resposta default — Playbook T17. Provável finding parcial para preservar o contrato.
Contrato: preservado (paginação só opcional)

### F-17 [MEDIUM] Integridade referencial não garantida (AP-18)
Arquivo: src/AppManager.js:131-137
Ocorrências: src/AppManager.js:12-16 (DDL sem FOREIGN KEY; sem `PRAGMA foreign_keys = ON`) | Nenhuma adicional
Descrição: `DELETE FROM users WHERE id = ?` remove o usuário sem tratar `enrollments`/`payments` dependentes — a própria resposta admite: "as matrículas e pagamentos ficaram sujos no banco". O schema não declara `FOREIGN KEY` e o SQLite não tem `PRAGMA foreign_keys = ON`.
Impacto: registros órfãos; relatórios com dados de usuários inexistentes.
Recomendação: declarar FKs com `ON DELETE CASCADE` (ou remover dependentes na mesma transação) e ativar `PRAGMA foreign_keys = ON` — Playbook T15.
Contrato: preservado (resposta continua texto 200)

### F-18 [LOW] Logging via console.log (AP-20)
Arquivo: src/utils.js:13
Ocorrências: src/app.js:13 (banner de inicialização) | Nenhuma adicional
Descrição: diagnóstico via `console.log` sem níveis nem estrutura em `logAndCache` (utils.js:13) e no banner de boot (app.js:13). O log de cartão (AppManager.js:45) é tratado em F-02.
Impacto: logs sem controle de nível/destino.
Recomendação: usar um logger simples com níveis, ou ao menos padronizar; manter banner de boot mínimo — Playbook T16.
Contrato: preservado

### F-19 [LOW] Magic numbers e literais duplicados (AP-21)
Arquivo: src/AppManager.js:46
Ocorrências: src/AppManager.js:46 (status `"PAID"`/`"DENIED"` e prefixo `"4"`), src/AppManager.js:68 (`"123456"`), src/utils.js:19 (`10000`, `2`, `10` em badCrypto) | Nenhuma adicional
Descrição: regra de pagamento usa o literal `"4"` e as strings de status `"PAID"`/`"DENIED"` espalhadas; default `"123456"`; constantes mágicas no hashing caseiro.
Impacto: significado de negócio implícito e espalhado, propenso a divergência.
Recomendação: nomear constantes de status e limiares num único lugar — Playbook T16.
Contrato: preservado

### F-20 [LOW] Código morto (AP-22)
Arquivo: src/utils.js:10
Ocorrências: src/utils.js:25 (export de `totalRevenue` e `globalCache`), src/AppManager.js:2 (import de `totalRevenue` nunca usado) | Nenhuma adicional
Descrição: `totalRevenue` é declarado, exportado e importado em AppManager, mas nunca lido nem escrito. `globalCache` é exportado mas ninguém o lê de fora.
Impacto: ruído e exports enganosos (ver F-07).
Recomendação: remover `totalRevenue` e o export de `globalCache`, além do import morto — Playbook T16.
Contrato: preservado

### F-21 [LOW] Nomenclatura pobre (AP-23)
Arquivo: src/AppManager.js:29-33
Ocorrências: src/AppManager.js:4 (classe `AppManager`), src/utils.js:17 (`badCrypto`) | Nenhuma adicional
Descrição: variáveis de uma letra no checkout (`u`, `e`, `p`, `cid`, `cc`); nomes genéricos/enganosos (`AppManager`, `utils`, `badCrypto`). As chaves JSON públicas `usr`/`eml`/`c_id`/`card` são mal nomeadas, mas **não serão renomeadas** (quebraria clientes).
Impacto: intenção pouco comunicada, leitura mais difícil.
Recomendação: renomear apenas identificadores internos para nomes descritivos; preservar as chaves JSON do contrato — Playbook T16.
Contrato: preservado

## APIs deprecated
| API ou dependência | Local | Substituto | Evidência |
|---|---|---|---|
| `sqlite3@5.1.7` → `tar@<7`, `cacache` (transitivas) | package.json:11 | `sqlite3@6.x` / `node:sqlite` / `better-sqlite3` | `npm audit`: 14 vulnerabilidades (2 critical, 8 high) em node-tar/cacache |

Verificação adicional: o boot com `node` não emitiu `DeprecationWarning`/`DEP0` (log `.refactor-arch/boot-antes.log` limpo). `Buffer.from` (utils.js:20) é a API moderna — não é `new Buffer`. Express 4 e `express.json()` estão em uso correto. Nenhuma outra API deprecated detectada pelos padrões do catálogo.

## Breaking Changes propostos
| # | Rota | Mudança no contrato | Finding que justifica |
|---|---|---|---|
| BC-01 | GET /api/admin/financial-report | passa a exigir `X-Admin-Token` válido; sem o header responde 401 em vez de 200. Com o token, resposta idêntica. | F-04 — relatório financeiro exposto a anônimos |
| BC-02 | DELETE /api/users/:id | passa a exigir `X-Admin-Token` válido; sem o header responde 401 em vez de 200. Com o token, resposta idêntica. | F-04 — remoção de usuários exposta a anônimos |

Observação: o smoke test envia `X-Admin-Token: ${ADMIN_TOKEN}` nas duas rotas; na validação da Fase 3 o token será configurado, de modo que as respostas autorizadas permaneçam idênticas ao baseline (sem divergência no diff).

## Plano de refatoração
Estrutura-alvo (MVC em camadas), a partir do monolito `src/AppManager.js`:

```
src/
  config/        config.js            (T02 — porta, segredos via env, flags)
  models/        db.js                (T11 — conexão + migrations/seed, promisificado)
                 userRepository.js    (T01/T05 — acesso a users)
                 courseRepository.js  (T01 — acesso a courses)
                 enrollmentRepository.js (T01/T07 — matrícula + pagamento transacional)
                 reportRepository.js  (T08 — relatório agregado por JOIN)
  services/      checkoutService.js   (T04/T06 — regra de checkout)
                 reportService.js     (T04 — regra do relatório)
                 paymentGateway.js    (T11 — interface de pagamento injetada)
                 passwordHasher.js    (T05 — hashing forte com salt)
  controllers/   checkoutController.js, reportController.js, userController.js (T04)
  middlewares/   auth.js (T14), errorHandler.js (T10)
  routes/        index.js             (T13/T14 — mapeamento de rotas)
  app.js         composition root + entry point (T11)
  utils.js       (esvaziado/removido ao final)
```

Ordem das camadas: config → models → services → controllers → routes → middlewares → composition root → limpeza.

================================
Total: 21 findings
================================
