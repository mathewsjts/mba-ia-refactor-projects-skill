================================
RELATÓRIO DE AUDITORIA DE ARQUITETURA
================================
Projeto:  ecommerce-api-legacy
Stack:    JavaScript (Node.js 22.23.1) + Express 4.22.1
Arquivos: 3 analisados | ~180 linhas de código
Data:     2026-11-04

## Resumo
CRITICAL: 5 | HIGH: 8 | MEDIUM: 3 | LOW: 4

| # | Severidade | Anti-pattern | Local principal |
|---|---|---|---|
| F-01 | CRITICAL | Segredos e credenciais hardcoded (AP-02) | src/utils.js:1-7 |
| F-02 | CRITICAL | Exposição de dados sensíveis (AP-03) | src/AppManager.js:45 |
| F-03 | CRITICAL | Armazenamento inseguro de senha (AP-04) | src/utils.js:17-23 |
| F-04 | CRITICAL | Operação privilegiada sem controle de acesso (AP-05) | src/AppManager.js:80-129 |
| F-05 | CRITICAL | God Class / God Module (AP-06) | src/AppManager.js:4-139 |
| F-06 | HIGH | Estado global mutável (AP-08) | src/utils.js:9-15 |
| F-07 | HIGH | Operação multi-passo sem transação (AP-09) | src/AppManager.js:40-75 |
| F-08 | HIGH | Configuração de execução insegura (AP-10) | src/AppManager.js:1 |
| F-09 | HIGH | Acoplamento forte sem injeção de dependência (AP-11) | src/AppManager.js:7 |
| F-10 | HIGH | Aninhamento profundo / callback hell (AP-12) | src/AppManager.js:37-77 |
| F-11 | HIGH | Validação ausente (AP-14) | src/AppManager.js:29-35 |
| F-12 | HIGH | Tratamento de erro não centralizado (AP-15) | src/AppManager.js:38-84 |
| F-13 | HIGH | Dependências deprecated e vulneráveis (AP-19) | package.json:10-11 |
| F-14 | MEDIUM | Query N+1 (AP-13) | src/AppManager.js:89-127 |
| F-15 | MEDIUM | Listagem sem paginação (AP-17) | src/AppManager.js:83 |
| F-16 | MEDIUM | Integridade referencial não garantida (AP-18) | src/AppManager.js:131-137 |
| F-17 | LOW | Logging via console.log (AP-20) | src/app.js:13 |
| F-18 | LOW | Magic numbers e literais duplicados (AP-21) | src/AppManager.js:46 |
| F-19 | LOW | Código morto (AP-22) | src/AppManager.js:2 |
| F-20 | LOW | Nomenclatura pobre e código verboso (AP-23) | src/AppManager.js:26-33 |

## Findings

### F-01 [CRITICAL] Segredos e credenciais hardcoded (AP-02)
Arquivo: src/utils.js:1-7
Ocorrências: src/AppManager.js:45 (chave do gateway impressa no log a cada checkout)
Descrição: o objeto `config` versionado traz `dbUser: "admin_master"` (linha 2), `dbPass: "senha_super_****"` (linha 3), `paymentGatewayKey: "pk_live_****"` (linha 4, prefixo de chave de produção) e `smtpUser` (linha 5). A chave do gateway ainda vaza no log em `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` (AppManager.js:45). `dbUser`, `dbPass` e `smtpUser` nunca são lidos (ver F-19).
Impacto: qualquer pessoa com acesso ao repositório ou aos logs obtém a chave live do gateway e a senha do banco; rotacionar exige novo deploy.
Recomendação: criar `src/config/index.js` que lê o ambiente uma vez (`PAYMENT_GATEWAY_KEY`, `ADMIN_TOKEN`, `PORT`, `DATABASE_FILE`), obrigatório em produção e sem fallback literal; `.env.example` só com os nomes; remover `dbUser`/`dbPass`/`smtpUser`, que não são usados; injetar a chave no gateway sem imprimi-la — Playbook T02 (e T16 para o código morto).
Contrato: preservado

