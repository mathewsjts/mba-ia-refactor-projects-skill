================================
RELATÓRIO DE AUDITORIA DE ARQUITETURA
================================
Projeto:  task-manager-api
Stack:    Python 3.9.6 + Flask 3.0.0
Arquivos: 17 analisados | ~1158 linhas de código
Data:     2026-11-04

## Resumo
CRITICAL: 5 | HIGH: 6 | MEDIUM: 8 | LOW: 4

| # | Severidade | Anti-pattern | Local principal |
|---|---|---|---|
| F-01 | CRITICAL | Segredos e credenciais hardcoded (AP-02) | app.py:13 |
| F-02 | CRITICAL | Exposição de dados sensíveis — hash de senha nas respostas (AP-03) | models/user.py:16-25 |
| F-03 | CRITICAL | Armazenamento inseguro de senha (AP-04) | models/user.py:27-32 |
| F-04 | CRITICAL | Operação privilegiada sem controle de acesso (AP-05) | routes/user_routes.py:207-211 |
| F-05 | CRITICAL | God Module (AP-06) | routes/report_routes.py:1-223 |
| F-06 | HIGH | Exposição de dados pessoais sem autenticação (AP-03) | routes/user_routes.py:10-25 |
| F-07 | HIGH | Regra de negócio na camada HTTP (AP-07) | routes/task_routes.py:11-299 |
| F-08 | HIGH | Operação multi-passo sem transação — unicidade de e-mail (AP-09) | routes/user_routes.py:67-90 |
| F-09 | HIGH | Configuração de execução insegura (AP-10) | app.py:34 |
| F-10 | HIGH | Acoplamento forte sem injeção de dependência (AP-11) | routes/task_routes.py:1-9 |
| F-11 | HIGH | Validação ausente ou duplicada (AP-14) | routes/task_routes.py:92-114 |
| F-12 | MEDIUM | Aninhamento profundo (AP-12) | models/task.py:50-60 |
| F-13 | MEDIUM | Query N+1 (AP-13) | routes/report_routes.py:55-56 |
| F-14 | MEDIUM | Tratamento de erro não centralizado (AP-15) | routes/report_routes.py:186 |
| F-15 | MEDIUM | CORS permissivo (AP-16) | app.py:15 |
| F-16 | MEDIUM | Listagem sem paginação (AP-17) | routes/report_routes.py:159 |
| F-17 | MEDIUM | Integridade referencial não garantida (AP-18) | models/task.py:13-14 |
| F-18 | MEDIUM | API deprecated e dependências com vulnerabilidades (AP-19) | routes/report_routes.py:105 |
| F-19 | MEDIUM | Serialização manual duplicada e divergente (AP-24) | routes/task_routes.py:17-28 |
| F-20 | LOW | Logging via print (AP-20) | routes/task_routes.py:149 |
| F-21 | LOW | Magic numbers e literais duplicados (AP-21) | models/task.py:39 |
| F-22 | LOW | Código morto (AP-22) | app.py:7 |
| F-23 | LOW | Nomenclatura pobre e código verboso (AP-23) | models/category.py:14-21 |

## Findings

