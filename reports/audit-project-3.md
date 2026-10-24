================================
RELATÓRIO DE AUDITORIA DE ARQUITETURA
================================
Projeto:  task-manager-api
Stack:    Python 3.9.6 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.0.52)
Arquivos: 15 analisados | ~1158 linhas de código
Data:     2026-10-24

## Resumo
CRITICAL: 3 | HIGH: 3 | MEDIUM: 7 | LOW: 4

| # | Severidade | Anti-pattern | Local principal |
|---|---|---|---|
| F-01 | CRITICAL | Segredos hardcoded (AP-02) | app.py:13 |
| F-02 | CRITICAL | Exposição de dados sensíveis (AP-03) | models/user.py:16-25 |
| F-03 | CRITICAL | Armazenamento inseguro de senha (AP-04) | models/user.py:27-32 |
| F-04 | HIGH | Operação privilegiada sem controle de acesso (AP-05) | routes/user_routes.py:207-211 |
| F-05 | HIGH | Regra de negócio na camada HTTP (AP-07) | routes/report_routes.py:12-155 |
| F-06 | HIGH | Configuração de execução insegura (AP-10) | app.py:11-33 |
| F-07 | MEDIUM | Query N+1 (AP-13) | routes/task_routes.py:41-57 |
| F-08 | MEDIUM | Validação ausente ou duplicada (AP-14) | routes/task_routes.py:85-213 |
| F-09 | MEDIUM | Tratamento de erro não centralizado (AP-15) | routes/task_routes.py:62 |
| F-10 | MEDIUM | CORS permissivo (AP-16) | app.py:15 |
| F-11 | MEDIUM | Integridade referencial não garantida (AP-18) | routes/user_routes.py:140-142 |
| F-12 | MEDIUM | API deprecated (AP-19) | models/task.py:15-16 |
| F-13 | MEDIUM | Serialização manual duplicada (AP-24) | routes/task_routes.py:16-59 |
| F-14 | LOW | Logging via `print` (AP-20) | routes/task_routes.py:149 |
| F-15 | LOW | Magic numbers e literais duplicados (AP-21) | routes/task_routes.py:96-114 |
| F-16 | LOW | Código morto (AP-22) | services/notification_service.py:1-49 |
| F-17 | LOW | Nomenclatura pobre e código verboso (AP-23) | models/task.py:38-60 |

## Findings

### F-01 [CRITICAL] Segredos e credenciais hardcoded (AP-02)
Arquivo: app.py:13
Ocorrências: services/notification_service.py:7-10 (`email_user = 'taskmanager@gmail.com'`, `email_password = 'senha123'`)
Descrição: `app.config['SECRET_KEY'] = 'super-secret-****'` fixa a chave de assinatura da aplicação no código versionado (app.py:13). O `NotificationService.__init__` grava host, usuário e senha SMTP literais (`'senha***'`). As senhas de seed em `seed.py` são de script de desenvolvimento executado manualmente e não entram como finding (falso positivo do catálogo).
Impacto: qualquer pessoa com acesso ao repositório obtém a `SECRET_KEY` (permite forjar tokens/sessões) e as credenciais SMTP; rotacionar exige novo deploy.
Recomendação: mover segredos para variáveis de ambiente lidas numa camada de configuração, com `.env.example` documentando as chaves sem valores — Playbook T02.
Contrato: preservado

### F-02 [CRITICAL] Exposição de dados sensíveis (AP-03)
Arquivo: models/user.py:16-25
Ocorrências: routes/user_routes.py:33 (get_user), routes/user_routes.py:85 (create_user), routes/user_routes.py:129 (update_user), routes/user_routes.py:209 (login)
Descrição: `User.to_dict()` inclui a chave `password` (o hash MD5 — user.py:21). Esse dicionário é devolvido ao cliente, sem autenticação, em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e dentro de `user` na resposta de `POST /login`. Confirmado no baseline: as respostas dessas quatro rotas contêm `password`. `GET /users` (lista) monta dicionário próprio sem a senha, o que torna a divergência ainda mais perigosa (ver F-13).
Impacto: vazamento direto do hash de senha por requisição anônima; combinado ao MD5 (F-03), permite recuperar as senhas em segundos. Violação de LGPD.
Recomendação: remover `password` do serializador e nunca devolvê-lo — Playbook T13. A chave desaparece das respostas (quebra de contrato autorizada por ser finding de segurança CRITICAL).
Contrato: exige BC-01, BC-02, BC-03, BC-04

