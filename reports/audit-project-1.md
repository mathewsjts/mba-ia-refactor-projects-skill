================================
RELATÓRIO DE AUDITORIA DE ARQUITETURA
================================
Projeto:  code-smells-project
Stack:    Python 3.9.6 + Flask 3.1.1 (flask-cors 5.0.1)
Arquivos: 4 analisados | ~780 linhas de código
Data:     2026-10-28

## Resumo
CRITICAL: 6 | HIGH: 5 | MEDIUM: 6 | LOW: 5

| # | Severidade | Anti-pattern | Local principal |
|---|---|---|---|
| F-01 | CRITICAL | SQL Injection por concatenação (AP-01) | models.py:28 |
| F-02 | CRITICAL | Segredos e credenciais hardcoded (AP-02) | app.py:7 |
| F-03 | CRITICAL | Exposição de dados sensíveis (AP-03) | controllers.py:285-289 |
| F-04 | CRITICAL | Armazenamento inseguro de senha (AP-04) | models.py:126-129 |
| F-05 | CRITICAL | Operação privilegiada sem controle de acesso (AP-05) | app.py:59-78 |
| F-06 | CRITICAL | God Module (AP-06) | models.py:1-315 |
| F-07 | HIGH | Regra de negócio na camada HTTP (AP-07) | controllers.py:208-210 |
| F-08 | HIGH | Estado global mutável (AP-08) | database.py:4-11 |
| F-09 | HIGH | Operação multi-passo sem transação (AP-09) | models.py:133-169 |
| F-10 | HIGH | Configuração de execução insegura (AP-10) | app.py:8,88 |
| F-11 | HIGH | Acoplamento forte sem injeção de dependência (AP-11) | database.py:7-11 |
| F-12 | MEDIUM | Query N+1 (AP-13) | models.py:171-201 |
| F-13 | MEDIUM | Validação ausente ou duplicada (AP-14) | controllers.py:28-54 |
| F-14 | MEDIUM | Tratamento de erro não centralizado (AP-15) | controllers.py:10-12 |
| F-15 | MEDIUM | CORS permissivo (AP-16) | app.py:9 |
| F-16 | MEDIUM | Listagem sem paginação (AP-17) | models.py:4-22 |
| F-17 | MEDIUM | Integridade referencial não garantida (AP-18) | database.py:14-53 |
| F-18 | LOW | Logging via print (AP-20) | controllers.py:8,208-210 |
| F-19 | LOW | Magic numbers e literais duplicados (AP-21) | models.py:257-262 |
| F-20 | LOW | Código morto (AP-22) | models.py:2 |
| F-21 | LOW | Nomenclatura pobre (AP-23) | models.py:187-193 |
| F-22 | LOW | Serialização manual duplicada (AP-24) | models.py:12-21 |

## Findings

### F-01 [CRITICAL] SQL Injection por concatenação (AP-01)
Arquivo: models.py:28
Ocorrências: models.py:47-50, models.py:57-61, models.py:68, models.py:92, models.py:109-111, models.py:126-129, models.py:140, models.py:148-166, models.py:174, models.py:188, models.py:192, models.py:220, models.py:224, models.py:279-281, models.py:289-297
Descrição: Toda a camada de dados monta SQL por concatenação de string com entrada do cliente. Ex.: `get_produto_por_id` faz `"SELECT * FROM produtos WHERE id = " + str(id)` (linha 28); `criar_produto` concatena `nome`, `descricao`, `categoria` direto no INSERT (47-50); `login_usuario` concatena `email` e `senha` no WHERE (109-111), permitindo bypass com `' OR '1'='1`; `buscar_produtos` constrói o WHERE com `termo`/`categoria` do querystring (289-297). Nenhuma query usa bind parameters (`?`).
Impacto: leitura, alteração e destruição arbitrária de dados; bypass de autenticação no login; exfiltração completa do banco por qualquer cliente.
Recomendação: substituir toda concatenação por queries parametrizadas com placeholders `?` e argumentos vinculados, em funções de acesso a dados por domínio — Playbook T01.
Contrato: preservado