### F-02 [CRITICAL] Exposição de dados sensíveis (AP-03)
Arquivo: src/AppManager.js:45
Ocorrências: Nenhuma adicional
Descrição: o handler de `POST /api/checkout` imprime o número completo do cartão (`Processando cartão ${cc} ...`) em todo checkout, inclusive nos recusados — confirmado em `.refactor-arch/boot-antes.log` (`Processando cartão 4111222233334444 ...`). A mesma linha vaza a chave do gateway (F-01).
Impacto: PAN completo em log viola PCI-DSS; qualquer acesso ao log (agregador, suporte, backup) expõe cartões de clientes.
Recomendação: o gateway de pagamento (service injetado) registra apenas um evento sem dado sensível (no máximo os 4 últimos dígitos) pelo logger central; nenhum log com `card` ou chave — Playbook T13 (passo 3, campos sensíveis fora da saída) e T16 (logger).
Contrato: preservado

### F-03 [CRITICAL] Armazenamento inseguro de senha (AP-04)
Arquivo: src/utils.js:17-23
Ocorrências: src/AppManager.js:68 (`badCrypto(p || "123456")` — senha padrão quando `pwd` não vem), src/AppManager.js:18 (seed grava a senha `'123'` em texto plano)
Descrição: `badCrypto` concatena 10.000 vezes os 2 primeiros caracteres do base64 da senha e devolve os 10 primeiros: o "hash" é só o prefixo base64 repetido, sem salt, e colide para toda senha que começa com o mesmo caractere. Conta nova sem `pwd` recebe a senha conhecida `"123456"`. O seed grava `'123'` sem hash.
Impacto: com um dump do banco a senha (ou um equivalente) é recuperada de imediato; contas criadas sem `pwd` têm senha pública.
Recomendação: `hashPassword`/`verifyPassword` com `crypto.scrypt` nativo e salt aleatório num único módulo; conta nova sem `pwd` vira erro de validação (`400 Bad Request`, BC-03); o seed grava o hash. Senhas legadas: o banco é em memória e recriado no boot, então não há hash antigo a migrar — Playbook T05.
Contrato: exige BC-03

### F-04 [CRITICAL] Operação privilegiada sem controle de acesso (AP-05)
Arquivo: src/AppManager.js:80-129
Ocorrências: src/AppManager.js:131-137
Descrição: `GET /api/admin/financial-report` devolve a receita por curso e o nome e o valor pago de cada aluno a qualquer cliente anônimo (dados financeiros e pessoais — também AP-03 HIGH). `DELETE /api/users/:id` apaga qualquer usuário sem nenhuma credencial. O projeto não tem login (nenhuma rota emite token). Classificação rota a rota pela tabela da T14:

| Rota | Linha da T14 | Ação |
|---|---|---|
| `GET /api/admin/financial-report` | Leitura ou gestão administrativa sem login no projeto | **Proteger** com `X-Admin-Token` lido da configuração (`ADMIN_TOKEN`), falha fechada |
| `DELETE /api/users/:id` | Leitura ou gestão administrativa sem login no projeto (remoção de usuários) | **Proteger** com `X-Admin-Token`, falha fechada |
| `POST /api/checkout` | Rota de criação que aceita `password` (`pwd`) | **Pública, declarada**: é o checkout de visitante num projeto sem login, que faz as vezes de cadastro público. O `pwd` só é gravado ao **criar** a conta; para e-mail já existente ele é ignorado e nunca sobrescreve a senha de outra conta. Não há campo de perfil (`role`) nem de estado (`active`) no corpo. |

Nenhuma rota executa SQL/código do cliente nem destrói dados em massa: não há situação "Remover".
Impacto: qualquer anônimo lê o faturamento e a lista de alunos pagantes e apaga contas arbitrárias.
Recomendação: middleware `requireAdmin(config)` com comparação em tempo constante, aplicado às duas rotas administrativas na camada de rotas; sem `ADMIN_TOKEN` configurado as rotas recusam tudo — Playbook T14.
Contrato: exige BC-01, BC-02

### F-05 [CRITICAL] God Class / God Module (AP-06)
Arquivo: src/AppManager.js:4-139
Ocorrências: src/app.js:8-10 (único consumidor)
Descrição: a classe `AppManager` abre a conexão (linha 7), cria schema e seed (10-23), registra as três rotas (25-138), executa SQL de cinco tabelas (users, courses, enrollments, payments, audit_logs), decide o pagamento (`cc.startsWith("4")`, linha 46), grava auditoria (57) e agrega o relatório financeiro (89-127). O handler de checkout tem 51 linhas (28-78) com SQL, regra de pagamento, criação de usuário e auditoria — regra de negócio na camada HTTP (AP-07), consolidada aqui por ter a mesma causa raiz.
Impacto: nada pode ser testado isoladamente; qualquer mudança (trocar o gateway, o banco ou uma mensagem) mexe na mesma classe.
Recomendação: separar em `models/` por domínio (user, course, enrollment, payment, audit, report) com conexão e schema em `models/database.js`; regras de checkout e de relatório em `services/`; controllers finos; rotas em `views/routes.js` — Playbook T03 e T04.
Contrato: preservado

