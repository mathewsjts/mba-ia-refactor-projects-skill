================================
RELATÓRIO DE AUDITORIA DE ARQUITETURA
================================
Projeto:  ecommerce-api-legacy
Stack:    JavaScript (Node.js 22.23.1) + Express 4.22.1 (declarado ^4.18.2)
Arquivos: 3 analisados | ~180 linhas de código
Data:     2026-11-04

## Resumo
CRITICAL: 5 | HIGH: 8 | MEDIUM: 3 | LOW: 4

| # | Severidade | Anti-pattern | Local principal |
|---|---|---|---|
| F-01 | CRITICAL | Segredos e credenciais hardcoded (AP-02) | src/utils.js:1-7 |
| F-02 | CRITICAL | Exposição de dados sensíveis (AP-03) | src/AppManager.js:45 |
| F-03 | CRITICAL | Armazenamento inseguro de senha (AP-04) | src/utils.js:17-23 |
| F-04 | CRITICAL | Operação privilegiada sem controle de acesso (AP-05) | src/AppManager.js:80 |
| F-05 | CRITICAL | God Class / God Module (AP-06) | src/AppManager.js:1-141 |
| F-06 | HIGH | Estado global mutável (AP-08) | src/utils.js:9-15 |
| F-07 | HIGH | Operação multi-passo sem transação (AP-09) | src/AppManager.js:40-75 |
| F-08 | HIGH | Configuração de execução insegura (AP-10) | src/app.js:12 |
| F-09 | HIGH | Acoplamento forte sem injeção de dependência (AP-11) | src/AppManager.js:7 |
| F-10 | HIGH | Aninhamento profundo / callback hell (AP-12) | src/AppManager.js:37-77 |
| F-11 | HIGH | Validação ausente (AP-14) | src/AppManager.js:29-35 |
| F-12 | HIGH | Tratamento de erro não centralizado (AP-15) | src/AppManager.js:133-136 |
| F-13 | HIGH | Dependência sem suporte com vulnerabilidade conhecida (AP-19) | package.json:10 |
| F-14 | MEDIUM | Query N+1 (AP-13) | src/AppManager.js:92-106 |
| F-15 | MEDIUM | Listagem sem paginação (AP-17) | src/AppManager.js:83 |
| F-16 | MEDIUM | Integridade referencial não garantida (AP-18) | src/AppManager.js:131-137 |
| F-17 | LOW | Logging via console.log (AP-20) | src/app.js:13 |
| F-18 | LOW | Magic numbers e literais duplicados (AP-21) | src/AppManager.js:46 |
| F-19 | LOW | Código morto (AP-22) | src/AppManager.js:2 |
| F-20 | LOW | Nomenclatura pobre e código verboso (AP-23) | src/AppManager.js:29-33 |

## Findings

### F-01 [CRITICAL] Segredos e credenciais hardcoded (AP-02)
Arquivo: src/utils.js:1-7
Ocorrências: src/AppManager.js:45 (vazamento da chave em log)
Descrição: o objeto `config` traz literais versionados: `dbUser: "admin_****"`, `dbPass: "senha_super_****"`, `paymentGatewayKey: "pk_live_****"` (prefixo de chave real de produção) e `smtpUser`. Além de estar no código, a chave do gateway é impressa em log a cada checkout: ``console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)`` (AppManager.js:45). Nenhum valor é lido de variável de ambiente.
Impacto: qualquer pessoa com acesso ao repositório ou aos logs obtém a chave live do gateway e a senha do banco; rotacionar exige novo deploy.
Recomendação: criar `src/config/index.js` que lê `PAYMENT_GATEWAY_KEY`, `ADMIN_TOKEN`, `PORT` etc. de `process.env`, sem default para segredos; remover `dbUser`/`dbPass`/`smtpUser` (não usados — SQLite em memória não tem usuário, não há SMTP); criar `.env.example` com placeholders; nunca logar a chave — Playbook T02.
Contrato: preservado

