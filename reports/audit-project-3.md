================================
RELATÓRIO DE AUDITORIA DE ARQUITETURA
================================
Projeto:  task-manager-api
Stack:    Python 3.9.6 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.0.54)
Arquivos: 15 analisados | ~1158 linhas de código
Data:     2026-10-10

## Resumo
CRITICAL: 3 | HIGH: 3 | MEDIUM: 7 | LOW: 5

| # | Severidade | Anti-pattern | Local principal |
|---|---|---|---|
| F-01 | CRITICAL | Segredos e credenciais hardcoded (AP-02) | app.py:13 |
| F-02 | CRITICAL | Exposição de dados sensíveis — senha/hash na resposta (AP-03) | models/user.py:22 |
| F-03 | CRITICAL | Armazenamento inseguro de senha — MD5 sem salt (AP-04) | models/user.py:29 |
| F-04 | HIGH | Autenticação falsa / operação privilegiada sem controle (AP-05) | routes/user_routes.py:210 |
| F-05 | HIGH | Regra de negócio e acesso a dados na camada HTTP (AP-07) | routes/task_routes.py:11-299 |
| F-06 | HIGH | Configuração de execução insegura (AP-10) | app.py:34 |
| F-07 | MEDIUM | Query N+1 (AP-13) | routes/task_routes.py:41-57 |
| F-08 | MEDIUM | Validação ausente ou duplicada (AP-14) | routes/task_routes.py:96-114 |
| F-09 | MEDIUM | Tratamento de erro não centralizado (AP-15) | routes/task_routes.py:62 |
| F-10 | MEDIUM | CORS permissivo (AP-16) | app.py:15 |
| F-11 | MEDIUM | Listagem sem paginação (AP-17) | routes/task_routes.py:14 |
| F-12 | MEDIUM | Integridade referencial não garantida (AP-18) | routes/user_routes.py:140-142 |
| F-13 | MEDIUM | APIs deprecated (AP-19) | models/task.py:15 |
| F-14 | LOW | Logging via `print` (AP-20) | routes/task_routes.py:149 |
| F-15 | LOW | Magic numbers e literais duplicados (AP-21) | routes/task_routes.py:110 |
| F-16 | LOW | Código morto (AP-22) | services/notification_service.py:1-49 |
| F-17 | LOW | Nomenclatura pobre e código verboso (AP-23) | models/task.py:38-60 |
| F-18 | LOW | Serialização manual duplicada (AP-24) | routes/task_routes.py:17-28 |

## Findings

### F-01 [CRITICAL] Segredos e credenciais hardcoded (AP-02)
Arquivo: app.py:13
Ocorrências: services/notification_service.py:9-10 (`email_user = 'taskmanager@gmail.com'`, `email_password = 'senha123'`)
Descrição: `app.config['SECRET_KEY'] = 'super-secret-****'` fixa a chave de assinatura de sessão em código versionado (app.py:13). O `NotificationService.__init__` grava usuário e senha SMTP literais (notification_service.py:9-10). A URI do banco também é literal (app.py:11).
Impacto: qualquer pessoa com acesso ao repositório obtém a `SECRET_KEY` (pode forjar sessões/cookies assinados) e as credenciais de e-mail; rotacionar exige novo deploy.
Recomendação: mover `SECRET_KEY`, URI do banco e credenciais SMTP para variáveis de ambiente lidas por uma classe de configuração, com `.env.example` documentando as chaves (sem valores reais) — Playbook T02.
Contrato: preservado

### F-02 [CRITICAL] Exposição de dados sensíveis — senha/hash na resposta (AP-03)
Arquivo: models/user.py:16-25
Ocorrências: routes/user_routes.py:85-86 (POST /users), routes/user_routes.py:129 (PUT /users/<id>), routes/user_routes.py:33 (GET /users/<id>), routes/user_routes.py:207-211 (POST /login)
Descrição: `User.to_dict()` inclui a chave `'password'` com o hash da senha (models/user.py:22). Todos os endpoints que serializam usuário via `to_dict()` devolvem o hash ao cliente: criação, atualização, detalhe e login. `GET /users` (listagem) **não** expõe — divergência perigosa de serialização (ver F-18).
Impacto: vazamento do hash de senha de qualquer usuário por requisição anônima; combinado com o MD5 sem salt (F-03), as senhas são recuperáveis em segundos. Violação de LGPD.
Recomendação: remover `password` da serialização do usuário em todos os pontos, centralizando num schema/serializer único — Playbook T13.
Contrato: exige BC-01

