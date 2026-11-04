================================
RELATÓRIO DE AUDITORIA DE ARQUITETURA
================================
Projeto:  task-manager-api
Stack:    Python 3.9.6 + Flask 3.0.0
Arquivos: 15 analisados | ~1158 linhas de código
Data:     2026-11-03

## Resumo
CRITICAL: 5 | HIGH: 5 | MEDIUM: 9 | LOW: 4

| # | Severidade | Anti-pattern | Local principal |
|---|---|---|---|
| F-01 | CRITICAL | Segredos e credenciais hardcoded (AP-02) | app.py:13 |
| F-02 | CRITICAL | Exposição de dados sensíveis — hash de senha nas respostas (AP-03) | models/user.py:16-25 |
| F-03 | CRITICAL | Armazenamento inseguro de senha (AP-04) | models/user.py:27-32 |
| F-04 | CRITICAL | Operação privilegiada sem controle de acesso (AP-05) | routes/user_routes.py:207-211 |
| F-05 | CRITICAL | God Module (AP-06) | routes/report_routes.py:1-223 |
| F-06 | HIGH | Exposição de dados pessoais a anônimos — e-mails (AP-03) | routes/user_routes.py:10-25 |
| F-07 | HIGH | Regra de negócio na camada HTTP (AP-07) | routes/task_routes.py:11-63 |
| F-08 | HIGH | Unicidade checada por leitura antes da escrita (AP-09) | routes/user_routes.py:67-90 |
| F-09 | HIGH | Configuração de execução insegura (AP-10) | app.py:34 |
| F-10 | HIGH | Acoplamento forte sem injeção de dependência (AP-11) | app.py:9-31 |
| F-11 | MEDIUM | Aninhamento profundo — pirâmide de `if` do atraso (AP-12) | routes/task_routes.py:30-39 |
| F-12 | MEDIUM | Query N+1 (AP-13) | routes/task_routes.py:41-57 |
| F-13 | MEDIUM | Validação ausente ou duplicada (AP-14) | routes/task_routes.py:92-124 |
| F-14 | MEDIUM | Tratamento de erro não centralizado (AP-15) | routes/task_routes.py:13-63 |
| F-15 | MEDIUM | CORS permissivo (AP-16) | app.py:15 |
| F-16 | MEDIUM | Listagem sem paginação (AP-17) | routes/task_routes.py:14 |
| F-17 | MEDIUM | Integridade referencial não garantida (AP-18) | routes/user_routes.py:140-142 |
| F-18 | MEDIUM | API deprecated (AP-19) | routes/task_routes.py:42 |
| F-19 | MEDIUM | Serialização manual duplicada e divergente (AP-24) | routes/task_routes.py:17-28 |
| F-20 | LOW | Logging via `print` (AP-20) | routes/task_routes.py:149 |
| F-21 | LOW | Magic numbers e literais duplicados (AP-21) | routes/task_routes.py:96-114 |
| F-22 | LOW | Código morto (AP-22) | utils/helpers.py:1-116 |
| F-23 | LOW | Nomenclatura pobre e código verboso (AP-23) | models/task.py:38-48 |

## Findings

### F-01 [CRITICAL] Segredos e credenciais hardcoded (AP-02)
Arquivo: app.py:13
Ocorrências: services/notification_service.py:7-10
Descrição: `app.config['SECRET_KEY'] = 'super-secret-****'` está literal no entry point versionado. `NotificationService.__init__` fixa host, porta, usuário (`'taskmanager@****'`) e senha SMTP (`'senha****'`). A URI do banco (`app.py:11`) e a porta (`app.py:34`) também são literais (ver F-09).
Impacto: quem lê o repositório obtém a chave que assina sessões, e passará a assinar os tokens de login (F-04), além da senha da conta de e-mail. Trocar qualquer segredo exige editar código e fazer novo deploy.
Recomendação: criar `config.py` que lê `SECRET_KEY`, `DATABASE_URL`, `PORT`, `DEBUG`, `CORS_ORIGINS` e as credenciais SMTP do ambiente (com `python-dotenv`, já declarado), sem segredo literal como default; `.env.example` com placeholders — Playbook T02.
Contrato: preservado