### F-03 [CRITICAL] Armazenamento inseguro de senha (AP-04)
Arquivo: models/user.py:27-32
Ocorrências: Nenhuma adicional
Descrição: `set_password()` grava `hashlib.md5(pwd.encode()).hexdigest()` (user.py:29) e `check_password()` compara MD5 (user.py:32). MD5 é hash rápido e sem salt. O mesmo trecho também configura AP-19 (algoritmo fraco), reportado aqui sob a severidade mais alta.
Impacto: com um dump do banco, as senhas são quebradas em segundos (rainbow tables, força bruta em GPU); o reuso de senha compromete outros sistemas dos usuários.
Recomendação: usar `werkzeug.security.generate_password_hash` / `check_password_hash` (já disponível via Flask) com algoritmo com salt — Playbook T05. O seed é reexecutado na validação, regerando os hashes; o login continua funcionando com as mesmas credenciais.
Contrato: preservado (o hash não é devolvido após F-02; `POST /login` segue retornando `token`)

### F-04 [HIGH] Operação privilegiada sem controle de acesso (AP-05)
Arquivo: routes/user_routes.py:207-211
Ocorrências: routes/task_routes.py:225-238 (DELETE task), routes/user_routes.py:134-151 (DELETE user), routes/report_routes.py:211-223 (DELETE category)
Descrição: `login()` devolve um token falso `'fake-jwt-token-' + str(user.id)` (user_routes.py:210), não assinado e não verificado. Nenhuma rota exige autenticação: as três rotas destrutivas `DELETE /tasks/<id>`, `DELETE /users/<id>` e `DELETE /categories/<id>` apagam dados a partir de qualquer cliente anônimo. Classificado HIGH: autenticação inexistente/falsa, dano restrito a remoção de registros (não há execução arbitrária nem destruição em massa).
Impacto: qualquer cliente anônimo apaga tarefas, usuários e categorias arbitrariamente.
Recomendação: emitir um token assinado real no login (ex.: `itsdangerous`, que acompanha o Flask, usando a `SECRET_KEY`) e exigir `Authorization: Bearer <token>` válido nas rotas destrutivas, retornando 401 sem credencial — Playbook T14. As rotas de escrita não destrutivas (POST/PUT) permanecem abertas para preservar o contrato; as destrutivas passam a exigir credencial.
Contrato: exige BC-05, BC-06, BC-07

### F-05 [HIGH] Regra de negócio na camada HTTP (AP-07)
Arquivo: routes/report_routes.py:12-155
Ocorrências: routes/task_routes.py:11-63 (get_tasks), routes/task_routes.py:273-299 (task_stats), routes/task_routes.py:240-271 (search_tasks), routes/user_routes.py:10-25 (get_users), routes/user_routes.py:153-183 (get_user_tasks)
Descrição: os handlers acessam o ORM diretamente e concentram agregação e regra de domínio. `summary_report` (report_routes.py:12-101) faz ~15 queries, laços de contagem por status/prioridade, cálculo de atraso e produtividade por usuário dentro da rota. `user_report` (103-155) repete a agregação. `task_stats` e `get_tasks` calculam `overdue` e `completion_rate` inline. A regra de atraso (`due_date < utcnow() and status not in ('done','cancelled')`) aparece replicada em 4 handlers.
Impacto: regra impossível de reutilizar e de testar sem subir HTTP; duplicação da lógica de atraso e de agregação entre rotas.
Recomendação: extrair repositórios por entidade (camada models/dados) e serviços de domínio (`TaskService`, `ReportService`, `UserService`) que concentrem agregação e a regra de atraso; os controllers só traduzem requisição/resposta — Playbook T03, T04.
Contrato: preservado

### F-06 [HIGH] Configuração de execução insegura (AP-10)
Arquivo: app.py:11-33
Ocorrências: Nenhuma adicional
Descrição: `app.run(debug=True, host='0.0.0.0', port=5000)` (app.py:33) ativa o debugger do Werkzeug (execução remota de código) exposto em todas as interfaces. A configuração (URI, flags, `SECRET_KEY`) está fixa no entry point (app.py:11-13) e `db.create_all()` roda no import do módulo (app.py:30-31).
Impacto: execução remota de código via debugger em produção; impossível configurar ambientes diferentes sem editar código; schema criado como efeito colateral de import.
Recomendação: mover configuração para uma camada dedicada lendo ambiente; `debug`, `host` e `port` vindos de config com defaults seguros; `db.create_all()` chamado explicitamente numa factory/composition root — Playbook T02, T11.
Contrato: preservado (porta e host passam a aceitar override por ambiente, mantendo defaults)