### F-02 [CRITICAL] Segredos e credenciais hardcoded (AP-02)
Arquivo: app.py:7
Ocorrências: controllers.py:289 (mesma chave vazada na resposta de `/health`), database.py:75-78 (usuário admin com senha fixa `admin123` semeado no boot)
Descrição: `SECRET_KEY` está literal no código: `app.config["SECRET_KEY"] = "minha-chave-****"` (app.py:7). A mesma chave é devolvida em texto pela rota pública `/health` (controllers.py:289). O seed cria `admin@loja.com` com senha fixa `admin123` embutida no código de produção (database.py:76).
Impacto: qualquer pessoa com acesso ao repositório obtém a chave e pode forjar sessões; rotacionar exige novo deploy; conta admin com senha pública conhecida.
Recomendação: mover `SECRET_KEY` e credenciais de seed para variáveis de ambiente lidas por uma camada de config, com `.env.example` documentando as chaves sem valores reais — Playbook T02. Remover a chave da resposta de `/health` (ver F-03).
Contrato: preservado (a remoção da chave de `/health` é tratada em F-03 / BC-03)

### F-03 [CRITICAL] Exposição de dados sensíveis (AP-03)
Arquivo: controllers.py:285-289
Ocorrências: models.py:83 e models.py:99 (`senha` incluída na serialização de usuário, devolvida por `GET /usuarios` e `GET /usuarios/<id>`)
Descrição: `health_check` devolve em rota pública `secret_key`, `debug`, `db_path` e `ambiente` (controllers.py:285-289). `get_todos_usuarios` (models.py:79-86) e `get_usuario_por_id` (models.py:95-102) incluem o campo `senha` no dicionário de resposta — o baseline confirma `dados[].senha` em `GET /usuarios` e `dados.senha` em `GET /usuarios/1`.
Impacto: vazamento direto de segredo da aplicação e das senhas de todos os usuários a qualquer cliente anônimo; violação de LGPD.
Recomendação: remover `secret_key`/`debug`/`db_path`/`ambiente` de `/health` (manter `status`, `database`, `counts`, `versao`) e nunca serializar `senha` — serializador de usuário dedicado sem o campo sensível — Playbook T13.
Contrato: exige BC-03 (remove `secret_key`, `debug`, `db_path`, `ambiente` de `/health`) e BC-04 (remove `senha` de `/usuarios` e `/usuarios/<id>`)

### F-04 [CRITICAL] Armazenamento inseguro de senha (AP-04)
Arquivo: models.py:126-129
Ocorrências: models.py:109-111 (login compara senha em texto no SQL), database.py:75-83 (seed grava senhas em texto plano)
Descrição: `criar_usuario` grava a senha recebida em texto plano no INSERT (models.py:126-129). O login compara `senha` por igualdade direta no WHERE (models.py:109-111). O seed insere `admin123`, `123456`, `senha123` em texto (database.py:76-78). Não há hashing.
Impacto: um dump do banco revela todas as senhas imediatamente; reuso de senha compromete outros sistemas dos usuários.
Recomendação: aplicar hash com salt (`werkzeug.security.generate_password_hash` / `check_password_hash`, já disponível via Flask) na criação e no login; semear o admin já com hash — Playbook T05. Login continua aceitando as mesmas credenciais, preservando o contrato.
Contrato: preservado (resposta de login inalterada; `senha` nunca sai na resposta — ver F-03)