### F-06 [HIGH] Estado global mutável (AP-08)
Arquivo: src/utils.js:9-15
Ocorrências: src/utils.js:25 (`globalCache` e `totalRevenue` exportados), src/AppManager.js:59 (`logAndCache` grava no cache global)
Descrição: `let globalCache = {}` é mutado por `logAndCache` a cada checkout; `let totalRevenue = 0` é exportado por valor (quem importa recebe uma cópia congelada) e nunca é atualizado nem lido.
Impacto: estado compartilhado por todo o processo, perdido no restart e divergente entre workers; testes interferem entre si.
Recomendação: `InMemoryCache` criado no composition root e injetado no service de checkout; remover `totalRevenue` (ninguém lê o valor) — Playbook T11.
Contrato: preservado

### F-07 [HIGH] Operação multi-passo sem transação (AP-09)
Arquivo: src/AppManager.js:40-75
Ocorrências: src/AppManager.js:12 (`users.email` sem `UNIQUE`)
Descrição: o checkout grava até quatro linhas em callbacks encadeados — `INSERT INTO users` (69), `INSERT INTO enrollments` (50), `INSERT INTO payments` (54) e `INSERT INTO audit_logs` (57) — sem `BEGIN`/`COMMIT`. Uma falha no pagamento responde `500 "Erro Pagamento"` e deixa a matrícula gravada sem pagamento; o usuário é criado (69) antes de a decisão de pagamento (46-48) recusar a compra. A unicidade do e-mail é só "buscar (40) e, se não existir, inserir (69)", sem `UNIQUE` no schema: dois checkouts paralelos com o mesmo e-mail novo criam dois usuários.
Impacto: matrícula sem pagamento, usuários duplicados e contas criadas para compras recusadas. A severidade padrão (HIGH) já reflete o dano a dados; não foi escalonada.
Recomendação: validar tudo e decidir o pagamento antes da primeira escrita; gravar usuário, matrícula, pagamento e auditoria numa única transação com rollback; `UNIQUE` em `users.email` com `INSERT ... ON CONFLICT(email) DO NOTHING` seguido de `SELECT` dentro da transação. Não há saldo/estoque neste domínio (cursos não têm vagas): a escrita condicional da T07 passo 3 se aplica só à unicidade — Playbook T07.
Contrato: preservado

### F-08 [HIGH] Configuração de execução insegura (AP-10)
Arquivo: src/AppManager.js:1
Ocorrências: src/utils.js:6 (`port: 3000` literal, sem leitura de ambiente)
Descrição: `require('sqlite3').verbose()` ativa stack traces longos do driver incondicionalmente; a porta é literal e não aceita override, o que impede configurar ambientes sem editar código.
Impacto: diagnósticos internos sempre ativos em produção; deploy em outra porta exige alterar o código.
Recomendação: porta lida de `PORT` com o mesmo default `3000`; driver sem modo verbose (a troca de driver de F-13 elimina a chamada) — Playbook T02.
Contrato: preservado

### F-09 [HIGH] Acoplamento forte sem injeção de dependência (AP-11)
Arquivo: src/AppManager.js:7
Ocorrências: src/AppManager.js:46 (gateway simulado embutido na regra), src/AppManager.js:2 (import direto de `utils` concreto)
Descrição: o construtor instancia `new sqlite3.Database(':memory:')`; a "integração" de pagamento é `let status = cc.startsWith("4") ? "PAID" : "DENIED"` dentro do handler, sem interface de gateway.
Impacto: impossível testar sem banco real ou trocar o gateway sem editar a regra de checkout.
Recomendação: composition root em `src/app.js` cria banco, models, `FakePaymentGateway`, cache e services e os injeta pelo construtor — Playbook T11 (e T04 passo 4 para o gateway).
Contrato: preservado