### F-02 [CRITICAL] Exposição de dados sensíveis (AP-03)
Arquivo: src/AppManager.js:45
Ocorrências: Nenhuma adicional
Descrição: o handler de `POST /api/checkout` grava em log o número completo do cartão (`Processando cartão ${cc} ...`). A saída real do baseline confirma: `.refactor-arch/boot-antes.log` contém `Processando cartão 4111222233334444 na chave pk_live_****`. O vazamento da chave na mesma linha está consolidado em F-01.
Impacto: PAN completo em log viola PCI-DSS; qualquer acesso a logs (agregadores, suporte) expõe cartões de clientes.
Recomendação: o gateway de pagamento registra no máximo os últimos 4 dígitos (`****4444`) via logger com nível; nenhum segredo ou PAN é serializado em log ou resposta — Playbook T13 (passo de campos explícitos aplicado ao log) com T16 para o logger.
Contrato: preservado

### F-03 [CRITICAL] Armazenamento inseguro de senha (AP-04)
Arquivo: src/utils.js:17-23
Ocorrências: src/AppManager.js:68 (default `badCrypto(p || "123456")`), src/AppManager.js:18 (seed grava `pass` = `'123'` em texto plano)
Descrição: `badCrypto()` repete 10.000 vezes os dois primeiros caracteres do base64 da senha e trunca em 10 — é determinístico, sem salt, reversível na prática e colide para qualquer senha com o mesmo prefixo. Quando `pwd` não é enviado, o checkout cria a conta com a senha padrão `"123456"`. O seed grava a senha `'123'` sem hash algum.
Impacto: com um dump do banco as senhas são recuperadas imediatamente; contas criadas sem `pwd` têm senha conhecida por qualquer um.
Recomendação: substituir por `crypto.scrypt` (Node nativo) com salt aleatório por senha, formato `scrypt$<salt>$<hash>` e verificação com `timingSafeEqual`; sem `pwd`, a conta é criada sem credencial (`pass` nulo), nunca com senha padrão; o seed passa a gravar a senha com hash — Playbook T05.
Contrato: preservado (`pwd` continua opcional; nenhuma resposta expõe senha)

### F-04 [CRITICAL] Operação privilegiada sem controle de acesso (AP-05)
Arquivo: src/AppManager.js:80
Ocorrências: src/AppManager.js:131-137
Descrição: as rotas abaixo respondem a qualquer cliente anônimo. Classificação rota a rota pela tabela da T14:
- `GET /api/admin/financial-report` (AppManager.js:80-129) — expõe receita por curso, nome de cada aluno e valor pago, sem autenticação alguma. Situação T14: "Leitura ou gestão administrativa (relatórios financeiros…) sem login no projeto" → **Proteger** com `X-Admin-Token`.
- `DELETE /api/users/:id` (AppManager.js:131-137) — qualquer anônimo apaga qualquer usuário por id. Situação T14: "…remoção de usuários sem login no projeto" → **Proteger** com `X-Admin-Token`.
- `POST /api/checkout` (AppManager.js:28) — analisada e **não** classificada como privilegiada: é cadastro público; grava `pass` apenas ao **criar** a conta do próprio comprador (linha 69) e nunca altera senha, perfil ou estado de conta existente (linha 74 só reaproveita o id); não aceita `role`/`ativo`. Permanece pública. A Fase 3 garante que continue sem sobrescrever credencial de conta existente.
Nenhuma rota executa SQL/código do cliente nem destrói dados em massa — não há situação "Remover".
Impacto: vazamento de dados financeiros e pessoais (nomes de alunos e valores pagos) e remoção arbitrária de contas por qualquer cliente.
Recomendação: middleware `requireAdmin` que compara `X-Admin-Token` com `ADMIN_TOKEN` da configuração via `crypto.timingSafeEqual`, falhando fechado quando a variável não está definida (401 texto `Não autorizado`), aplicado às duas rotas — Playbook T14.
Contrato: exige BC-01, BC-02