### F-03 [CRITICAL] Armazenamento inseguro de senha — MD5 sem salt (AP-04)
Arquivo: models/user.py:27-32
Ocorrências: Nenhuma adicional
Descrição: `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()` (models/user.py:29) e `check_password` compara por igualdade de MD5 (models/user.py:32). MD5 é hash rápido e sem salt. (O uso de MD5 também seria AP-19 por algoritmo fraco; consolidado aqui sob AP-04 por ser o mais severo.)
Impacto: com um dump do banco, as senhas caem em segundos (tabelas rainbow / brute force em GPU); reuso de senha compromete outros sistemas dos usuários.
Recomendação: usar `werkzeug.security.generate_password_hash` / `check_password_hash` (já disponível via dependência Werkzeug do Flask), que aplica salt e algoritmo forte — Playbook T05. O seed (`python seed.py`) regenera os hashes, então o fluxo documentado continua funcionando.
Contrato: preservado (muda apenas o valor armazenado do hash, não a estrutura das respostas; o seed re-hasheia no estado inicial)

### F-04 [HIGH] Autenticação falsa / operação privilegiada sem controle (AP-05)
Arquivo: routes/user_routes.py:185-211
Ocorrências: routes/task_routes.py:225-238 (DELETE /tasks), routes/user_routes.py:134-151 (DELETE /users), routes/report_routes.py:211-223 (DELETE /categories)
Descrição: `login` emite um token não assinado e previsível: `'fake-jwt-token-' + str(user.id)` (user_routes.py:210). Nenhuma rota verifica token algum — todos os endpoints, inclusive os destrutivos (DELETE de tasks, users e categories), são acessíveis anonimamente.
Impacto: qualquer cliente anônimo pode criar, alterar e apagar tasks, usuários e categorias; o token não serve como credencial de autorização.
Recomendação: (a) substituir o token falso por um assinado com `itsdangerous`/`SECRET_KEY` (melhoria sem quebra de contrato); (b) impor autenticação/autorização nas rotas privilegiadas via decorator — Playbook T14. Observação de contrato: **impor** auth faria rotas hoje abertas passarem a responder 401/403, o que quebraria o contrato atual e **não** é autorizado para finding HIGH; portanto a Fase 3 aplica só a parte (a) e deixa a parte (b) como recomendação.
Contrato: preservado (assinatura do token não muda o shape da resposta de `/login`; a imposição de auth não será aplicada por exigir quebra não autorizada)

### F-05 [HIGH] Regra de negócio e acesso a dados na camada HTTP (AP-07)
Arquivo: routes/task_routes.py:11-299
Ocorrências: routes/user_routes.py:10-211, routes/report_routes.py:12-223
Descrição: os handlers concentram HTTP + acesso a dados + regra + validação + serialização. Exemplos: `get_tasks` consulta o ORM e calcula atraso e enriquecimento (task_routes.py:14-59); `task_stats` agrega contagens e taxa de conclusão (task_routes.py:273-299); `summary_report` monta todo o relatório com loops e agregações (report_routes.py:13-101); `user_report` classifica tasks por status/prioridade/atraso em laço (report_routes.py:119-135). Nenhuma camada de serviço é usada (a única, `NotificationService`, está morta — F-16).
Impacto: regra impossível de reutilizar (CLI, fila, outro endpoint) e de testar sem subir HTTP; duplicação (cálculo de atraso repetido em 4 lugares, ver F-18).
Recomendação: extrair regras e acesso a dados para serviços/repositórios por domínio, deixando controllers finos que só orquestram entrada→serviço→status — Playbook T04.
Contrato: preservado

