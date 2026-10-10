================================
RELATÓRIO DE AUDITORIA DE ARQUITETURA
================================
Projeto:  code-smells-project
Stack:    Python 3.9.6 + Flask 3.1.1 (flask-cors 5.0.1, sqlite3 stdlib)
Arquivos: 4 analisados | ~780 linhas de código
Data:     2026-10-10

## Resumo
CRITICAL: 6 | HIGH: 5 | MEDIUM: 7 | LOW: 4

| # | Severidade | Anti-pattern | Local principal |
|---|---|---|---|
| F-01 | CRITICAL | SQL Injection por concatenação (AP-01) | models.py:28 |
| F-02 | CRITICAL | Segredos e credenciais hardcoded (AP-02) | app.py:7 |
| F-03 | CRITICAL | Exposição de dados sensíveis (AP-03) | controllers.py:285-289 |
| F-04 | CRITICAL | Armazenamento inseguro de senha (AP-04) | models.py:126-129 |
| F-05 | CRITICAL | Operação privilegiada sem controle de acesso (AP-05) | app.py:59-78 |
| F-06 | CRITICAL | God Module (AP-06) | models.py:1-314 |
| F-07 | HIGH | Regra de negócio na camada HTTP (AP-07) | controllers.py:188-255 |
| F-08 | HIGH | Estado global mutável (AP-08) | database.py:4-10 |
| F-09 | HIGH | Operação multi-passo sem transação (AP-09) | models.py:133-169 |
| F-10 | HIGH | Configuração de execução insegura (AP-10) | app.py:8,88 |
| F-11 | HIGH | Acoplamento forte sem injeção de dependência (AP-11) | database.py:7-10 |
| F-12 | MEDIUM | Query N+1 (AP-13) | models.py:171-233 |
| F-13 | MEDIUM | Validação ausente ou duplicada (AP-14) | controllers.py:30-54 |
| F-14 | MEDIUM | Tratamento de erro não centralizado (AP-15) | controllers.py (todos os handlers) |
| F-15 | MEDIUM | CORS permissivo (AP-16) | app.py:9 |
| F-16 | MEDIUM | Listagem sem paginação (AP-17) | models.py:7,75,206 |
| F-17 | MEDIUM | Integridade referencial não garantida (AP-18) | database.py:14-53 |
| F-18 | MEDIUM | Serialização manual duplicada (AP-24) | models.py:12-21 |
| F-19 | LOW | Logging via `print` (AP-20) | controllers.py (vários) |
| F-20 | LOW | Magic numbers e literais duplicados (AP-21) | models.py:256-262 |
| F-21 | LOW | Código morto (AP-22) | models.py:2 |
| F-22 | LOW | Nomenclatura pobre (`id` sombreia built-in) (AP-23) | controllers.py:14 |

## Findings

### F-01 [CRITICAL] SQL Injection por concatenação (AP-01)
Arquivo: models.py:28
Ocorrências: models.py:48-50, models.py:57-61, models.py:68, models.py:92, models.py:109-111, models.py:126-129, models.py:140, models.py:148-151, models.py:155, models.py:157-166, models.py:174, models.py:188, models.py:192, models.py:220, models.py:224, models.py:279-281, models.py:289-297; app.py:69 (ver também F-05)
Descrição: Todas as funções de acesso a dados montam SQL por concatenação de string com os valores recebidos, sem bind parameters. Exemplos: `get_produto_por_id` faz `"SELECT * FROM produtos WHERE id = " + str(id)` (models.py:28); `login_usuario` faz `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"` (models.py:109-111), explorável com `' OR '1'='1` para bypass de autenticação; `buscar_produtos` concatena `termo`/`categoria` vindos da query string direto no `LIKE`/`WHERE` (models.py:289-297); `criar_produto`/`criar_usuario` interpolam nome, descrição, email no `INSERT` (models.py:48-50, 126-129). Mesmo onde o valor vem de `<int:id>` da rota, a função de dados não pode depender do chamador.
Impacto: leitura, alteração ou destruição arbitrária de dados e bypass do login por injeção em campo de texto não convertido.
Recomendação: substituir toda concatenação por consultas parametrizadas (`cursor.execute(sql, (param, ...))`), construindo a cláusula dinâmica de `buscar_produtos` com placeholders e lista de parâmetros — Playbook T01.
Contrato: preservado