### F-05 [CRITICAL] God Class / God Module (AP-06)
Arquivo: src/AppManager.js:1-141
Ocorrências: src/utils.js:1-25 (módulo "faz-tudo": configuração, cache, criptografia e acumulador global no mesmo arquivo)
Descrição: a classe `AppManager` abre a conexão (`new sqlite3.Database(':memory:')`, linha 7), cria o schema e o seed (10-23), registra as rotas (25-138), executa SQL de quatro domínios (usuários, cursos, matrículas/pagamentos, auditoria), decide a regra de pagamento (`cc.startsWith("4")`, linha 46), simula a integração com o gateway (45-46), monta o relatório financeiro (80-129) e serializa as respostas. Matriz de responsabilidades: HTTP + Dados + Regra + Validação + Serialização + Integração no mesmo arquivo; a regra de negócio mora dentro dos handlers (AP-07 consolidado aqui).
Impacto: nada é testável sem subir HTTP e banco; toda mudança atinge a classe inteira; impossível reutilizar a regra de checkout ou do relatório.
Recomendação: dividir em models por domínio (`user`, `course`, `enrollment`, `report`) sobre um `Database` injetado, services (`checkout`, `report`, `user`, gateway de pagamento), controllers finos, rotas em `views/routes.js` e composition root em `app.js`; `utils.js` é desmembrado em `config/`, `services/password` e logger — Playbook T03 (com T04 para a regra nos handlers).
Contrato: preservado

### F-06 [HIGH] Estado global mutável (AP-08)
Arquivo: src/utils.js:9-15
Ocorrências: src/utils.js:25, src/AppManager.js:2, src/AppManager.js:59
Descrição: `let globalCache = {}` é mutado por `logAndCache()` a cada checkout (`globalCache[key] = data`) e exportado; cresce sem limite e nunca é lido. `let totalRevenue = 0` é exportado por valor (quem importa recebe cópia congelada) e importado em AppManager.js:2 sem uso.
Impacto: vazamento de memória proporcional ao número de checkouts; estado que não é compartilhado entre processos e some no restart, sugerindo um cache que não existe.
Recomendação: substituir por um cache por instância (`Map` com limite de entradas) criado no composition root e injetado no service de checkout; eliminar `totalRevenue` — Playbook T11.
Contrato: preservado

### F-07 [HIGH] Operação multi-passo sem transação (AP-09)
Arquivo: src/AppManager.js:40-75
Ocorrências: src/AppManager.js:12 (`users.email` sem `UNIQUE`), src/AppManager.js:57 (auditoria fora de qualquer transação, erro ignorado)
Descrição: o checkout faz até quatro escritas encadeadas sem `BEGIN/COMMIT`: `INSERT INTO users` (69), `INSERT INTO enrollments` (50), `INSERT INTO payments` (54) e `INSERT INTO audit_logs` (57). Uma falha em qualquer passo responde 500 sem desfazer os anteriores — matrícula sem pagamento, usuário sem matrícula. A unicidade do e-mail é checada por leitura (`SELECT id FROM users WHERE email = ?`, linha 40) seguida de `INSERT` (69), sem restrição `UNIQUE` no schema: dois checkouts simultâneos com e-mail novo criam dois usuários. Evidência real: no teste com `card` numérico o usuário foi gravado (linha 69) e o processo caiu antes da matrícula (`.refactor-arch/crash-antes.log`).
Impacto: dados inconsistentes em qualquer falha parcial; usuários duplicados sob concorrência.
Recomendação: validar e decidir o pagamento antes de qualquer escrita; executar usuário, matrícula, pagamento e auditoria numa única transação serializada na conexão compartilhada, com `ROLLBACK` em erro; `UNIQUE` em `users.email` com `INSERT ... ON CONFLICT(email) DO NOTHING` seguido de leitura — Playbook T07.
Contrato: preservado