### F-01 [CRITICAL] Segredos e credenciais hardcoded (AP-02)
Arquivo: app.py:13
Ocorrências: services/notification_service.py:7-10
Descrição: `app.config['SECRET_KEY'] = 'super-secr****'` está literal no entry point. `NotificationService.__init__` fixa host SMTP, usuário `taskmanager@****` e senha `'senh****'` (linha 10) e os usa em `server.login(...)` (linha 17). Nenhum valor é lido do ambiente; a URI do banco (`app.py:11`) também é literal.
Impacto: quem tem acesso ao repositório obtém a conta SMTP e a chave que assinará tokens e sessões (a T14 passará a usá-la para assinar o token de login); rotacionar exige editar código e novo deploy.
Recomendação: criar `config/settings.py` que lê `SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `PORT`, `HOST`, `FLASK_DEBUG` do ambiente (com `.env` via python-dotenv e `.env.example` só com placeholders). Sem `SECRET_KEY` no ambiente, gerar uma chave aleatória por processo com aviso no log (nunca um literal). As credenciais SMTP saem com a remoção do `NotificationService` (F-10/F-22) — Playbook T02.
Contrato: preservado

### F-02 [CRITICAL] Exposição de dados sensíveis — hash de senha nas respostas (AP-03)
Arquivo: models/user.py:16-25
Ocorrências: routes/user_routes.py:33 (`GET /users/<id>`), routes/user_routes.py:85 (`POST /users`), routes/user_routes.py:129 (`PUT /users/<id>`), routes/user_routes.py:209 (`POST /login`), routes/user_routes.py:89 (log)
Descrição: `User.to_dict()` inclui `'password': self.password` (linha 21), e as quatro rotas o devolvem — o baseline confirma a chave `password` em `GET /users/1`, `POST /users`, `PUT /users/2` e `user.password` no `POST /login`. Em `create_user`, `print(f"ERRO: {str(e)}")` (linha 89) grava no log a mensagem da `IntegrityError` do SQLAlchemy, que inclui os parâmetros do `INSERT`, entre eles o hash.
Impacto: qualquer cliente anônimo obtém o hash MD5 sem salt de qualquer conta (`GET /users/<id>`) e o quebra em segundos (F-03), assumindo a conta, inclusive a de admin.
Recomendação: serializer de usuário com lista explícita de campos sem `password` (`routes/serializers.py`), usado por todas as rotas; logs sem `str(e)` de erros de banco — Playbook T13.
Contrato: exige BC-01

### F-03 [CRITICAL] Armazenamento inseguro de senha (AP-04)
Arquivo: models/user.py:27-32
Ocorrências: routes/user_routes.py:64, routes/user_routes.py:115 (política mínima de 4 caracteres)
Descrição: `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()` e `check_password` compara por igualdade direta (`==`, linha 32), sem salt e sem comparação em tempo constante. A política aceita senhas de 4 caracteres. MD5 para senha também é API inadequada (AP-19), reportada aqui pela regra 4 de escalonamento.
Impacto: com o hash (exposto em F-02, ou num dump do banco), a senha é recuperada por tabela rainbow; senhas reutilizadas comprometem outros sistemas.
Recomendação: `models/passwords.py` com `hash_password`/`verify_password` usando `werkzeug.security.generate_password_hash(method="pbkdf2:sha256:600000")` — `scrypt` não está disponível neste Python (LibreSSL 2.8.3, `hasattr(hashlib, 'scrypt') == False`); verificar MD5 legado com `hmac.compare_digest` e regravar com o hash novo no primeiro login bem-sucedido; seed passa a gravar o hash novo (já usa `set_password`); mínimo de 8 caracteres para senha nova — Playbook T05.
Contrato: exige BC-06 e BC-07 (apenas a nova política de tamanho mínimo); o hash em si não altera o contrato

### F-04 [CRITICAL] Operação privilegiada sem controle de acesso (AP-05)
Arquivo: routes/user_routes.py:207-211
Ocorrências: routes/task_routes.py:85, routes/task_routes.py:156, routes/task_routes.py:225, routes/user_routes.py:42, routes/user_routes.py:52, routes/user_routes.py:71-78, routes/user_routes.py:92, routes/user_routes.py:114-125, routes/user_routes.py:134, routes/report_routes.py:167, routes/report_routes.py:190, routes/report_routes.py:211
Descrição: o login devolve `'token': 'fake-jwt-token-' + str(user.id)` — não assinado e nunca conferido. Nenhuma das 9 rotas de escrita exige credencial: um anônimo cria usuário com `role: "admin"` (`POST /users`, linhas 52 e 71-78), troca senha, `role` e `active` de qualquer conta (`PUT /users/<id>`, linhas 114-125), apaga qualquer usuário com todas as suas tasks (`DELETE /users/<id>`), reescreve ou apaga qualquer task e qualquer categoria. Não há rota que execute SQL/código do cliente nem destruição em massa, então nenhuma rota é removida.
Impacto: tomada de conta (inclusive admin) e destruição de todos os dados por um cliente anônimo, registro a registro.
Recomendação: aplicar a T14 por completo. (a) Token assinado com `itsdangerous.URLSafeTimedSerializer` (vem com o Flask), validade de 24 h, na mesma chave `token`; (b) middleware `require_auth` que valida `Authorization: Bearer`, recarrega o usuário do banco a cada requisição (conta apagada/inativa → 401) e põe em `g.user`; (c) regra de quem escreve no service (`ensure_owner_or_admin`, `ensure_admin`), na ordem 401 → 404 → 403 → 400. Rota a rota:

| Rota | Linha da T14 | Quem pode escrever |
|---|---|---|
| `POST /login` | — | pública: é o próprio login |
| `POST /users` | criação que aceita campo de perfil | pública: é o único cadastro da API (cadastro público). Sem token de admin, `role` é ignorado e grava `user`; admin autenticado pode definir `role` |
| `PUT /users/<id>` | atualização de perfil/credencial/estado + escrita com login | token; o próprio usuário altera nome, e-mail e a própria senha; só admin altera `role`, `active` ou dados de outra conta (403) |
| `DELETE /users/<id>` | escrita com login (recurso com dono = a própria conta) | token; o próprio usuário ou admin (403) |
| `POST /tasks` | escrita com login (dono `tasks.user_id`) | token; sem `user_id` no corpo o dono é quem chama; criar para outra conta só admin (403) |
| `PUT /tasks/<id>` | escrita com login | token; dono atual ou admin; transferir `user_id` para outra conta só admin (403) |
| `DELETE /tasks/<id>` | escrita com login | token; dono ou admin (403) |
| `POST /categories` | escrita com login, recurso compartilhado (sem coluna de dono) | token; só admin (403) |
| `PUT /categories/<id>` | escrita com login, recurso compartilhado | token; só admin (403) |
| `DELETE /categories/<id>` | escrita com login, recurso compartilhado | token; só admin (403) |

Como `POST /users` não cria mais admin, a Fase 3 oferece `flask --app app create-admin` para o primeiro admin (armadilha da T14) — Playbook T14.
Contrato: exige BC-02, BC-03, BC-04, BC-05, BC-06, BC-07, BC-08, BC-09, BC-10, BC-11

### F-05 [CRITICAL] God Module (AP-06)
Arquivo: routes/report_routes.py:1-223
Ocorrências: Nenhuma adicional
Descrição: o blueprint `reports` mistura dois domínios — relatórios (`summary_report`, linhas 12-101; `user_report`, 103-155) e o CRUD completo de categorias (`get_categories`, `create_category`, `update_category`, `delete_category`, linhas 157-223) — e todas as camadas: HTTP (`request`, `jsonify`, status), dados (`Task.query`, `db.session.add/commit/delete`), regras (contagem por status/prioridade, atraso, taxa de conclusão, linhas 30-68 e 119-151), validação (linhas 169-175) e serialização manual (138-153).
Impacto: categorias não têm módulo próprio — quem procura o CRUD de categorias não o encontra; nenhuma regra de relatório é testável sem HTTP e banco.
Recomendação: separar `routes/category_routes.py` e `routes/report_routes.py` (só mapeamento), `controllers/category_controller.py` e `controllers/report_controller.py`, `services/category_service.py` e `services/report_service.py` (agregações), com acesso a dados nos models/repositórios por domínio — Playbook T03, T04.
Contrato: preservado (paths e respostas iguais; categorias ganham proteção pelo F-04)

### F-06 [HIGH] Exposição de dados pessoais sem autenticação (AP-03)
Arquivo: routes/user_routes.py:10-25
Ocorrências: routes/user_routes.py:27-40 (`GET /users/<id>`), routes/report_routes.py:137-142 (`GET /reports/user/<id>`)
Descrição: `GET /users` responde a anônimos a lista de todas as contas com `email`, `role` e `active`; `GET /users/<id>` e `GET /reports/user/<id>` devolvem o e-mail de qualquer conta. Como o cadastro é público (F-04), exigir "qualquer token" não basta: qualquer pessoa cria uma conta e lê tudo.
Impacto: coleta em massa de e-mails e mapeamento de quem é admin (alvo para F-03); violação de LGPD.
Recomendação: exigir token com o mesmo `require_auth` da T14: `GET /users` só admin; `GET /users/<id>` e `GET /reports/user/<id>` o próprio usuário ou admin (401 anônimo, 404 inexistente, 403 outra conta). As demais leituras (`/tasks`, `/users/<id>/tasks`, `/reports/summary`, `/categories`) não trazem e-mail e continuam públicas (ver R-03) — Playbook T13, T14.
Contrato: exige BC-12, BC-13, BC-14

### F-07 [HIGH] Regra de negócio na camada HTTP (AP-07)
Arquivo: routes/task_routes.py:11-299
Ocorrências: routes/user_routes.py:42-151, routes/user_routes.py:153-183, routes/user_routes.py:185-211
Descrição: os handlers calculam atraso (`task_routes.py:30-39`, `71-80`, `user_routes.py:171-180`), agregam estatísticas (`task_stats`, `task_routes.py:273-299`), decidem existência de usuário/categoria, convertem tags e datas, acessam `Task.query`/`db.session` diretamente e fazem a cascata de remoção de tasks (`user_routes.py:140-142`); `login` decide credencial e estado da conta no handler. `create_task` tem 70 linhas, `update_task` 68. A regra `Task.is_overdue()` existe no model (`models/task.py:50-60`) e não é usada.
Impacto: as mesmas regras (atraso em 6 lugares) divergem com o tempo; nada é testável sem subir HTTP e banco.
Recomendação: controllers finos (extraem entrada, chamam o service, escolhem status) e services com as regras (`task_service`, `user_service`, `auth_service`), com o cálculo de atraso num único lugar do model — Playbook T04.
Contrato: preservado

### F-08 [HIGH] Operação multi-passo sem transação — unicidade de e-mail (AP-09)
Arquivo: routes/user_routes.py:67-90
Ocorrências: routes/user_routes.py:109-112 e 127-132 (`PUT /users/<id>`)
Descrição: `create_user` busca `User.query.filter_by(email=email).first()` (linha 67) e só depois insere (linhas 80-82). Duas requisições paralelas com o mesmo e-mail passam ambas pela checagem; a coluna tem `unique=True` (`models/user.py:10`), então a segunda falha no `commit` com `IntegrityError`, capturada pelo `except Exception` genérico e respondida como `500 'Erro ao criar usuário'` em vez do `409 'Email já cadastrado'` do caminho sequencial. O mesmo ocorre na troca de e-mail do `PUT`.
Impacto: sob concorrência, o cliente recebe 500 para um conflito de negócio, e o log grava a mensagem de banco com o hash (F-02).
Recomendação: manter a checagem prévia (mensagem original), garantir `UNIQUE` no boot (`CREATE UNIQUE INDEX IF NOT EXISTS` sobre `users.email` para bancos antigos) e converter a `IntegrityError` de e-mail no mesmo `409 'Email já cadastrado'`; validar tudo antes da escrita e manter `DELETE /users/<id>` (tasks + usuário) num único commit com rollback — Playbook T07 (passos 1, 2 e 3-unicidade).
Contrato: preservado

### F-09 [HIGH] Configuração de execução insegura (AP-10)
Arquivo: app.py:34
Ocorrências: app.py:11, app.py:30-31
Descrição: `app.run(debug=True, host='0.0.0.0', port=5000)` liga o debugger do Werkzeug (execução de código pelo navegador) escutando em todas as interfaces; porta e host são literais. `db.create_all()` roda no import do módulo (linhas 30-31), e a URI `sqlite:///tasks.db` é literal.
Impacto: qualquer máquina da rede que provoque uma exceção obtém um console Python no servidor; impossível configurar ambientes sem editar código (a porta 5000 colide com o AirPlay no macOS).
Recomendação: `FLASK_DEBUG` (padrão desligado), `HOST` (padrão `127.0.0.1`), `PORT` (padrão `5000`) e `DATABASE_URL` vindos da configuração; criação de schema dentro da factory `create_app()`, não no import — Playbook T02.
Contrato: preservado