### F-10 [HIGH] Aninhamento profundo / callback hell (AP-12)
Arquivo: src/AppManager.js:37-77
Ocorrências: src/AppManager.js:26 (`const self = this`), src/AppManager.js:86-121 (contadores manuais `coursesPending--`/`enrPending--`), erros ignorados em src/AppManager.js:57, 92, 104, 106, 133
Descrição: o checkout tem cinco níveis de callbacks (`db.get` → `db.get` → `db.run` → `db.run` → `db.run`); o relatório usa contadores manuais para saber quando responder. O callback da linha 92 ignora `err` e lê `enrollments.length` — se a consulta falhar, o `TypeError` é lançado fora de qualquer handler e derruba o processo; o mesmo vale para qualquer exceção dentro dos callbacks (ver F-11).
Impacto: erros ignorados por construção, risco de requisição sem resposta e de queda do processo.
Recomendação: fluxo linear de cima para baixo; com o driver síncrono de F-13 os callbacks desaparecem, e os laços do relatório viram uma única consulta (F-14) — Playbook T06.
Contrato: preservado

### F-11 [HIGH] Validação ausente (AP-14)
Arquivo: src/AppManager.js:29-35
Ocorrências: src/AppManager.js:46 (`cc.startsWith`), src/AppManager.js:68 (`badCrypto(p ...)` → `Buffer.from`), src/AppManager.js:132 (`id` do path sem checagem)
Descrição: a única validação é a truthiness de `usr`, `eml`, `c_id` e `card`. Verificado contra o original: `{"card": 4111222233334444}` (número) lança `TypeError: cc.startsWith is not a function` e `{"pwd": 123456}` lança `ERR_INVALID_ARG_TYPE` dentro do callback do sqlite3 — **o processo cai** e a requisição fica sem resposta (status `000`). `usr`/`eml` numéricos e `c_id: true` respondem 200 e gravam dado inválido. Escalonado de MEDIUM para HIGH (regra 1: alcançável por requisição anônima, derruba a API para todos).
Impacto: negação de serviço com uma única requisição anônima; dados inválidos no banco.
Recomendação: `parseCheckout` em `controllers/validators.js` traduz as chaves públicas e valida tipos, mantendo a mensagem `Bad Request`; `c_id` em texto ou número que não seja id válido segue como "não encontrado" (404), como no original; `id` do path que não é inteiro válido responde como id inexistente — Playbook T09.
Contrato: exige BC-04

### F-12 [HIGH] Tratamento de erro não centralizado (AP-15)
Arquivo: src/AppManager.js:38-84
Ocorrências: src/AppManager.js:57-60 e 133-135 (erros engolidos com resposta de sucesso), src/app.js:5-10 (nenhum middleware de erro)
Descrição: cada callback responde à sua maneira (`"Erro DB"`, `"Erro Matrícula"`, `"Erro Pagamento"`, `"Erro ao criar usuário"`); a falha ao gravar auditoria (57) é ignorada e o cliente recebe `Sucesso`; `DELETE /api/users/:id` ignora `err` e responde 200 mesmo se a remoção falhar (133-135). Não há middleware `(err, req, res, next)`. Escalonado para HIGH pelo próprio catálogo: erro engolido retorna sucesso falso.
Impacto: falhas silenciosas e respostas de sucesso falsas; formato de erro inconsistente.
Recomendação: erros de domínio (`errors.js`), `asyncHandler` e um middleware central que responde em texto, como o projeto já faz, e devolve mensagem genérica em erro inesperado — Playbook T10.
Contrato: preservado