### F-02 [CRITICAL] Segredos e credenciais hardcoded (AP-02)
Arquivo: app.py:7
Ocorrências: database.py:75-79 (usuário admin `admin@loja.com` / senha `admin123` semeado no boot); controllers.py:289 (a mesma `SECRET_KEY` é devolvida na resposta de `/health` — ver F-03)
Descrição: `app.config["SECRET_KEY"] = "minha-chave-****"` está fixa no código versionado (app.py:7). O seed de produção cria um administrador com senha fixa `admin123` e dois usuários com senhas literais (database.py:75-79). O mesmo segredo ainda é ecoado em texto na resposta pública de `/health`.
Impacto: qualquer pessoa com acesso ao repositório obtém o segredo e as credenciais; sessões/tokens assinados com a `SECRET_KEY` podem ser forjados; rotacionar exige novo deploy.
Recomendação: ler `SECRET_KEY` e credenciais de seed de variáveis de ambiente, com o seed de desenvolvimento isolado da configuração de produção — Playbook T02.
Contrato: preservado (a remoção do segredo da resposta de `/health` é tratada em F-03 / BC-01)

### F-03 [CRITICAL] Exposição de dados sensíveis (AP-03)
Arquivo: controllers.py:285-289
Ocorrências: models.py:83 e models.py:99 (campo `senha` serializado e devolvido por `GET /usuarios` e `GET /usuarios/<id>`)
Descrição: `health_check` devolve `secret_key`, `debug`, `db_path` e `ambiente` na resposta pública de `/health` (controllers.py:285-289). As funções `get_todos_usuarios` e `get_usuario_por_id` incluem o campo `senha` no dicionário serializado (models.py:83, 99), exposto sem autenticação por `GET /usuarios` e `GET /usuarios/<id>`.
Impacto: vazamento direto do segredo da aplicação e de detalhes de infraestrutura; exposição de senhas de todos os usuários a qualquer cliente anônimo (violação de LGPD).
Recomendação: remover `secret_key`/`debug`/`db_path`/`ambiente` de `/health` (mantendo `status`, `database`, `counts`, `versao`) e nunca serializar `senha` nas respostas de usuário — Playbook T13.
Contrato: exige BC-01 (remoção de campos de `/health`) e BC-02 (remoção de `senha` de `/usuarios`)

### F-04 [CRITICAL] Armazenamento inseguro de senha (AP-04)
Arquivo: models.py:126-129
Ocorrências: models.py:109-111 (`login_usuario` compara senha em texto plano no SQL); database.py:75-83 (seed grava senhas em texto plano)
Descrição: `criar_usuario` grava a senha recebida diretamente no `INSERT`, em texto plano (models.py:126-129). O login compara a senha por igualdade dentro da query (`... AND senha = '" + senha + "'`, models.py:109-111). O seed insere `admin123`, `123456`, `senha123` em claro (database.py:75-83).
Impacto: um dump do banco revela todas as senhas imediatamente; reuso de senha compromete outros sistemas dos usuários.
Recomendação: aplicar hash com salt (`werkzeug.security.generate_password_hash`/`check_password_hash`) na criação, no login e no seed, preservando as credenciais dos usuários de exemplo para o login continuar funcionando — Playbook T05.
Contrato: preservado (mesmas credenciais, mesmo formato de resposta de `/login`)

### F-05 [CRITICAL] Operação privilegiada sem controle de acesso (AP-05)
Arquivo: app.py:59-78
Ocorrências: app.py:47-57 (`/admin/reset-db` apaga todas as tabelas sem autenticação)
Descrição: `/admin/query` executa SQL arbitrário vindo do corpo da requisição (`cursor.execute(query)`, app.py:69) sem qualquer autenticação. `/admin/reset-db` executa `DELETE FROM` em todas as tabelas sem autenticação (app.py:51-55). Ambas são alcançáveis por qualquer cliente anônimo.
Impacto: qualquer cliente anônimo pode exfiltrar todo o banco, executar comandos destrutivos arbitrários ou apagar todos os dados.
Recomendação: exigir token de administrador (`X-Admin-Token` lido da configuração) nas rotas administrativas, retornando 401 sem token válido; parametrizar/restringir drasticamente o uso de `/admin/query` — Playbook T14.
Contrato: exige BC-03 (rotas `/admin/*` passam a exigir `X-Admin-Token`)