### F-07 [MEDIUM] Query N+1 (AP-13)
Arquivo: routes/task_routes.py:41-57
Ocorrências: routes/user_routes.py:22 (`len(u.tasks)` por usuário na listagem), routes/report_routes.py:56 (tasks por usuário em laço), routes/report_routes.py:163 (`Task.query.filter_by(category_id=c.id).count()` por categoria)
Descrição: `get_tasks` executa `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` dentro do laço sobre todas as tasks (task_routes.py:42,51) — uma consulta por item. `get_users` acessa `len(u.tasks)` (lazy) por usuário; `summary_report` consulta tasks por usuário em laço; `get_categories` conta tasks por categoria em laço.
Impacto: o tempo de resposta cresce linearmente com o volume; listagens disparam centenas de consultas.
Recomendação: usar `joinedload`/`selectinload` ou agregações com `GROUP BY` nos repositórios — Playbook T08.
Contrato: preservado

### F-08 [MEDIUM] Validação ausente ou duplicada (AP-14)
Arquivo: routes/task_routes.py:85-213
Ocorrências: routes/user_routes.py:54-72 vs 102-122 (validação de email/role/senha repetida em create e update), utils/helpers.py:57-108 (`process_task_data` — validador completo nunca chamado), routes/task_routes.py:113 (`priority < 1` sem conversão de tipo)
Descrição: as validações de título (3-200), status (enum literal), prioridade (1-5) e data estão copiadas entre `create_task` e `update_task` (task_routes.py:96-114 e 166-205). O mesmo vale para email/role/senha em `create_user`/`update_user`. Existe um validador pronto (`process_task_data`, helpers.py:57) que nenhuma rota usa. `priority` é comparado sem conversão (`data['priority'] < 1`), gerando 500 se vier como string.
Impacto: regras divergentes entre endpoints, erros 500 com entrada inválida, manutenção duplicada.
Recomendação: centralizar validação numa função/serviço por entidade, reutilizada em create e update — Playbook T09. (Marshmallow está declarado mas não usado — ver F-16.)
Contrato: preservado

### F-09 [MEDIUM] Tratamento de erro não centralizado (AP-15)
Arquivo: routes/task_routes.py:62
Ocorrências: routes/task_routes.py:62,151,221,236; routes/user_routes.py:87,130,149; routes/report_routes.py:186,207,221 (blocos `except`/`except:` espalhados), app.py (nenhum `@app.errorhandler`)
Descrição: cada handler trata exceções à sua maneira — `except:` nu em `get_tasks` (task_routes.py:62) engole qualquer erro e devolve 500 genérico; os demais repetem `except Exception` com rollback e mensagem própria. Não há handler global (`register_error_handler`).
Impacto: formatos de erro inconsistentes, bugs silenciosos (o `except:` nu mascara a causa), duplicação.
Recomendação: registrar um error handler central (middleware) que traduz exceções para JSON padronizado; remover os `try/except` genéricos dos handlers — Playbook T10.
Contrato: preservado (mantém status e formato `{"error": ...}`)

### F-10 [MEDIUM] CORS permissivo (AP-16)
Arquivo: app.py:15
Ocorrências: Nenhuma adicional
Descrição: `CORS(app)` libera todas as origens sem restrição de `origins`/`resources`. Não há `supports_credentials`, então permanece MEDIUM.
Impacto: qualquer site pode chamar a API a partir do navegador de um usuário.
Recomendação: restringir origens via configuração (lista de origens permitidas) — Playbook T02.
Contrato: preservado (requisições same-origin e server-to-server, como o smoke test, não são afetadas)

### F-11 [MEDIUM] Integridade referencial não garantida (AP-18)
Arquivo: routes/user_routes.py:140-142
Ocorrências: routes/task_routes.py:225-238 (delete_task), routes/report_routes.py:211-223 (delete_category), database.py:1-3 (sem `PRAGMA foreign_keys`)
Descrição: `delete_user` apaga as tasks do usuário em laço manual (user_routes.py:140-142). Já `delete_category` e `delete_task` removem o registro sem tratar as tasks que referenciam `category_id`/`user_id`, deixando FKs apontando para registros inexistentes. O SQLite não tem `PRAGMA foreign_keys = ON`, então as FKs declaradas nos models não são aplicadas.
Impacto: tasks órfãs após remover uma categoria; relatórios referenciando entidades inexistentes.
Recomendação: declarar cascata/`ondelete` no relacionamento do ORM e ativar `PRAGMA foreign_keys` no SQLite; remover a cascata manual — Playbook T15.
Contrato: preservado