### F-02 [CRITICAL] Exposição de dados sensíveis — hash de senha nas respostas (AP-03)
Arquivo: models/user.py:16-25
Ocorrências: routes/user_routes.py:33 (`GET /users/<id>`), routes/user_routes.py:85-86 (`POST /users`), routes/user_routes.py:129 (`PUT /users/<id>`), routes/user_routes.py:209 (`POST /login`, em `user`)
Descrição: `User.to_dict()` inclui `'password': self.password` (linha 21), que é o hash MD5 da senha, e quatro rotas devolvem esse dicionário. O baseline confirma a chave `password` nas respostas de `GET /users/1`, `POST /users`, `PUT /users/2` e em `user.password` no login. Só `GET /users` (user_routes.py:15-23) monta outro dicionário e omite o campo (ver F-19).
Impacto: qualquer cliente anônimo lê o hash de qualquer usuário com `GET /users/<id>`. Com MD5 sem salt (F-03), a senha original sai em segundos.
Recomendação: serializer de usuário com campos explícitos, sem `password`, usado em todas as rotas — Playbook T13.
Contrato: exige BC-01, BC-02, BC-03, BC-04

### F-03 [CRITICAL] Armazenamento inseguro de senha (AP-04)
Arquivo: models/user.py:27-32
Ocorrências: Nenhuma adicional
Descrição: `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()` e `check_password` compara por igualdade direta (`==`), com MD5 rápido e sem salt. Também conta como AP-19 (algoritmo obsoleto para senha), consolidado aqui pela regra 4.
Impacto: com um dump do banco, ou só com F-02, as senhas saem por rainbow table. A comparação com `==` não é em tempo constante.
Recomendação: hash com KDF e salt (`werkzeug.security.generate_password_hash`/`check_password_hash`, já instalado com o Flask), verificação de hash legado MD5 com re-hash no login bem-sucedido, e coluna `password` com tamanho suficiente — Playbook T05.
Contrato: preservado

### F-04 [CRITICAL] Operação privilegiada sem controle de acesso (AP-05)
Arquivo: routes/user_routes.py:207-211
Ocorrências: routes/task_routes.py:225-238 (`DELETE /tasks/<id>`), routes/user_routes.py:134-151 (`DELETE /users/<id>`), routes/report_routes.py:211-223 (`DELETE /categories/<id>`), routes/user_routes.py:52,71-78 (`POST /users` aceita `role`), routes/user_routes.py:114-125 (`PUT /users/<id>` aceita `password`, `role`, `active`)
Descrição: o login devolve `'token': 'fake-jwt-token-' + str(user.id)`, um token previsível e não assinado, e nenhuma rota verifica token algum: não há decorator nem middleware de autenticação no projeto. Com isso, um cliente anônimo:
- apaga qualquer task, usuário (e as tasks dele) ou categoria;
- cria um usuário com `"role":"admin"` (`POST /users`; o baseline confirma 201);
- troca a senha, o perfil ou o estado `active` de qualquer conta (`PUT /users/<id>`), o que permite tomar a conta.
Impacto: tomada de qualquer conta, autopromoção a admin e destruição de todos os dados por iteração de ids, tudo anonimamente (escalonamento por exposição externa).
Recomendação, rota a rota pela tabela de situações da T14 (nenhuma rota executa SQL/código do cliente nem faz destruição em massa, então nenhuma é **removida**):
- `POST /login`, linha "Token falso" (a): emitir token assinado com `itsdangerous.URLSafeTimedSerializer` (vem com o Flask), com `max_age`, na mesma chave `token`.
- `DELETE /tasks/<id>` e `DELETE /categories/<id>`, linha "Token falso" (b): **proteger**, exigindo `Authorization: Bearer <token>`. O middleware recarrega o usuário a cada requisição, e conta apagada ou inativa recebe 401.
- `DELETE /users/<id>`, linhas "Token falso" (b) + "perfil/credencial/estado": **proteger** com Bearer. Só o próprio usuário ou um admin pode apagar a conta; os demais recebem 403.
- `PUT /users/<id>`, linha "perfil/credencial/estado": **proteger** com Bearer. Só o próprio usuário altera os próprios dados e a própria senha. Só um admin altera `role` ou `active`, ou dados de outra conta; os demais recebem 403.
- `POST /users`, linha "perfil/credencial/estado": o cadastro continua público, mas `role` vindo do corpo só é aplicado quando quem chama é admin autenticado. Do contrário, grava o perfil padrão `user`. A validação do valor de `role` (400 `Role inválido`) continua.
- Primeiro admin: o seed de desenvolvimento cria `joao@email.com` como admin; para produção, comando `flask --app app create-admin`, documentado no README.
Playbook T14.
Contrato: exige BC-05, BC-06, BC-07, BC-08, BC-09, BC-10