### F-06 [CRITICAL] God Module (AP-06)
Arquivo: models.py:1-314
Ocorrências: Nenhuma adicional
Descrição: `models.py` concentra, para os três domínios (produtos, usuários, pedidos), acesso a dados (SQL de todas as tabelas), regra de negócio (orquestração de pedido com baixa de estoque em `criar_pedido`, models.py:133-169; cálculo de desconto e ticket médio em `relatorio_vendas`, models.py:256-272) e serialização manual das respostas (models.py:12-21, 31-40, 78-86, 177-199). São três responsabilidades de natureza diferente misturadas em um único módulo de 314 linhas que atravessa múltiplos domínios.
Impacto: impossível testar em isolamento; qualquer alteração tem raio de impacto global; a camada de dados não pode ser trocada sem mexer em regra de negócio.
Recomendação: dividir por domínio em repositórios (dados), extrair a regra de negócio para serviços e a montagem de resposta para a camada de views/serializers — Playbook T03.
Contrato: preservado

### F-07 [HIGH] Regra de negócio na camada HTTP (AP-07)
Arquivo: controllers.py:188-255
Ocorrências: controllers.py:208-210 (envio simulado de e-mail/SMS/push em `criar_pedido`); controllers.py:248-250 (notificações de mudança de status); controllers.py:42-54 (regras de preço/estoque/categoria em `criar_produto`); models.py:143,145 (camada de dados retornando `{"erro": ...}` consumido pelo controller para decidir o status, controllers.py:205-206)
Descrição: handlers decidem regras de domínio e disparam integrações em vez de delegar. `criar_pedido` dispara os efeitos de e-mail/SMS/push diretamente no handler (controllers.py:208-210); `atualizar_status_pedido` contém as regras de notificação por status (controllers.py:247-250); `criar_produto` embute regras de preço negativo, tamanho de nome e enum de categoria. No sentido inverso, `models.criar_pedido` devolve `{"erro": ...}` que o controller usa para montar a resposta HTTP.
Impacto: regra impossível de reutilizar (CLI, fila, outro endpoint) e de testar sem subir HTTP; acoplamento entre camada de dados e formato de resposta.
Recomendação: mover regras e integrações para serviços de domínio, deixando os controllers finos (extrair entrada, chamar serviço, escolher status); representar erros de negócio por exceções/retornos neutros, não por dicionários de resposta HTTP — Playbook T04.
Contrato: preservado

### F-08 [HIGH] Estado global mutável (AP-08)
Arquivo: database.py:4-10
Ocorrências: Nenhuma adicional
Descrição: `db_connection = None` é uma variável de módulo reatribuída dentro de `get_db` via `global db_connection` (database.py:4,8-10), e a conexão é criada com `check_same_thread=False` (database.py:10), sendo compartilhada entre as threads do servidor.
Impacto: condições de corrida sob concorrência (cursores da mesma conexão compartilhados), testes que interferem entre si, bugs que só aparecem com múltiplos workers.
Recomendação: encapsular a conexão por requisição/contexto sem estado global mutável, criando-a no composition root e injetando-a nos repositórios — Playbook T11.
Contrato: preservado

### F-09 [HIGH] Operação multi-passo sem transação (AP-09)
Arquivo: models.py:133-169
Ocorrências: Nenhuma adicional
Descrição: `criar_pedido` lê o estoque num primeiro laço (models.py:139-146), insere o pedido (148-151), insere cada item e decrementa o estoque num segundo laço (154-166) e só então faz `commit()` (168), sem transação explícita nem `rollback`. A verificação de estoque e o decréscimo ocorrem em instruções separadas (leitura em 144, update em 163-166), não atômicas.
Impacto: em falha parcial entre as escritas, o pedido pode ficar inconsistente (itens ou baixa de estoque incompletos); sob concorrência, duas vendas podem decrementar o mesmo estoque.
Recomendação: validar todos os itens antes de escrever e envolver inserções e baixa de estoque numa única transação, com rollback em exceção — Playbook T07.
Contrato: preservado