### F-05 [CRITICAL] Operação privilegiada sem controle de acesso (AP-05)
Arquivo: app.py:59-78
Ocorrências: app.py:47-57 (`/admin/reset-db` destrói todas as tabelas sem WHERE nem autenticação)
Descrição: `POST /admin/query` executa SQL arbitrário enviado pelo cliente — `cursor.execute(query)` onde `query = dados.get("sql")` (app.py:59-78). `POST /admin/reset-db` apaga `itens_pedido`, `pedidos`, `produtos` e `usuarios` em massa (app.py:47-57). Nenhuma das duas exige autenticação; o sistema não possui mecanismo de token (o `/login` não emite token).
Impacto: qualquer cliente anônimo executa SQL arbitrário e apaga o banco inteiro.
Recomendação: aplicar a T14 por completo, rota a rota pela tabela de situações — ambas se enquadram em "Remover": `/admin/query` executa SQL do cliente e `/admin/reset-db` destrói dados em massa. Apagar rota, método do controller e qualquer código que execute a entrada. Proteger com token **não** corrige o finding — Playbook T14.
Contrato: exige BC-01 (`POST /admin/query` removida → 404) e BC-02 (`POST /admin/reset-db` removida → 404)

### F-06 [CRITICAL] God Module (AP-06)
Arquivo: models.py:1-315
Ocorrências: Nenhuma adicional
Descrição: `models.py` concentra, num único módulo de 314 linhas, o acesso a dados dos três domínios (produtos, usuários, pedidos/itens) **e** regras de negócio: cálculo de desconto escalonado em `relatorio_vendas` (257-262), orquestração de estoque e totais em `criar_pedido` (133-169). Mistura camada de dados com camada de regra, cruzando domínios distintos.
Impacto: impossível testar em isolamento; toda mudança tem raio de impacto global; a regra de negócio fica presa ao acesso a dados.
Recomendação: dividir por domínio em `models/` (produto, usuario, pedido) com acesso a dados puro e mover regras (desconto, montagem de pedido) para `services/` — Playbook T03.
Contrato: preservado

### F-07 [HIGH] Regra de negócio na camada HTTP (AP-07)
Arquivo: controllers.py:208-210
Ocorrências: controllers.py:247-250 (decisão de notificação por status no handler), app.py:49-55 e app.py:66-77 (acesso a dados/SQL direto em handlers de rota)
Descrição: `criar_pedido` dispara integrações (e-mail/SMS/push, simulados por `print`) dentro do handler HTTP (controllers.py:208-210); `atualizar_status_pedido` decide notificações por status no handler (247-250). As rotas admin de `app.py` executam `cursor.execute` diretamente no handler (49-55, 66-77), acoplando HTTP e dados.
Impacto: regra e integrações impossíveis de reutilizar fora do HTTP e de testar sem subir a API; duplicação quando outro fluxo precisar notificar.
Recomendação: mover integrações para um `notificacao_service` e a orquestração para `services/`, deixando o controller fino (extrai entrada, chama serviço, escolhe status) — Playbook T04/T09.
Contrato: preservado

### F-08 [HIGH] Estado global mutável (AP-08)
Arquivo: database.py:4-11
Ocorrências: Nenhuma adicional
Descrição: `db_connection = None` em nível de módulo, reatribuída dentro de `get_db` via `global` (database.py:4,8-9), compartilhada entre threads com `check_same_thread=False` (linha 10). Uma única conexão global serve toda a aplicação.
Impacto: condições de corrida sob concorrência, cursores interferindo entre requisições, bugs que só aparecem com múltiplos workers.
Recomendação: encapsular a criação de conexão numa factory e fornecer conexão por requisição/contexto, montada no composition root e injetada — Playbook T11.
Contrato: preservado

### F-09 [HIGH] Operação multi-passo sem transação (AP-09)
Arquivo: models.py:133-169
Ocorrências: Nenhuma adicional
Descrição: `criar_pedido` insere o pedido (148-151), grava cada item em laço (157-161) e decrementa estoque (163-166), com um único `commit()` no fim (168), mas sem bloco transacional explícito nem `rollback` em exceção. A verificação de estoque (144) é lida antes e o decremento acontece depois, em instruções separadas (leitura-depois-escrita não atômica).
Impacto: falha parcial no meio das escritas deixa pedido sem itens ou estoque divergente; corrida entre checagem e decremento permite estoque negativo.
Recomendação: validar todos os itens antes de escrever e envolver as escritas numa transação única (`with conexao:`) com rollback em exceção — Playbook T07.
Contrato: preservado