### F-10 [HIGH] Acoplamento forte sem injeção de dependência (AP-11)
Arquivo: routes/task_routes.py:1-9
Ocorrências: routes/user_routes.py:1-8, routes/report_routes.py:1-10, app.py:9-20, services/notification_service.py:4-48
Descrição: os três blueprints importam os models concretos e `db` no nível do módulo e consultam o banco direto do handler; não há factory — `app` é criado e configurado no import (`app.py:9-20`), então testes não conseguem trocar banco ou configuração. `NotificationService` instancia `smtplib.SMTP(...)` dentro de `send_email` (linha 15) e guarda notificações numa lista em memória da instância (`self.notifications = []`, linha 6; mutada em 31-36 — AP-08), perdida no restart e não compartilhada entre workers. A classe nunca é importada (F-22).
Impacto: impossível testar regras sem banco e rede reais; trocar a infraestrutura exige editar a regra.
Recomendação: `create_app(config)` como composition root, que cria services e controllers e os injeta nos blueprints (`register_*_routes(app, controller, auth)`); services recebem os repositórios no construtor. O `NotificationService` não é usado por nenhum fluxo da API: remover o módulo (T16) em vez de ligá-lo, o que também elimina a credencial SMTP de F-01 e o estado em memória — Playbook T11.
Contrato: preservado