### F-08 [HIGH] Configuração de execução insegura (AP-10)
Arquivo: src/app.js:12
Ocorrências: src/utils.js:6 (`port: 3000` literal), src/AppManager.js:1 (`require('sqlite3').verbose()` incondicional)
Descrição: a porta é literal e não há leitura de `PORT` — foi impossível subir em outra porta sem editar código. `sqlite3.verbose()` ativa stack traces longos do driver em produção. Schema e seed rodam no boot (comportamento documentado no README para o banco em memória).
Impacto: impossível configurar ambientes sem editar código; rastros internos do driver em produção.
Recomendação: porta e modo verbose vindos de `config` (`PORT`, default 3000; `SQLITE_VERBOSE`), seed mantido no boot por ser contrato documentado do banco em memória — Playbook T02.
Contrato: preservado

### F-09 [HIGH] Acoplamento forte sem injeção de dependência (AP-11)
Arquivo: src/AppManager.js:7
Ocorrências: src/AppManager.js:45-46 (gateway simulado embutido na regra), src/AppManager.js:2 e src/app.js:3 (import direto do módulo concreto `utils`)
Descrição: o construtor de `AppManager` instancia `new sqlite3.Database(':memory:')`; a decisão de pagamento `cc.startsWith("4") ? "PAID" : "DENIED"` está no meio do handler, sem interface de gateway; config e cache são importados como singletons de módulo.
Impacto: impossível testar o checkout sem SQLite real; trocar o gateway significa editar a regra de negócio.
Recomendação: composition root em `app.js` cria `Database`, models, `PaymentGateway`, services e controllers e os injeta por construtor — Playbook T11.
Contrato: preservado

### F-10 [HIGH] Aninhamento profundo / callback hell (AP-12)
Arquivo: src/AppManager.js:37-77
Ocorrências: src/AppManager.js:83-128 (relatório com contadores manuais `coursesPending`/`enrPending`), src/AppManager.js:26 (`const self = this`)
Descrição: o checkout tem cinco níveis de callbacks (`db.get` → `db.get` → `db.run` → `db.run` → `db.run`). O relatório usa contadores manuais (86, 93, 117-121) e ignora `err` em 92, 104 e 106: se a consulta da linha 92 falhar, `enrollments` é `undefined` e `enrollments.length` lança dentro do callback, derrubando o processo e deixando a requisição sem resposta.
Impacto: erros ignorados por construção, risco de requisição sem resposta e de queda do processo.
Recomendação: model com API de Promises sobre o driver (`run`/`get`/`all`), services e controllers com `async/await` e guard clauses — Playbook T06.
Contrato: preservado

### F-11 [HIGH] Validação ausente (AP-14)
Arquivo: src/AppManager.js:29-35
Ocorrências: src/AppManager.js:46 (`cc.startsWith`), src/AppManager.js:68 (`Buffer.from(pwd)`), src/AppManager.js:132 (`req.params.id` direto)
Descrição: a única validação é `if (!u || !e || !cid || !cc)`, por truthiness. Não há checagem de tipo nem de formato: `card` numérico chega a `cc.startsWith("4")` e lança `TypeError` dentro de um callback do driver — **o processo inteiro cai** (verificado: `.refactor-arch/crash-antes.log`, curl recebeu `000`). `pwd` numérico derruba da mesma forma em `Buffer.from`. `c_id`, `eml` e o `id` do `DELETE` são usados sem validação. Escalonado de MEDIUM para HIGH: alcançável por requisição anônima (regra 1) e grava dado parcial antes da queda (regra 2).
Impacto: negação de serviço com uma única requisição anônima; dados inválidos no banco.
Recomendação: `controllers/validators.js` com validação de presença, tipo e formato (`usr`/`eml`/`card` strings não vazias, `eml` com formato de e-mail, `pwd` opcional string, `c_id` inteiro positivo ou string de dígitos, `id` inteiro positivo seguro), respondendo 400 `Bad Request` como hoje — Playbook T09.
Contrato: preservado para todas as entradas válidas e todas as do baseline; entradas de tipo inválido, que hoje derrubam o processo ou são aceitas em silêncio, passam a 400