### F-05 [CRITICAL] God Module (AP-06)
Arquivo: routes/report_routes.py:1-223
Ocorrências: Nenhuma adicional
Descrição: o Blueprint `reports` mistura dois domínios, relatórios (linhas 12-155) e o CRUD completo de categorias (linhas 157-223), e quatro responsabilidades: HTTP (`request`, `jsonify`, status codes), dados (`Task.query`, `User.query`, `Category.query`, `db.session` em todas as funções), regra de negócio (contagem por status e prioridade, atraso e taxa de conclusão nas linhas 15-68 e 119-151) e validação (linhas 170-175). As rotas de categorias estão num arquivo chamado `report_routes`.
Impacto: nada ali se testa sem HTTP e banco. Mudar categorias mexe no arquivo de relatórios, e as regras de atraso e conclusão ficam presas à rota.
Recomendação: separar em `CategoryRepository`/`CategoryService`/`CategoryController` + `category_routes.py` e `ReportService`/`ReportController` + `report_routes.py`, com agregação no repositório — Playbook T03 (com T04).
Contrato: preservado

### F-06 [HIGH] Exposição de dados pessoais a anônimos — e-mails (AP-03)
Arquivo: routes/user_routes.py:10-25
Ocorrências: routes/user_routes.py:27-40 (`GET /users/<id>`), routes/report_routes.py:103-155 (`GET /reports/user/<id>`, e-mail na linha 141)
Descrição: `GET /users` lista nome, e-mail e perfil de todos os usuários. `GET /users/<id>` e `GET /reports/user/<id>` devolvem o e-mail de qualquer id. Tudo isso responde a clientes anônimos. Os nomes continuam públicos, porque aparecem como responsável em `GET /tasks` (`user_name`) e em `/reports/summary`. O e-mail é o identificador de login e de contato.
Impacto: enumeração anônima de todos os e-mails e perfis (inclusive quem é admin), o que facilita força bruta no `/login` e phishing. Fere a LGPD (dado pessoal sem controle de acesso).
Recomendação: exigir `Authorization: Bearer <token>` (o mesmo middleware de F-04) nas três rotas que devolvem e-mail — Playbook T14 (com T13).
Contrato: exige BC-11, BC-12, BC-13

### F-07 [HIGH] Regra de negócio na camada HTTP (AP-07)
Arquivo: routes/task_routes.py:11-63
Ocorrências: routes/task_routes.py:85-154 (`create_task`, 70 linhas), routes/task_routes.py:156-223 (`update_task`), routes/task_routes.py:273-299 (`task_stats`: contagens e `completion_rate`), routes/user_routes.py:42-90 (`create_user`), routes/user_routes.py:92-132 (`update_user`), routes/user_routes.py:153-183 (`get_user_tasks`)
Descrição: os handlers fazem tudo: consultam o banco (`Task.query`, `User.query.get`, `db.session.add/commit`), calculam o atraso (`overdue`) inline, verificam se usuário e categoria existem, calculam a taxa de conclusão e montam a resposta. `get_tasks` tem 53 linhas, `create_task` 70. Os métodos de domínio que já existem, `Task.is_overdue`/`validate_status`/`validate_priority` (models/task.py:38-60), não são usados.
Impacto: as regras de atraso e conclusão, copiadas em 7 lugares (F-11), não se reaproveitam nem se testam sem HTTP, e cada cópia pode divergir.
Recomendação: controllers finos (entrada → service → status) e services com as regras (`TaskService`, `UserService`, `ReportService`), usando a regra de atraso única do model — Playbook T04.
Contrato: preservado

### F-08 [HIGH] Unicidade checada por leitura antes da escrita (AP-09)
Arquivo: routes/user_routes.py:67-90
Ocorrências: routes/user_routes.py:109-112 + 127-132 (`PUT /users/<id>`)
Descrição: `create_user` faz `User.query.filter_by(email=email).first()` (linha 67) e, se não houver registro, insere (linhas 80-82). `update_user` faz o mesmo antes de trocar o e-mail. O `UNIQUE` existe no schema (models/user.py:10), mas a violação causada por duas requisições paralelas cai no `except Exception` e vira `500 {"error": "Erro ao criar usuário"}` (linhas 87-90) ou `500 "Erro ao atualizar"` (linhas 130-132), em vez do `409 "Email já cadastrado"` do caminho sequencial.
Impacto: em requisições simultâneas com o mesmo e-mail, o cliente recebe 500 em vez do erro de negócio. O UNIQUE no banco evita duplicata, mas o contrato do caminho de conflito não é cumprido sob concorrência.
Recomendação: manter a checagem prévia para a mensagem, garantir `UNIQUE` (também `CREATE UNIQUE INDEX IF NOT EXISTS` no boot para bancos antigos) e converter `IntegrityError` no mesmo `409 "Email já cadastrado"`, com rollback, dentro da transação da escrita — Playbook T07 (passos 1-3, unicidade).
Contrato: preservado