### F-13 [HIGH] Dependências deprecated e vulneráveis (AP-19)
Arquivo: package.json:10-11
Ocorrências: package-lock.json (árvore transitiva)
Descrição: `sqlite3@5.1.7` puxa `inflight@1.0.6`, `glob@7.2.3`, `rimraf@3.0.2`, `tar@6.2.1`, `npmlog@6.0.2`, `gauge@4.0.4`, `are-we-there-yet@3.0.1`, `prebuild-install@7.1.3` e `@npmcli/move-file@1.1.2`, todos com `npm warn deprecated` em `.refactor-arch/install.log`; `npm audit` aponta `tar` com vulnerabilidade **critical** via `sqlite3 → node-gyp`. `express@4.22.1` traz `proxy-addr` (critical), `body-parser` e `path-to-regexp` (high) e `qs` (moderate), corrigidos em `express@4.22.3`. Escalonado para HIGH: dependência deprecated com vulnerabilidade critical conhecida.
Impacto: superfície de ataque conhecida na cadeia de instalação e no parser HTTP.
Recomendação: trocar `sqlite3` por `better-sqlite3@^13.0.3` (só depende de `node-addon-api`; API síncrona com transações nativas, o que também resolve F-07 e F-10) e atualizar `express` para `^4.22.3`. Conferido num manifesto de teste: `npm audit` → `found 0 vulnerabilities`, nenhum `deprecated`. A alternativa `sqlite3@6.0.1` ainda puxa `prebuild-install` (deprecated) e `node-gyp` — Playbook T12.
Contrato: preservado (a troca só entra se o smoke test ficar idêntico)

### F-14 [MEDIUM] Query N+1 (AP-13)
Arquivo: src/AppManager.js:89-127
Ocorrências: src/AppManager.js:92, 104, 106
Descrição: para cada curso, `SELECT * FROM enrollments WHERE course_id = ?`; para cada matrícula, `SELECT name, email FROM users` e `SELECT amount, status FROM payments` — 1 + C + 2·M consultas.
Impacto: o relatório cresce linearmente em consultas com o número de matrículas.
Recomendação: uma consulta com `LEFT JOIN` de courses → enrollments → users → payments, `ORDER BY c.id, e.id`, preservando os fallbacks `'Unknown'` e `0` e a soma de receita só para `PAID` — Playbook T08.
Contrato: preservado

### F-15 [MEDIUM] Listagem sem paginação (AP-17)
Arquivo: src/AppManager.js:83
Ocorrências: src/AppManager.js:92
Descrição: o relatório carrega todos os cursos (`SELECT * FROM courses`) e todas as matrículas em memória.
Impacto: memória e tempo de resposta crescem com o volume.
Recomendação: paginação **opcional** por curso (`?limit=&offset=`); sem parâmetros, a resposta é idêntica à atual — Playbook T17.
Contrato: preservado

### F-16 [MEDIUM] Integridade referencial não garantida (AP-18)
Arquivo: src/AppManager.js:131-137
Ocorrências: src/AppManager.js:14-15 (`user_id`, `course_id`, `enrollment_id` sem `FOREIGN KEY`)
Descrição: `DELETE FROM users WHERE id = ?` não trata matrículas nem pagamentos; a própria resposta admite: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."`. O relatório passa a listar esses alunos como `'Unknown'`.
Impacto: registros órfãos e relatório financeiro com alunos inexistentes.
Recomendação: remoção em cascata explícita (payments → enrollments → users) numa transação, dentro do model; `FOREIGN KEY ... ON DELETE CASCADE` no schema; `200` mantido para id inexistente (como o original), com recomendação de `404` registrada aqui — Playbook T15.
Contrato: preservado no status e no tipo de corpo; o texto que descrevia o bug muda (declarado em BC-02)

### F-17 [LOW] Logging via console.log (AP-20)
Arquivo: src/app.js:13
Ocorrências: src/utils.js:13 (`[LOG] Salvando no cache`); a ocorrência de src/AppManager.js:45 é tratada em F-02
Descrição: banner e eventos de cache via `console.log`, sem nível nem estrutura.
Impacto: logs sem nível, difíceis de filtrar e de rotear.
Recomendação: `config/logger.js` como ponto único (JSON com nível) — Playbook T16.
Contrato: preservado

### F-18 [LOW] Magic numbers e literais duplicados (AP-21)
Arquivo: src/AppManager.js:46
Ocorrências: src/AppManager.js:48, 108 (`'PAID'`/`'DENIED'` repetidos), src/utils.js:19 (`10000`), src/AppManager.js:68 (`"123456"`)
Descrição: o prefixo de cartão aprovado `"4"` e os status de pagamento são literais espalhados; o número de iterações do "hash" é literal.
Impacto: regra de aprovação e status divergem facilmente entre o checkout e o relatório.
Recomendação: constantes nomeadas (`PAYMENT_STATUS.PAID/DENIED`, `APPROVED_CARD_PREFIX`) num único módulo — Playbook T16.
Contrato: preservado

