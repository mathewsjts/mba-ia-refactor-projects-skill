================================
RELATÓRIO DE AUDITORIA DE ARQUITETURA
================================
Projeto:  code-smells-project
Stack:    Python 3.9.6 + Flask 3.1.1
Arquivos: 4 analisados | ~780 linhas de código
Data:     2026-11-03

## Resumo
CRITICAL: 6 | HIGH: 6 | MEDIUM: 5 | LOW: 5

| # | Severidade | Anti-pattern | Local principal |
|---|---|---|---|
| F-01 | CRITICAL | SQL Injection por concatenação (AP-01) | models.py:28 |
| F-02 | CRITICAL | Segredos e credenciais hardcoded (AP-02) | app.py:7 |
| F-03 | CRITICAL | Exposição de dados sensíveis (AP-03) | models.py:72-103 |
| F-04 | CRITICAL | Armazenamento inseguro de senha (AP-04) | models.py:105-131 |
| F-05 | CRITICAL | Operação privilegiada sem controle de acesso (AP-05) | app.py:47-78 |
| F-06 | CRITICAL | God Module (AP-06) | models.py:1-314 |
| F-07 | HIGH | Regra de negócio na camada HTTP (AP-07) | controllers.py:188-220 |
| F-08 | HIGH | Estado global mutável (AP-08) | database.py:4-10 |
| F-09 | HIGH | Operação multi-passo sem transação (AP-09) | models.py:133-169 |
| F-10 | HIGH | Configuração de execução insegura (AP-10) | app.py:8 |
| F-11 | HIGH | Acoplamento forte sem injeção de dependência (AP-11) | app.py:3-4 |
| F-12 | HIGH | Validação ausente ou duplicada (AP-14) | controllers.py:24-96 |
| F-13 | MEDIUM | Query N+1 (AP-13) | models.py:171-201 |
| F-14 | MEDIUM | Tratamento de erro não centralizado (AP-15) | controllers.py:10-12 |
| F-15 | MEDIUM | CORS permissivo (AP-16) | app.py:9 |
| F-16 | MEDIUM | Listagem sem paginação (AP-17) | models.py:7 |
| F-17 | MEDIUM | Integridade referencial não garantida (AP-18) | database.py:36-53 |
| F-18 | LOW | Logging via print (AP-20) | app.py:56 |
| F-19 | LOW | Magic numbers e literais duplicados (AP-21) | controllers.py:47-54 |
| F-20 | LOW | Código morto (AP-22) | database.py:2 |
| F-21 | LOW | Nomenclatura pobre e código verboso (AP-23) | controllers.py:14 |
| F-22 | LOW | Serialização manual duplicada (AP-24) | models.py:12-21 |

## Findings

### F-01 [CRITICAL] SQL Injection por concatenação (AP-01)
Arquivo: models.py:28
Ocorrências: models.py:47-50, models.py:57-61, models.py:68, models.py:92, models.py:109-111, models.py:126-129, models.py:140, models.py:148-151, models.py:155, models.py:157-161, models.py:163-166, models.py:174, models.py:188, models.py:192, models.py:220, models.py:224, models.py:279-281, models.py:289-299
Descrição: todas as funções de `models.py` montam SQL por concatenação de strings. Os casos com texto livre do cliente são diretamente exploráveis: `login_usuario` (`"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`, linha 110) aceita `' OR '1'='1` e autentica sem senha; `criar_produto`/`atualizar_produto` (linhas 48-49, 58-60) e `criar_usuario` (linha 128) concatenam `nome`, `descricao`, `categoria`, `email`, `senha`; `buscar_produtos` acrescenta `termo` e `categoria` da query string ao `WHERE` (linhas 291, 293); `atualizar_status_pedido` concatena `novo_status` (linha 280). Os demais concatenam ids — protegidos hoje só pelo conversor `<int:>` da rota ou por `str()` de valores do corpo JSON (`item["produto_id"]`, `item["quantidade"]`, `usuario_id`, que podem ser strings arbitrárias em `criar_pedido`, linhas 140, 150, 159-165).
Impacto: bypass de autenticação, leitura de toda a base (incluindo senhas), alteração e destruição de dados por qualquer cliente anônimo.
Recomendação: usar placeholders `?` com parâmetros vinculados em todas as consultas; montar o `WHERE` dinâmico da busca com lista de cláusulas fixas e lista de parâmetros — Playbook T01.
Contrato: preservado