### F-10 [HIGH] Configuração de execução insegura (AP-10)
Arquivo: app.py:8,88
Ocorrências: app.py:88 (`host="0.0.0.0"`, `debug=True`, `port=5000` literais no `app.run`)
Descrição: `app.config["DEBUG"] = True` (app.py:8) e `app.run(host="0.0.0.0", port=5000, debug=True)` (app.py:88) fixam modo debug e host/porta no código. Com debug ativo, o debugger do Werkzeug permite execução remota de código.
Impacto: execução remota de código via debugger exposto, vazamento de stack traces, impossibilidade de configurar ambientes sem editar código.
Recomendação: ler `DEBUG`, `HOST` e `PORT` de ambiente numa camada de config, com default seguro (`debug=False`) — Playbook T02.
Contrato: preservado (o campo `debug` sai de `/health` via BC-03)

### F-11 [HIGH] Acoplamento forte sem injeção de dependência (AP-11)
Arquivo: database.py:7-11
Ocorrências: models.py:1 e controllers.py:3 (`from database import get_db` acoplando regra/dados ao SQLite concreto)
Descrição: `get_db` instancia `sqlite3.connect` diretamente (database.py:10) e é importada por `models.py` (linha 1) e `controllers.py` (linha 3). Regra e dados dependem da infraestrutura concreta, sem interface nem injeção.
Impacto: testes exigem SQLite real; trocar o banco significa editar a camada de dados inteira.
Recomendação: criar a conexão no composition root (factory da app) e injetá-la nos repositórios/serviços — Playbook T11.
Contrato: preservado

### F-12 [MEDIUM] Query N+1 (AP-13)
Arquivo: models.py:171-201
Ocorrências: models.py:203-233 (`get_todos_pedidos` com o mesmo padrão), models.py:239-254 (cinco `COUNT(*)` sequenciais em `relatorio_vendas` que caberiam num `GROUP BY`)
Descrição: `get_pedidos_usuario` consulta os pedidos (174) e, para cada pedido, consulta os itens (188) e, para cada item, consulta o nome do produto (192) — N×M consultas. `get_todos_pedidos` repete o padrão (220-224).
Impacto: tempo de resposta cresce com o volume; uma listagem com muitos pedidos dispara milhares de consultas.
Recomendação: resolver com JOIN ou carregar itens e nomes de produto em lote — Playbook T08.
Contrato: preservado

### F-13 [MEDIUM] Validação ausente ou duplicada (AP-14)
Arquivo: controllers.py:28-54
Ocorrências: controllers.py:72-90 (bloco de validação quase idêntico em `atualizar_produto`, sem a checagem de categoria), controllers.py:118-121 (`float(preco_min)` sem tratamento → 500 com entrada não numérica)
Descrição: `criar_produto` e `atualizar_produto` repetem quase o mesmo bloco de validação manual; a lista de categorias válidas existe só em `criar_produto` (52-54), divergindo entre os dois. `buscar_produtos` converte `preco_min`/`preco_max` com `float()` sem try (118-121), gerando 500 em entrada inválida.
Impacto: regras divergentes entre criar e atualizar; erros 500 em entrada malformada.
Recomendação: centralizar validação por entidade em `controllers/validators` ou `services`, reutilizada em criar e atualizar — Playbook T09.
Contrato: preservado

### F-14 [MEDIUM] Tratamento de erro não centralizado (AP-15)
Arquivo: controllers.py:10-12
Ocorrências: todo handler de controllers.py (ex.: 21-22, 95-96, 125-126, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262) e app.py:77-78 repetem `except Exception as e: return jsonify({"erro": str(e)}), 500`
Descrição: cada handler captura `Exception` e devolve `str(e)` com 500, duplicando o padrão ~17 vezes e vazando a mensagem interna. Não há `@app.errorhandler` global.
Impacto: respostas inconsistentes, vazamento de detalhes internos, duplicação massiva.
Recomendação: registrar handlers de erro globais (`@app.errorhandler`) que traduzem exceções de domínio em status adequados, sem vazar `str(e)` — Playbook T10.
Contrato: preservado (status e tipo de corpo dos erros atuais mantidos)