### F-12 [HIGH] Tratamento de erro não centralizado (AP-15)
Arquivo: src/AppManager.js:133-136
Ocorrências: src/AppManager.js:38 (erro de banco vira 404), src/AppManager.js:57 (erro da auditoria ignorado), src/AppManager.js:92, 104, 106 (`err` ignorado), src/AppManager.js:41, 51, 55, 70, 84 (mensagens 500 diferentes por ponto: "Erro DB", "Erro Matrícula", "Erro Pagamento", "Erro ao criar usuário")
Descrição: cada callback trata erro à sua maneira e vários os engolem. O `DELETE /api/users/:id` ignora `err` e responde 200 "Usuário deletado…" mesmo quando o `DELETE` falha — sucesso falso. Na linha 38, um erro de banco é respondido como "Curso não encontrado" (404). Não existe middleware de erro `(err, req, res, next)`. Escalonado para HIGH (erro engolido que retorna sucesso falso).
Impacto: falhas silenciosas, respostas enganosas e formatos inconsistentes.
Recomendação: classes de erro de domínio (`NotFoundError`, `ValidationError`, `PaymentDeclinedError`), `asyncHandler` nas rotas e um `errorHandler` central que traduz para os mesmos status e corpos de texto atuais (400/404/500) e loga o erro interno sem vazá-lo — Playbook T10.
Contrato: preservado

### F-13 [HIGH] Dependência sem suporte com vulnerabilidade conhecida (AP-19)
Arquivo: package.json:10
Ocorrências: package.json:9 (express ^4.18.2 resolvido para 4.22.1 com transitivas vulneráveis)
Descrição: `sqlite3@5.1.7` puxa `tar@6.2.1` (critical no `npm audit`), `node-gyp@8`, `glob@7.2.3`, `inflight@1.0.6`, `rimraf@3.0.2`, `npmlog`, `gauge`, `are-we-there-yet`, `@npmcli/move-file` — todos com `npm warn deprecated` em `.refactor-arch/install.log`; `npm audit` aponta o próprio `sqlite3` como high, com correção em `sqlite3@6.0.1` (engines `node >=20.17.0`, atendido pelo Node 22.23.1). As transitivas do Express (`body-parser`, `path-to-regexp`, `qs`, `proxy-addr` critical) têm correção dentro do range 4.x via `npm audit fix`. Nenhum padrão de API deprecated no código (`new Buffer`, `url.parse`, `app.del`, `req.param`…) e nenhum aviso com `--trace-deprecation`.
Impacto: 17 vulnerabilidades conhecidas (2 critical, 8 high) na árvore de dependências; pacotes sem manutenção.
Recomendação: atualizar `sqlite3` para `^6.0.1` e aplicar `npm audit fix` (sem `--force`) para as transitivas do Express 4; manter Express 4 (migração para 5 só com smoke test equivalente) — Playbook T12.
Contrato: preservado (a confirmar pelo smoke test)

### F-14 [MEDIUM] Query N+1 (AP-13)
Arquivo: src/AppManager.js:92-106
Ocorrências: Nenhuma adicional
Descrição: `GET /api/admin/financial-report` faz 1 consulta de cursos, 1 de matrículas por curso (92) e, para cada matrícula, 1 consulta de usuário (104) e 1 de pagamento (106): 1 + C + 2·M consultas.
Impacto: tempo de resposta cresce linearmente com matrículas; com milhares de alunos, milhares de consultas por chamada.
Recomendação: uma única consulta com `LEFT JOIN` de cursos → matrículas → usuários → pagamentos, agregada no service mantendo `course`, `revenue`, `students[].student`, `students[].paid` — Playbook T08.
Contrato: preservado

### F-15 [MEDIUM] Listagem sem paginação (AP-17)
Arquivo: src/AppManager.js:83
Ocorrências: src/AppManager.js:92
Descrição: o relatório carrega todos os cursos (`SELECT * FROM courses`) e todas as matrículas de cada curso em memória e devolve tudo numa só resposta.
Impacto: memória e tempo de resposta crescem com o volume.
Recomendação: paginação **opcional** por `?limit=&offset=` sobre cursos; sem os parâmetros, a resposta é idêntica à atual — Playbook T17.
Contrato: preservado

