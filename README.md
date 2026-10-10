# Refatoração Arquitetural Automatizada — Skill `refactor-arch`

Skill do Claude Code que analisa uma API backend legada, audita a codebase contra um catálogo de anti-patterns e a refatora para o padrão MVC, validando que a aplicação continua funcionando. Ela é agnóstica de tecnologia e foi construída para rodar sem ajustes em três projetos: dois em Python/Flask e um em Node.js/Express.

> O enunciado original do desafio está preservado em [DESAFIO.md](DESAFIO.md).

| Etapa | Situação |
|---|---|
| Análise manual dos 3 projetos | ✅ Concluída — [seção A](#a-análise-manual) |
| Skill `refactor-arch` (SKILL.md + 6 arquivos de referência) | ✅ Construída e testada contra os projetos originais — [seção B](#b-construção-da-skill) |
| Execução da skill nos 3 projetos | ⏳ Pendente — [seção D](#d-como-executar) |
| Relatórios em `reports/` e resultados | ⏳ Pendente — [seção C](#c-resultados) |

## Sumário

- [Estrutura do repositório](#estrutura-do-repositório)
- [A) Análise Manual](#a-análise-manual)
- [B) Construção da Skill](#b-construção-da-skill)
- [C) Resultados](#c-resultados)
- [D) Como Executar](#d-como-executar)

## Estrutura do repositório

```
.
├── DESAFIO.md                              # enunciado original
├── README.md
├── reports/                                # audit-project-{1,2,3}.md — saída da Fase 2
├── code-smells-project/                    # Projeto 1 — Python/Flask, e-commerce
│   └── .claude/skills/refactor-arch/
│       ├── SKILL.md                        # orquestrador das 3 fases
│       ├── analise-de-projeto.md           # heurísticas de detecção
│       ├── catalogo-anti-patterns.md       # 24 anti-patterns + APIs deprecated
│       ├── template-relatorio.md           # formato do relatório de auditoria
│       ├── guidelines-arquitetura.md       # regras do MVC alvo
│       ├── playbook-refatoracao.md         # 17 transformações antes/depois
│       └── protocolo-validacao.md          # baseline, smoke test e diff
├── ecommerce-api-legacy/                   # Projeto 2 — Node.js/Express, LMS com checkout
│   └── .claude/skills/refactor-arch/       # cópia byte-idêntica
└── task-manager-api/                       # Projeto 3 — Python/Flask, task manager
    └── .claude/skills/refactor-arch/       # cópia byte-idêntica
```

---

## A) Análise Manual

### Método

1. **Leitura integral** das 2.118 linhas dos três projetos.
2. **Execução dos projetos originais** para confirmar cada suspeita com evidência: boot, chamadas aos endpoints, saída do instalador de dependências e avisos de depreciação em runtime. Achados confirmados assim estão marcados com ▶.
3. **Classificação** pela escala de severidade do enunciado, com o anti-pattern correspondente do catálogo da skill (coluna AP). Essa coluna é a rastreabilidade entre a análise manual e a skill.

Segredos aparecem redigidos (`pk_live_****`) mesmo sendo dados de exemplo — a mesma regra que a skill aplica nos relatórios.

| Projeto | Stack verificada | Arquivos | Linhas | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|---|---|
| `code-smells-project` | Python 3.9 · Flask 3.1.1 · sqlite3 | 4 | 780 | 4 | 5 | 4 | 4 | **17** |
| `ecommerce-api-legacy` | Node 22 · Express 4.22.1 · sqlite3 5.1.7 | 3 | 180 | 5 | 5 | 3 | 3 | **16** |
| `task-manager-api` | Python 3.9 · Flask 3.0.0 · Flask-SQLAlchemy 3.1.1 · SQLAlchemy 2.0 | 15 | 1.158 | 3 | 3 | 6 | 4 | **16** |

### Projeto 1 — `code-smells-project` (Python/Flask, e-commerce)

Monolito em quatro arquivos. Os nomes `models.py` e `controllers.py` sugerem MVC, mas `models.py` concentra SQL, regra de negócio e formatação de quatro domínios, e `app.py` mistura configuração, rotas e endpoints administrativos.

| # | Sev. | AP | Problema | Local | Por que importa |
|---|---|---|---|---|---|
| 1 | CRITICAL | 01 | SQL Injection por concatenação em 19 chamadas `execute()` | [models.py:28](code-smells-project/models.py#L28), [47-50](code-smells-project/models.py#L47-L50), [109-111](code-smells-project/models.py#L109-L111), [289-299](code-smells-project/models.py#L289-L299) e outras 15 | O login monta `WHERE email = '...' AND senha = '...'`: a senha `' OR '1'='1` autentica sem credencial. Todo campo de texto permite ler ou apagar tabelas. |
| 2 | CRITICAL | 05 | `POST /admin/query` executa SQL vindo do corpo e `POST /admin/reset-db` apaga todas as tabelas, ambos sem autenticação | [app.py:47-78](code-smells-project/app.py#L47-L78) | Uma requisição anônima exfiltra ou destrói o banco inteiro. ▶ `/admin/query` respondeu 200 com o resultado de um `SELECT`. |
| 3 | CRITICAL | 02, 03 | `SECRET_KEY` hardcoded (`'minha-chave-****'`) e devolvida em texto claro pelo `/health` | [app.py:7](code-smells-project/app.py#L7), [controllers.py:285-289](code-smells-project/controllers.py#L285-L289) | Com a chave, cookies e sessões assinados podem ser forjados. O endpoint público entrega também `debug` e o caminho do banco. ▶ `GET /health` retornou `secret_key`. |
| 4 | CRITICAL | 04, 03 | Senhas em texto plano: gravadas assim, comparadas no SQL e devolvidas nas respostas | [database.py:75-83](code-smells-project/database.py#L75-L83), [models.py:83](code-smells-project/models.py#L83), [99](code-smells-project/models.py#L99), [126-129](code-smells-project/models.py#L126-L129) | Um `GET /usuarios` entrega a senha de todos, inclusive a do admin semeado. ▶ a resposta contém o campo `senha`. |
| 5 | HIGH | 06 | God module: `models.py` reúne SQL, regras (descontos) e formatação de produtos, usuários, pedidos e relatórios | [models.py:1-314](code-smells-project/models.py) | Qualquer mudança em pedidos pode quebrar produtos; nenhuma regra é testável sem banco. |
| 6 | HIGH | 08 | Conexão SQLite global, mutável e compartilhada entre threads | [database.py:4-10](code-smells-project/database.py#L4-L10) | `check_same_thread=False` desliga a proteção do driver: requisições concorrentes dividem a mesma transação. |
| 7 | HIGH | 09 | `criar_pedido` grava pedido, itens e estoque sem transação | [models.py:133-169](code-smells-project/models.py#L133-L169) | Se algo falha no meio, os inserts ficam pendentes na conexão global e são efetivados pelo próximo `commit()` de **outra** requisição: pedido sem itens ou estoque baixado a mais. |
| 8 | HIGH | 07 | E-mail, SMS e push disparados inline no controller; o cancelamento promete devolver estoque e não devolve | [controllers.py:208-210](code-smells-project/controllers.py#L208-L210), [247-250](code-smells-project/controllers.py#L247-L250) | A regra de notificação não é reutilizável nem substituível, e a promessa de devolução de estoque ficou só no `print`. |
| 9 | HIGH | 10 | `DEBUG=True` e bind `0.0.0.0` fixos no código | [app.py:8](code-smells-project/app.py#L8), [88](code-smells-project/app.py#L88) | O debugger do Werkzeug exposto na rede permite execução de código. A porta fixa impede o boot quando ocupada. ▶ `python app.py` falhou com `Address already in use` (porta 5000 do AirPlay no macOS). |
| 10 | MEDIUM | 13 | N+1: uma consulta por pedido e outra por item | [models.py:187-199](code-smells-project/models.py#L187-L199), [219-231](code-smells-project/models.py#L219-L231) | `GET /pedidos` com 100 pedidos de 3 itens dispara cerca de 400 consultas. |
| 11 | MEDIUM | 14 | Validação duplicada e divergente entre criar e atualizar produto | [controllers.py:28-54](code-smells-project/controllers.py#L28-L54), [72-90](code-smells-project/controllers.py#L72-L90) | A atualização não valida categoria nem tamanho do nome: um produto pode ser gravado com dados que a criação rejeita. |
| 12 | MEDIUM | 15 | `except Exception` em 16 handlers, devolvendo `str(e)` ao cliente | [controllers.py](code-smells-project/controllers.py) | Mensagens internas do banco vazam e não há formato de erro garantido. |
| 13 | MEDIUM | 16, 17 | CORS aberto para qualquer origem e listagens sem paginação | [app.py:9](code-smells-project/app.py#L9), [models.py:4-22](code-smells-project/models.py#L4-L22), [203-233](code-smells-project/models.py#L203-L233) | Qualquer site chama a API pelo navegador do usuário; as listagens crescem sem limite. |
| 14 | LOW | 20 | `print()` como log em 14 pontos, incluindo e-mails no login | [controllers.py:161](code-smells-project/controllers.py#L161), [179-182](code-smells-project/controllers.py#L179-L182) | Sem nível nem destino configurável, e com dado pessoal em log. |
| 15 | LOW | 21 | Magic numbers nas faixas de desconto | [models.py:256-262](code-smells-project/models.py#L256-L262) | Mudar a política comercial exige caçar `10000`, `0.1`, `5000`, `0.05`… |
| 16 | LOW | 24 | Dicionário de produto copiado três vezes | [models.py:12-21](code-smells-project/models.py#L12-L21), [31-40](code-smells-project/models.py#L31-L40), [304-313](code-smells-project/models.py#L304-L313) | Um campo novo exige lembrar das três cópias. |
| 17 | LOW | 22 | Imports não usados (`sqlite3`, `os`) | [models.py:2](code-smells-project/models.py#L2), [database.py:2](code-smells-project/database.py#L2) | Ruído que sugere dependências inexistentes. |

**APIs deprecated:** nenhuma. Flask 3.1.1 e `sqlite3` da biblioteca padrão são usados sem construções legadas.

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

Uma God Class (`AppManager`) cria o banco em memória, faz o seed, registra as rotas e implementa checkout, pagamento, auditoria e relatório. `utils.js` guarda configuração com segredos, estado global e um "hash" caseiro.

| # | Sev. | AP | Problema | Local | Por que importa |
|---|---|---|---|---|---|
| 1 | CRITICAL | 02 | Senha de banco e chave `pk_live_****` do gateway hardcoded | [src/utils.js:2-5](ecommerce-api-legacy/src/utils.js#L2-L5) | Os segredos de produção ficam no repositório; rotacionar exige deploy. |
| 2 | CRITICAL | 03 | Número do cartão e chave do gateway escritos no log | [src/AppManager.js:45](ecommerce-api-legacy/src/AppManager.js#L45) | Viola PCI-DSS: todo agregador de logs passa a guardar cartões. ▶ o log registrou `Processando cartão 4111********4444 na chave pk_live_****`. |
| 3 | CRITICAL | 04 | "Hash" de senha caseiro que colide em massa, com senha padrão quando o campo não vem | [src/utils.js:17-23](ecommerce-api-legacy/src/utils.js#L17-L23), [src/AppManager.js:68](ecommerce-api-legacy/src/AppManager.js#L68) | O resultado depende só dos primeiros 12 bits da senha. ▶ `senhaforte`, `segredo` e `sa` geram o mesmo `c2c2c2c2c2`. Sem `pwd`, o usuário nasce com `123456`. |
| 4 | CRITICAL | 06 | God Class `AppManager` | [src/AppManager.js:4-139](ecommerce-api-legacy/src/AppManager.js#L4-L139) | Banco, schema, seed, rotas, pagamento, auditoria e relatório numa classe: nada é testável em isolamento. |
| 5 | CRITICAL | 05 | Relatório financeiro e remoção de usuários sem autenticação | [src/AppManager.js:80](ecommerce-api-legacy/src/AppManager.js#L80), [131](ecommerce-api-legacy/src/AppManager.js#L131) | Qualquer cliente anônimo lê a receita por curso com nomes de alunos ou apaga usuários. ▶ `GET /api/admin/financial-report` respondeu 200 sem credencial. |
| 6 | HIGH | 12 | Callback hell de cinco níveis no checkout | [src/AppManager.js:37-77](ecommerce-api-legacy/src/AppManager.js#L37-L77) | O erro da gravação de auditoria (linha 57) é ignorado, e qualquer alteração arrisca resposta dupla ou requisição sem resposta. |
| 7 | HIGH | 09 | Checkout grava matrícula, pagamento e auditoria sem transação | [src/AppManager.js:50-63](ecommerce-api-legacy/src/AppManager.js#L50-L63) | Se o `INSERT` do pagamento falha, a matrícula já existe: aluno matriculado sem pagamento registrado. |
| 8 | HIGH | 08 | Estado global mutável e primitivo exportado por valor | [src/utils.js:9-10](ecommerce-api-legacy/src/utils.js#L9-L10), [25](ecommerce-api-legacy/src/utils.js#L25) | `globalCache` cresce sem limite e é compartilhado entre requisições; `totalRevenue` é importado em `AppManager.js:2` e nunca usado — uma cópia congelada que jamais poderia ser atualizada. |
| 9 | HIGH | 11 | Gateway de pagamento simulado dentro da regra de checkout | [src/AppManager.js:46](ecommerce-api-legacy/src/AppManager.js#L46) | A aprovação é `cc.startsWith("4")`. Plugar o gateway real exige reescrever o checkout, e não há como testar o fluxo sem ele. |
| 10 | HIGH | 19 | Dependências com pacotes deprecated e vulnerabilidades conhecidas | [package.json:10-11](ecommerce-api-legacy/package.json#L10-L11) | ▶ `npm ci` emitiu 9 avisos `deprecated` (`inflight`, `glob@7`, `tar@6`, `rimraf@3`…) puxados por `sqlite3@5.1.7`. ▶ `npm audit`: 12 vulnerabilidades, 1 crítica (`tar`), `sqlite3` como dependência direta *high* e ReDoS *high* em `path-to-regexp` via Express 4. |
| 11 | MEDIUM | 13 | N+1 assíncrono com contadores manuais no relatório financeiro | [src/AppManager.js:83-128](ecommerce-api-legacy/src/AppManager.js#L83-L128) | São 1 + cursos + 2 × matrículas consultas. A ordem do resultado é a de conclusão dos callbacks. ▶ "Docker" veio antes de "Clean Architecture". |
| 12 | MEDIUM | 18 | Remoção de usuário sem cascade e ignorando o erro do driver | [src/AppManager.js:131-137](ecommerce-api-legacy/src/AppManager.js#L131-L137) | Matrículas e pagamentos ficam órfãos (a própria resposta admite), e a rota responde 200 mesmo se o `DELETE` falhar. |
| 13 | MEDIUM | 14, 15 | Validação ausente e erros como texto sem padrão | [src/AppManager.js:35](ecommerce-api-legacy/src/AppManager.js#L35) | `pwd` não é exigido; e-mail e cartão não são validados. ▶ `POST /api/checkout` com `{}` → 400 `text/html` "Bad Request". |
| 14 | LOW | 23 | Variáveis de uma a três letras | [src/AppManager.js:29-33](ecommerce-api-legacy/src/AppManager.js#L29-L33) | `u`, `e`, `p`, `cid`, `cc` obrigam a reler de onde vem cada valor. |
| 15 | LOW | 23 | Contrato público com chaves abreviadas | [api.http:8-12](ecommerce-api-legacy/api.http#L8-L12) | `usr`, `eml`, `pwd`, `c_id` expõem nomenclatura interna aos clientes e não podem ser corrigidos sem quebrar integrações. |
| 16 | LOW | 20 | `console.log` como log | [src/utils.js:13](ecommerce-api-legacy/src/utils.js#L13), [src/app.js:13](ecommerce-api-legacy/src/app.js#L13) | Sem níveis — e é o mesmo canal que vazou o cartão. |

### Projeto 3 — `task-manager-api` (Python/Flask, task manager)

Tem `models/`, `routes/`, `services/` e `utils/`, mas as pastas não correspondem a responsabilidades: as rotas contêm consultas, regras e serialização; o único serviço nunca é chamado; o validador pronto em `utils/` também não.

| # | Sev. | AP | Problema | Local | Por que importa |
|---|---|---|---|---|---|
| 1 | CRITICAL | 04 | Senha com MD5 sem salt | [models/user.py:27-32](task-manager-api/models/user.py#L27-L32) | MD5 cai em segundos para senhas comuns. O seed usa `1234`, cujo MD5 está em qualquer rainbow table. |
| 2 | CRITICAL | 03 | `to_dict()` inclui o hash da senha, devolvido em quatro endpoints, inclusive no login | [models/user.py:21](task-manager-api/models/user.py#L21), [routes/user_routes.py:33](task-manager-api/routes/user_routes.py#L33), [85](task-manager-api/routes/user_routes.py#L85), [129](task-manager-api/routes/user_routes.py#L129), [209](task-manager-api/routes/user_routes.py#L209) | Somado ao MD5, entrega a senha de qualquer usuário. `GET /users` monta outro dicionário sem a senha, e as duas serializações divergem. ▶ `POST /login` retornou `"password": "81dc9bdb…"` (MD5 de `1234`). |
| 3 | CRITICAL | 02 | `SECRET_KEY` e usuário/senha SMTP hardcoded | [app.py:13](task-manager-api/app.py#L13), [services/notification_service.py:9-10](task-manager-api/services/notification_service.py#L9-L10) | A senha do e-mail está no repositório; a chave permite forjar sessões. |
| 4 | HIGH | 05 | Autenticação de fachada | [routes/user_routes.py:210](task-manager-api/routes/user_routes.py#L210) | O token é `fake-jwt-token-<id>` — previsível — e nenhuma rota o exige: a API inteira, inclusive a remoção de usuários, é anônima. |
| 5 | HIGH | 07 | Consultas, regras e serialização dentro das rotas; `report_routes.py` também acumula o CRUD de categorias | [routes/task_routes.py:11-63](task-manager-api/routes/task_routes.py#L11-L63), [routes/report_routes.py:12-101](task-manager-api/routes/report_routes.py#L12-L101), [157-223](task-manager-api/routes/report_routes.py#L157-L223) | Não existe camada de controller nem uso real de services; relatórios e categorias mudam pelo mesmo arquivo. |
| 6 | HIGH | 10 | `debug=True` com bind `0.0.0.0`, e `db.create_all()` executado no import | [app.py:30-34](task-manager-api/app.py#L30-L34) | Debugger exposto na rede; importar `app` (como faz o `seed.py`) cria tabelas como efeito colateral. |
| 7 | MEDIUM | 13 | N+1 em listagens e relatórios | [routes/task_routes.py:41-57](task-manager-api/routes/task_routes.py#L41-L57), [routes/report_routes.py:53-68](task-manager-api/routes/report_routes.py#L53-L68), [163](task-manager-api/routes/report_routes.py#L163), [routes/user_routes.py:22](task-manager-api/routes/user_routes.py#L22) | `GET /tasks` faz duas consultas extras por task; `/reports/summary`, uma por usuário. |
| 8 | MEDIUM | 07, 22 | Cálculo de atraso reimplementado seis vezes, enquanto `Task.is_overdue()` nunca é chamado | [routes/task_routes.py:30-39](task-manager-api/routes/task_routes.py#L30-L39), [71-80](task-manager-api/routes/task_routes.py#L71-L80), [283-287](task-manager-api/routes/task_routes.py#L283-L287), [routes/user_routes.py:171-180](task-manager-api/routes/user_routes.py#L171-L180), [routes/report_routes.py:34-37](task-manager-api/routes/report_routes.py#L34-L37), [132-135](task-manager-api/routes/report_routes.py#L132-L135), [models/task.py:50-60](task-manager-api/models/task.py#L50-L60) | Uma mudança na regra de atraso precisa ser feita em seis lugares — e o método que resolveria já existe. |
| 9 | MEDIUM | 14 | Validação duplicada e sem conversão de tipo, enquanto o validador pronto não é usado | [routes/task_routes.py:92-114](task-manager-api/routes/task_routes.py#L92-L114), [166-184](task-manager-api/routes/task_routes.py#L166-L184), [utils/helpers.py:57-108](task-manager-api/utils/helpers.py#L57-L108) | `process_task_data()` já valida e converte, mas ninguém o chama. ▶ `POST /tasks` com `"priority": "2"` → 500 em HTML. |
| 10 | MEDIUM | 15 | `except:` sem tipo em 12 pontos | [routes/task_routes.py:62](task-manager-api/routes/task_routes.py#L62), [routes/user_routes.py:130](task-manager-api/routes/user_routes.py#L130), [routes/report_routes.py:186](task-manager-api/routes/report_routes.py#L186), [utils/helpers.py:46](task-manager-api/utils/helpers.py#L46) e outros 8 | Captura até `SystemExit`/`KeyboardInterrupt` e apaga a causa real dos erros. |
| 11 | MEDIUM | 19 | APIs deprecated: `Query.get()` em 16 pontos e `datetime.utcnow()` em 22 | [routes/task_routes.py:42](task-manager-api/routes/task_routes.py#L42), [67](task-manager-api/routes/task_routes.py#L67), [models/task.py:15-16](task-manager-api/models/task.py#L15-L16) | `Query.get()` é legado no SQLAlchemy 2.0 (substituto: `db.session.get()`), e `utcnow()` está deprecated desde o Python 3.12. ▶ o boot com `-W default` emitiu `LegacyAPIWarning` em `task_routes.py:42, 51, 67`, `user_routes.py:29, 155` e `report_routes.py:105`. |
| 12 | MEDIUM | 16, 17 | Listagens sem paginação e CORS aberto | [routes/task_routes.py:14](task-manager-api/routes/task_routes.py#L14), [app.py:15](task-manager-api/app.py#L15) | Listagens e relatórios carregam tabelas inteiras na memória; qualquer site chama a API. |
| 13 | LOW | 22 | Código morto: serviço, imports e três dependências sem uso | [services/notification_service.py:4-48](task-manager-api/services/notification_service.py#L4-L48), [routes/report_routes.py:7](task-manager-api/routes/report_routes.py#L7), [requirements.txt:4-6](task-manager-api/requirements.txt#L4-L6) | `marshmallow`, `requests` e `python-dotenv` são instalados e nunca importados. |
| 14 | LOW | 21 | Constantes declaradas e ignoradas, com os literais espalhados | [utils/helpers.py:110-116](task-manager-api/utils/helpers.py#L110-L116), [routes/task_routes.py:110](task-manager-api/routes/task_routes.py#L110), [177](task-manager-api/routes/task_routes.py#L177) | `VALID_STATUSES` existe, mas a lista de status é repetida à mão. |
| 15 | LOW | 23 | Código verboso | [models/user.py:34-38](task-manager-api/models/user.py#L34-L38), [models/task.py:38-48](task-manager-api/models/task.py#L38-L48) | `if x: return True else: return False` onde cabe `return x`. |
| 16 | LOW | 14, 22 | Regex de e-mail frouxo e triplicado; imports não usados | [utils/helpers.py:21](task-manager-api/utils/helpers.py#L21), [routes/user_routes.py:61](task-manager-api/routes/user_routes.py#L61), [106](task-manager-api/routes/user_routes.py#L106), [app.py:7](task-manager-api/app.py#L7), [routes/task_routes.py:7](task-manager-api/routes/task_routes.py#L7) | O regex aceita `a@b`; `os`, `sys`, `json` e `time` são importados sem uso. |

---

## B) Construção da Skill

### Anatomia

O `SKILL.md` é o **procedimento**: três fases, regras invioláveis e os formatos de saída. O **conhecimento** fica nos arquivos de referência, cada um lido só na fase que precisa dele.

| Área de conhecimento exigida | Arquivo | Conteúdo | Lido em |
|---|---|---|---|
| Análise de projeto | `analise-de-projeto.md` | Inventário de arquivos; detecção de linguagem (8), framework (11) e banco; mapeamento de rotas; matriz de responsabilidades e rubrica de arquitetura; inferência de domínio | Fase 1 |
| Catálogo de anti-patterns | `catalogo-anti-patterns.md` | 24 anti-patterns com sinais de detecção, falsos positivos, severidade e escalonamento; tabela de 28 APIs deprecated | Fase 2 |
| Template de relatório | `template-relatorio.md` | Estrutura, regras de ordenação e numeração, seções de APIs deprecated e Breaking Changes, exemplos preenchidos | Fase 2 |
| Guidelines de arquitetura | `guidelines-arquitetura.md` | Camadas, regra de dependência, proibições verificáveis por grep, caminhos por ponto de partida, fatia vertical de referência em Python e JS | Fase 3 |
| Playbook de refatoração | `playbook-refatoracao.md` | 17 transformações com antes/depois em Python e JavaScript e armadilhas que quebram contrato | Fase 3 |
| *(extra)* Validação | `protocolo-validacao.md` | Ambiente, estado reprodutível, boot, `smoke.sh`, baseline, diff e varredura final | Fases 1 e 3 |

### Decisões de design

1. **Procedimento enxuto, conhecimento sob demanda.** O `SKILL.md` tem uma tabela dizendo qual referência ler em cada momento. A Fase 1 não carrega o playbook e a Fase 3 não carrega as heurísticas de detecção, o que mantém o contexto do agente focado na tarefa da fase.
2. **Invocação só manual.** `disable-model-invocation: true` no frontmatter: uma skill que reescreve o projeto inteiro não deve ser acionada por inferência do modelo, só quando alguém digita `/refactor-arch`.
3. **Confirmação com mecanismo concreto.** "Pedir confirmação" virou instrução operacional: usar `AskUserQuestion` quando disponível; senão, terminar o turno com `[s/n]` e esperar. Qualquer resposta ambígua encerra a skill, e em execução não interativa ela para na Fase 2. Antes da aprovação, a única escrita permitida é em `.refactor-arch/`.
4. **Baseline antes de tocar no código.** "Os endpoints continuam respondendo" só é verificável comparando com o comportamento anterior. A Fase 1 sobe a aplicação original e grava a resposta de cada rota; a Fase 3 repete e compara. A comparação usa status, tipo de corpo e **estrutura de chaves** (não valores, que variam legitimamente), o que detecta um campo `senha` sumindo ou uma lista virando erro.
5. **Contrato preservado por padrão.** Quebras de contrato só são aceitas para corrigir findings CRITICAL de segurança — por exemplo, remover `/admin/query` ou tirar `senha` dos payloads. Cada quebra aparece como `BC-xx` no relatório **antes** da aprovação, e a validação classifica toda divergência não declarada como regressão.
6. **Evidência obrigatória.** Findings só com `arquivo:linha` conferidos lendo o código; depreciação só com fonte (aviso em runtime, saída do instalador ou versão de remoção); saída final com `✓`/`✗` sem suavizar falhas.
7. **Adaptação ao ponto de partida.** A rubrica da Fase 1 separa monolito, God Class, camadas parciais e camadas adequadas. Monolitos ganham a estrutura canônica em `src/`, com o entry point documentado mantido na raiz. Projetos com camadas parciais evoluem no lugar: `routes/` é reconhecido como Views em vez de renomeado, e o `app` importado por `seed.py` continua exportado.
8. **Artefatos isolados e sem commits.** Relatório, baseline, logs e evidências ficam em `.refactor-arch/` (ignorado pelo git). Versionar é decisão humana.

### Catálogo: quais anti-patterns e por quê

Os 24 anti-patterns saíram da análise manual, generalizados para outras stacks. Cada um aparece em pelo menos um dos três projetos, e a maioria em dois ou três — que é o que torna a skill reutilizável em vez de sob medida para um projeto.

| AP | Anti-pattern | Severidade | P1 | P2 | P3 |
|---|---|---|:-:|:-:|:-:|
| 01 | SQL Injection por concatenação | CRITICAL | ✔ | | |
| 02 | Segredos e credenciais hardcoded | CRITICAL | ✔ | ✔ | ✔ |
| 03 | Exposição de dados sensíveis | CRITICAL | ✔ | ✔ | ✔ |
| 04 | Armazenamento inseguro de senha | CRITICAL | ✔ | ✔ | ✔ |
| 05 | Operação privilegiada sem controle de acesso | CRITICAL | ✔ | ✔ | ✔ |
| 06 | God Class / God Module | CRITICAL | ✔ | ✔ | |
| 07 | Regra de negócio na camada HTTP | HIGH | ✔ | | ✔ |
| 08 | Estado global mutável | HIGH | ✔ | ✔ | |
| 09 | Operação multi-passo sem transação | HIGH | ✔ | ✔ | |
| 10 | Configuração de execução insegura | HIGH | ✔ | | ✔ |
| 11 | Acoplamento forte sem injeção de dependência | HIGH | | ✔ | |
| 12 | Aninhamento profundo / callback hell | HIGH | | ✔ | |
| 13 | Query N+1 | MEDIUM | ✔ | ✔ | ✔ |
| 14 | Validação ausente ou duplicada | MEDIUM | ✔ | ✔ | ✔ |
| 15 | Tratamento de erro não centralizado | MEDIUM | ✔ | ✔ | ✔ |
| 16 | CORS permissivo | MEDIUM | ✔ | | ✔ |
| 17 | Listagem sem paginação | MEDIUM | ✔ | | ✔ |
| 18 | Integridade referencial não garantida | MEDIUM | | ✔ | |
| 19 | API deprecated ou dependência sem suporte | MEDIUM | | ✔ | ✔ |
| 20 | Logging via `print` / `console.log` | LOW | ✔ | ✔ | |
| 21 | Magic numbers e literais duplicados | LOW | ✔ | | ✔ |
| 22 | Código morto | LOW | ✔ | | ✔ |
| 23 | Nomenclatura pobre e código verboso | LOW | | ✔ | ✔ |
| 24 | Serialização manual duplicada | LOW | ✔ | | |

- **CRITICAL** cobre o que expõe dados ou destrói a separação de camadas. Credenciais, exposição de dados sensíveis, senhas fracas e endpoints privilegiados abertos aparecem **nos três projetos**: são o núcleo do catálogo.
- **HIGH** cobre violações de MVC/SOLID que travam manutenção e testes. Callback hell e gateway acoplado vieram do Node; o estado global e a falta de transação, de ambas as stacks.
- **MEDIUM** inclui AP-19 (APIs deprecated), exigido pelo enunciado, com uma tabela de substitutos para Python, SQLAlchemy, Flask, Werkzeug, Node, Express, npm e Mongoose — além das stacks dos projetos, para não ficar sob medida.
- **LOW** fica com legibilidade e higiene, com uma ressalva explícita: chaves JSON públicas mal nomeadas são reportadas, mas não renomeadas.

As regras de escalonamento tratam os casos de fronteira — dependência deprecated **com** vulnerabilidade conhecida sobe para HIGH (projeto 2); MD5 em senha é AP-04, não AP-19 (projeto 3).

### Como a skill se mantém agnóstica de tecnologia

- **Detecção por sinais, não por nomes.** A matriz de responsabilidades classifica cada arquivo pelo que ele faz (HTTP, dados, regra, integração…). Um `models.py` que executa regra de negócio é identificado como tal, e uma pasta `services/` sem uso não conta como camada de serviço.
- **Sinais com variantes por stack e falsos positivos documentados.** Exemplos: `Task.title.like(f"%{q}%")` do SQLAlchemy **não** é SQL Injection (vira bind parameter); `db = SQLAlchemy()` com `init_app` **não** é estado global problemático.
- **Playbook bilíngue.** Cada transformação tem antes/depois em Python e JavaScript, com domínios genéricos; o que se copia é o padrão.
- **Validação pela interface HTTP.** `curl` + `diff` não dependem da linguagem do alvo, e a tabela de override de porta cobre Flask, FastAPI, Django e Node.
- **Uma única cópia da skill.** Os três diretórios `.claude/skills/refactor-arch/` são byte-idênticos (conferível com `shasum`, seção D). Se um projeto precisasse de ajuste, a skill teria falhado.

### Desafios encontrados e como foram resolvidos

Todos surgiram ao executar os projetos originais durante a construção da skill, não em hipótese.

| Desafio | Evidência | Solução |
|---|---|---|
| Porta 5000 ocupada no macOS | `python app.py` → `Address already in use`; `curl :5000` → `403` com `Server: AirTunes` (AirPlay Receiver). Uma checagem ingênua de prontidão daria a aplicação como "no ar". | Protocolo A3: verificar o dono da porta com `lsof` antes de confiar no `curl`; subir em porta alternativa **sem editar código** (`flask --app app run --port N --no-reload`); depois da refatoração, a porta vem da configuração. |
| `generate_password_hash()` padrão quebra em runtime | O Python 3.9.6 do sistema usa LibreSSL 2.8.3, sem `hashlib.scrypt` — o método padrão do Werkzeug 3 → `AttributeError`. | T05 fixa `pbkdf2:sha256` e documenta a armadilha. Sem isso, a Fase 3 do projeto 3 derrubaria o login. |
| Depreciações invisíveis por padrão | `LegacyAPIWarning` só aparece com `-W default` **e** quando a rota é exercitada. | AP-19 exige evidência; a validação ativa os avisos e relê o log **depois** do replay. |
| Respostas cujos valores mudam a cada execução | ids, datas e totais variam. | O smoke test compara caminhos de chave até 4 níveis, unindo os elementos de listas. ▶ 23 requisições no projeto 1, duas execuções com banco limpo, saídas idênticas. |
| Shell do usuário é zsh | Uma URL com `?` abortou um comando (`no matches found`) e deixou um servidor órfão; `kill $pids` não divide PIDs no zsh. | Paths entre aspas simples no `smoke.sh`; encerramento com `for pid in $(lsof -ti …)`. |
| Modo debug com reloader | O PID do comando não é o processo que escuta a porta. | Encerramento sempre pela porta, nunca pelo PID. |
| Datas naive × aware ao trocar `utcnow()` | `datetime.now(timezone.utc)` quebra comparações com colunas sem timezone e muda o texto das datas nas respostas. | T12 introduz um helper `utcnow()` que devolve UTC sem `tzinfo`. |
| `@app.errorhandler(Exception)` engole 404/405 | Rota inexistente passaria a responder 500. | T10 registra um handler de `HTTPException` que preserva o comportamento nativo. |
| Exemplos de código inválidos | A checagem automática encontrou 5 blocos que eram fragmentos sem sintaxe válida. | Todos os blocos Python e JavaScript das referências passam em `ast.parse` e `node --check`. |

---

## C) Resultados

> ⏳ **Pendente.** Esta seção é preenchida depois de executar a skill nos três projetos ([seção D](#d-como-executar)).

### Resumo dos relatórios de auditoria

| Projeto | Análise manual | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---|---|---|---|---|---|
| `code-smells-project` | 17 | — | — | — | — | — | [audit-project-1.md](reports/audit-project-1.md) |
| `ecommerce-api-legacy` | 16 | — | — | — | — | — | [audit-project-2.md](reports/audit-project-2.md) |
| `task-manager-api` | 16 | — | — | — | — | — | [audit-project-3.md](reports/audit-project-3.md) |

### Estrutura antes e depois

**Projeto 1 — `code-smells-project`**

```
ANTES                                              DEPOIS
code-smells-project/                               <árvore impressa pela Fase 3>
├── app.py          # app, config, rotas, admin
├── controllers.py  # HTTP + validação + notificações
├── models.py       # SQL de 4 domínios + regras
├── database.py     # conexão global, schema, seed
└── requirements.txt
```

**Projeto 2 — `ecommerce-api-legacy`**

```
ANTES                                              DEPOIS
ecommerce-api-legacy/                              <árvore impressa pela Fase 3>
├── api.http
├── package.json
└── src/
    ├── app.js         # bootstrap do Express
    ├── AppManager.js  # God Class
    └── utils.js       # segredos, cache global, hash caseiro
```

**Projeto 3 — `task-manager-api`**

```
ANTES                                              DEPOIS
task-manager-api/                                  <árvore impressa pela Fase 3>
├── app.py         # app, config, create_all no import
├── database.py
├── seed.py
├── models/        # user, task, category
├── routes/        # regras, consultas e serialização
├── services/      # notification_service (sem uso)
└── utils/         # helpers (validador sem uso)
```

### Checklist de validação

<details>
<summary><strong>Projeto 1 — code-smells-project</strong></summary>

#### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade (4)

#### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

#### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente

</details>

<details>
<summary><strong>Projeto 2 — ecommerce-api-legacy</strong></summary>

#### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade (3)

#### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

#### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente

</details>

<details>
<summary><strong>Projeto 3 — task-manager-api</strong></summary>

#### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente (Task Manager)
- [ ] Número de arquivos analisados condiz com a realidade (15)

#### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

#### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente

</details>

### Evidências de execução

> Colar por projeto: o bloco `FASE 3: REFATORAÇÃO CONCLUÍDA`, a seção "Smoke test" de `.refactor-arch/validacao.md` e um trecho de `boot-depois.log`.

### Comportamento da skill em stacks diferentes

> Registrar após as execuções: diferenças de detecção entre Flask e Express, como a Fase 3 tratou o monolito (P1), a God Class (P2) e as camadas parciais (P3), e quantas iterações nas referências foram necessárias.

---

## D) Como Executar

### Pré-requisitos

| Ferramenta | Versão usada na construção | Para quê |
|---|---|---|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview), autenticado | — | Executar a skill |
| Python | 3.9.6 | Projetos 1 e 3 |
| Node.js / npm | 22.23.1 / 10.9.8 | Projeto 2 |
| `bash`, `curl`, `lsof`, `python3` | bash 3.2, curl 8.7 | Smoke test do protocolo de validação |

> **macOS:** o AirPlay Receiver ocupa a porta 5000, usada pelos dois projetos Flask. A skill detecta o conflito e sobe em outra porta. Para liberar a 5000, desative em *Ajustes do Sistema → Geral → AirDrop e Handoff → Receptor AirPlay*.

A skill instala as dependências sozinha na Fase 1 (`.venv/` e `node_modules/`, ambos ignorados pelo git).

### 1. Commitar a skill antes de executá-la

Assim, uma refatoração ruim pode ser desfeita com `git restore` sem arriscar a pasta da skill, que ainda não está versionada.

```bash
git add .gitignore DESAFIO.md README.md reports/.gitkeep \
        code-smells-project/.claude ecommerce-api-legacy/.claude task-manager-api/.claude
git commit -m "feat: skill refactor-arch + análise manual dos 3 projetos"
```

Confira que as três cópias da skill são idênticas — cada hash deve aparecer 3 vezes:

```bash
shasum -a 256 */.claude/skills/refactor-arch/* | awk '{print $1}' | sort | uniq -c
```

### 2. Executar em cada projeto

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"
```

O fluxo esperado:

1. **Fase 1** imprime `FASE 1: ANÁLISE DO PROJETO` e grava o baseline em `.refactor-arch/baseline.txt`.
2. **Fase 2** imprime o relatório completo e pergunta se deve prosseguir. Revise a seção **Breaking Changes propostos** antes de aprovar.
3. **Fase 3** refatora, valida e imprime `FASE 3: REFATORAÇÃO CONCLUÍDA`, com `✓`/`✗` por verificação.

Ao terminar, copie o relatório e commite:

```bash
cp .refactor-arch/relatorio-auditoria.md ../reports/audit-project-1.md
cd ..
git add code-smells-project reports/audit-project-1.md
git commit -m "refactor(code-smells-project): MVC via refactor-arch"
```

Repita para os demais:

| Projeto | Diretório | Relatório | Mensagem de commit |
|---|---|---|---|
| 2 | `ecommerce-api-legacy` | `reports/audit-project-2.md` | `refactor(ecommerce-api-legacy): MVC via refactor-arch` |
| 3 | `task-manager-api` | `reports/audit-project-3.md` | `refactor(task-manager-api): MVC via refactor-arch` |

### 3. Validar a refatoração

**Pela evidência da skill** — `.refactor-arch/validacao.md` precisa mostrar **zero regressões**: toda divergência em relação ao baseline corresponde a um `BC-xx` aprovado.

**Manualmente** — com banco recém-criado (mova o `.db` do projeto para outro lugar e, no projeto 3, rode `python seed.py`):

```bash
# terminal 1 — dentro do projeto, depois da refatoração (a porta vem da configuração)
PORT=5051 .venv/bin/python app.py        # projetos Flask
PORT=3000 npm start                      # projeto Node

# terminal 2
bash .refactor-arch/smoke.sh 'http://127.0.0.1:5051' > /tmp/agora.txt
diff .refactor-arch/baseline.txt /tmp/agora.txt
```

O `diff` deve conter apenas as linhas listadas em *Breaking Changes*. Depois, marque o checklist do projeto na [seção C](#checklist-de-validação).

### 4. Se a skill não atingir os critérios

O enunciado prevê de 2 a 4 iterações. Anote o que falhou (findings a menos, relatório fora do template, regressão no smoke test), ajuste o arquivo de referência responsável e reexecute do zero:

```bash
git restore --source=HEAD --staged --worktree -- code-smells-project
git clean -fdn -- code-smells-project    # confira o que seria removido
git clean -fd  -- code-smells-project    # remove arquivos novos criados pela refatoração
```

Como `.venv/`, `node_modules/` e `.refactor-arch/` são ignorados pelo git, o `git clean -fd` (sem `-x`) os preserva. Ajustes na skill devem ser feitos no projeto 1 e copiados para os outros dois, mantendo as três cópias idênticas.