### F-12 [MEDIUM] API deprecated (AP-19)
Arquivo: models/task.py:15-16
Ocorrências: `datetime.utcnow()` em 18 pontos (models/task.py:15-16, models/user.py:14, routes/task_routes.py:31,72,215,285, routes/user_routes.py:172, routes/report_routes.py:35,42,45,71, utils/helpers.py:38, seed.py); `Model.query.get()` em 16 pontos (routes/task_routes.py:67,158,227 etc., routes/user_routes.py:29,94,136,155, routes/report_routes.py:105,192,213)
Descrição: `datetime.utcnow()` está deprecated desde o Python 3.12 (substituto `datetime.now(timezone.utc)`); no runtime atual (3.9.6) não emite warning, mas é incompatível com versões futuras. `Model.query.get()` é API legada do SQLAlchemy 2.0 — confirmado em runtime: importar e executar `Task.query.get(1)` emite `LegacyAPIWarning` (SQLAlchemy 2.0.52). Substituto: `db.session.get(Model, id)`.
Impacto: quebra em upgrades de runtime/ORM; warnings poluindo logs.
Recomendação: trocar `datetime.utcnow()` por `datetime.now(timezone.utc)` e `Model.query.get()` por `db.session.get(Model, id)` nos repositórios — Playbook T12.
Contrato: preservado

### F-13 [MEDIUM] Serialização manual duplicada (AP-24)
Arquivo: routes/task_routes.py:16-59
Ocorrências: routes/user_routes.py:15-24 (get_users monta dict sem `password`), routes/user_routes.py:162-181 (get_user_tasks monta subconjunto), models/task.py:23-36 (`to_dict` existente)
Descrição: `get_tasks` remonta campo a campo o dicionário da task (task_routes.py:17-28) duplicando `Task.to_dict()`, e recalcula `overdue` inline. Escalado para MEDIUM porque as cópias divergem de forma perigosa: `get_users` (user_routes.py:15-24) omite `password`, enquanto `User.to_dict()` (F-02) o inclui — o mesmo recurso é serializado com e sem o segredo conforme a rota.
Impacto: inconsistência de contrato entre rotas e risco de vazamento conforme o serializador usado.
Recomendação: um único serializador por entidade (sem campos sensíveis), reutilizado por todas as rotas; `overdue` vindo do serviço — Playbook T13.
Contrato: preservado (as chaves públicas atuais são mantidas, exceto `password`, tratado em F-02)

### F-14 [LOW] Logging via `print` (AP-20)
Arquivo: routes/task_routes.py:149
Ocorrências: routes/task_routes.py:153,219,234; routes/user_routes.py:83,89,147; services/notification_service.py:21,24. `print` em seed.py é falso positivo (script de operador).
Descrição: diagnóstico via `print()` em handlers e no serviço, sem níveis nem destino configurável (11 ocorrências fora do seed).
Impacto: logs sem estrutura nem controle de verbosidade.
Recomendação: usar o módulo `logging` com níveis — Playbook T16.
Contrato: preservado

### F-15 [LOW] Magic numbers e literais duplicados (AP-21)
Arquivo: routes/task_routes.py:96-114
Ocorrências: listas `['pending','in_progress','done','cancelled']` em task_routes.py:110,177 e models/task.py:39; `['user','admin','manager']` em user_routes.py:71,120; limites de título 3/200 e prioridade 1/5 repetidos; senha mínima 4 em user_routes.py:64,115. Constantes já declaradas (e não usadas) em utils/helpers.py:110-116.
Descrição: limiares e enums de negócio espalhados como literais, embora `utils/helpers.py:110-116` já declare `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH` etc. — nunca importados.
Impacto: alterar uma regra exige caçar literais em vários arquivos.
Recomendação: centralizar constantes e reusá-las na validação — Playbook T16.
Contrato: preservado