### F-10 [HIGH] Configuração de execução insegura (AP-10)
Arquivo: app.py:8,88
Ocorrências: app.py:82 (`get_db()` disparado no bloco `__main__`)
Descrição: `app.config["DEBUG"] = True` (app.py:8) e `app.run(host="0.0.0.0", port=5000, debug=True)` (app.py:88) fixam modo debug e host/porta literais no código. O debugger do Werkzeug com `host=0.0.0.0` permite execução remota de código.
Impacto: execução remota de código via debugger, vazamento de stack traces, impossibilidade de configurar ambientes diferentes sem editar código.
Recomendação: ler `DEBUG`, `HOST` e `PORT` da configuração/ambiente, com `debug` desligado por padrão — Playbook T02.
Contrato: preservado

### F-11 [HIGH] Acoplamento forte sem injeção de dependência (AP-11)
Arquivo: database.py:7-10
Ocorrências: models.py:1 e controllers.py:3 (`from database import get_db`); models.py:4-5 etc. (cada função chama `get_db()` diretamente)
Descrição: a infraestrutura concreta (`sqlite3.connect`) é instanciada dentro de `get_db` (database.py:10) e importada diretamente por `models.py` e `controllers.py` (`from database import get_db`). Nenhuma dependência é injetada; a regra de negócio conhece o SQLite concreto.
Impacto: testes exigem banco real; trocar SQLite por outro engine significa editar todas as funções de dados; nada é substituível por dublê em teste.
Recomendação: criar a conexão/repositórios no composition root e injetá-los nas camadas de serviço/dados — Playbook T11.
Contrato: preservado

### F-12 [MEDIUM] Query N+1 (AP-13)
Arquivo: models.py:171-201
Ocorrências: models.py:203-233 (`get_todos_pedidos` repete o mesmo padrão)
Descrição: `get_pedidos_usuario` consulta os pedidos e, para cada pedido, consulta os itens (models.py:188) e, para cada item, consulta o nome do produto (models.py:192) — consultas aninhadas dentro de laços sobre resultados do banco. `get_todos_pedidos` faz o mesmo (models.py:220,224).
Impacto: o número de consultas cresce linearmente com pedidos e itens; a listagem de pedidos pode disparar milhares de queries.
Recomendação: substituir por `JOIN` entre `pedidos`, `itens_pedido` e `produtos`, ou carregar itens/produtos em lote — Playbook T08.
Contrato: preservado

### F-13 [MEDIUM] Validação ausente ou duplicada (AP-14)
Arquivo: controllers.py:30-54
Ocorrências: controllers.py:74-90 (bloco de validação de produto quase idêntico em `atualizar_produto`); controllers.py:118-121 (`float(preco_min/preco_max)` sem tratamento → 500 com entrada não numérica); controllers.py:242 e 52-53 (listas de enum `status` e `categoria` repetidas como literais)
Descrição: as validações de `criar_produto` e `atualizar_produto` são blocos quase idênticos duplicados; `buscar_produtos` converte `preco_min`/`preco_max` com `float()` sem try (erro 500 em entrada inválida); os enums de categoria e de status são listas literais repetidas em pontos diferentes.
Impacto: regras divergem com o tempo entre criar/atualizar; entrada inválida gera 500 em vez de 400; enums duplicados saem de sincronia.
Recomendação: centralizar validação por recurso (função/esquema único reutilizado em criar e atualizar) e converter tipos com tratamento de erro — Playbook T09.
Contrato: preservado

### F-14 [MEDIUM] Tratamento de erro não centralizado (AP-15)
Arquivo: controllers.py (todos os handlers)
Ocorrências: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292; app.py:77-78
Descrição: cada handler repete `except Exception as e: return jsonify({"erro": str(e)}), 500`, duplicando o tratamento e vazando a mensagem interna da exceção ao cliente. Não há `@app.errorhandler`/`register_error_handler` global.
Impacto: respostas inconsistentes, vazamento de detalhes internos, duplicação em ~16 pontos.
Recomendação: registrar um handler de erros central (`@app.errorhandler`) que traduz exceções em respostas padronizadas sem vazar `str(e)`, removendo os try/except repetidos dos handlers — Playbook T10.
Contrato: preservado (status e formato `{"erro": ...}` mantidos para os casos já tratados)