### F-16 [MEDIUM] Integridade referencial não garantida (AP-18)
Arquivo: src/AppManager.js:131-137
Ocorrências: src/AppManager.js:12-15 (`enrollments.user_id`, `enrollments.course_id`, `payments.enrollment_id` sem `FOREIGN KEY`; sem `PRAGMA foreign_keys = ON`)
Descrição: `DELETE FROM users WHERE id = ?` não trata matrículas e pagamentos do usuário — a própria resposta admite: "as matrículas e pagamentos ficaram sujos no banco". O relatório passa a listar alunos `'Unknown'`.
Impacto: registros órfãos e relatório financeiro com alunos inexistentes.
Recomendação: `FOREIGN KEY ... ON DELETE CASCADE` no schema com `PRAGMA foreign_keys = ON`, e remoção explícita de pagamentos → matrículas → usuário numa transação — Playbook T15.
Contrato: preservado (200 texto; a mensagem deixa de admitir dados sujos)

### F-17 [LOW] Logging via console.log (AP-20)
Arquivo: src/app.js:13
Ocorrências: src/utils.js:13, src/AppManager.js:45 (conteúdo sensível tratado em F-01/F-02)
Descrição: banner de boot, log de cache e log do gateway via `console.log`, sem nível nem controle de destino.
Impacto: impossível filtrar por severidade ou silenciar em produção.
Recomendação: logger mínimo com níveis (`info`/`warn`/`error`) controlado por `LOG_LEVEL`, injetado onde for preciso — Playbook T16.
Contrato: preservado

### F-18 [LOW] Magic numbers e literais duplicados (AP-21)
Arquivo: src/AppManager.js:46
Ocorrências: src/AppManager.js:21, 48, 54, 108 (`'PAID'`/`'DENIED'` repetidos), src/AppManager.js:68 (`"123456"`), src/utils.js:19 (`10000`)
Descrição: a regra "cartão começando com `"4"` é aprovado" e os status de pagamento são literais espalhados.
Impacto: mudar um status ou a regra do gateway exige caçar literais.
Recomendação: constantes `PAYMENT_STATUS = { PAID, DENIED }` e `APPROVED_CARD_PREFIX` no gateway — Playbook T16.
Contrato: preservado

### F-19 [LOW] Código morto (AP-22)
Arquivo: src/AppManager.js:2
Ocorrências: src/utils.js:2-3, 5 (`dbUser`, `dbPass`, `smtpUser` nunca lidos), src/utils.js:10, 25 (`totalRevenue`, `globalCache` exportados e nunca lidos)
Descrição: `totalRevenue` é importado e nunca usado; credenciais de banco e SMTP são configuradas sem nenhum consumidor; `globalCache` é exportado e ninguém o lê.
Impacto: ruído e falsa impressão de integrações que não existem.
Recomendação: remover — Playbook T16.
Contrato: preservado

### F-20 [LOW] Nomenclatura pobre e código verboso (AP-23)
Arquivo: src/AppManager.js:29-33
Ocorrências: src/AppManager.js:4 (`AppManager`), src/utils.js:17 (`badCrypto`), src/utils.js:12 (`logAndCache`), src/app.js:13 ("Frankenstein LMS")
Descrição: variáveis `u`, `e`, `p`, `cid`, `cc`; nomes genéricos ou enganosos (`AppManager`, `utils`, `badCrypto`); `let` para valores nunca reatribuídos. As chaves JSON públicas `usr`, `eml`, `pwd`, `c_id` também são pobres, mas são contrato.
Impacto: leitura lenta e intenção obscura.
Recomendação: renomear apenas identificadores internos (`name`, `email`, `password`, `courseId`, `cardNumber`); manter as chaves públicas — Playbook T16.
Contrato: preservado