### F-16 [LOW] Código morto (AP-22)
Arquivo: services/notification_service.py:1-49
Ocorrências: utils/helpers.py (`format_date`/`calculate_percentage` importados em report_routes.py:7 mas nunca usados; `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `is_valid_color`, `process_task_data` nunca chamados); imports não usados `json/os/sys` em app.py:7, `json/os/sys/time` em task_routes.py:7, `hashlib/json` em user_routes.py:6, `json` em report_routes.py:8; dependências `marshmallow`, `requests`, `python-dotenv` declaradas em requirements.txt e nunca importadas
Descrição: `NotificationService` (módulo inteiro) nunca é instanciado. Vários utilitários de `helpers.py` não têm chamador. Três dependências declaradas não são usadas. Diversos imports ociosos.
Impacto: superfície de manutenção e dependências inúteis; `requests`/`marshmallow` carregam risco de supply chain sem benefício.
Recomendação: remover módulo/funções/imports/dependências sem uso; manter apenas o que o código vivo consome — Playbook T16.
Contrato: preservado

### F-17 [LOW] Nomenclatura pobre e código verboso (AP-23)
Arquivo: models/task.py:38-60
Ocorrências: models/user.py:34-38 (`is_admin` com if/else retornando bool), models/task.py:50-60 (`is_overdue` em pirâmide de if), variáveis de 1 letra `t/u/c/p/cat` em task_routes.py/user_routes.py/report_routes.py
Descrição: `validate_status`/`is_overdue`/`is_admin` usam `if cond: return True else: return False` e pirâmides de `if` aninhado que cabem numa expressão booleana; identificadores de uma letra nos laços de serialização.
Impacto: legibilidade e verbosidade; nenhuma chave JSON pública é afetada.
Recomendação: simplificar para expressões booleanas e nomes descritivos em identificadores internos — Playbook T16.
Contrato: preservado (chaves JSON públicas não são renomeadas)

## APIs deprecated
| API ou dependência | Local | Substituto | Evidência |
|---|---|---|---|
| `datetime.utcnow()` | models/task.py:15-16 e +16 pontos | `datetime.now(timezone.utc)` | deprecated no Python 3.12 (busca no código; runtime 3.9.6 não emite warning) |
| `Model.query.get(id)` | routes/*.py (16 pontos) | `db.session.get(Model, id)` | `LegacyAPIWarning` emitido em runtime (SQLAlchemy 2.0.52) |
| MD5 para senha | models/user.py:29,32 | hash com salt (werkzeug) | algoritmo fraco — tratado em F-03 (AP-04) |

## Breaking Changes propostos
| # | Rota | Mudança no contrato | Finding que justifica |
|---|---|---|---|
| BC-01 | GET /users/<id> | remove a chave `password` da resposta; demais chaves permanecem | F-02 — hash de senha exposto sem autenticação |
| BC-02 | POST /users | remove a chave `password` da resposta | F-02 — hash de senha exposto |
| BC-03 | PUT /users/<id> | remove a chave `password` da resposta | F-02 — hash de senha exposto |
| BC-04 | POST /login | remove `password` de dentro de `user`; `token` e demais chaves permanecem | F-02 — hash de senha exposto |
| BC-05 | DELETE /tasks/<id> | passa a exigir `Authorization: Bearer <token>`; chamada anônima responde 401 (antes 404/200) | F-04 — remoção destrutiva sem autenticação |
| BC-06 | DELETE /users/<id> | passa a exigir `Authorization: Bearer <token>`; chamada anônima responde 401 | F-04 — remoção destrutiva sem autenticação |
| BC-07 | DELETE /categories/<id> | passa a exigir `Authorization: Bearer <token>`; chamada anônima responde 401 | F-04 — remoção destrutiva sem autenticação |

## Plano de refatoração
Estrutura-alvo (refina as camadas parciais já existentes):

```
config.py                  (config)         — settings de ambiente, SECRET_KEY, CORS, debug/host/port (T02)
database.py                (infra)          — db = SQLAlchemy() + PRAGMA foreign_keys (T15)
constants.py               (domínio)        — enums/limites centralizados (T16)
models/                    (models)         — entidades + repositórios por domínio
  task.py, user.py, category.py             — entidade + to_dict sem segredos (T13), hash seguro (T05)
  repositories.py                           — acesso a dados sem N+1, db.session.get (T08, T12)
services/                  (services)       — regra de negócio e integrações
  task_service.py, user_service.py, report_service.py (T04, T09)
  auth_service.py                           — token assinado + verificação (T14)
controllers/               (controllers)    — orquestram requisição/resposta finos (T04)
routes/                    (views)          — blueprints mapeando rota→controller + serializers (T13, T14)
middlewares/error_handler.py (middleware)   — tratamento de erro central (T10)
app.py                     (composition)    — factory create_app, monta dependências (T11)
```

Ordem de execução: config → models/repositories → services → controllers → routes → middlewares → composition root → limpeza (remover notification_service, helpers mortos, imports e deps sem uso).

================================
Total: 17 findings
================================