### F-09 [HIGH] Configuração de execução insegura (AP-10)
Arquivo: app.py:34
Ocorrências: app.py:30-31 (`db.create_all()` no import do módulo), app.py:11 (URI do banco literal)
Descrição: `app.run(debug=True, host='0.0.0.0', port=5000)` liga o debugger do Werkzeug, que permite executar código pelo navegador, escutando em todas as interfaces. A porta é literal, sem leitura de ambiente; no macOS a 5000 conflita com o AirPlay, e o baseline teve de usar `flask run --port 5050`. O schema é criado como efeito colateral do import.
Impacto: execução remota de código para quem alcançar a máquina, e não há como configurar ambientes diferentes sem editar código.
Recomendação: `DEBUG` (padrão `False`), `HOST` (padrão `127.0.0.1`) e `PORT` (padrão `5000`) vindos do `config.py`, e `create_all` dentro da factory — Playbook T02.
Contrato: preservado

### F-10 [HIGH] Acoplamento forte sem injeção de dependência (AP-11)
Arquivo: app.py:9-31
Ocorrências: routes/task_routes.py:2-5, routes/user_routes.py:2-4, routes/report_routes.py:2-5, services/notification_service.py:15, seed.py:2
Descrição: a aplicação é um objeto global montado no import (`app = Flask(__name__)`, sem factory), e o `seed.py` depende dele. Todo arquivo de rotas importa `database.db` e as classes de model concretas e chama `db.session`/`Model.query` direto do handler. Não há ponto para substituir o acesso a dados. `NotificationService.send_email` instancia `smtplib.SMTP(self.email_host, ...)` dentro do método (host fixo nas linhas 7-8).
Impacto: testar exige o banco real e o módulo global. Não há como trocar o banco ou o SMTP sem editar a regra, e os testes interferem entre si pelo estado do app global.
Recomendação: `create_app(config)` como composition root, que instancia repositories → services → controllers e os injeta nos blueprints. Manter `app = create_app()` no módulo para `python app.py`, `flask --app app` e `seed.py`. A classe SMTP é removida como código morto (F-22) — Playbook T11.
Contrato: preservado

### F-11 [MEDIUM] Aninhamento profundo — pirâmide de `if` do atraso (AP-12)
Arquivo: routes/task_routes.py:30-39
Ocorrências: routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180, routes/report_routes.py:34-43, routes/report_routes.py:132-135, models/task.py:50-60
Descrição: a regra "atrasada = tem `due_date` no passado e status fora de `done`/`cancelled`" é escrita sete vezes como pirâmide de `if`/`else` com 3 ou 4 níveis (dentro de laço), atribuindo `True`/`False` em cada ramo.
Impacto: só legibilidade e duplicação (o código é síncrono e correto); qualquer mudança na regra precisa ser feita sete vezes.
Recomendação: uma expressão booleana com guard clause em `Task.is_overdue()`, usada por todos — Playbook T06.
Contrato: preservado

### F-12 [MEDIUM] Query N+1 (AP-13)
Arquivo: routes/task_routes.py:41-57
Ocorrências: routes/user_routes.py:22 (`len(u.tasks)` lazy por usuário), routes/report_routes.py:55-56 (`Task.query.filter_by(user_id=u.id).all()` por usuário), routes/report_routes.py:162-163 (`count()` por categoria), routes/task_routes.py:275-279 (5 `COUNT` seguidos), routes/report_routes.py:15-28 (12 `COUNT` seguidos)
Descrição: `get_tasks` faz `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` para cada task, ou seja, 1 + 2N consultas. As listagens de usuários e categorias e o relatório consultam por item. Os totais por status e prioridade são feitos com uma consulta por valor, quando caberiam num `GROUP BY`.
Impacto: o tempo de resposta cresce linearmente com o volume; 1.000 tasks geram cerca de 2.000 consultas em `GET /tasks`.
Recomendação: eager loading (`selectinload`/`joinedload`) dos relacionamentos, contagens com `GROUP BY` agregadas no repositório — Playbook T08.
Contrato: preservado

