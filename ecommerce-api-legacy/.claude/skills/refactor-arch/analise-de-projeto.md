# Análise de Projeto — Heurísticas de Detecção

Referência da **Fase 1**. O objetivo é um retrato fiel do projeto, com evidência para cada afirmação. Quando duas heurísticas discordarem, vale a evidência mais forte, nesta ordem:

**código que efetivamente executa > lockfile/ambiente instalado > manifesto > estrutura de pastas > README**

---

## 1. Inventário de arquivos-fonte

Arquivo-fonte é código escrito pela equipe do projeto — incluindo scripts auxiliares como seeds e migrations, e arquivos `__init__.py`/`index.js` mesmo quando curtos.

**Excluir sempre**

| Categoria | Padrões |
|---|---|
| Dependências e ambientes | `node_modules/`, `vendor/`, `.venv/`, `venv/`, `env/`, `__pycache__/`, `site-packages/` |
| Build e artefatos | `dist/`, `build/`, `target/`, `.next/`, `coverage/`, `*.pyc`, `*.min.js`, `*.map` |
| Ferramentas | `.git/`, `.claude/`, `.refactor-arch/`, `.idea/`, `.vscode/` |
| Lockfiles e dados | `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `*.db`, `*.sqlite*`, `instance/` |

**Comando de inventário** (funciona com ou sem git):

```bash
find . \( -name node_modules -o -name vendor -o -name .venv -o -name venv -o -name env \
          -o -name __pycache__ -o -name .git -o -name .claude -o -name .refactor-arch \
          -o -name dist -o -name build -o -name target -o -name coverage -o -name instance \) -prune \
  -o -type f \( -name '*.py' -o -name '*.js' -o -name '*.mjs' -o -name '*.cjs' -o -name '*.ts' \
          -o -name '*.go' -o -name '*.java' -o -name '*.kt' -o -name '*.rb' -o -name '*.php' -o -name '*.cs' \) \
  -print | sort