### F-11 [HIGH] Validação ausente ou duplicada (AP-14)
Arquivo: routes/task_routes.py:92-114
Ocorrências: routes/task_routes.py:166-213, routes/task_routes.py:113, routes/task_routes.py:182, routes/task_routes.py:96-100, routes/task_routes.py:167-170, routes/task_routes.py:261, routes/task_routes.py:264, routes/user_routes.py:54-72, routes/user_routes.py:102-125, routes/user_routes.py:194, routes/report_routes.py:173-180, routes/report_routes.py:196-202, utils/helpers.py:57-108
Descrição: as regras de task estão copiadas entre `create_task` e `update_task` e as de usuário entre `create_user` e `update_user`. Não há checagem de tipo: `priority < 1` com `"3"` lança `TypeError` (500); `len(title)` com número lança `TypeError` (500); `int(priority)`/`int(user_id)` da busca lançam `ValueError` (500); `check_password(123)` no login quebra em `.encode` (500); `update_category` com corpo `null` faz `'name' in None` (500); `active`, `color`, `description` e `tags` não são validados. `priority: 2.5` passa na faixa e é gravado como `2.5` numa coluna `Integer` (verificado num SQLite descartável), sumindo das contagens por prioridade — dado inválido no banco, o que eleva o finding para HIGH (regra 2 de escalonamento). O regex de e-mail aceita `a@b`. `process_task_data` (utils/helpers.py:57-108) já valida tipos e nunca é chamado.
Impacto: 500 com entrada inválida, dados corrompidos e regras divergentes entre criar e atualizar.
Recomendação: `controllers/validators.py` único por recurso (criar e atualizar com `partial`), checando presença, tipo (`bool` não conta como número), faixa, enum e formato, levantando `ValidationError` com as mensagens atuais; parâmetros numéricos de query validados; corpo não-objeto → 400 — Playbook T09.
Contrato: preservado para todo caso do baseline; entradas de tipo inválido que hoje geram 500 passam a 400

### F-12 [MEDIUM] Aninhamento profundo (AP-12)
Arquivo: models/task.py:50-60
Ocorrências: routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:284-287, routes/user_routes.py:171-180, routes/report_routes.py:34-43, routes/report_routes.py:132-135
Descrição: o cálculo de atraso é uma pirâmide de quatro níveis de `if`/`else` que só devolve booleano, repetida seis vezes. Síncrono e correto, por isso MEDIUM.
Impacto: leitura difícil e cópias que divergem.
Recomendação: guard clauses / expressão booleana única em `Task.is_overdue(now)`, usada por todos — Playbook T06.
Contrato: preservado

### F-13 [MEDIUM] Query N+1 (AP-13)
Arquivo: routes/report_routes.py:55-56
Ocorrências: routes/report_routes.py:161-163, routes/task_routes.py:41-57, routes/user_routes.py:22, routes/report_routes.py:15-28, routes/task_routes.py:275-279
Descrição: `summary_report` faz `Task.query.filter_by(user_id=u.id).all()` por usuário; `get_categories` faz um `count()` por categoria; `get_tasks` faz `User.query.get` e `Category.query.get` por task; `get_users` acessa `len(u.tasks)` (lazy) por usuário. O resumo dispara 13 `COUNT` separados que cabem em dois `GROUP BY`.
Impacto: número de consultas cresce linearmente com tasks/usuários/categorias.
Recomendação: `GROUP BY` para contagens por status, prioridade, usuário e categoria; `joinedload`/`selectinload` para usuário e categoria das tasks — Playbook T08.
Contrato: preservado

