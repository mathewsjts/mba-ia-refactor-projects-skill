# Catálogo de Anti-patterns

Referência da **Fase 2**. São 24 anti-patterns, cada um com sinais de detecção acionáveis, falsos positivos conhecidos, severidade e a transformação do playbook que o corrige.

## Escala de severidade

| Nível | Definição |
|---|---|
| **CRITICAL** | Falha grave de arquitetura ou segurança que impede o funcionamento correto, expõe dados sensíveis (credenciais hardcoded, SQL Injection) ou viola completamente a separação de responsabilidades (God Class com banco, regras e roteamento no mesmo lugar). |
| **HIGH** | Violação forte de MVC ou SOLID que dificulta muito manutenção e testes: regra de negócio pesada em controllers, acoplamento forte sem injeção de dependência, estado global mutável. |
| **MEDIUM** | Problemas de padronização, duplicação ou performance moderada: queries N+1, middlewares mal usados, validação ausente nas rotas. |
| **LOW** | Legibilidade, nomenclatura, magic numbers. |

## Como aplicar

Para cada anti-pattern, em ordem:

1. **Buscar** — rode os sinais de detecção (regex/grep) sobre os arquivos-fonte do inventário.
2. **Confirmar** — leia o trecho ao redor de cada ocorrência. Descarte os falsos positivos listados.
3. **Localizar** — registre `arquivo:linha` ou `arquivo:inicio-fim` exatos, conferidos no arquivo.
4. **Classificar** — use a severidade padrão e aplique as [regras de escalonamento](#regras-de-escalonamento).
5. **Consolidar** — ocorrências com a mesma causa raiz formam um único finding.

Os regex são ponto de partida para encontrar candidatos, nunca prova. Nenhum finding entra no relatório sem leitura do código.

## Índice

| ID | Anti-pattern | Severidade padrão | Transformação |
|---|---|---|---|
| AP-01 | SQL Injection por concatenação | CRITICAL | T01 |
| AP-02 | Segredos e credenciais hardcoded | CRITICAL | T02 |
| AP-03 | Exposição de dados sensíveis | CRITICAL | T13 |
| AP-04 | Armazenamento inseguro de senha | CRITICAL | T05 |
| AP-05 | Operação privilegiada sem controle de acesso | CRITICAL | T14 |
| AP-06 | God Class / God Module | CRITICAL | T03 |
| AP-07 | Regra de negócio na camada HTTP | HIGH | T04 |
| AP-08 | Estado global mutável | HIGH | T11 |
| AP-09 | Operação multi-passo sem transação | HIGH | T07 |
| AP-10 | Configuração de execução insegura | HIGH | T02 |
| AP-11 | Acoplamento forte sem injeção de dependência | HIGH | T11 |
| AP-12 | Aninhamento profundo / callback hell | HIGH | T06 |
| AP-13 | Query N+1 | MEDIUM | T08 |
| AP-14 | Validação ausente ou duplicada | MEDIUM | T09 |
| AP-15 | Tratamento de erro não centralizado | MEDIUM | T10 |
| AP-16 | CORS permissivo | MEDIUM | T02 |
| AP-17 | Listagem sem paginação | MEDIUM | T17 |
| AP-18 | Integridade referencial não garantida | MEDIUM | T15 |
| AP-19 | API deprecated ou dependência sem suporte | MEDIUM | T12 |
| AP-20 | Logging via `print` / `console.log` | LOW | T16 |
| AP-21 | Magic numbers e literais duplicados | LOW | T16 |
| AP-22 | Código morto | LOW | T16 |
| AP-23 | Nomenclatura pobre e código verboso | LOW | T16 |
| AP-24 | Serialização manual duplicada | LOW | T13 |

---

## CRITICAL

### AP-01 · SQL Injection por concatenação

**O que é:** valores externos inseridos na string SQL por concatenação, interpolação ou formatação, em vez de parâmetros vinculados (bind parameters).

**Sinais de detecção**
- Python: `execute(` cuja string usa `+`, `%` como operador, `.format(` ou f-string com variáveis; construção incremental como `query += " AND campo = '" + valor + "'"`.
- Node: template literal com `${` ou `+` dentro de `db.run|get|all|exec|query(`.
- Busca: `grep -rnE "(execute|query|run|get|all|exec)\(\s*(f[\"']|[\"'][^\"']*[\"']\s*\+|\`[^\`]*\\$\{)"`, seguida de leitura das linhas seguintes — a concatenação costuma quebrar em várias linhas.

**Falsos positivos**
- Placeholders com valores passados à parte: `?`, `%s` como segundo argumento, `$1`, `:nome`.
- Métodos de ORM que parametrizam internamente: SQLAlchemy `Model.col.like(f"%{q}%")`, `filter_by(...)`, `where` do Sequelize. A f-string ali monta o **valor**, que vira bind parameter.
- Concatenação apenas de fragmentos SQL literais e constantes, sem entrada externa.

Um valor numérico garantido pelo conversor da rota (`<int:id>`) reduz a explorabilidade daquela ocorrência, mas não elimina o finding: a função de acesso a dados não pode depender de quem a chama.

**Impacto:** leitura, alteração ou destruição arbitrária de dados; bypass de autenticação (`' OR '1'='1`).

---

### AP-02 · Segredos e credenciais hardcoded

**O que é:** chaves, senhas, tokens ou strings de conexão escritos literalmente no código versionado.

**Sinais de detecção**
- Atribuição de literal a nomes como `secret`, `password`, `passwd`, `pwd`, `pass`, `token`, `api_key`, `private_key`, `credential`:
  `grep -rniE "(secret|passw(or)?d|pwd|pass|token|api_?key|credential)[\"']?\s*[:=]\s*[\"'][^\"']{3,}[\"']"`
- `SECRET_KEY` literal: `app.config['SECRET_KEY'] = '...'`, `SECRET_KEY = '...'`.
- Prefixos de chaves reais: `pk_live_`, `sk_live_`, `AKIA`, `ghp_`, `xoxb-`.
- Strings de conexão com usuário e senha: `://usuario:senha@`.
- Credenciais SMTP ou de terceiros em construtores de serviço.
- Usuário administrador com senha fixa criado automaticamente no boot (seed embutido no código de produção).

**Falsos positivos:** leitura de variável de ambiente sem default literal; placeholders óbvios em `.env.example`; fixtures de teste; scripts de seed de desenvolvimento executados manualmente.

**Impacto:** qualquer pessoa com acesso ao repositório obtém os segredos; rotacionar exige novo deploy; sessões podem ser forjadas com a `SECRET_KEY`.

**Consolidação:** se o mesmo segredo também aparece em resposta HTTP ou em log, inclua essas localizações no mesmo finding e cite o vazamento na descrição.

---

### AP-03 · Exposição de dados sensíveis

**O que é:** respostas HTTP, logs ou mensagens de erro contendo senhas ou hashes, segredos, dados de cartão, configuração interna ou detalhes de infraestrutura.

**Sinais de detecção**
- Serializadores e dicionários de resposta com chaves `senha`, `password`, `pass`, `hash`, `secret`, `token`, `card`, `cvv`, `cpf`.
- `to_dict()` / `toJSON()` de entidade de usuário que inclui a senha — e todos os pontos que o retornam.
- `SELECT *` de tabela de usuários devolvido direto ao cliente.
- Logs com dados sensíveis: `print(... senha ...)`, `console.log(\`... ${card} ...\`)`.
- Endpoints de health/debug que retornam `secret_key`, `debug`, caminho do banco, variáveis de ambiente.

**Severidade:** CRITICAL para credenciais, segredos e dados de pagamento. HIGH para dados pessoais expostos sem autenticação. Mensagem de exceção interna (`str(e)`) devolvida ao cliente é tratada em AP-15.

**Impacto:** vazamento direto de credenciais e violação de LGPD/PCI-DSS.

---

### AP-04 · Armazenamento inseguro de senha

**O que é:** senha guardada em texto plano, com hash rápido sem salt (MD5, SHA-1, SHA-256 puro) ou com "criptografia" caseira.

**Sinais de detecção**
- `INSERT`/atribuição da senha recebida sem passar por função de hash.
- Comparação de senha no SQL (`WHERE email = ? AND senha = ?`) ou por igualdade direta.
- `hashlib.md5(`, `hashlib.sha1(`, `hashlib.sha256(` aplicados a senha; `crypto.createHash('md5'|'sha1'|'sha256')` idem.
- Algoritmos caseiros: base64, reversão, truncamento, loops concatenando partes (`Buffer.from(pwd).toString('base64')`).
- Default de senha quando o campo não é enviado (`pwd || "123456"`).

**Falsos positivos:** MD5/SHA usados para ETag, chave de cache ou checksum — não para senha.

**Impacto:** com um dump do banco, as senhas são recuperadas em segundos (tabelas rainbow, força bruta em GPU); reuso de senha compromete outros sistemas dos usuários.

---

### AP-05 · Operação privilegiada sem controle de acesso

**O que é:** endpoints que executam código/SQL arbitrário, destroem dados em massa ou expõem funções administrativas sem autenticação e autorização reais.

**Sinais de detecção**
- Execução de entrada do cliente: `execute(dados["sql"])`, `eval(`, `exec(`, `child_process.exec(` com dados da requisição.
- Paths com `admin`, `reset`, `debug`, `query`, `exec`, `internal`, `financial` sem decorator ou middleware de autenticação (`@login_required`, `@jwt_required`, `authenticate`, verificação de `req.user`).
- `DELETE FROM <tabela>` sem `WHERE` acessível por rota.
- Token de autenticação falso ou não assinado: `'fake-jwt-token-' + id`, token igual ao id, ausência de verificação de token nas demais rotas.

**Severidade:** CRITICAL para execução arbitrária, destruição em massa ou dados financeiros. HIGH quando a autenticação é falsa ou inexistente, mas o dano possível é limitado a leitura de dados não sensíveis.

**Impacto:** qualquer cliente anônimo pode apagar o banco, exfiltrar tudo ou assumir contas.

**Nota de contrato:** em CRITICAL ou HIGH, a Fase 3 aplica a T14 por completo, rota a rota, e cada mudança é declarada como Breaking Change. Rota que executa SQL ou código enviado pelo cliente, ou que destrói dados em massa, é **removida** — protegê-la com token mantém a capacidade de exfiltrar ou destruir o banco e não corrige o finding. As demais rotas privilegiadas ou destrutivas passam a exigir credencial. Assinar o token falso sem exigi-lo nas rotas deixa o impacto intacto e não corrige o finding.

---

### AP-06 · God Class / God Module

**O que é:** uma classe ou módulo que concentra responsabilidades de várias camadas (HTTP, dados, regra, integração) e, em geral, de vários domínios.

**Sinais de detecção**
- Na matriz de responsabilidades (`analise-de-projeto.md`, seção 8.1), três ou mais responsabilidades de natureza diferente no mesmo arquivo.
- Funções de acesso a dados de vários domínios no mesmo módulo (`get_produtos`, `criar_usuario`, `criar_pedido`, `relatorio_vendas`).
- Classe com nome genérico (`Manager`, `AppManager`, `Helper`, `Utils`, `Service`) que abre conexão, registra rotas e implementa regra de negócio.
- Arquivo com mais de ~300 linhas misturando domínios.

**Localização:** o intervalo da classe ou do módulo inteiro (`arquivo:1-315`), com as linhas das responsabilidades mais graves na descrição.

**Severidade:** CRITICAL quando mistura camadas **e** domínios. Se o módulo tem um só domínio e mistura duas ou três responsabilidades, classifique como AP-07 (HIGH).

**Impacto:** impossível testar em isolamento; toda mudança tem raio de impacto global; conflitos constantes entre quem mexe no código.

---

## HIGH

### AP-07 · Regra de negócio na camada HTTP

**O que é:** handlers de rota ou controllers que calculam, decidem regras do domínio, acessam o banco diretamente ou disparam integrações, em vez de delegar.

**Sinais de detecção**
- Handler com mais de ~30 linhas.
- Chamadas de ORM/SQL dentro do handler (`Model.query`, `db.session`, `cursor.execute`, `db.get(`).
- Cálculos e agregações do domínio: loops somando valores, contagem por status, cálculo de atraso, desconto, frete.
- Efeitos colaterais de negócio no handler: envio de e-mail/SMS/push (ou `print` simulando), gravação de auditoria.
- O inverso também conta: camada de dados devolvendo estruturas de resposta HTTP (`return {"erro": "..."}` usado pelo controller para decidir status).

**Falsos positivos:** controllers finos que extraem entrada, chamam um serviço e escolhem o status code.

**Impacto:** regra impossível de reutilizar (CLI, fila, outro endpoint) e de testar sem subir HTTP; duplicação quando a mesma regra é necessária em duas rotas.

---

### AP-08 · Estado global mutável

**O que é:** dados ou recursos compartilhados guardados em variáveis de módulo reatribuídas ou mutadas em tempo de execução.

**Sinais de detecção**
- Python: `global <nome>`; variável de módulo iniciada com `None` e reatribuída (`db_connection = None`); `sqlite3.connect(..., check_same_thread=False)` compartilhada entre threads.
- Node: `let` no escopo do módulo mutado por funções; objetos `{}`/arrays exportados e alterados (`globalCache[key] = data`).
- Primitivo exportado por valor que o código espera ver atualizado (`module.exports = { totalRevenue }` — quem importa recebe uma cópia congelada).
- Listas em memória usadas como armazenamento em instâncias de serviço (`self.notifications = []`): perdidas no restart e não compartilhadas entre workers.

**Falsos positivos**
- Constantes de módulo (MAIÚSCULAS, nunca reatribuídas).
- Objetos de extensão projetados para inicialização global com `init_app` (`db = SQLAlchemy()`, `cors = CORS()`) — é o padrão recomendado, não um finding.
- Pool de conexões criado uma vez no composition root e injetado.

**Impacto:** condições de corrida sob concorrência, testes que interferem entre si, bugs que só aparecem em produção com múltiplos workers.

---

### AP-09 · Operação multi-passo sem transação

**O que é:** fluxo que executa duas ou mais escritas relacionadas sem garantir atomicidade.

**Sinais de detecção**
- Sequência de `INSERT`/`UPDATE`/`DELETE` sem `BEGIN`/`COMMIT`/`ROLLBACK`, sem `with conexao:` e sem bloco transacional do ORM.
- `return` ou `throw` possível **entre** duas escritas (validação no meio do laço de escrita).
- `commit()` chamado após cada passo em vez de uma vez ao final.
- Callbacks aninhados em que cada nível grava algo e os erros dos níveis internos só respondem ao cliente, sem desfazer os anteriores.
- Verificação seguida de escrita não atômica (ler estoque, depois decrementar em outra instrução).

**Impacto:** dados inconsistentes em qualquer falha parcial — pedido sem itens, matrícula sem pagamento, estoque decrementado para pedido inexistente.

---

### AP-10 · Configuração de execução insegura

**O que é:** flags e parâmetros de execução próprios de desenvolvimento fixados no código que roda em produção.

**Sinais de detecção**
- `debug=True`, `DEBUG = True`, `app.config["DEBUG"] = True` literais.
- `host="0.0.0.0"` fixo junto com debug ativo (o debugger do Werkzeug permite execução de código).
- Porta e host literais sem leitura de ambiente.
- `sqlite3.verbose()`, logs de SQL ou stack traces ativos incondicionalmente.
- Criação de schema ou seed executados no import do módulo (`db.create_all()` em nível de módulo) — sinal secundário, classifique como MEDIUM se for o único problema.

**Impacto:** execução remota de código via debugger, vazamento de stack traces, impossibilidade de configurar ambientes diferentes sem editar código.

---

### AP-11 · Acoplamento forte sem injeção de dependência

**O que é:** código de negócio que instancia ou importa diretamente a infraestrutura concreta (banco, SMTP, gateway), impedindo substituição e teste.

**Sinais de detecção**
- `sqlite3.connect(`, `new sqlite3.Database(`, `smtplib.SMTP(`, clientes HTTP criados dentro de funções de negócio ou construtores de classes de domínio.
- Todo módulo importando o mesmo módulo concreto de banco (`from database import get_db` em models **e** controllers).
- Serviço instanciado dentro do handler a cada chamada (`NotificationService()`).
- Integração simulada embutida na regra (`status = card.startsWith("4") ? "PAID" : "DENIED"`), sem uma interface de gateway.

**Falsos positivos:** o composition root (factory da aplicação, `main`) criando as dependências concretas — esse é exatamente o lugar certo.

**Impacto:** testes exigem banco e rede reais; trocar SQLite por PostgreSQL ou o gateway de pagamento significa editar a regra de negócio.

---

### AP-12 · Aninhamento profundo / callback hell

**O que é:** fluxo com muitos níveis de callbacks aninhados ou condicionais em pirâmide.

**Sinais de detecção**
- Quatro ou mais níveis de callbacks aninhados (`(err, row) => { ... (err) => { ...`).
- Contadores manuais para saber quando laços assíncronos terminam (`pending--; if (pending === 0) res.json(...)`).
- `const self = this` para contornar escopo em callbacks.
- Callbacks que ignoram o parâmetro `err`.
- Pirâmides de `if`/`else` com quatro ou mais níveis retornando booleanos.

**Severidade:** HIGH quando o aninhamento esconde erro ignorado, risco de resposta dupla ou de requisição sem resposta. MEDIUM quando é apenas legibilidade (pirâmide de `if` síncrona e correta).

**Impacto:** tratamento de erro incompleto por construção, fluxo difícil de seguir e de alterar.

---

## MEDIUM

### AP-13 · Query N+1

**O que é:** uma consulta para a lista e mais uma (ou mais) para cada item da lista.

**Sinais de detecção**
- Chamada ao banco dentro de laço sobre resultado do banco: `for row in rows: cursor.execute(`, `for t in tasks: User.query.get(t.user_id)`, `rows.forEach(r => db.get(`.
- Acesso a relacionamento lazy dentro de laço: `len(u.tasks)`, `t.user.name`, `task.category`.
- Contagens por item em laço: `Task.query.filter_by(category_id=c.id).count()` para cada categoria.
- Várias consultas `COUNT(*) ... WHERE status = 'x'` seguidas que caberiam num `GROUP BY` — sinal mais fraco, cite dentro do mesmo finding.

**Impacto:** tempo de resposta cresce linearmente com o volume; um endpoint de listagem com 1.000 itens dispara milhares de consultas.

---

### AP-14 · Validação ausente ou duplicada

**O que é:** entrada usada sem validação de presença, tipo e formato, ou as mesmas regras copiadas em vários handlers.

**Sinais de detecção**
- Blocos de validação idênticos ou quase idênticos em criar e atualizar.
- Comparação numérica com dado não convertido (`data['priority'] < 1` quando `priority` pode vir como string → erro 500).
- Conversão sem tratamento (`float(request.args["preco_min"])`, `int(priority)`).
- Campos da requisição usados diretamente sem checagem (`req.body.x` direto numa query ou regra).
- Validador existente que não é chamado em lugar nenhum, enquanto as rotas repetem a validação à mão.
- Regex frouxo ou inconsistente para o mesmo campo em lugares diferentes.
- Enum validado com lista literal repetida em vários arquivos.

**Impacto:** erros 500 com entrada inválida, regras divergentes entre endpoints, dados inválidos no banco.

---

### AP-15 · Tratamento de erro não centralizado

**O que é:** cada handler trata exceções à sua maneira, sem um ponto central de tradução para respostas HTTP.

**Sinais de detecção**
- `except:` sem tipo; `except Exception as e:` repetido em todos os handlers.
- `return jsonify({"erro": str(e)}), 500` — além de duplicado, vaza detalhes internos.
- Erros engolidos: `except: pass`, callbacks que recebem `err` e não o usam, `catch {}` vazio.
- Formatos de erro diferentes entre endpoints do mesmo projeto.
- Ausência de handler global: nenhum `@app.errorhandler` / `register_error_handler` (Flask), nenhum middleware de 4 argumentos `(err, req, res, next)` (Express).

**Severidade:** sobe para HIGH quando um erro engolido pode deixar dados corrompidos ou retornar sucesso falso.

**Impacto:** bugs silenciosos, respostas inconsistentes, vazamento de mensagens internas, duplicação.

---

### AP-16 · CORS permissivo

**O que é:** API aceitando requisições cross-origin de qualquer origem sem necessidade.

**Sinais de detecção:** `CORS(app)` sem `origins`/`resources`; `cors()` sem opções; `Access-Control-Allow-Origin: *` manual.

**Severidade:** HIGH se combinado com credenciais (`supports_credentials=True`, `credentials: true`) e origem refletida ou wildcard.

**Impacto:** qualquer site pode chamar a API a partir do navegador de um usuário.

---

### AP-17 · Listagem sem paginação

**O que é:** endpoints que devolvem todos os registros de uma tabela.

**Sinais de detecção:** `SELECT * FROM <tabela>` sem `LIMIT` numa rota de listagem; `Model.query.all()`, `find({})`, `db.all("SELECT ...")` devolvidos diretamente; relatórios que carregam a tabela inteira em memória para contar.

**Impacto:** uso de memória e tempo de resposta crescem com o volume; um endpoint pode derrubar o servidor.

**Nota de contrato:** paginação obrigatória muda o formato e o conteúdo da resposta. Na Fase 3 aplique apenas de forma opcional (T17).

---

### AP-18 · Integridade referencial não garantida

**O que é:** relacionamentos entre tabelas sem garantia de consistência na remoção ou na criação.

**Sinais de detecção**
- `DELETE` de registro pai sem tratar dependentes: sem `FOREIGN KEY ... ON DELETE`, sem cascade no ORM, sem checagem prévia.
- Colunas `*_id` sem `FOREIGN KEY` no DDL; SQLite sem `PRAGMA foreign_keys = ON`.
- Cascata manual em laço (`for t in tasks: db.session.delete(t)`) sem transação ou sem necessidade.
- Mensagens ou comentários que reconhecem dados órfãos.
- Erro do driver ignorado na remoção, respondendo sucesso mesmo quando nada foi removido.

**Impacto:** registros órfãos, relatórios com dados de entidades que não existem mais, falhas tardias difíceis de rastrear.

---

### AP-19 · API deprecated ou dependência sem suporte

**O que é:** uso de funções, módulos ou pacotes marcados como deprecated, legados ou removidos em versões atuais da linguagem, do framework ou das bibliotecas.

**Como detectar e confirmar** — cite sempre a evidência no finding; não aponte depreciação sem fonte:

- **Aviso em runtime:** suba ou importe a aplicação com `python -W default ...` e procure `DeprecationWarning` / `LegacyAPIWarning`; em Node, `node --trace-deprecation`.
- **Instalação:** a saída de `npm ci` / `npm install` lista `npm warn deprecated <pacote>@<versão>: <motivo>`.
- **Vulnerabilidades:** `npm audit`, `pip-audit` (se disponível).
- **Busca no código:** os padrões da tabela abaixo.

**Severidade:** MEDIUM por padrão. HIGH quando a dependência deprecated tem vulnerabilidade high/critical conhecida ou quando a API já foi **removida** na próxima versão maior em uso comum. LOW para aliases apenas desencorajados, sem remoção prevista. Algoritmo fraco usado para senha é classificado como AP-04.

| Ecossistema | Deprecated / legado | Substituto moderno | Referência |
|---|---|---|---|
| Python | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)`, `datetime.fromtimestamp(ts, timezone.utc)` | deprecated no 3.12 |
| Python | módulos `distutils`, `imp`, `asynchat`, `asyncore`, `smtpd` | `setuptools`, `importlib`, `asyncio`, `aiosmtpd` | removidos no 3.12 |
| Python | `pkg_resources` | `importlib.metadata`, `importlib.resources` | deprecated no setuptools |
| Python | `typing.List`, `typing.Dict`, `typing.Optional` | `list[...]`, `dict[...]`, `X \| None` | aliases desencorajados desde 3.9 (LOW) |
| SQLAlchemy 2.x | `Query.get(id)`, `Model.query.get(id)` | `session.get(Model, id)`, `db.session.get(Model, id)` | `LegacyAPIWarning` desde 2.0 |
| SQLAlchemy 2.x | `session.query(Model)`, `Model.query.filter(...)` | `session.execute(select(Model).where(...)).scalars()` | API legada no 2.0 |
| SQLAlchemy 2.x | `engine.execute()`, `sqlalchemy.ext.declarative.declarative_base` | `with engine.connect() as conn: conn.execute(...)`, `sqlalchemy.orm.DeclarativeBase` | removido / movido no 2.0 |
| Flask-SQLAlchemy 3.x | `Model.query.get_or_404(id)` | `db.get_or_404(Model, id)` | legado desde 3.0 |
| Flask | `@app.before_first_request` | inicialização na factory ou em `with app.app_context()` | removido no 2.3 |
| Flask | `FLASK_ENV`, `app.config["ENV"]` | `--debug` / `FLASK_DEBUG` | removido no 2.3 |
| Flask | `flask.json.JSONEncoder`, `app.json_encoder` | `app.json` (`DefaultJSONProvider`) | removido no 2.3 |
| Flask | `send_file(attachment_filename=...)` | `send_file(download_name=...)` | removido no 2.2 |
| Werkzeug | `werkzeug.urls.url_quote`, `url_parse` | `urllib.parse.quote`, `urllib.parse.urlsplit` | removido no 3.0 |
| Node.js | `new Buffer(x)` | `Buffer.from(x)`, `Buffer.alloc(n)` | DEP0005 |
| Node.js | `url.parse()` | `new URL()` | DEP0169 |
| Node.js | `fs.exists()` | `fs.existsSync()`, `fs.promises.access()` | DEP0034 |
| Node.js | `util.isArray()`, `util.isDate()` e demais `util.is*` | `Array.isArray()`, `instanceof`, `typeof` | DEP0044–DEP0058 |
| Node.js | `crypto.createCipher()` | `crypto.createCipheriv()` | removido no Node 22 |
| Node.js | `require('punycode')` | `url.domainToASCII()` ou pacote `punycode` do npm | DEP0040 |
| Express 4 → 5 | `app.del()` | `app.delete()` | removido no 5.0 |
| Express 4 → 5 | `req.param(name)` | `req.params`, `req.body`, `req.query` | removido no 5.0 |
| Express 4 → 5 | `res.send(status)`, `res.json(obj, status)` | `res.sendStatus(status)`, `res.status(status).json(obj)` | removido no 5.0 |
| Express 4 → 5 | `res.sendfile()` | `res.sendFile()` | removido no 5.0 |
| Express | `bodyParser()` genérico, `body-parser` só para JSON | `express.json()`, `express.urlencoded()` | nativo desde 4.16 |
| npm | `request` | `fetch` nativo (Node 18+), `undici` | deprecated em 2020 |
| npm | `moment` | `date-fns`, `Luxon`, `Intl` | modo manutenção desde 2020 |
| npm (transitivas) | `inflight`, `glob@<9`, `rimraf@<4`, `tar@<7`, `npmlog`, `gauge`, `are-we-there-yet`, `prebuild-install` | atualizar ou substituir a dependência **direta** que as puxa (`npm ls <pacote>`) | aviso `npm warn deprecated` |
| Mongoose | opções `useNewUrlParser`, `useUnifiedTopology`, `useCreateIndex` | remover | sem efeito desde 6.0 |

**Nota de contrato:** migrar uma dependência de versão maior (Express 4 → 5, por exemplo) pode alterar comportamento sutil. Na Fase 3, só aplique se o smoke test comprovar equivalência; caso contrário, recomende no relatório e marque o finding como parcial.

---

## LOW

### AP-20 · Logging via `print` / `console.log`

**O que é:** saída de diagnóstico sem níveis, sem estrutura e sem controle de destino.

**Sinais de detecção:** `print(` em código de aplicação; `console.log` em handlers e serviços; mensagens que simulam integrações (`"ENVIANDO EMAIL"`); banners de inicialização com `print`.

**Falsos positivos:** scripts de linha de comando (seed, migrations) que reportam progresso ao operador.

**Escalonamento:** se o log contém segredo, senha ou dado de cartão, é AP-03.

---

### AP-21 · Magic numbers e literais duplicados

**O que é:** valores com significado de negócio espalhados como literais.

**Sinais de detecção**
- Limiares e taxas em regras: `if faturamento > 10000`, `* 0.1`, `priority <= 2`.
- Listas de valores válidos (`['pending', 'in_progress', 'done', 'cancelled']`) repetidas em vários pontos.
- Tamanhos mínimos e máximos literais (`len(title) < 3`, `> 200`).
- Constantes nomeadas **declaradas mas não usadas**, enquanto os literais continuam espalhados.

---

### AP-22 · Código morto

**O que é:** código, imports ou dependências que não participam da execução.

**Sinais de detecção**
- Imports não usados: para cada `import x` / `from m import a, b`, `grep -c` do nome no restante do arquivo.
- Funções e classes nunca chamadas: `grep -rn "<nome>"` retorna apenas a definição.
- Dependências declaradas no manifesto e nunca importadas (`analise-de-projeto.md`, seção 4).
- Valores exportados e nunca lidos; código comentado.

**Escalonamento:** se o código morto é uma implementação correta que o código vivo duplica de forma pior (validador pronto e não usado), registre a duplicação como AP-14 e cite o código morto no mesmo finding.

---

### AP-23 · Nomenclatura pobre e código verboso

**O que é:** nomes que não comunicam intenção e construções que dizem em várias linhas o que cabe em uma.

**Sinais de detecção**
- Variáveis de uma a três letras fora de índices de laço e lambdas curtas (`u`, `e`, `p`, `cc`, `cid`).
- Nomes que sombreiam built-ins (`id`, `type`, `list`, `filter` em Python).
- Nomes enganosos ou genéricos (`AppManager`, `utils`, `data2`, `badCrypto`).
- `if cond: return True else: return False` em vez de `return cond`.
- Pirâmide de `if` aninhado que cabe numa expressão booleana.

**Nota de contrato:** chaves JSON públicas mal nomeadas (`usr`, `eml`, `c_id`) são reportadas, mas **não** renomeadas na Fase 3 — renomear quebra os clientes. Renomeie apenas identificadores internos.

---

### AP-24 · Serialização manual duplicada

**O que é:** a mesma conversão de entidade para resposta repetida em vários lugares.

**Sinais de detecção**
- Mesmo dicionário/objeto de resposta construído campo a campo em duas ou mais funções.
- `to_dict()` existente, mas handlers remontam a resposta manualmente.
- A mesma entidade serializada com campos ou formatos diferentes em endpoints diferentes.

**Escalonamento:** MEDIUM quando as cópias divergem de forma perigosa — por exemplo, uma omite a senha e outra a inclui.

---

## Regras de escalonamento

1. **Exposição externa agrava.** Um problema alcançável por requisição anônima sobe um nível em relação ao mesmo problema só alcançável internamente.
2. **Dano a dados agrava.** Erro engolido, falta de transação ou validação ausente que pode gravar dados corrompidos sobe um nível.
3. **Código de desenvolvimento atenua.** Problema restrito a script local executado manualmente (seed, fixture) desce um nível, nunca abaixo de LOW.
4. **Uma causa raiz, um finding.** Se a mesma linha configura dois anti-patterns (MD5 para senha é AP-04 e AP-19), reporte uma vez sob o mais severo e cite o outro ID na descrição.
5. **Na dúvida entre dois níveis,** releia as definições da [escala](#escala-de-severidade) e escolha o nível cuja definição o impacto concreto satisfaz por completo.