## APIs deprecated
| API ou dependência | Local | Substituto | Evidência |
|---|---|---|---|
| `sqlite3@5.1.7` (high no `npm audit`) e transitivas `tar@6.2.1` (critical), `glob@7.2.3`, `inflight@1.0.6`, `rimraf@3.0.2`, `npmlog@6`, `gauge@4`, `are-we-there-yet@3`, `@npmcli/move-file@1` | package.json:10 | `sqlite3@^6.0.1` (puxa `tar@^7.5.10`, sem `node-gyp@8`) | `npm warn deprecated` em `.refactor-arch/install.log`; `npm audit` (fix: `sqlite3@6.0.1`) |
| `prebuild-install@7.1.3` | package.json:10 (via sqlite3) | permanece em `sqlite3@6.0.1`; sem alternativa sem trocar de driver | `npm warn deprecated prebuild-install@7.1.3` |
| Transitivas do Express 4: `body-parser`, `path-to-regexp`, `qs`, `proxy-addr` (critical) | package.json:9 | versões corrigidas dentro do range `^4` via `npm audit fix` | `npm audit` (`fixAvailable: true`, sem `--force`) |
| APIs deprecated no código | — | — | Nenhuma: busca pelos padrões do catálogo (`new Buffer(`, `url.parse`, `fs.exists(`, `util.is*`, `createCipher(`, `app.del(`, `req.param(`, `sendfile`, `bodyParser`) sem ocorrências; boot e checkout com `NODE_OPTIONS=--trace-deprecation` sem aviso |

## Breaking Changes propostos
| # | Rota | Mudança no contrato | Finding que justifica |
|---|---|---|---|
| BC-01 | GET /api/admin/financial-report | passa a exigir `X-Admin-Token` igual a `ADMIN_TOKEN`; sem header ou com valor inválido (ou com `ADMIN_TOKEN` não configurado) responde 401 texto `Não autorizado`; com token válido, resposta idêntica | F-04 — relatório financeiro com dados de alunos aberto a anônimos (T14, "Proteger") |
| BC-02 | DELETE /api/users/:id | passa a exigir `X-Admin-Token`; sem credencial válida responde 401 texto `Não autorizado`; com token válido, 200 texto como hoje | F-04 — remoção de usuários por qualquer anônimo (T14, "Proteger") |

## Plano de refatoração
```
src/
├── app.js                       composition root + listen (entry: npm start / node src/app.js)
├── errors.js                    erros de domínio
├── config/
│   ├── index.js                 config de process.env (T02)
│   └── logger.js                logger com níveis (T16)
├── models/
│   ├── database.js              wrapper Promise + transação serializada + schema/seed (T06, T07, T11, T15)
│   ├── user.model.js            users (T07 unicidade, T15 cascade)
│   ├── course.model.js          courses
│   ├── enrollment.model.js      enrollments + payments + audit_logs
│   └── report.model.js          consulta agregada com JOIN (T08, T17)
├── services/
│   ├── password.js              scrypt + salt (T05)
│   ├── payment.gateway.js       gateway simulado com log mascarado (T11, T13, T16)
│   ├── cache.js                 cache limitado por instância (T11)
│   ├── checkout.service.js      regra do checkout em transação (T04, T07)
│   ├── report.service.js        agregação do relatório (T04, T08)
│   └── user.service.js          remoção com integridade (T15)
├── controllers/
│   ├── validators.js            validação reutilizável (T09)
│   ├── checkout.controller.js
│   ├── report.controller.js
│   └── user.controller.js
├── views/
│   ├── routes.js                mapeamento de rotas + requireAdmin (T14)
│   └── serializers.js           respostas com campos explícitos (T13)
└── middlewares/
    ├── asyncHandler.js
    ├── errorHandler.js          tratamento central (T10)
    └── requireAdmin.js          X-Admin-Token com timingSafeEqual (T14)
```
Ordem: config (T02) → models (T03, T05, T07, T08, T11, T12, T15) → services (T04, T06, T09) → controllers (T04, T09) → views/routes (T13, T14, T17) → middlewares (T10) → composition root (T11) → limpeza (T16; remoção de `AppManager.js` e `utils.js`). Fora do código: `sqlite3@^6.0.1` + `npm audit fix` (T12), `.env.example` e README com `ADMIN_TOKEN`/`PORT`.

================================
Total: 20 findings
================================