### F-14 [MEDIUM] Tratamento de erro não centralizado (AP-15)
Arquivo: routes/report_routes.py:186
Ocorrências: routes/report_routes.py:207, routes/report_routes.py:221, routes/task_routes.py:62, routes/task_routes.py:137, routes/task_routes.py:151, routes/task_routes.py:204, routes/task_routes.py:221, routes/task_routes.py:236, routes/user_routes.py:87, routes/user_routes.py:130, routes/user_routes.py:149
Descrição: `except:` sem tipo em 9 pontos e `except Exception as e` em 3, cada um com sua resposta; não existe `@app.errorhandler` — exceções fora dos `try` (ex.: `TypeError` de F-11) viram a página HTML 500 do Werkzeug, enquanto o resto da API responde JSON `{'error': ...}`.
Impacto: formato de erro inconsistente (JSON vs HTML), erros reais escondidos (o `except:` de `get_tasks` engole qualquer bug).
Recomendação: `errors.py` com exceções de domínio (`ValidationError`, `NotFoundError`, `ConflictError`, `UnauthorizedError`, `ForbiddenError`) e `middlewares/error_handler.py` registrado na factory, traduzindo para `{'error': msg}` com o status certo, `HTTPException` preservada e 500 genérico em JSON com log — Playbook T10.
Contrato: preservado (a página HTML de 500 passa a JSON; nenhum caso do baseline responde 500)

### F-15 [MEDIUM] CORS permissivo (AP-16)
Arquivo: app.py:15
Ocorrências: Nenhuma adicional
Descrição: `CORS(app)` sem `origins` responde `Access-Control-Allow-Origin: *` a qualquer origem. Sem `supports_credentials`, por isso MEDIUM.
Impacto: qualquer site pode chamar a API do navegador do usuário; com o token Bearer novo, a origem passa a importar.
Recomendação: `CORS(app, origins=config.CORS_ORIGINS)`, lista lida do ambiente (padrão `http://localhost:3000,http://127.0.0.1:3000`) — Playbook T02.
Contrato: preservado (status e corpo iguais; só o cabeçalho CORS para origens não listadas muda — ver R-07)

### F-16 [MEDIUM] Listagem sem paginação (AP-17)
Arquivo: routes/report_routes.py:159
Ocorrências: routes/task_routes.py:14, routes/task_routes.py:266, routes/user_routes.py:12, routes/report_routes.py:30, routes/report_routes.py:53, routes/task_routes.py:281
Descrição: `GET /tasks`, `/tasks/search`, `/users` e `/categories` devolvem `.all()`; `summary_report` e `task_stats` carregam todas as tasks em memória para contar atrasadas.
Impacto: memória e tempo crescem com o volume.
Recomendação: paginação **opcional** (`?page=&per_page=`, com teto); sem os parâmetros a resposta continua a lista completa. Contagem de atrasadas por consulta (`WHERE due_date < now AND status NOT IN (...)`) — Playbook T17, T08.
Contrato: preservado

### F-17 [MEDIUM] Integridade referencial não garantida (AP-18)
Arquivo: models/task.py:13-14
Ocorrências: models/task.py:20-21, routes/user_routes.py:140-142, routes/report_routes.py:218
Descrição: `tasks.user_id` e `tasks.category_id` têm `ForeignKey` sem `ondelete`, e o SQLite roda com `PRAGMA foreign_keys = 0` (verificado): o banco aceita órfãos — num teste descartável, `DELETE FROM users` deixou a task com `user_id` apontando para usuário inexistente. A remoção de usuário depende de um laço manual no handler (`for t in tasks: db.session.delete(t)`), e a de categoria depende do comportamento implícito do ORM de anular `category_id`.
Impacto: qualquer escrita fora desse handler (script, seed, outra rota) deixa tasks órfãs que aparecem com `user_name: null`.
Recomendação: `PRAGMA foreign_keys=ON` em cada conexão; cascata declarada no model (`User.tasks` com `cascade="all, delete-orphan"`, `ondelete="CASCADE"`; `Category.tasks` com `ondelete="SET NULL"` explícito) e remoção do laço manual — Playbook T15.
Contrato: preservado