### F-15 [MEDIUM] CORS permissivo (AP-16)
Arquivo: app.py:9
Ocorrências: Nenhuma adicional
Descrição: `CORS(app)` sem `origins`/`resources` (app.py:9) libera requisições cross-origin de qualquer origem. Não há `supports_credentials`, então permanece MEDIUM.
Impacto: qualquer site pode chamar a API a partir do navegador de um usuário.
Recomendação: restringir origens a uma allowlist configurável por ambiente — Playbook T02.
Contrato: preservado (requisições same-origin do smoke test não mudam)

### F-16 [MEDIUM] Listagem sem paginação (AP-17)
Arquivo: models.py:4-22
Ocorrências: models.py:72-87 (`get_todos_usuarios`), models.py:203-233 (`get_todos_pedidos`)
Descrição: `get_todos_produtos`, `get_todos_usuarios` e `get_todos_pedidos` fazem `SELECT *` sem `LIMIT` e devolvem a tabela inteira.
Impacto: memória e tempo de resposta crescem com o volume; a listagem pode derrubar o servidor.
Recomendação: aceitar `limit`/`offset` opcionais mantendo o default atual (sem paginação quando não informado), para não quebrar o contrato — Playbook T17.
Contrato: preservado (paginação aplicada só de forma opcional)

### F-17 [MEDIUM] Integridade referencial não garantida (AP-18)
Arquivo: database.py:14-53
Ocorrências: models.py:65-70 (`deletar_produto` sem checar `itens_pedido`)
Descrição: nenhuma tabela declara `FOREIGN KEY` e não há `PRAGMA foreign_keys = ON` (database.py:14-53, confirmado por busca). `deletar_produto` remove o produto sem tratar itens de pedido que o referenciam (models.py:65-70), deixando órfãos.
Impacto: itens de pedido apontando para produtos inexistentes; relatórios inconsistentes.
Recomendação: declarar FKs no DDL, habilitar `PRAGMA foreign_keys = ON` na conexão e tratar dependentes na remoção — Playbook T15.
Contrato: preservado

### F-18 [LOW] Logging via print (AP-20)
Arquivo: controllers.py:8,208-210
Ocorrências: controllers.py:11,57,61,106,161,179,182,219,248,250; app.py:56,83-86
Descrição: diagnóstico e banners via `print` espalhados por controllers e `app.py` (14 em controllers, 5 em app.py), incluindo simulações de integração ("ENVIANDO EMAIL/SMS/PUSH") em controllers.py:208-210.
Impacto: logs sem níveis, estrutura ou destino controlado.
Recomendação: substituir por `logging` com níveis; as integrações simuladas vão para o `notificacao_service` (F-07) — Playbook T16.
Contrato: preservado

### F-19 [LOW] Magic numbers e literais duplicados (AP-21)
Arquivo: models.py:257-262
Ocorrências: controllers.py:47-50 (tamanhos `2`/`200` de nome), controllers.py:52 e 242 (listas de enum literais: categorias e status)
Descrição: limiares e taxas de desconto (`10000`/`5000`/`1000`, `0.1`/`0.05`/`0.02`) em `relatorio_vendas` (257-262); tamanhos mínimos/máximos de nome (controllers.py:47-50); listas de categorias e de status válidos como literais inline.
Impacto: regra de negócio difícil de encontrar e alterar com consistência.
Recomendação: extrair para constantes nomeadas na camada de serviço/config — Playbook T16.
Contrato: preservado

### F-20 [LOW] Código morto (AP-22)
Arquivo: models.py:2
Ocorrências: database.py:2 (`import os` nunca usado)
Descrição: `import sqlite3` em models.py:2 nunca é referenciado (o acesso vem de `get_db`); `import os` em database.py:2 também não é usado (confirmado por busca).
Impacto: ruído, sugere dependências inexistentes.
Recomendação: remover os imports não usados — Playbook T16.
Contrato: preservado