### F-06 [HIGH] Configuração de execução insegura (AP-10)
Arquivo: app.py:34
Ocorrências: app.py:11-13 (config literal), app.py:30-31 (`db.create_all()` em nível de módulo)
Descrição: `app.run(debug=True, host='0.0.0.0', port=5000)` fixa debug e host no código (app.py:34). Com `debug=True` o debugger do Werkzeug permite execução remota de código. Porta/host/config são literais sem leitura de ambiente (app.py:11-13). `db.create_all()` roda no import do módulo (app.py:30-31), criando schema como efeito colateral de importação.
Impacto: execução remota de código via debugger exposto em `0.0.0.0`; impossível configurar ambientes distintos sem editar código; efeito colateral de schema no import dificulta testes e scripts.
Recomendação: ler `DEBUG`, `HOST`, `PORT`, `SECRET_KEY` e URI do ambiente via classe de config; mover `db.create_all()` para a factory/`__main__` e aceitar `PORT` por ambiente — Playbook T02.
Contrato: preservado (comando `python app.py` segue subindo na porta 5000 por default)

### F-07 [MEDIUM] Query N+1 (AP-13)
Arquivo: routes/task_routes.py:41-57
Ocorrências: routes/user_routes.py:22 (`len(u.tasks)` por usuário em laço), routes/report_routes.py:56-61 (`Task.query.filter_by(user_id=u.id)` por usuário), routes/report_routes.py:163 (`Task.query.filter_by(category_id=c.id).count()` por categoria)
Descrição: `get_tasks` consulta `User.query.get` e `Category.query.get` dentro do laço sobre todas as tasks (task_routes.py:42-57). `summary_report` roda uma query por usuário (report_routes.py:56) e `get_categories` uma contagem por categoria (report_routes.py:163). Além disso, `task_stats`/`summary_report` disparam vários `COUNT(*)` por status/prioridade que caberiam num agrupamento.
Impacto: número de consultas cresce linearmente com o volume; listagens e relatórios ficam lentos com muitos registros.
Recomendação: usar `joinedload`/`selectinload` ou joins e agregações `GROUP BY` na camada de dados — Playbook T08.
Contrato: preservado

### F-08 [MEDIUM] Validação ausente ou duplicada (AP-14)
Arquivo: routes/task_routes.py:96-114
Ocorrências: routes/task_routes.py:166-213 (mesmas regras de título/status/prioridade repetidas em `update_task`), routes/user_routes.py:61 e routes/user_routes.py:106 (regex de e-mail duplicado), utils/helpers.py:57-108 (`process_task_data`, validador completo nunca chamado), utils/helpers.py:19-55 (`validate_email`, `is_valid_color` etc. mortos)
Descrição: as regras de tamanho de título (3–200), status válido e prioridade 1–5 são escritas à mão em `create_task` e de novo em `update_task`. O regex de e-mail aparece literal em dois handlers. Existe um validador pronto (`process_task_data`) e vários helpers de validação em `utils/helpers.py` que **nenhum** handler usa (ver F-16). Em `update_task`, `data['priority'] < 1` (task_routes.py:182) assume inteiro: um valor string resultaria em erro 500.
Impacto: regras divergem com o tempo entre criar e atualizar; entrada inválida pode gerar 500; validador correto fica apodrecendo sem uso.
Recomendação: centralizar validação num schema único (usar `marshmallow`, já declarado) consumido por create e update — Playbook T09.
Contrato: preservado

### F-09 [MEDIUM] Tratamento de erro não centralizado (AP-15)
Arquivo: routes/task_routes.py:62
Ocorrências: routes/task_routes.py:236 (`except:` nu), routes/task_routes.py:151-154, routes/task_routes.py:221-223, routes/user_routes.py:87-90, routes/user_routes.py:130-132, routes/user_routes.py:149-151, routes/report_routes.py:186-188, routes/report_routes.py:207-209, routes/report_routes.py:221-223 (blocos `except ... rollback ... jsonify(erro) 500` repetidos); ausência de `@app.errorhandler`
Descrição: `get_tasks` e `delete_task` usam `except:` nu (task_routes.py:62,236), que engole qualquer erro e sempre responde 500 genérico. O padrão `try/except Exception/rollback/return 500` é copiado em quase todos os handlers de escrita. Não há handler de erro global registrado.
Impacto: bugs silenciosos, respostas inconsistentes e duplicação do tratamento de erro em cada handler.
Recomendação: registrar `@app.errorhandler` por tipo (validação→400, não encontrado→404, genérico→500) e remover os `try/except` repetidos dos handlers — Playbook T10.
Contrato: preservado (mesmos status codes e formato `{"error": ...}`)