### F-18 [MEDIUM] API deprecated e dependências com vulnerabilidades (AP-19)
Arquivo: routes/report_routes.py:105
Ocorrências: routes/report_routes.py:192, routes/report_routes.py:213, routes/task_routes.py:42, routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:188, routes/task_routes.py:195, routes/task_routes.py:227, routes/user_routes.py:29, routes/user_routes.py:94, routes/user_routes.py:136, routes/user_routes.py:155, models/task.py:15-16, models/task.py:52, models/user.py:14, models/category.py:11, routes/task_routes.py:31, requirements.txt:1-6
Descrição: 16 chamadas `Model.query.get(id)` emitem `LegacyAPIWarning` (confirmado com `python -W default`); `Model.query.filter...` é API legada do SQLAlchemy 2.0; `datetime.utcnow()` (22 ocorrências) é deprecated no Python 3.12. `pip-audit` sobre `requirements.txt` aponta Flask 3.0.0 (CVE-2026-27205), Flask-Cors 4.0.0 (CVE-2024-6221, CVE-2024-1681, CVE-2024-6866, CVE-2024-6839, CVE-2024-6844), python-dotenv 1.0.0 (CVE-2026-28684), requests 2.31.0 e marshmallow 3.20.1 (as duas sem uso). A severidade das CVEs não foi conferida por ferramenta, por isso o finding fica no padrão MEDIUM. O runtime Python 3.9 está fora de suporte desde outubro de 2025.
Impacto: quebra na próxima versão maior do SQLAlchemy/Python; vulnerabilidades conhecidas em produção.
Recomendação: `db.session.get(Model, id)` / `db.get_or_404`, `select(...)` via `db.session.execute`, `datetime.now(timezone.utc)` com colunas guardando o mesmo formato naive UTC de hoje (para não mudar o formato de `created_at`); atualizar e remover dependências conforme a linha `Dependências` do plano — Playbook T12.
Contrato: preservado

### F-19 [MEDIUM] Serialização manual duplicada e divergente (AP-24)
Arquivo: routes/task_routes.py:17-28
Ocorrências: routes/user_routes.py:15-23, routes/user_routes.py:162-169, routes/report_routes.py:38-43, routes/report_routes.py:138-142, models/user.py:16-25, models/task.py:23-36
Descrição: `get_tasks` remonta campo a campo o que `Task.to_dict()` já faz; `get_users` monta o usuário sem `password` enquanto `User.to_dict()` (usado em 4 rotas) inclui o hash — cópias que divergem de forma perigosa, por isso MEDIUM; `get_user_tasks` monta uma terceira forma de task.
Impacto: corrigir um campo exige achar todas as cópias; a cópia errada vaza a senha (F-02).
Recomendação: `routes/serializers.py` com `serialize_task`, `serialize_task_summary` (forma de `/users/<id>/tasks`), `serialize_user`, `serialize_category`, cada um com campos explícitos e as mesmas chaves de hoje — Playbook T13.
Contrato: preservado (salvo a remoção de `password`, declarada em BC-01)

### F-20 [LOW] Logging via print (AP-20)
Arquivo: routes/task_routes.py:149
Ocorrências: routes/task_routes.py:153, routes/task_routes.py:219, routes/task_routes.py:234, routes/user_routes.py:83, routes/user_routes.py:89, routes/user_routes.py:147, services/notification_service.py:21, services/notification_service.py:24, utils/helpers.py:39, utils/helpers.py:41
Descrição: eventos e erros vão para `print` sem nível nem destino; o de `user_routes.py:89` vaza o hash (consolidado em F-02). Os `print` de `seed.py:93-96` são saída de script de linha de comando (falso positivo).
Impacto: sem filtro por nível, sem integração com coleta de logs.
Recomendação: `logging.getLogger(__name__)` configurado na factory — Playbook T16.
Contrato: preservado

### F-21 [LOW] Magic numbers e literais duplicados (AP-21)
Arquivo: models/task.py:39
Ocorrências: routes/task_routes.py:110, routes/task_routes.py:177, routes/user_routes.py:71, routes/user_routes.py:120, utils/helpers.py:75, routes/task_routes.py:96-100, routes/task_routes.py:113, routes/user_routes.py:64, routes/report_routes.py:129, models/category.py:10, routes/report_routes.py:180, utils/helpers.py:110-116
Descrição: lista de status em 4 lugares, de perfis em 2, limites de título 3/200, prioridade 1-5, senha 4, "alta prioridade" `priority <= 2`, cor padrão `'#000000'`. As constantes de `utils/helpers.py:110-116` existem e nenhuma é usada.
Impacto: mudar uma regra exige caçar literais.
Recomendação: `constants.py` com os valores nomeados, usado por models, validators e services — Playbook T16.
Contrato: preservado

### F-22 [LOW] Código morto (AP-22)
Arquivo: app.py:7
Ocorrências: routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, models/task.py:38-48, models/user.py:34-38, utils/helpers.py:1-116, services/notification_service.py:1-48, requirements.txt:4-5
Descrição: imports não usados (`os, sys, json` em app.py; `json, os, sys, time` em task_routes; `hashlib, json` em user_routes; `format_date, calculate_percentage, json` em report_routes; `json` em models/task); `Task.validate_status`, `Task.validate_priority` e `User.is_admin` nunca chamados; `utils/helpers.py` inteiro sem uso real (o validador `process_task_data` está consolidado em F-11); `NotificationService` nunca importado; `marshmallow` e `requests` declarados e nunca importados (`python-dotenv` passa a ser usado pela T02).
Impacto: ruído, superfície de ataque (dependências com CVE sem uso) e falsa impressão de funcionalidade (notificações por e-mail).
Recomendação: remover imports, métodos, `utils/` e `services/notification_service.py`; remover `marshmallow` e `requests` do manifesto — Playbook T16.
Contrato: preservado