### F-13 [MEDIUM] Validação ausente ou duplicada (AP-14)
Arquivo: routes/task_routes.py:92-124
Ocorrências: routes/task_routes.py:166-198 (cópia em `update_task`), routes/user_routes.py:54-72 e 102-122 (cópia em criar/atualizar usuário), routes/report_routes.py:196-202 (`PUT /categories` sem validação), utils/helpers.py:19-23, 52-55, 57-108 (validadores prontos e nunca chamados), models/task.py:38-48 (idem)
Descrição: as regras de título, status, prioridade, data, e-mail, senha e role estão copiadas entre criar e atualizar. Não há checagem de tipo, e o original devolve 500 em todos estes casos, verificados com o test client:
- `POST /tasks {"priority":"abc"}`: `TypeError` em `priority < 1` (task_routes.py:113);
- `POST /tasks ["x"]`: `AttributeError` em `data.get` (task_routes.py:92);
- `POST /users {"email":123}`: `TypeError` no `re.match` (user_routes.py:61);
- `GET /tasks/search?priority=abc`: `ValueError` em `int(priority)` (task_routes.py:261);
- `PUT /categories/1 {"name":null}`: `IntegrityError` (report_routes.py:197-198);
- `PUT /users/2 {"active":"abc"}`: erro de tipo do SQLAlchemy (user_routes.py:124-125).

`color` da categoria nunca é validada, apesar de `is_valid_color` existir. `process_task_data` e `validate_email` em `utils/helpers.py` estão prontos, mas ninguém os chama.
Impacto: erros 500 com entrada inválida e regras que podem divergir entre criar e atualizar.
Recomendação: validadores reutilizáveis por entidade (um para criar e outro para atualizar), com checagem de tipo antes de comparar. As mensagens e os status de hoje se mantêm, e o tipo inválido vira 400 — Playbook T09.
Contrato: preservado (entradas que hoje dão 500 passam a dar 400)

### F-14 [MEDIUM] Tratamento de erro não centralizado (AP-15)
Arquivo: routes/task_routes.py:13-63
Ocorrências: `except:` sem tipo em routes/task_routes.py:62, 137, 204, 236; routes/user_routes.py:130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46, 49, 88. `except Exception as e` em routes/task_routes.py:151, 221; routes/user_routes.py:87; services/notification_service.py:23
Descrição: há 16 blocos `try/except` espalhados, 12 deles sem tipo, e nenhum `@app.errorhandler`. `get_tasks` embrulha o handler inteiro e transforma qualquer bug em `500 {"error": "Erro interno"}`. Exceções não capturadas nas outras rotas (veja F-13) saem como a página HTML 500 do Flask, então o formato de erro varia entre JSON e texto.
Impacto: bugs silenciosos, respostas inconsistentes e tratamento duplicado em cada handler.
Recomendação: exceções de domínio (`NotFoundError`, `ValidationError`, `ConflictError`, `UnauthorizedError`, `ForbiddenError`) e um error handler central que preserva `HTTPException` (404/405 do framework) e devolve `{"error": ...}` — Playbook T10.
Contrato: preservado

### F-15 [MEDIUM] CORS permissivo (AP-16)
Arquivo: app.py:15
Ocorrências: Nenhuma adicional
Descrição: `CORS(app)` sem `origins` libera qualquer origem em todas as rotas. Não há `supports_credentials`, por isso fica em MEDIUM.
Impacto: qualquer site pode chamar a API pelo navegador de um usuário.
Recomendação: origens permitidas lidas de `CORS_ORIGINS` no `config.py` — Playbook T02.
Contrato: preservado (cabeçalhos CORS não fazem parte do contrato comparado; status e corpo não mudam)

### F-16 [MEDIUM] Listagem sem paginação (AP-17)
Arquivo: routes/task_routes.py:14
Ocorrências: routes/task_routes.py:266 (`/tasks/search`), routes/user_routes.py:12 (`/users`), routes/report_routes.py:159 (`/categories`), routes/task_routes.py:281 e routes/report_routes.py:30, 53 (relatórios carregam tabelas inteiras para contar)
Descrição: `Task.query.all()`, `User.query.all()` e `Category.query.all()` são devolvidos sem limite. As estatísticas carregam todas as tasks em memória para contar as atrasadas.
Impacto: memória e tempo crescem com o volume.
Recomendação: paginação **opcional** (`?page=&per_page=`; sem os parâmetros a resposta é a lista completa, como hoje) e contagem de atrasadas por SQL — Playbook T17 (com T08).
Contrato: preservado