### F-10 [MEDIUM] CORS permissivo (AP-16)
Arquivo: app.py:15
Ocorrências: Nenhuma adicional
Descrição: `CORS(app)` (app.py:15) habilita CORS para qualquer origem, sem restrição de `origins`/`resources`.
Impacto: qualquer site pode chamar a API a partir do navegador de um usuário.
Recomendação: restringir `origins` a uma lista configurável por ambiente — Playbook T02.
Contrato: preservado (sem credenciais cross-origin no fluxo atual)

### F-11 [MEDIUM] Listagem sem paginação (AP-17)
Arquivo: routes/task_routes.py:14
Ocorrências: routes/task_routes.py:266 (search), routes/user_routes.py:12, routes/report_routes.py:159, routes/report_routes.py:30 (carrega todas as tasks em memória)
Descrição: `get_tasks`, `search_tasks`, `get_users`, `get_categories` e `summary_report` devolvem/consomem `Model.query.all()` sem limite.
Impacto: memória e tempo de resposta crescem com o volume; uma tabela grande pode derrubar o endpoint.
Recomendação: paginação **opcional** (`?page`/`?per_page`) preservando o formato de lista quando os parâmetros não são enviados — Playbook T17.
Contrato: preservado (paginação só quando solicitada)

### F-12 [MEDIUM] Integridade referencial não garantida (AP-18)
Arquivo: routes/user_routes.py:140-142
Ocorrências: routes/report_routes.py:211-223 (delete_category não trata tasks com aquele `category_id`), models/task.py:13-14 (FKs sem `ondelete`)
Descrição: `delete_user` faz cascata manual apagando as tasks do usuário em laço (user_routes.py:140-142). `delete_category` apaga a categoria sem tratar as tasks que a referenciam, deixando `category_id` órfão. As FKs em `Task` (models/task.py:13-14) não definem `ondelete`, e o SQLite não força `PRAGMA foreign_keys` por padrão.
Impacto: tasks com `category_id` apontando para categoria inexistente; relatórios com dados inconsistentes.
Recomendação: definir comportamento explícito de FK (cascade/set null) no modelo e tratar dependentes dentro de uma operação transacional de serviço — Playbook T15.
Contrato: preservado

### F-13 [MEDIUM] APIs deprecated (AP-19)
Arquivo: models/task.py:15
Ocorrências: `datetime.utcnow()` em models/task.py:15-16, models/category.py:11, models/user.py:14, routes/task_routes.py:31,72,215,285, routes/user_routes.py:172, routes/report_routes.py:35,42,45,46,71,133; `Model.query.get()` (API legada SQLAlchemy 2.x) em routes/task_routes.py:42,51,67,158,227, routes/user_routes.py:29,94,117(indireto),136,155, routes/report_routes.py:105,192,213 (16 ocorrências de `.query.get(`)
Descrição: `datetime.utcnow()` está deprecated desde o Python 3.12 (substituto `datetime.now(timezone.utc)`). `Model.query.get(id)` é API legada no SQLAlchemy 2.x — confirmado em runtime com `LegacyAPIWarning` (ver `.refactor-arch/deprecation-evidence.log`); substituto `db.session.get(Model, id)`.
Impacto: avisos de depreciação hoje; quebra em versões futuras do Python/SQLAlchemy.
Recomendação: trocar por `datetime.now(timezone.utc)` e `db.session.get(Model, id)` ao mover o acesso a dados para a camada de modelos/repositórios — Playbook T12.
Contrato: preservado (o campo de data continua serializado via `str(...)`)