### F-23 [LOW] Nomenclatura pobre e código verboso (AP-23)
Arquivo: models/category.py:14-21
Ocorrências: models/task.py:40-43, models/task.py:46-48, models/user.py:35-38, routes/report_routes.py:24-28, routes/report_routes.py:55, routes/task_routes.py:14-16, utils/helpers.py:21-23
Descrição: variáveis `d`, `u`, `t`, `c`, `cat`, `p1`…`p5`; `if cond: return True else: return False` em vez de `return cond`; dicionário montado campo a campo para depois ser devolvido.
Impacto: leitura mais lenta, intenção escondida.
Recomendação: nomes descritivos e expressões diretas nos identificadores internos; chaves JSON públicas não mudam — Playbook T16.
Contrato: preservado

## APIs deprecated
| API ou dependência | Local | Substituto | Evidência |
|---|---|---|---|
| `Model.query.get(id)` | routes/task_routes.py:42 (+15 ocorrências, F-18) | `db.session.get(Model, id)` | `LegacyAPIWarning: The Query.get() method is considered legacy ... (deprecated since: 2.0)` com `python -W default` |
| `Model.query.filter/filter_by/count/all` | routes/report_routes.py:15-56, routes/task_routes.py:247-266 e demais | `db.session.execute(select(...))` / `db.session.scalar(...)` | API legada no SQLAlchemy 2.0 (catálogo AP-19) |
| `datetime.utcnow()` | models/task.py:15-16 (+21 ocorrências) | `datetime.now(timezone.utc)` (gravado como UTC naive) | deprecated no Python 3.12 (sem aviso no 3.9 em uso) |
| `hashlib.md5` para senha | models/user.py:29, 32 | `werkzeug.security` PBKDF2 | tratado como AP-04 (F-03) |
| flask 3.0.0 | requirements.txt:1 | flask 3.1.3 | pip-audit: CVE-2026-27205 (fix 3.1.3) |
| flask-cors 4.0.0 | requirements.txt:3 | flask-cors 6.0.2 | pip-audit: CVE-2024-6221 (fix 4.0.2), CVE-2024-6866/6839/6844 (fix 6.0.0), CVE-2024-1681 |
| python-dotenv 1.0.0 | requirements.txt:6 | python-dotenv 1.2.1 (maior versão instalável no Python 3.9) | pip-audit: CVE-2026-28684 (fix 1.2.2, que não instala no 3.9 — R-04) |
| requests 2.31.0 | requirements.txt:5 | remover (sem uso) | pip-audit: 3 vulnerabilidades (fix 2.32.0+) |
| marshmallow 3.20.1 | requirements.txt:4 | remover (sem uso) | pip-audit: 1 vulnerabilidade (fix 3.26.2) |
| Python 3.9 (runtime) | .venv | Python ≥ 3.11 | fim de suporte em 2025-10; fora do escopo do código (R-05) |

## Breaking Changes propostos
| # | Rota | Mudança no contrato | Finding que justifica |
|---|---|---|---|
| BC-01 | GET /users/<id>, POST /users, PUT /users/<id>, POST /login | remove a chave `password` (no login, `user.password`); demais chaves iguais | F-02 — hash de senha exposto |
| BC-02 | POST /login | `token` continua na mesma chave, mas passa a ser assinado (itsdangerous, 24 h) em vez de `fake-jwt-token-<id>`; é o único aceito em `Authorization: Bearer` | F-04 — token falso |
| BC-03 | POST /tasks | exige token (401 anônimo); sem `user_id` no corpo, o dono gravado é quem chama; `user_id` de outra conta só para admin (403) | F-04 — escrita anônima |
| BC-04 | PUT /tasks/<id> | exige token (401); só dono ou admin (403); transferir `user_id` só admin (403) | F-04 — reescrita anônima de tasks |
| BC-05 | DELETE /tasks/<id> | exige token (401); só dono ou admin (403) | F-04 — remoção anônima |
| BC-06 | POST /users | continua público (cadastro); sem token de admin, `role` é ignorado e grava `user`; senha nova com menos de 8 caracteres → 400 | F-04 — autopromoção a admin; F-03 — política de senha |
| BC-07 | PUT /users/<id> | exige token (401); o próprio usuário altera nome, e-mail e senha; `role`, `active` e dados de outra conta só admin (403); senha nova < 8 → 400 | F-04 — tomada de conta |
| BC-08 | DELETE /users/<id> | exige token (401); só o próprio usuário ou admin (403) | F-04 — remoção anônima de contas |
| BC-09 | POST /categories | exige token (401) de admin (403) | F-04 — recurso compartilhado |
| BC-10 | PUT /categories/<id> | exige token (401) de admin (403) | F-04 — recurso compartilhado |
| BC-11 | DELETE /categories/<id> | exige token (401) de admin (403) | F-04 — recurso compartilhado |
| BC-12 | GET /users | exige token (401) de admin (403) | F-06 — e-mails de todas as contas |
| BC-13 | GET /users/<id> | exige token (401); só o próprio usuário ou admin (403) | F-06 — e-mail exposto |
| BC-14 | GET /reports/user/<id> | exige token (401); só o próprio usuário ou admin (403) | F-06 — e-mail exposto |