### F-17 [MEDIUM] Integridade referencial não garantida (AP-18)
Arquivo: routes/user_routes.py:140-142
Ocorrências: routes/report_routes.py:211-223 (`delete_category`), models/task.py:13-14, 20-21 (FKs e relationships sem `ondelete`/`cascade`), app.py:11 (SQLite sem `PRAGMA foreign_keys = ON`)
Descrição: `delete_user` apaga as tasks do usuário num laço manual (`for t in tasks: db.session.delete(t)`) antes de apagar o usuário. `delete_category` depende do comportamento implícito do SQLAlchemy, que anula o `category_id` das tasks porque o backref não tem cascade declarado. O SQLite não aplica FKs (`foreign_keys` desligado), então qualquer escrita fora do ORM, ou com id inexistente, deixa órfãos.
Impacto: a regra de remoção não está declarada em lugar nenhum; uma mudança no relacionamento passa a gerar órfãos ou apagar dados sem aviso.
Recomendação: cascade explícito no relationship (`User.tasks`: `cascade="all, delete-orphan"`; `Category.tasks`: anula `category_id`, declarado com `passive_deletes`/`ondelete='SET NULL'`), `PRAGMA foreign_keys=ON` em cada conexão SQLite e remoção sem o laço manual — Playbook T15.
Contrato: preservado

### F-18 [MEDIUM] API deprecated (AP-19)
Arquivo: routes/task_routes.py:42
Ocorrências: `Model.query.get(id)` em routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213. `datetime.utcnow()` em models/category.py:11; models/task.py:15, 16, 52; models/user.py:14; routes/report_routes.py:35, 42, 45, 71, 133; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; services/notification_service.py:35; utils/helpers.py:38; seed.py:66, 67, 69, 70, 74
Descrição: `Query.get()` emite `LegacyAPIWarning` no SQLAlchemy 2.0.52 instalado, confirmado com `python -W default` em `task_routes.py:42, 51, 67`. `datetime.utcnow()` está deprecated desde o Python 3.12. O runtime atual (3.9) não avisa, mas o código quebra o upgrade. O MD5 para senha está em F-03.
Impacto: avisos em runtime hoje e remoção prevista em versões futuras do SQLAlchemy e do Python.
Recomendação: `db.session.get(Model, id)` e um relógio único `utcnow()` baseado em `datetime.now(timezone.utc)` (sem tzinfo na gravação, para manter o formato das datas nas respostas) — Playbook T12.
Contrato: preservado

### F-19 [MEDIUM] Serialização manual duplicada e divergente (AP-24)
Arquivo: routes/task_routes.py:17-28
Ocorrências: routes/user_routes.py:15-23 (usuário sem `password`, enquanto `User.to_dict` inclui), routes/user_routes.py:162-169 (task parcial), routes/report_routes.py:38-43, 139-142
Descrição: `get_tasks` remonta campo a campo o mesmo dicionário de `Task.to_dict()`. `get_users` monta um usuário sem `password`, enquanto `to_dict()` (models/user.py:16-25), usado nas outras rotas, inclui. `get_user_tasks` serializa um subconjunto próprio. Cópias divergentes na exposição da senha elevam o finding a MEDIUM.
Impacto: uma rota esconde a senha e outra expõe, e qualquer campo novo precisa ser lembrado em cada cópia.
Recomendação: serializers com campos explícitos por formato de resposta (task completa, task resumida do usuário, usuário público), mantendo exatamente as chaves de hoje em cada rota — Playbook T13.
Contrato: preservado (a remoção de `password` já está declarada em F-02)

### F-20 [LOW] Logging via `print` (AP-20)
Arquivo: routes/task_routes.py:149
Ocorrências: routes/task_routes.py:153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39, 41
Descrição: eventos e erros vão para stdout com `print`, sem nível nem destino configurável. `print(f"ERRO: {str(e)}")` mistura erro com saída comum. Os `print` do `seed.py` são falso positivo (script de linha de comando).
Impacto: não há filtro por nível nem integração com coleta de logs.
Recomendação: `logging.getLogger(__name__)` com nível configurável — Playbook T16.
Contrato: preservado