### F-14 [LOW] Logging via `print` (AP-20)
Arquivo: routes/task_routes.py:149
Ocorrências: routes/task_routes.py:153,219,234, routes/user_routes.py:83,89,147, services/notification_service.py:21,24
Descrição: handlers e serviço usam `print(...)` para diagnóstico (ex.: "Task criada", "ERRO: ...") sem níveis nem destino configurável. (Os `print` em seed.py são progresso de script CLI — falso positivo, preservados.)
Impacto: logs sem estrutura, nível ou controle de destino.
Recomendação: usar o módulo `logging` com níveis apropriados — Playbook T16.
Contrato: preservado

### F-15 [LOW] Magic numbers e literais duplicados (AP-21)
Arquivo: routes/task_routes.py:110
Ocorrências: lista de status `['pending','in_progress','done','cancelled']` repetida em routes/task_routes.py:110,177, models/task.py:39, utils/helpers.py:75,110; tamanhos de título 3/200 em routes/task_routes.py:96-100,167-170; prioridade 1/5 em routes/task_routes.py:113,182, models/task.py:46; senha mínima 4 em routes/user_routes.py:64,115; roles em routes/user_routes.py:71,120; constantes `VALID_STATUSES`/`MAX_TITLE_LENGTH` etc. declaradas em utils/helpers.py:110-116 mas **não usadas**
Descrição: valores de negócio espalhados como literais, enquanto existem constantes nomeadas correspondentes nunca referenciadas.
Impacto: mudança de regra exige editar vários pontos; risco de divergência.
Recomendação: consolidar em constantes/enums num único módulo e referenciá-las — Playbook T16.
Contrato: preservado