### F-19 [LOW] Código morto (AP-22)
Arquivo: src/AppManager.js:2
Ocorrências: src/utils.js:2, 3, 5 (`dbUser`, `dbPass`, `smtpUser` nunca lidos), src/utils.js:10, 25 (`totalRevenue` e `globalCache` exportados e nunca lidos)
Descrição: `totalRevenue` é importado em AppManager.js:2 e não é usado; três chaves de configuração nunca são lidas.
Impacto: ruído e falsa impressão de que existem integrações com banco remoto e SMTP.
Recomendação: remover — Playbook T16.
Contrato: preservado

### F-20 [LOW] Nomenclatura pobre e código verboso (AP-23)
Arquivo: src/AppManager.js:26-33
Ocorrências: src/AppManager.js:4 (`AppManager`), src/utils.js:17 (`badCrypto`), src/utils.js:1 (módulo genérico `utils`)
Descrição: `u`, `e`, `p`, `cid`, `cc` e `self`; nomes genéricos para a classe e o módulo. As chaves públicas `usr`, `eml`, `pwd`, `c_id` também são pobres, mas fazem parte do contrato.
Impacto: leitura e manutenção mais lentas.
Recomendação: renomear só identificadores internos (`name`, `email`, `password`, `courseId`, `card`); traduzir as chaves públicas num único ponto (validador), **sem** renomeá-las — Playbook T16.
Contrato: preservado

## APIs deprecated
| API ou dependência | Local | Substituto | Evidência |
|---|---|---|---|
| `sqlite3@5.1.7` → transitivas `inflight@1.0.6`, `glob@7.2.3`, `rimraf@3.0.2`, `tar@6.2.1`, `npmlog@6.0.2`, `gauge@4.0.4`, `are-we-there-yet@3.0.1`, `prebuild-install@7.1.3`, `@npmcli/move-file@1.1.2` | package.json:11 | `better-sqlite3@^13.0.3` | `npm warn deprecated` em `.refactor-arch/install.log`; `npm audit`: `tar` critical via `sqlite3 → node-gyp`; `npm ls` confirma `sqlite3` como dependência direta responsável |
| `express@4.22.1` (`proxy-addr` critical, `body-parser` ≤1.20.8 e `path-to-regexp` <0.1.13 high, `qs` moderate) | package.json:10 | `express@^4.22.3` | `npm audit` (fix disponível sem versão maior); manifesto de teste com `express@4.22.3` + `better-sqlite3@13.0.3` → `found 0 vulnerabilities` |

Busca pelos padrões de código do catálogo (`new Buffer(`, `url.parse(`, `fs.exists(`, `util.is*`, `crypto.createCipher(`, `app.del(`, `req.param(`, `res.send(<status>)`, `bodyParser`): nenhuma ocorrência — `Buffer.from` e `express.json()` já são os substitutos modernos.

## Breaking Changes propostos
| # | Rota | Mudança no contrato | Finding que justifica |
|---|---|---|---|
| BC-01 | GET /api/admin/financial-report | passa a exigir `X-Admin-Token` igual a `ADMIN_TOKEN`; sem ele ou com valor errado → `401` texto `Não autorizado` (antes `200` para qualquer cliente). Com o token, corpo e status inalterados | F-04 — dados financeiros e pessoais expostos a anônimos |
| BC-02 | DELETE /api/users/:id | passa a exigir `X-Admin-Token`; sem ele → `401` texto `Não autorizado`. Com o token continua `200` texto (inclusive para id inexistente), mas o texto passa de `Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.` para `Usuário deletado` | F-04 — remoção de contas por anônimos; F-16 — o texto descrevia o bug corrigido |
| BC-03 | POST /api/checkout | e-mail **novo** sem `pwd` → `400` texto `Bad Request` (antes `200`, conta criada com a senha padrão `123456`). Para e-mail já cadastrado o `pwd` continua opcional | F-03 — senha padrão conhecida |
| BC-04 | POST /api/checkout | `usr`, `eml`, `pwd` ou `card` que não sejam texto, ou `c_id` booleano/objeto/lista → `400` texto `Bad Request` (antes: `pwd`/`card` não-texto derrubavam o processo sem resposta; `usr`/`eml` numéricos e `c_id: true` respondiam `200` gravando dado inválido) | F-11 — negação de serviço por requisição anônima |