### F-02 [CRITICAL] Segredos e credenciais hardcoded (AP-02)
Arquivo: app.py:7
Ocorrências: controllers.py:289, database.py:75-83
Descrição: `app.config["SECRET_KEY"] = "minha-chave-****"` literal no código versionado; o mesmo segredo é devolvido em texto puro por `GET /health` (`"secret_key": "minha-chave-****"`, controllers.py:289). O seed executado automaticamente no boot de produção (`get_db`, database.py:75-83) cria o usuário `admin@loja.com` com senha fixa `admi****` e tipo `admin`, além de dois clientes com senhas fixas.
Impacto: qualquer pessoa com acesso ao repositório — ou a `GET /health`, sem autenticação — obtém a chave usada para assinar sessões/tokens; toda instalação nova nasce com um administrador de senha conhecida.
Recomendação: mover `SECRET_KEY` para a configuração lida do ambiente (obrigatória em produção, aleatória por processo só em desenvolvimento); remover o segredo da resposta de `/health`; restringir o seed com credenciais de exemplo a ambientes fora de produção — Playbook T02.
Contrato: exige BC-01

### F-03 [CRITICAL] Exposição de dados sensíveis (AP-03)
Arquivo: models.py:72-103
Ocorrências: controllers.py:128-144, controllers.py:284-289
Descrição: `get_todos_usuarios` e `get_usuario_por_id` fazem `SELECT * FROM usuarios` e copiam `"senha": row["senha"]` para o dicionário de resposta (models.py:83, 99), devolvido sem filtro por `GET /usuarios` e `GET /usuarios/<id>` (controllers.py:132, 140) — o baseline confirma `dados[].senha`. As cópias divergem: `login_usuario` (models.py:114-119) omite a senha. `GET /health` expõe ainda `db_path`, `debug` e `ambiente` (controllers.py:286-288) a qualquer cliente.
Impacto: vazamento direto das senhas (hoje em texto plano, ver F-04) de todos os usuários e de detalhes de infraestrutura para clientes anônimos.
Recomendação: serializer de usuário com campos explícitos, sem `senha`, usado por todas as rotas; `/health` responde só status, banco e contagens — Playbook T13.
Contrato: exige BC-01, BC-03, BC-04

### F-04 [CRITICAL] Armazenamento inseguro de senha (AP-04)
Arquivo: models.py:105-131
Ocorrências: database.py:75-83
Descrição: `criar_usuario` grava a senha recebida sem hash (`INSERT ... '" + senha + "'`, models.py:126-129); `login_usuario` compara a senha dentro do SQL (`AND senha = '" + senha + "'`, models.py:110); o seed grava `admi****`, `1234**`, `senh****` em texto plano (database.py:76-78).
Impacto: com um dump do banco (ou via F-03/F-05, por HTTP), todas as senhas ficam legíveis; reuso de senha compromete outras contas dos usuários.
Recomendação: hash com KDF e salt (`werkzeug.security.generate_password_hash`/`check_password_hash`, já instalado com o Flask); login busca por e-mail e verifica o hash em Python; senhas legadas em texto plano são migradas para hash no primeiro login bem-sucedido — Playbook T05.
Contrato: preservado