### F-21 [LOW] Magic numbers e literais duplicados (AP-21)
Arquivo: routes/task_routes.py:96-114
Ocorrências: lista de status em routes/task_routes.py:110, 177; models/task.py:39; utils/helpers.py:75. Roles em routes/user_routes.py:71, 120. Título 3/200 em routes/task_routes.py:96, 99, 167, 169. Senha 4 em routes/user_routes.py:64, 115. Prioridade 1..5 em routes/task_routes.py:104, 113, 182; models/task.py:46. Alta prioridade `<= 2` em routes/report_routes.py:129. 7 dias em routes/report_routes.py:45. Constantes declaradas e não usadas em utils/helpers.py:110-116
Descrição: os limites e enums do domínio aparecem como literais repetidos, e as constantes que os nomeiam existem em `utils/helpers.py` sem ninguém usar.
Impacto: mudar uma regra exige caçar literais em vários arquivos.
Recomendação: `constants.py` com os valores do domínio, usado pelos validadores e services — Playbook T16.
Contrato: preservado

### F-22 [LOW] Código morto (AP-22)
Arquivo: utils/helpers.py:1-116
Ocorrências: services/notification_service.py:1-48 (classe nunca instanciada, com AP-08 latente: `self.notifications = []` como armazenamento em memória, linha 6), imports não usados em app.py:7 (`os, sys, json`), routes/task_routes.py:7 (`json, os, sys, time`), routes/user_routes.py:6 (`hashlib, json`), routes/report_routes.py:7-8 (`format_date, calculate_percentage, json`), models/task.py:3 (`json`), utils/helpers.py:3-7; métodos nunca chamados em models/task.py:38-60 e models/user.py:34-38; dependências declaradas e nunca importadas em requirements.txt:4-6 (`marshmallow`, `requests`, `python-dotenv`)
Descrição: nenhuma função de `utils/helpers.py` é chamada; `format_date` e `calculate_percentage` são importadas em `report_routes.py:7` e não usadas. `NotificationService` não é referenciada em nenhum lugar. Os validadores prontos e não usados estão em F-13.
Impacto: ruído e falsa impressão de funcionalidade (notificações por e-mail que não existem). Também mantém credenciais SMTP no repositório (F-01).
Recomendação: remover módulos, imports e métodos mortos. Remover `marshmallow` e `requests`; `python-dotenv` passa a ser usado pelo `config.py` (T02). Se a notificação por e-mail for desejada, reintroduzi-la depois, injetada pelo composition root — Playbook T16.
Contrato: preservado

### F-23 [LOW] Nomenclatura pobre e código verboso (AP-23)
Arquivo: models/task.py:38-48
Ocorrências: models/user.py:34-38, utils/helpers.py:21-23, 53-55 (`if cond: return True else: return False`); nomes curtos `u`, `t`, `c`, `p`, `cat`, `d` em routes/user_routes.py:14, routes/task_routes.py:16, routes/report_routes.py:55, 161, models/category.py:14; `type(tags) == list` em routes/task_routes.py:141, 210
Descrição: retornos booleanos verbosos, variáveis de uma letra fora de laços curtos e comparação de tipo por igualdade em vez de `isinstance`.
Impacto: só legibilidade.
Recomendação: retornar a expressão, usar nomes descritivos e `isinstance` em identificadores internos (chaves JSON não mudam) — Playbook T16.
Contrato: preservado