### F-15 [MEDIUM] CORS permissivo (AP-16)
Arquivo: app.py:9
Ocorrências: Nenhuma adicional
Descrição: `CORS(app)` é aplicado sem restrição de `origins`/`resources` (app.py:9), liberando requisições cross-origin de qualquer site.
Impacto: qualquer site pode chamar a API a partir do navegador de um usuário.
Recomendação: restringir as origens permitidas por configuração (`origins` explícitas) — Playbook T02.
Contrato: preservado (sem origens de produção definidas, mantém o comportamento para o smoke test local)

### F-16 [MEDIUM] Listagem sem paginação (AP-17)
Arquivo: models.py:7
Ocorrências: models.py:75 (`SELECT * FROM usuarios`), models.py:206 (`SELECT * FROM pedidos`)
Descrição: `get_todos_produtos`, `get_todos_usuarios` e `get_todos_pedidos` executam `SELECT *` sem `LIMIT` e devolvem a tabela inteira (models.py:7,75,206).
Impacto: memória e tempo de resposta crescem com o volume; uma tabela grande pode derrubar o servidor.
Recomendação: oferecer paginação **opcional** (`?limit`/`?offset`) preservando a resposta padrão quando os parâmetros não são enviados — Playbook T17.
Contrato: preservado (paginação opcional, sem parâmetros o formato continua idêntico)

### F-17 [MEDIUM] Integridade referencial não garantida (AP-18)
Arquivo: database.py:14-53
Ocorrências: models.py:65-70 (`deletar_produto` remove o produto sem tratar `itens_pedido` que o referenciam)
Descrição: o DDL não declara `FOREIGN KEY` nas colunas `usuario_id`, `produto_id`, `pedido_id` nem ativa `PRAGMA foreign_keys = ON` (database.py:14-53). `deletar_produto` apaga o produto sem verificar itens de pedido dependentes, gerando itens órfãos.
Impacto: registros órfãos, relatórios com itens de produtos inexistentes, inconsistências difíceis de rastrear.
Recomendação: declarar as foreign keys no schema e ativar `PRAGMA foreign_keys = ON` na conexão; checar dependências antes de remover — Playbook T15.
Contrato: preservado

### F-18 [MEDIUM] Serialização manual duplicada (AP-24)
Arquivo: models.py:12-21
Ocorrências: models.py:31-40 e models.py:304-313 (mesmo dicionário de produto remontado); models.py:78-86 e models.py:95-102 (usuário com `senha`) versus models.py:114-119 (login sem `senha`) — divergência perigosa; models.py:177-199 e models.py:211-231 (pedido)
Descrição: a montagem de resposta é copiada campo a campo em várias funções. O produto é serializado três vezes; o usuário é serializado incluindo `senha` em duas funções (models.py:83,99) mas sem `senha` no login (models.py:114-119) — divergência que mantém o vazamento de F-03 em alguns caminhos.
Impacto: alterações de contrato precisam ser replicadas em vários pontos; a divergência de campos sensíveis (`senha`) já causa o vazamento de F-03.
Recomendação: centralizar a serialização de cada entidade em um único serializer por domínio, sem campos sensíveis — Playbook T13.
Contrato: preservado (após remoção de `senha` já declarada em BC-02)

### F-19 [LOW] Logging via `print` (AP-20)
Arquivo: controllers.py:8
Ocorrências: controllers.py:11,57,61,106,161,179,182,219; app.py:56,83-86 (banner e aviso de reset). Os prints de integração (controllers.py:208-210,248-250) são tratados em F-07.
Descrição: diagnósticos e banners usam `print` sem níveis nem destino configurável.
Impacto: sem controle de nível/destino de log; ruído no stdout de produção.
Recomendação: substituir por `logging` configurado na aplicação — Playbook T16.
Contrato: preservado

### F-20 [LOW] Magic numbers e literais duplicados (AP-21)
Arquivo: models.py:256-262
Ocorrências: controllers.py:47-50 (tamanhos `2`/`200` de nome); controllers.py:52 e 242 (listas de enum); models.py:257-262 (limiares `10000`/`5000`/`1000` e taxas `0.1`/`0.05`/`0.02` de desconto)
Descrição: limiares e taxas de desconto e tamanhos de validação estão espalhados como literais no código de regra.
Impacto: significado de negócio difícil de localizar e alterar com consistência.
Recomendação: extrair para constantes nomeadas na camada de serviço/configuração — Playbook T16.
Contrato: preservado