### F-21 [LOW] Nomenclatura pobre (AP-23)
Arquivo: models.py:187-193
Ocorrências: controllers.py (uso de `id` sombreando o built-in como parâmetro em vários handlers, ex.: 14,64,98,136)
Descrição: cursores numerados `cursor2`/`cursor3` (models.py:187,191,219,223) e parâmetro `id` sombreando o built-in em funções de produto/usuário.
Impacto: legibilidade; `id` como sombra de built-in é armadilha sutil.
Recomendação: renomear identificadores internos (`produto_id`, cursores por intenção). Chaves JSON públicas não são renomeadas — Playbook T16.
Contrato: preservado (só identificadores internos)

### F-22 [LOW] Serialização manual duplicada (AP-24)
Arquivo: models.py:12-21
Ocorrências: models.py:31-40 e models.py:304-313 (dicionário de produto repetido 3×), models.py:79-86 e 95-102 (usuário), models.py:178-199 e 211-231 (pedido)
Descrição: o mesmo dicionário de resposta é montado campo a campo em várias funções: produto (3 vezes), usuário (2) e pedido (2). A duplicação do usuário é a que inclui `senha` (ligada a F-03).
Impacto: divergência de formato entre endpoints e risco de reexpor `senha` ao editar só uma cópia.
Recomendação: um serializador por entidade, reutilizado — Playbook T13.
Contrato: preservado (chaves públicas mantidas, exceto a remoção de `senha` em F-03/BC-04)

## APIs deprecated
Nenhuma API deprecated detectada. Verificação: (1) busca pelos padrões do catálogo (`utcnow`, `before_first_request`, `json_encoder`, `FLASK_ENV`, `url_quote`, `distutils`, `get_or_404`) — nenhuma ocorrência; (2) o projeto não usa SQLAlchemy nem Node; (3) dependências pinadas em versões atuais (Flask 3.1.1, flask-cors 5.0.1). A Parte B reexecuta o boot com `PYTHONWARNINGS=default` para confirmar ausência de `DeprecationWarning`.

## Breaking Changes propostos
| # | Rota | Mudança no contrato | Finding que justifica |
|---|---|---|---|
| BC-01 | POST /admin/query | rota removida da API (T14, "Executa SQL enviado pelo cliente"); passa a responder 404 com ou sem credencial | F-05 — execução de SQL arbitrário por cliente anônimo |
| BC-02 | POST /admin/reset-db | rota removida da API (T14, "Destrói dados em massa"); passa a responder 404 com ou sem credencial | F-05 — destruição em massa do banco sem autenticação |
| BC-03 | GET /health | remove os campos `secret_key`, `debug`, `db_path` e `ambiente`; `status`, `database`, `counts` e `versao` permanecem | F-03/F-02 — segredo e config interna expostos em endpoint público |
| BC-04 | GET /usuarios, GET /usuarios/<id> | remove o campo `senha` da resposta | F-03 — senhas de usuários expostas a qualquer cliente |

## Plano de refatoração
Estrutura-alvo (MVC em camadas):
```
config/        settings (DEBUG, PORT, HOST, SECRET_KEY, CORS, ADMIN) via ambiente — T02
models/        database (factory de conexão, DDL, FKs, PRAGMA — T11/T15), produto, usuario, pedido (SQL parametrizado — T01, serialização — T13)
services/      produto, usuario (hash de senha — T05), pedido (transação — T07, regra de desconto/estoque), notificacao (integrações — T04) — T03/T06/T09
controllers/   produto, usuario, pedido, relatorio, meta (health/index); controllers finos — T04/T09
views/routes   registro de rotas + serializers (T13); rotas /admin removidas — T14
middlewares/   error_handler global (@app.errorhandler) — T10
app.py         composition root: cria config, conexão, serviços, controllers e registra rotas — T11
```
Ordem de execução: config → models → services → controllers → views/routes → middlewares → composition root → limpeza (T16).

================================
Total: 22 findings
================================