## Riscos residuais
| # | Risco | Finding | Por que permanece | Mitigação recomendada |
|---|---|---|---|---|
| R-01 | Cliente cobrado sem matrícula: a cobrança no gateway acontece depois de todas as validações, mas antes da transação; se a transação falhar, a cobrança já foi feita | F-07 | Efeito externo irreversível não participa da transação do SQLite (T07, passo 2) | Registrar um pagamento `PENDING` antes de cobrar e confirmá-lo depois, ou estornar no `catch` da transação; chave de idempotência no gateway real |
| R-02 | Checkout com o e-mail de uma conta existente matricula essa conta sem provar posse dela (o `pwd` é ignorado) | F-04 | O projeto não tem login; exigir senha no checkout de conta existente mudaria o contrato de um fluxo declarado público | Introduzir login/verificação de e-mail e exigir autenticação para comprar em nome de conta existente |
| R-03 | Requisição repetida gera duas matrículas e duas cobranças para o mesmo curso | F-07 | O original permite matrícula duplicada (o seed já matricula o usuário 1 no curso 1 e o checkout aceita de novo); impedir mudaria o contrato | `UNIQUE(user_id, course_id)` com resposta de conflito, ou chave de idempotência por checkout |
| R-04 | `ADMIN_TOKEN` é uma credencial compartilhada e estática, sem identidade nem rotação; vazada, dá acesso total às duas rotas administrativas | F-04 | Sem login no projeto, a T14 prevê credencial administrativa lida da configuração | Login com perfil admin e token assinado com expiração; rotação periódica do `ADMIN_TOKEN` |
| R-05 | Banco e cache em memória: dados zeram a cada restart e não são compartilhados entre processos | F-06 | Comportamento documentado do projeto (README) e base do baseline | Configurar `DATABASE_FILE` com um arquivo e trocar o cache por um serviço externo antes de escalar |

## Plano de refatoração
```
src/
├── app.js                        composition root + entry point (node src/app.js)
├── errors.js                     erros de domínio com status
├── config/
│   ├── index.js                  T02 — PORT, ADMIN_TOKEN, PAYMENT_GATEWAY_KEY, DATABASE_FILE
│   └── logger.js                 T16 — logger central
├── models/
│   ├── database.js               T03/T15 — conexão better-sqlite3, schema (UNIQUE, FK), seed, transação
│   ├── user.model.js             T07/T15 — upsert por e-mail, remoção em cascata
│   ├── course.model.js
│   ├── enrollment.model.js
│   ├── payment.model.js
│   ├── audit.model.js
│   └── report.model.js           T08/T17 — JOIN único, paginação opcional
├── services/
│   ├── password.js               T05 — scrypt + salt
│   ├── payment.gateway.js        T04/T11 — FakePaymentGateway injetado, sem PAN no log
│   ├── cache.js                  T11 — InMemoryCache
│   ├── checkout.service.js       T04/T06/T07 — validações → cobrança → transação
│   ├── report.service.js         T04 — agregação da receita
│   └── user.service.js
├── controllers/
│   ├── validators.js             T09 — parseCheckout, ids, paginação
│   ├── checkout.controller.js
│   ├── report.controller.js
│   └── user.controller.js
├── views/
│   ├── routes.js                 T14 — rotas; requireAdmin nas administrativas
│   └── serializers.js            T13 — saída do relatório com campos explícitos
└── middlewares/
    ├── asyncHandler.js           T10
    ├── errorHandler.js           T10 — erro em texto, como o projeto já responde
    └── requireAdmin.js           T14 — X-Admin-Token, tempo constante, falha fechada
```
Ordem: config (T02) → models (T03, T05, T07, T08, T12, T15, T17) → services (T04, T05, T06, T11) → controllers (T04, T09) → views/rotas (T13, T14, T17) → middlewares (T10) → composition root (T11) → limpeza (T16: remover `AppManager.js` e `utils.js`, logger, constantes, nomes). Arquivos novos de apoio: `.env.example`, `.gitignore` (com `.refactor-arch/`) e README com as variáveis.
Dependências: trocar `sqlite3` (`^5.1.6`, instalado 5.1.7) por `better-sqlite3@^13.0.3`; atualizar `express` de `^4.18.2` (instalado 4.22.1) para `^4.22.3`. Nenhuma outra adição (hash de senha com `node:crypto`).

================================
Total: 20 findings
================================