### F-21 [LOW] Código morto (AP-22)
Arquivo: models.py:2
Ocorrências: database.py:2 (`import os` nunca usado)
Descrição: `import sqlite3` em models.py:2 não é referenciado (o acesso é via `get_db`); `import os` em database.py:2 não é usado.
Impacto: ruído e falsa impressão de dependências.
Recomendação: remover os imports não usados — Playbook T16.
Contrato: preservado

### F-22 [LOW] Nomenclatura pobre (`id` sombreia built-in) (AP-23)
Arquivo: controllers.py:14
Ocorrências: controllers.py:64,98,136; models.py:24,43,54,65,89 (parâmetro `id` sombreando o built-in `id` do Python)
Descrição: diversas funções usam `id` como nome de parâmetro, sombreando o built-in do Python. É um identificador interno (não é chave JSON pública).
Impacto: legibilidade e risco de confusão; sem impacto de contrato.
Recomendação: renomear para `produto_id`/`usuario_id` nos identificadores internos — Playbook T16.
Contrato: preservado (renomeação apenas interna; chaves JSON `id` da resposta não mudam)

## APIs deprecated
Nenhuma API deprecated detectada. Verificação: import da aplicação com `python -W default -c "import app"` não emitiu `DeprecationWarning`/`LegacyAPIWarning`; versões instaladas são atuais (Flask 3.1.1, flask-cors 5.0.1); busca pelos padrões do catálogo (`datetime.utcnow`, `before_first_request`, `Model.query.get`, `url_quote`, etc.) não encontrou ocorrências. O projeto usa `sqlite3` da stdlib, sem ORM.

## Breaking Changes propostos
| # | Rota | Mudança no contrato | Finding que justifica |
|---|---|---|---|
| BC-01 | GET /health | remove os campos `secret_key`, `debug`, `db_path` e `ambiente`; `status`, `database`, `counts` e `versao` permanecem | F-03 — segredo e infraestrutura expostos em endpoint público |
| BC-02 | GET /usuarios e GET /usuarios/<id> | remove o campo `senha` de cada usuário na resposta | F-03/F-04 — senha de usuários exposta sem autenticação |
| BC-03 | POST /admin/reset-db e POST /admin/query | passam a exigir o header `X-Admin-Token` válido; sem ele respondem 401 | F-05 — execução de SQL arbitrário e destruição em massa sem autenticação |

Observação: o smoke test já envia `X-Admin-Token` nas rotas `/admin/*` nas duas execuções (ignorado pelo original, exigido após T14). Na validação (Fase 3) o boot define `ADMIN_TOKEN`, de modo que as rotas administrativas voltam a responder como no baseline.

## Plano de refatoração
Estrutura-alvo (refinada no início da Fase 3 com as guidelines):

```
app.py                      # composition root + entry point (lê config, registra blueprints e error handler)
config.py                   # SECRET_KEY, DEBUG, HOST/PORT, ADMIN_TOKEN, CORS origins — tudo via ambiente (T02)
db/
  connection.py             # criação/ciclo de vida da conexão sqlite, PRAGMA foreign_keys (T11, T15)
  schema.py / seed.py       # DDL e seed isolados, seed com senha via hash (T05, T15)
repositories/               # acesso a dados parametrizado, por domínio (T01, T03)
  produto_repository.py
  usuario_repository.py
  pedido_repository.py
services/                   # regra de negócio e integrações (T04, T06, T07, T09)
  produto_service.py
  usuario_service.py
  pedido_service.py
  relatorio_service.py
  notificacao_service.py    # abstrai e-mail/SMS/push hoje em print (T04)
controllers/                # controllers finos: entrada → serviço → status (T04, T09)
views/ (serializers)        # serialização central por entidade, sem campos sensíveis (T13, T24)
middlewares/
  error_handler.py          # @app.errorhandler central (T10)
```

Ordem de execução por camada: config → repositories (models/dados) → services → controllers → views/rotas → middlewares → composition root → limpeza. Transformações principais: T01 (SQL parametrizado), T02 (config/segredos/CORS/debug), T05 (hash de senha), T14 (auth admin), T03 (quebra do God Module), T04/T07 (regra e transação em serviços), T10 (erro central), T08 (N+1), T09 (validação), T13 (serialização), T15 (integridade), T16/T17 (limpeza e paginação opcional).

================================
Total: 22 findings
================================