### F-16 [LOW] Código morto (AP-22)
Arquivo: services/notification_service.py:1-49
Ocorrências: imports não usados em app.py:7 (`os, sys, json`), routes/task_routes.py:7 (`json, os, sys, time`), routes/user_routes.py:6 (`hashlib, json`), routes/report_routes.py:8 (`json`); `utils/helpers.py` inteiro sem uso efetivo (`format_date`/`calculate_percentage` importados em report_routes.py:7 mas nunca chamados; `process_task_data`, `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `is_valid_color` sem referência); dependências declaradas e nunca importadas: `marshmallow`, `requests`, `python-dotenv`
Descrição: `NotificationService` nunca é instanciado em lugar algum (também exibe AP-02 — creds SMTP, AP-08 — `self.notifications = []` como armazenamento em memória, e AP-11 — `smtplib.SMTP` acoplado; todos sem impacto por estar morto). Vários imports e todo o `utils/helpers.py` não participam da execução. Três dependências do `requirements.txt` jamais são importadas.
Impacto: ruído, falsa impressão de funcionalidade, superfície de manutenção desnecessária.
Recomendação: remover imports e código mortos; decidir entre reaproveitar `marshmallow` (validação, T09) e remover `requests`/`python-dotenv` do manifesto, ou passar a usá-los — Playbook T16.
Contrato: preservado

### F-17 [LOW] Nomenclatura pobre e código verboso (AP-23)
Arquivo: models/task.py:38-60
Ocorrências: models/task.py:45-48 (`validate_priority`), models/task.py:50-60 (`is_overdue`, pirâmide de `if/else`), models/user.py:34-38 (`is_admin` com `if/else` retornando bool), cálculo de atraso em pirâmide em routes/task_routes.py:30-39,71-80, routes/user_routes.py:171-180
Descrição: funções que fazem `if cond: return True else: return False` em vez de `return cond`; aninhamento profundo de `if` para calcular atraso; variáveis de uma letra (`u`, `t`, `c`, `p`, `td`).
Impacto: legibilidade e manutenção.
Recomendação: simplificar para expressões booleanas e nomes descritivos — Playbook T16. (Chaves JSON públicas não são renomeadas.)
Contrato: preservado

### F-18 [LOW] Serialização manual duplicada (AP-24)
Arquivo: routes/task_routes.py:17-28
Ocorrências: routes/user_routes.py:162-169 (task remontada à mão), models/task.py:23-36 (`to_dict` existente), cálculo de atraso duplicado em routes/task_routes.py:30-39,71-80, routes/user_routes.py:171-180, routes/report_routes.py:34-37,132-135; serialização de usuário divergente (routes/user_routes.py:15-24 omite senha vs. models/user.py:16-25 inclui) — cruzamento com F-02
Descrição: a conversão de `Task` para dict é reescrita campo a campo em `get_tasks` e `get_user_tasks`, embora `Task.to_dict()` já exista. O cálculo de "overdue" aparece copiado em quatro lugares. A serialização de `User` diverge entre listagem (sem senha) e detalhe/login (com senha — perigoso, F-02).
Impacto: campos e formatos podem divergir entre endpoints; a divergência já expõe senha em uns e não em outros.
Recomendação: unificar a serialização num schema/serializer por entidade e um único `is_overdue` no modelo — Playbook T13.
Contrato: preservado (o shape de cada endpoint é mantido, exceto a remoção de `password` tratada em BC-01)

## APIs deprecated
| API ou dependência | Local | Substituto | Evidência |
|---|---|---|---|
| `datetime.utcnow()` | models/task.py:15-16, models/category.py:11, models/user.py:14, routes/task_routes.py:31,72,215,285, routes/user_routes.py:172, routes/report_routes.py:35,42,45,46,71,133 | `datetime.now(timezone.utc)` | deprecated no Python 3.12 (catálogo AP-19); runtime 3.9.6 não emite warning |
| `Model.query.get(id)` | 16 ocorrências de `.query.get(` em routes/*.py (ex.: task_routes.py:67, user_routes.py:29, report_routes.py:105) | `db.session.get(Model, id)` | `LegacyAPIWarning` confirmado em runtime — `.refactor-arch/deprecation-evidence.log` |
| `marshmallow`, `requests`, `python-dotenv` | requirements.txt:4-6 | — (nunca importadas) | busca por imports: nenhuma ocorrência (F-16) |

## Breaking Changes propostos
| # | Rota | Mudança no contrato | Finding que justifica |
|---|---|---|---|
| BC-01 | POST /users, PUT /users/<id>, GET /users/<id>, POST /login | remove a chave `password` do corpo da resposta (em `/login`, de `user.password`); todas as demais chaves permanecem | F-02 — hash de senha exposto em resposta a requisição anônima (CRITICAL de segurança) |

## Plano de refatoração
Ponto de partida: camadas parciais (pastas por papel existem, mas responsabilidades vazam para as rotas). A refatoração **refina** a estrutura, sem renomear o que já cumpre o papel certo (`models/`, `database.py`, `seed.py`).

Estrutura-alvo (resumo):
```
app.py                 # composition root / factory + entry point (__main__)
config.py              # configuração e segredos via ambiente (T02)
database.py            # extensão db (mantido)
extensions.py?         # CORS restrito (T02)  [ou dentro da factory]
errors.py              # handlers de erro globais (T10)
models/                # entidades + acesso a dados por domínio (T01/T03/T05/T08/T12/T15)
  user.py  task.py  category.py
services/              # regras de negócio e integrações (T04/T06/T09)
  task_service.py  user_service.py  category_service.py  report_service.py
  notification_service.py  (corrigido ou removido — F-16)
schemas/               # validação + serialização marshmallow (T09/T13)
  task_schema.py  user_schema.py  category_schema.py
routes/ (views/controllers)  # controllers finos + registro de rotas (T04/T13/T14/T17)
  task_routes.py  user_routes.py  category_routes.py  report_routes.py
utils/helpers.py       # só o que for de fato usado (T16)
seed.py                # mantido (contrato de execução)
```
Ordem de execução (por camada): config → models → services → controllers → views/routes → middlewares (erros) → composition root → limpeza. Transformações principais: T02 (config/CORS/db.create_all), T05 (hash seguro), T13 (serializer sem senha), T04 (extrair regra/dados para serviços), T08 (N+1), T09 (schemas), T10 (errorhandlers), T12 (deprecated), T15 (integridade), T16 (limpeza), T17 (paginação opcional), T14 (assinar token, sem impor auth).

================================
Total: 18 findings
================================