```

Linhas de código: `wc -l` sobre a lista. Reporte o número de arquivos e o total de linhas — ambos precisam bater com a realidade, não com uma estimativa.

---

## 2. Linguagem

| Manifesto ou arquivo | Linguagem | Confirmação |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | arquivos `.py` no inventário |
| `package.json` sem `tsconfig.json` | JavaScript (Node.js) | `.js`/`.mjs`/`.cjs`; `"type": "module"` indica ESM |
| `package.json` + `tsconfig.json` | TypeScript | `.ts` no inventário |
| `go.mod` | Go | `.go` |
| `pom.xml`, `build.gradle(.kts)` | Java / Kotlin | `.java` / `.kt` |
| `Gemfile` | Ruby | `.rb` |
| `composer.json` | PHP | `.php` |
| `*.csproj`, `*.sln` | C# | `.cs` |

**Versão do runtime:** a do ambiente que vai rodar o projeto (`.venv/bin/python --version`, `node --version`). Confira se ela atende ao que o projeto pede: `python_requires`, `engines` do `package.json`, `.nvmrc`, `.python-version`. Incompatibilidade aqui é a causa mais comum de "a aplicação não sobe".

---

## 3. Framework

| Dependência declarada | Framework | Evidência no código |
|---|---|---|
| `flask` | Flask | `Flask(__name__)`, `@app.route`, `Blueprint(`, `add_url_rule(` |
| `django` | Django | `manage.py`, `settings.py`, `urls.py`, `INSTALLED_APPS` |
| `fastapi` | FastAPI | `FastAPI()`, `@app.get(`, `APIRouter(` |
| `express` | Express | `express()`, `app.get(`, `express.Router()` |
| `fastify` | Fastify | `fastify()`, `fastify.get(` |
| `@nestjs/core` | NestJS | `@Controller(`, `@Module(`, `NestFactory.create` |
| `koa` | Koa | `new Koa()`, `ctx.body` |
| `spring-boot-starter-web` | Spring Boot | `@RestController`, `@GetMapping` |
| `rails` | Rails | `config/routes.rb`, `ApplicationController` |
| `laravel/framework` | Laravel | `routes/api.php`, `artisan` |
| `github.com/gin-gonic/gin` | Gin | `gin.Default()`, `r.GET(` |

**Versão:** a versão **instalada**, não o range declarado.

- Node: `package-lock.json` → `packages["node_modules/<nome>"].version`, ou `npm ls <nome>`.
- Python: `.venv/bin/pip show <nome>` ou `pip freeze`; o pin `==` do `requirements.txt` quando não houver ambiente.
- Reporte as duas quando divergirem, ex.: `Express 4.22.1 (declarado ^4.18.2)`.

---

## 4. Dependências relevantes

Liste as dependências diretas agrupadas por papel: extensões do framework (CORS, auth), ORM ou driver de banco, validação, cliente HTTP, configuração, e-mail/filas/pagamento.

Para cada dependência declarada, verifique se ela é **usada**:

```bash
grep -rn --include='*.py' -E '^\s*(import|from)\s+<modulo>' .      # Python
grep -rn --include='*.js' -E "require\(['\"]<pacote>|from ['\"]<pacote>" .   # Node
```

Dependência declarada e nunca importada vira finding de código morto (AP-22). Atenção ao nome do módulo diferente do pacote: `python-dotenv` → `dotenv`, `flask-sqlalchemy` → `flask_sqlalchemy`, `flask-cors` → `flask_cors`.

---

## 5. Banco de dados

| Sinal | Engine / acesso |
|---|---|
| `import sqlite3`, `sqlite:///`, `require('sqlite3')`, `better-sqlite3` | SQLite |
| `:memory:` | SQLite em memória — estado zera a cada boot |
| `psycopg`, `pg`, `postgres://`, `postgresql://` | PostgreSQL |
| `pymysql`, `mysql2`, `mysql://` | MySQL/MariaDB |
| `mongoose`, `pymongo`, `mongodb://` | MongoDB |
| `flask_sqlalchemy`, `sqlalchemy`, `sequelize`, `typeorm`, `prisma`, `knex` | ORM / query builder (identifique também o engine por baixo) |

**Tabelas e entidades** — combine as fontes disponíveis:

- SQL: `CREATE TABLE (IF NOT EXISTS)? <nome>`
- SQLAlchemy: `__tablename__ = '<nome>'` e classes que herdam de `db.Model` / `Base`
- Django: classes que herdam de `models.Model`
- Mongoose: `mongoose.model('<Nome>'`, Prisma: `model <Nome> {` em `schema.prisma`
- Sequelize: `sequelize.define('<nome>'` ou `Model.init(`

**Modo de persistência e estado inicial** — anote como o banco nasce e é populado, porque isso define como o baseline será reprodutível:

- Arquivo criado no primeiro boot? Onde? (Flask-SQLAlchemy 3.x resolve `sqlite:///arquivo.db` relativo a `instance/`.)
- Seed automático no boot ou script separado (`seed.py`, `npm run seed`, fixtures)?
- Em memória (reinicia limpo) ou servidor externo (não pode ser resetado pela skill)?

---

## 6. Entry point, comandos e porta

| Stack | Onde procurar |
|---|---|
| Python | `if __name__ == "__main__":`, `app.run(`, `create_app(`, `wsgi.py`, `manage.py`, `Procfile`, README |
| Node | `package.json` → `scripts.start` e `main`; `app.listen(` / `server.listen(`; README |
| Geral | `Dockerfile` (`CMD`/`ENTRYPOINT`), `docker-compose.yml`, `Makefile` |

Registre:

- **Comando de instalação** e **comando de execução** documentados — são contrato (regra 4 do SKILL.md).
- **Porta e host**: literal no código (`port=5000`, `listen(3000)`), variável de ambiente (`process.env.PORT`) ou default do framework.
- **Efeitos colaterais de import**: criação de tabelas, seed, conexões abertas ou `listen` executados ao importar o módulo. Eles influenciam como testar sem subir o servidor.

---

## 7. Mapeamento de rotas

| Framework | Padrões a buscar | Atenção |
|---|---|---|
| Flask | `@<x>.route(`, `@<x>.get/post/put/delete(`, `add_url_rule(` | `Blueprint(..., url_prefix=)` e `register_blueprint(..., url_prefix=)` somam prefixo; `methods=` ausente = `GET` |
| FastAPI | `@<x>.get/post/...(`, `APIRouter(prefix=)`, `include_router(..., prefix=)` | |
| Django | `path(`, `re_path(` em `urls.py`, `include(` | |
| Express | `app.<verbo>(`, `router.<verbo>(`, `app.use('<prefixo>', router)` | `app.all(` e middlewares com path |
| Fastify / Koa | `fastify.<verbo>(`, `router.<verbo>(` | |
| Spring | `@RequestMapping` na classe + `@GetMapping` etc. no método | |

Produza a tabela de rotas, que alimenta o smoke test:

| Método | Path | Handler | Local | Parâmetros de entrada |
|---|---|---|---|---|
| GET | `/recurso/<id>` | `buscar_recurso` | `arquivo.py:13` | path `id:int`; query `q` |

Inclua rotas registradas fora do arquivo principal de rotas (ex.: `@app.route` no entry point, rotas administrativas, health check).

---

## 8. Classificação da arquitetura

### 8.1 Matriz de responsabilidades

Para cada arquivo-fonte, marque quais responsabilidades ele exerce:

| Responsabilidade | Sinais |
|---|---|
| **HTTP** | objeto de requisição/resposta (`request`, `req`, `res`, `jsonify`), decorators de rota, status codes |
| **Dados** | SQL, chamadas de ORM (`.query`, `session`, `find(`, `db.run`), abertura de conexão |
| **Regra de negócio** | cálculos e decisões do domínio: preços, descontos, estoque, estados, permissões |
| **Validação** | checagem de campos obrigatórios, tamanhos, formatos, enums |
| **Serialização** | montagem manual de dicionários/objetos de resposta, `to_dict`, `toJSON` |
| **Integração externa** | e-mail, SMS, gateway de pagamento, HTTP para terceiros, filas |
| **Configuração** | segredos, URLs, portas, flags, constantes de ambiente |

Um arquivo com **três ou mais** responsabilidades de natureza diferente (ex.: HTTP + Dados + Regra) é um vazamento de camada e evidência direta para AP-06 ou AP-07.

### 8.2 Rubrica

| Classificação | Quando usar |
|---|---|
| **Monolítica sem camadas** | Poucos arquivos, e as responsabilidades da matriz aparecem misturadas na maioria deles. Nomes como `models.py`/`controllers.py` não bastam: conta o que o arquivo faz, não como se chama. |
| **God Class / God Module** | Uma única classe ou módulo concentra a maior parte das responsabilidades da aplicação (rotas + dados + regras + integrações). |
| **Camadas parciais** | Existem pastas por papel (`models/`, `routes/`, `services/`...), mas as responsabilidades vazam entre elas: query e regra dentro de rota, serviço existente sem uso, validação duplicada. |
| **Em camadas** | Dependências fluem num único sentido e cada arquivo exerce uma responsabilidade principal. |

Justifique a classificação com a evidência mais forte da matriz, em uma frase — ex.: "rotas, SQL e regras de desconto convivem em `models.py`".

---

## 9. Domínio

Deduza o domínio cruzando, em ordem de peso: nomes de tabelas/entidades, substantivos dos paths de rota, dados de seed e o README.

| Assinatura típica de entidades | Domínio provável |
|---|---|
| produtos/products, pedidos/orders, itens de pedido, carrinho | E-commerce |
| cursos/courses, matrículas/enrollments, pagamentos, alunos | LMS / plataforma de cursos |
| tarefas/tasks, projetos, categorias, responsáveis | Gestão de tarefas |
| posts, comentários, autores, tags | Blog / CMS |
| contas, transações, saldos, transferências | Financeiro |
| pacientes, consultas, profissionais, agendas | Saúde / agendamento |
| estoque, fornecedores, movimentações | Inventário |

A tabela é ponto de partida, não gabarito: combinações diferentes existem. Uma plataforma de cursos com fluxo de checkout é "LMS com checkout", não "e-commerce". Formato de saída: `<Domínio> API (<entidade 1>, <entidade 2>, <entidade 3>)`.