## APIs deprecated
| API ou dependência | Local | Substituto | Evidência |
|---|---|---|---|
| `Model.query.get(id)` (SQLAlchemy 2.0) | routes/task_routes.py:42 e mais 15 ocorrências (F-18) | `db.session.get(Model, id)` | `LegacyAPIWarning` em runtime com `python -W default` (task_routes.py:42, 51, 67) |
| `datetime.utcnow()` | models/task.py:15 e mais 21 ocorrências (F-18) | `datetime.now(timezone.utc)` | deprecated no Python 3.12 (catálogo); sem aviso no 3.9.6 em uso |
| `hashlib.md5` para senha | models/user.py:29, 32 | KDF com salt (`werkzeug.security`) | algoritmo obsoleto para senha; consolidado em F-03 (AP-04) |
| `Model.query.filter(...)` / `filter_by` (API legada do 2.0) | routes/*.py | `db.session.execute(select(...))` | legada no 2.0 sem aviso em runtime; migrada junto com os repositórios (F-18) |

## Breaking Changes propostos
| # | Rota | Mudança no contrato | Finding que justifica |
|---|---|---|---|
| BC-01 | GET /users/<id> | remove a chave `password` do objeto do usuário; as demais chaves e `tasks[]` permanecem | F-02 — hash de senha exposto a anônimos |
| BC-02 | POST /users | remove a chave `password` da resposta 201 | F-02 — hash de senha exposto |
| BC-03 | PUT /users/<id> | remove a chave `password` da resposta 200 | F-02 — hash de senha exposto |
| BC-04 | POST /login | remove `user.password` da resposta 200 | F-02 — hash de senha exposto |
| BC-05 | POST /login | o valor de `token` passa a ser assinado (`itsdangerous`, validade de 24h) em vez de `fake-jwt-token-<id>`; mesma chave e mesmo tipo (texto) | F-04 — token falso/previsível |
| BC-06 | POST /users | `role` do corpo só é aplicado quando quem chama é admin autenticado (`Authorization: Bearer`); anônimo ou não-admin grava `role = "user"`. Status e chaves iguais; `role` inválido continua 400 | F-04 — autopromoção a admin |
| BC-07 | PUT /users/<id> | exige `Authorization: Bearer`: sem token ou com token inválido → `401 {"error"}`; não-admin alterando outra conta, ou `role`/`active` → `403 {"error"}` | F-04 — tomada de conta e escalada de privilégio |
| BC-08 | DELETE /tasks/<id> | exige `Authorization: Bearer`; sem token → `401 {"error"}` (antes da busca do id) | F-04 — remoção anônima |
| BC-09 | DELETE /users/<id> | exige `Authorization: Bearer`; sem token → 401; não-admin apagando outra conta → `403 {"error"}` | F-04 — remoção anônima de contas |
| BC-10 | DELETE /categories/<id> | exige `Authorization: Bearer`; sem token → `401 {"error"}` | F-04 — remoção anônima |
| BC-11 | GET /users | exige `Authorization: Bearer`; sem token → `401 {"error"}` | F-06 — e-mails expostos a anônimos |
| BC-12 | GET /users/<id> | exige `Authorization: Bearer`; sem token → `401 {"error"}` | F-06 — e-mail exposto a anônimos |
| BC-13 | GET /reports/user/<id> | exige `Authorization: Bearer`; sem token → `401 {"error"}` | F-06 — e-mail exposto a anônimos |

Divergências esperadas no `smoke.sh`: as chamadas anônimas `GET /users`, `GET /users/999999`, `GET /reports/user/999999`, `PUT /users/999999`, `DELETE /tasks/999999`, `DELETE /categories/999999` e `DELETE /users/999999` passam de 200/404 para 401. As respostas com usuário perdem `password`. As chamadas com token mantêm status e chaves.

## Plano de refatoração
Ponto de partida: camadas parciais (`models/`, `routes/`, `services/`, `utils/`). A estrutura que já cumpre o papel é mantida, e as camadas que faltam são acrescentadas:

```
app.py                     composition root: create_app(), app = create_app(), __main__ com config
config.py                  configuração lida do ambiente (T02)
constants.py               enums e limites do domínio (T16)
clock.py                   utcnow() único (T12)
passwords.py               hash KDF + verificação de legado MD5 (T05)
errors.py                  exceções de domínio (T10)
database.py                db + PRAGMA foreign_keys + índice único (T15, T07)
models/                    entidades (task, user, category) + repositories.py (T03, T05, T08, T12, T15)
services/                  task_service, user_service, category_service, report_service, auth_service (T04, T07, T14)
controllers/               task, user, category, report + validators.py (T04, T09)
routes/                    task_routes, user_routes, category_routes, report_routes + serializers.py (T13, T14, T17)
middlewares/               auth.py (require_auth), error_handler.py (T10, T14)
seed.py                    continua `python seed.py`
```

Ordem: config (T02) → models e repositórios (T03, T05, T07, T08, T12, T15) → services (T04, T07, T14) → controllers e validadores (T04, T09) → routes e serializers (T13, T14, T17) → middlewares (T10, T14) → composition root (T11) → limpeza (T16: `utils/` e `services/notification_service.py` removidos, imports, `print` → `logging`, `requirements.txt`).

Comandos preservados: `pip install -r requirements.txt`, `python seed.py`, `python app.py` (porta via `PORT`, padrão 5000).

================================
Total: 23 findings
================================