### F-05 [CRITICAL] Operação privilegiada sem controle de acesso (AP-05)
Arquivo: app.py:47-78
Ocorrências: app.py:11-30, controllers.py:167-186
Descrição: `POST /admin/query` (app.py:59-78) executa `cursor.execute(query)` com o SQL enviado pelo cliente em `dados["sql"]` e faz `commit()` para comandos que não são `SELECT`; `POST /admin/reset-db` (app.py:47-57) executa `DELETE FROM` sem `WHERE` nas quatro tabelas. Nenhuma das duas exige qualquer credencial. O projeto tem login (`POST /login`, controllers.py:167-186), mas ele não emite token nem existe verificação de identidade em rota alguma: qualquer cliente anônimo apaga e altera produtos, lista todos os usuários, lê todos os pedidos e o relatório financeiro, muda o status de qualquer pedido e cria pedidos em nome de qualquer `usuario_id` (app.py:11-28).
Impacto: exfiltração e destruição do banco inteiro por requisição anônima; fraude de pedidos e de preços; leitura de dados pessoais e financeiros.
Recomendação, rota a rota (tabela de situações da T14):
- `POST /admin/query` — "Executa SQL enviado pelo cliente" → **Remover** (rota, handler e o código que executa o SQL recebido).
- `POST /admin/reset-db` — "Destruição em massa" → **Remover** da API; oferecer como comando local `flask --app app reset-db`.
- Demais rotas — "Token de autenticação falso/inexistente (o projeto tem login)" → (a) `POST /login` passa a emitir token assinado (`itsdangerous.URLSafeTimedSerializer`, já instalado com o Flask, com `max_age`) em `dados.token`; (b) exigir `Authorization: Bearer <token>`:
  - perfil `admin`: `POST /produtos`, `PUT /produtos/<id>`, `DELETE /produtos/<id>`, `GET /usuarios`, `GET /pedidos`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas`;
  - o próprio usuário ou `admin`: `GET /usuarios/<id>`, `GET /pedidos/usuario/<usuario_id>`, `POST /pedidos` (o `usuario_id` do corpo precisa ser o do token, salvo admin).
  - permanecem públicas: `GET /`, `GET /health`, `GET /produtos`, `GET /produtos/<id>`, `GET /produtos/busca`, `POST /usuarios` (cadastro, sempre como `cliente`) e `POST /login`.
Sem token válido a resposta é 401; com token de perfil insuficiente, 403 — Playbook T14.
Contrato: exige BC-02 a BC-14

### F-06 [CRITICAL] God Module (AP-06)
Arquivo: models.py:1-314
Ocorrências: controllers.py:1-292, app.py:1-88
Descrição: `models.py` concentra acesso a dados dos quatro domínios (produtos, usuários, pedidos, relatórios), regras de negócio (checagem de estoque e cálculo do total em `criar_pedido`, linhas 139-146; faixas de desconto em `relatorio_vendas`, linhas 256-262), mensagens de erro de negócio (linhas 143, 145) e serialização manual. `controllers.py` mistura HTTP, validação, SQL direto (`health_check`, linhas 266-274) e "integrações" de notificação (linhas 208-210, 247-250) de todos os domínios. `app.py` junta configuração, roteamento e SQL administrativo (linhas 47-78).
Impacto: nenhuma regra é testável em isolamento; qualquer mudança em um domínio toca os mesmos arquivos de todos os outros.
Recomendação: separar em models por domínio com conexão injetada, services com as regras, controllers finos, rotas e serializers — Playbook T03 (com T04, T11, T13).
Contrato: preservado

### F-07 [HIGH] Regra de negócio na camada HTTP (AP-07)
Arquivo: controllers.py:188-220
Ocorrências: controllers.py:237-255, controllers.py:264-292, app.py:47-78, models.py:143-145
Descrição: `criar_pedido` dispara as "notificações" de e-mail, SMS e push no handler (linhas 208-210) e `atualizar_status_pedido` decide notificações por status (linhas 247-250); `health_check` executa SQL direto (linhas 266-274); os handlers de `/admin/*` executam SQL em `app.py`. No sentido inverso, a camada de dados devolve estrutura de resposta (`return {"erro": ...}`, models.py:143, 145) que o controller usa para decidir o status 400 (controllers.py:205-206).
Impacto: regra de pedido e notificação inacessível fora do HTTP; acoplamento entre formato de resposta e camada de dados.
Recomendação: `PedidoService` com a regra do pedido e um `NotificacaoService` injetado; erros de negócio como exceções de domínio traduzidas no controller/middleware; `health` via model — Playbook T04.
Contrato: preservado

### F-08 [HIGH] Estado global mutável (AP-08)
Arquivo: database.py:4-10
Ocorrências: Nenhuma adicional
Descrição: `db_connection = None` em nível de módulo, reatribuída com `global db_connection` em `get_db()` e aberta com `sqlite3.connect(db_path, check_same_thread=False)`: uma única conexão (e uma única transação implícita) compartilhada por todas as threads do servidor.
Impacto: requisições concorrentes compartilham cursor e transação — escritas não confirmadas de uma requisição que falhou são confirmadas pelo `commit()` de outra; testes não isolam estado.
Recomendação: objeto `Database` criado no composition root, com conexão por requisição (`flask.g`) fechada no `teardown_appcontext` — Playbook T11.
Contrato: preservado

### F-09 [HIGH] Operação multi-passo sem transação (AP-09)
Arquivo: models.py:133-169
Ocorrências: Nenhuma adicional
Descrição: `criar_pedido` lê o estoque (linhas 140-145), e só depois insere o pedido (148-152), insere cada item (157-161) e decrementa o estoque com `UPDATE produtos SET estoque = estoque - <qtd> WHERE id = <id>` (163-166), sem condição no `WHERE` nem checagem de linhas afetadas, e com um único `commit()` sem `rollback` em caso de exceção (168). Uma exceção no meio deixa escritas pendentes na conexão compartilhada (F-08), confirmadas depois pelo `commit` de outra requisição.
Impacto: pedido sem itens ou estoque decrementado para pedido incompleto em falha parcial; duas requisições simultâneas passam pela mesma checagem e deixam o estoque negativo.
Recomendação: validar todos os itens antes de escrever, executar as escritas numa transação única com rollback, e decrementar com escrita condicional `... SET estoque = estoque - ? WHERE id = ? AND estoque >= ?` checando `rowcount` (erro de negócio "Estoque insuficiente" se 0) — Playbook T07 (passos 1, 2 e 3).
Contrato: preservado

### F-10 [HIGH] Configuração de execução insegura (AP-10)
Arquivo: app.py:8
Ocorrências: app.py:85-88, controllers.py:286-288
Descrição: `app.config["DEBUG"] = True` literal e `app.run(host="0.0.0.0", port=5000, debug=True)` (app.py:88): o debugger interativo do Werkzeug fica exposto em todas as interfaces de rede. Porta e host são literais; `/health` declara `"ambiente": "producao"` e `"debug": True` fixos.
Impacto: execução remota de código pelo console do debugger; impossível configurar ambientes sem editar código.
Recomendação: `DEBUG`, `HOST` e `PORT` lidos do ambiente com defaults seguros (`debug` desligado, host `127.0.0.1`, porta 5000) — Playbook T02.
Contrato: exige BC-15

### F-11 [HIGH] Acoplamento forte sem injeção de dependência (AP-11)
Arquivo: app.py:3-4
Ocorrências: controllers.py:2-3, models.py:1
Descrição: `app.py`, `controllers.py` e `models.py` importam o mesmo módulo concreto (`from database import get_db`) e chamam a função global em cada operação; `app.py` importa `controllers` como módulo e registra funções soltas; não existe ponto de montagem das dependências.
Impacto: impossível trocar o banco ou isolar uma camada em teste sem monkeypatch de módulo.
Recomendação: `create_app()` como composition root que cria `Database`, models, services e controllers e os injeta por construtor — Playbook T11.
Contrato: preservado

### F-12 [HIGH] Validação ausente ou duplicada (AP-14)
Arquivo: controllers.py:24-96
Ocorrências: controllers.py:111-126, controllers.py:167-175, controllers.py:188-201, controllers.py:237-243, models.py:139-146
Descrição: `criar_produto` e `atualizar_produto` repetem o mesmo bloco de validação (linhas 28-50 e 72-90), mas a atualização não valida tamanho do nome nem categoria. Tipos não são checados: `preco < 0` com `"preco": "10"` lança `TypeError` → 500; `float(preco_min)` na busca (linhas 118-121) → 500 com texto; `login` com corpo vazio chama `.get` em `None` → 500. `criar_pedido` não valida os itens: `quantidade` negativa passa na checagem de estoque (models.py:144) e o `UPDATE ... estoque - -5` **aumenta** o estoque e gera total negativo; item sem `produto_id` → `KeyError` → 500. Escalado de MEDIUM para HIGH pela regra 2 (validação ausente grava dados corrompidos).
Impacto: dados corrompidos (estoque inflado, pedidos de valor negativo, categorias inválidas) e erros 500 com entrada simples.
Recomendação: validadores reutilizáveis por recurso (produto, usuário, pedido, status, filtros de busca) que levantam erro de validação com a mesma mensagem e status atuais — Playbook T09.
Contrato: preservado

### F-13 [MEDIUM] Query N+1 (AP-13)
Arquivo: models.py:171-201
Ocorrências: models.py:203-233, models.py:154-156, models.py:239-254
Descrição: `get_pedidos_usuario` e `get_todos_pedidos` fazem uma consulta por pedido em `itens_pedido` (`cursor2`, linhas 188, 220) e mais uma por item em `produtos` (`cursor3`, linhas 192, 224). `criar_pedido` relê o preço de cada produto já lido (linha 155). `relatorio_vendas` faz cinco consultas separadas que cabem em uma agregação (linhas 239-254).
Impacto: listagem de pedidos cresce para 1 + P + I consultas.
Recomendação: um `JOIN` de pedidos, itens e produtos agrupado em memória; agregação única com `SUM(CASE ...)` no relatório — Playbook T08.
Contrato: preservado

### F-14 [MEDIUM] Tratamento de erro não centralizado (AP-15)
Arquivo: controllers.py:10-12
Ocorrências: app.py:77-78, controllers.py:21-22, controllers.py:60-62, controllers.py:95-96, controllers.py:108-109, controllers.py:125-126, controllers.py:133-134, controllers.py:143-144, controllers.py:164-165, controllers.py:185-186, controllers.py:218-220, controllers.py:226-227, controllers.py:234-235, controllers.py:254-255, controllers.py:261-262, controllers.py:291-292
Descrição: 17 blocos `except Exception as e: return jsonify({"erro": str(e)}), 500` repetidos; nenhum `@app.errorhandler`. A mensagem interna da exceção vai para o cliente; `health_check` usa outro formato (`{"status": "erro", "detalhes": ...}`).
Impacto: vazamento de detalhes internos (texto de exceções do SQLite), formatos inconsistentes, duplicação.
Recomendação: exceções de domínio + error handler central registrado na factory, que preserva os status e chaves atuais (`erro`, `sucesso` onde já existe) e responde 500 genérico sem `str(e)` — Playbook T10.
Contrato: preservado

### F-15 [MEDIUM] CORS permissivo (AP-16)
Arquivo: app.py:9
Ocorrências: Nenhuma adicional
Descrição: `CORS(app)` sem `origins`: qualquer origem pode chamar a API pelo navegador.
Impacto: qualquer site pode consumir a API a partir do navegador de um usuário.
Recomendação: origens lidas de `CORS_ORIGINS`; `*` apenas fora de produção, lista vazia em produção se não configurada — Playbook T02.
Contrato: preservado (em desenvolvimento o comportamento é o mesmo; em produção as origens passam a ser explícitas)

### F-16 [MEDIUM] Listagem sem paginação (AP-17)
Arquivo: models.py:7
Ocorrências: models.py:75, models.py:206
Descrição: `GET /produtos`, `GET /usuarios` e `GET /pedidos` devolvem `SELECT *` da tabela inteira.
Impacto: memória e tempo de resposta crescem com o volume.
Recomendação: paginação **opcional** por `limit`/`offset` na query string; sem os parâmetros a resposta é idêntica à atual — Playbook T17.
Contrato: preservado

### F-17 [MEDIUM] Integridade referencial não garantida (AP-18)
Arquivo: database.py:36-53
Ocorrências: models.py:65-70, models.py:196, models.py:228
Descrição: `pedidos.usuario_id`, `itens_pedido.pedido_id` e `itens_pedido.produto_id` não têm `FOREIGN KEY` e não há `PRAGMA foreign_keys = ON`. `deletar_produto` (models.py:65-70) apaga o produto sem tratar os `itens_pedido` que o referenciam; as listagens de pedidos já reconhecem o órfão (`"Desconhecido"`, linhas 196, 228). `criar_pedido` aceita `usuario_id` inexistente.
Impacto: itens de pedido órfãos e pedidos de usuários inexistentes.
Recomendação: remoção explícita e transacional, sem apagar histórico de pedidos: produto referenciado por itens é desativado (`ativo = 0`) em vez de apagado; produto sem itens é removido; `usuario_id` inexistente no pedido é rejeitado com 400 — Playbook T15.
Contrato: preservado (mesmo status e corpo em `DELETE /produtos/<id>`)

### F-18 [LOW] Logging via print (AP-20)
Arquivo: app.py:56
Ocorrências: app.py:83-86, controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:208-210, controllers.py:219, controllers.py:248, controllers.py:250
Descrição: 19 `print` como log, incluindo e-mails de usuários em claro (linhas 161, 179, 182) e notificações simuladas.
Impacto: sem níveis nem destino configurável; dados pessoais em stdout.
Recomendação: `logging` com logger por módulo; e-mail fora das mensagens de log — Playbook T16.
Contrato: preservado

### F-19 [LOW] Magic numbers e literais duplicados (AP-21)
Arquivo: controllers.py:47-54
Ocorrências: controllers.py:242, models.py:256-262, app.py:36, controllers.py:285
Descrição: limites de nome `2`/`200` e lista de categorias literais no controller; lista de status literal (linha 242); faixas de desconto `10000/0.1`, `5000/0.05`, `1000/0.02` no relatório; versão `"1.0.0"` repetida em `/` e `/health`.
Impacto: regra espalhada e difícil de alterar com segurança.
Recomendação: constantes nomeadas no domínio (`CATEGORIAS_VALIDAS`, `STATUS_VALIDOS`, `FAIXAS_DESCONTO`, `VERSAO_API`) — Playbook T16.
Contrato: preservado

### F-20 [LOW] Código morto (AP-22)
Arquivo: database.py:2
Ocorrências: models.py:2
Descrição: `import os` (database.py:2) e `import sqlite3` (models.py:2) nunca usados.
Impacto: ruído e falsa impressão de dependência.
Recomendação: remover imports e arquivos sem uso — Playbook T16.
Contrato: preservado

### F-21 [LOW] Nomenclatura pobre e código verboso (AP-23)
Arquivo: controllers.py:14
Ocorrências: controllers.py:56, controllers.py:64, controllers.py:98, controllers.py:136, controllers.py:160, models.py:24, models.py:43, models.py:54, models.py:65, models.py:89, models.py:187-193, models.py:219-225
Descrição: parâmetro e variável `id` sombreando o built-in em handlers e models; `cursor2`, `cursor3`, `prod`; `return True` sem significado em `atualizar_produto`/`deletar_produto`/`atualizar_status_pedido`.
Impacto: legibilidade.
Recomendação: renomear identificadores internos (`produto_id`, `usuario_id`); chaves JSON públicas não mudam — Playbook T16.
Contrato: preservado

### F-22 [LOW] Serialização manual duplicada (AP-24)
Arquivo: models.py:12-21
Ocorrências: models.py:31-40, models.py:304-313, models.py:79-86, models.py:95-102, models.py:114-119, models.py:178-199, models.py:211-231
Descrição: o dicionário de produto é montado campo a campo três vezes, o de usuário três vezes (com e sem `senha` — a divergência perigosa está tratada em F-03) e o de pedido com itens duas vezes.
Impacto: campos divergem entre endpoints a cada mudança.
Recomendação: serializers com campos explícitos em `views/serializers.py` — Playbook T13.
Contrato: preservado

## APIs deprecated
Nenhuma API deprecated detectada no código. Verificação: (1) import da aplicação com `python -W default -c "import app"` — nenhum `DeprecationWarning`; (2) boot e replay do baseline — `boot-antes.log` sem avisos; (3) `pip check` sem conflitos (`install.log`); (4) busca pelos padrões do catálogo (`utcnow`, `before_first_request`, `FLASK_ENV`, `json_encoder`, `attachment_filename`, `werkzeug.urls`, `pkg_resources`, `distutils`, `typing.List/Dict/Optional`) — nenhuma ocorrência.

| API ou dependência | Local | Substituto | Evidência |
|---|---|---|---|
| Runtime Python 3.9.6 (observação de ambiente, não é código do projeto) | `.venv/bin/python` | Python ≥ 3.10 (recriar o `.venv`) | Python 3.9 chegou ao fim de suporte em 2025-10 (PEP 596); o projeto não fixa versão de runtime. Não entra na contagem de findings: a correção é de ambiente, fora do código. |

## Breaking Changes propostos
| # | Rota | Mudança no contrato | Finding que justifica |
|---|---|---|---|
| BC-01 | GET /health | remove `secret_key`, `debug` e `db_path` da resposta; `status`, `database`, `counts`, `versao` e `ambiente` (agora lido da configuração) permanecem | F-02, F-03 — segredo e configuração interna expostos em rota pública |
| BC-02 | POST /login | resposta de sucesso ganha `dados.token` (token assinado com `SECRET_KEY`, validade limitada) | F-05 — login sem credencial verificável |
| BC-03 | GET /usuarios | exige `Authorization: Bearer` de usuário `admin` (401 sem token válido, 403 sem perfil); remove `dados[].senha` | F-05, F-03 — dados pessoais e senhas de todos os usuários para anônimos |
| BC-04 | GET /usuarios/<id> | exige token do próprio usuário ou de `admin` (401/403); remove `dados.senha` | F-05, F-03 |
| BC-05 | POST /produtos | exige token `admin` (401/403) | F-05 — gestão do catálogo anônima |
| BC-06 | PUT /produtos/<id> | exige token `admin` (401/403) | F-05 — alteração de preço/estoque anônima |
| BC-07 | DELETE /produtos/<id> | exige token `admin` (401/403) | F-05 — rota destrutiva anônima |
| BC-08 | POST /pedidos | exige token; `usuario_id` do corpo precisa ser o do token, salvo `admin` (401/403) | F-05 — pedidos em nome de terceiros |
| BC-09 | GET /pedidos | exige token `admin` (401/403) | F-05 — pedidos de todos os clientes para anônimos |
| BC-10 | GET /pedidos/usuario/<usuario_id> | exige token do próprio usuário ou de `admin` (401/403) | F-05 |
| BC-11 | PUT /pedidos/<id>/status | exige token `admin` (401/403) | F-05 — aprovação/cancelamento anônimos |
| BC-12 | GET /relatorios/vendas | exige token `admin` (401/403) | F-05 — dados financeiros para anônimos |
| BC-13 | POST /admin/query | rota removida da API (T14, "Executa SQL enviado pelo cliente"); passa a responder 404 com ou sem credencial | F-05 — execução de SQL arbitrário |
| BC-14 | POST /admin/reset-db | rota removida da API (T14, "Destruição em massa"); responde 404; o reset passa a ser o comando local `flask --app app reset-db` | F-05 — destruição do banco por requisição anônima |
| BC-15 | (execução) `python app.py` | debug desligado por padrão (`DEBUG=1` liga) e host padrão `127.0.0.1` (`HOST=0.0.0.0` para expor); porta continua 5000, configurável por `PORT` | F-10 — debugger do Werkzeug exposto na rede |

## Plano de refatoração
```
app.py                         # entry point: create_app() + app.run com HOST/PORT/DEBUG da config
src/
  app.py                       # composition root: create_app(), injeção, CLI reset-db
  errors.py                    # exceções de domínio (validação, não encontrado, negócio, auth)
  config/settings.py           # Settings lidas do ambiente (SECRET_KEY, DEBUG, HOST, PORT, CORS, DB_PATH)
  models/
    database.py                # Database: conexão por requisição, schema, seed, transação
    passwords.py               # hash/verificação de senha (KDF)
    produto_model.py | usuario_model.py | pedido_model.py | admin_model.py
  services/
    produto_service.py | usuario_service.py | auth_service.py
    pedido_service.py | relatorio_service.py | notificacao_service.py
  controllers/
    validators.py | produto_controller.py | usuario_controller.py
    pedido_controller.py | relatorio_controller.py | meta_controller.py
  views/
    routes.py | serializers.py
  middlewares/
    error_handler.py | auth.py
```
Ordem: config (T02) → models (T01, T03, T05, T07, T08, T15) → services (T04, T06 N/A) → controllers (T04, T09) → views/routes (T13, T14, T17) → middlewares (T10, auth da T14) → composition root (T11) → limpeza (T16).

================================
Total: 22 findings
================================