Divergências esperadas no `smoke.sh`: as chamadas anônimas de prova (`GET /users`, `GET /users/999999`, `GET /reports/user/999999`, `POST /tasks {}`, `POST /categories {}`, `PUT`/`DELETE .../999999` sem header) passam de 200/400/404 a 401; as linhas que devolvem usuário perdem `password`.

## Riscos residuais
| # | Risco | Finding | Por que permanece | Mitigação recomendada |
|---|---|---|---|---|
| R-01 | `SECRET_KEY` e senha SMTP antigas continuam no histórico git | F-01 | a refatoração não reescreve histórico (regra 6) | rotacionar a senha da conta SMTP e definir `SECRET_KEY` nova no ambiente |
| R-02 | Contas que nunca mais fizerem login continuam com hash MD5 | F-03 | a migração é feita no primeiro login bem-sucedido (T05, passo 4) | forçar redefinição de senha das contas com hash de 32 hex depois de um prazo |
| R-03 | Nomes de usuários continuam públicos em `GET /tasks` (`user_name`), `GET /reports/summary` (`user_productivity[].user_name`) | F-06 | protegê-los exigiria fechar as leituras públicas de tasks, quebra que nenhum finding de segurança CRITICAL/HIGH exige (não há e-mail nem credencial) | decidir uma política de leitura autenticada para a API inteira |
| R-04 | python-dotenv 1.2.1 ainda tem CVE-2026-28684 | F-18 | o fix (1.2.2) não instala no Python 3.9; a falha está em `set_key`/`unset_key`, que o projeto não chama (usa só `load_dotenv`) | atualizar o runtime (R-05) e então python-dotenv ≥ 1.2.2 |
| R-05 | Runtime Python 3.9 sem suporte, ligado a LibreSSL (sem `hashlib.scrypt`) | F-18 | o runtime vem do ambiente (`.venv`), não do manifesto | migrar para Python ≥ 3.11 com OpenSSL |
| R-06 | Token sem revogação: troca de senha não invalida tokens já emitidos (vale até 24 h) | F-04 | token assinado é stateless; só conta apagada/inativa perde acesso (o usuário é recarregado a cada requisição) | coluna de versão de token ou lista de revogação |
| R-07 | Sem `SECRET_KEY` no ambiente, a chave é aleatória por processo: tokens morrem no restart e não valem entre workers | F-01 | não pode haver chave literal no código | definir `SECRET_KEY` no ambiente de qualquer deploy (documentado no README e no `.env.example`) |
| R-08 | Login sem limite de tentativas | F-04 | rate limiting exige dependência ou infraestrutura fora do escopo do plano | limitar tentativas por IP/conta no proxy ou com Flask-Limiter |
| R-09 | Front-end em origem não listada deixa de receber CORS | F-15 | o padrão agora é uma lista restrita | configurar `CORS_ORIGINS` no ambiente |
| R-10 | Bancos já existentes não ganham `ON DELETE` no DDL | F-17 | `db.create_all()` não altera tabelas existentes e não há migrations | a cascata do ORM cobre a API; recriar o banco (seed) ou adotar Alembic |

## Plano de refatoração
```
app.py                        composition root: create_app(), app = create_app(), __main__, comando create-admin
config/settings.py            T02 — ambiente/.env (SECRET_KEY, DATABASE_URL, HOST, PORT, FLASK_DEBUG, CORS_ORIGINS)
constants.py                  T16 — status, perfis, limites
database.py                   db = SQLAlchemy(); PRAGMA foreign_keys=ON; índice único de e-mail
errors.py                     T10 — exceções de domínio
models/
  task.py user.py category.py T15/T12 — entidades, cascata, is_overdue único, consultas por domínio
  passwords.py                T05 — hash/verify com migração do MD5
services/
  auth_service.py             T14 — token assinado, login
  authorization.py            T14 — ensure_owner_or_admin / ensure_admin
  task_service.py user_service.py category_service.py report_service.py   T04/T07/T08
controllers/
  task_controller.py user_controller.py category_controller.py report_controller.py   T04
  validators.py               T09
routes/
  task_routes.py user_routes.py category_routes.py report_routes.py system_routes.py   T13/T14/T17
  serializers.py              T13
middlewares/
  auth.py                     T14 — require_auth
  error_handler.py            T10
seed.py                       mantido (python seed.py)
```
Ordem: config (T02) → models (T03, T05, T07-unicidade, T08, T12, T15) → services (T04, T06, T07, T14-regras) → controllers (T04, T09) → routes (T13, T14, T17) → middlewares (T10, T14) → composition root (T11) → limpeza (T16: remove `utils/`, `services/notification_service.py`, imports e prints). Comandos documentados preservados: `pip install -r requirements.txt`, `python seed.py`, `python app.py` (agora aceitando `PORT`).
Dependências: atualizar flask 3.0.0 → 3.1.3, flask-cors 4.0.0 → 6.0.2, python-dotenv 1.0.0 → 1.2.1; remover requests 2.31.0 e marshmallow 3.20.1; manter flask-sqlalchemy 3.1.1; nenhuma adição (werkzeug.security e itsdangerous já vêm com o Flask)

================================
Total: 23 findings
================================
