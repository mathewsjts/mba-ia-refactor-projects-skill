# Playbook de Refatoração

Referência da **Fase 3**. São 17 transformações; cada uma diz quando se aplica, os passos, código antes/depois e as armadilhas que quebram contrato sem ninguém perceber.

Os exemplos usam nomes genéricos. Adapte ao domínio, ao idioma dos identificadores e às convenções do projeto: o que se copia é o padrão, não o código literal.

## Índice

| ID | Transformação | Corrige | Camada |
|---|---|---|---|
| T01 | Concatenação SQL → query parametrizada | AP-01 | models |
| T02 | Segredos e flags → módulo de configuração | AP-02, AP-10, AP-16 | config |
| T03 | God Class/Module → models por domínio | AP-06 | models |
| T04 | Regra na rota → controller + service | AP-07 | services, controllers |
| T05 | Senha fraca → hash com KDF e salt | AP-04 | models, services |
| T06 | Aninhamento profundo → async/await e guard clauses | AP-12 | services, models |
| T07 | Escritas soltas → transação | AP-09 | models |
| T08 | N+1 → JOIN, eager loading ou agregação | AP-13 | models |
| T09 | Validação inline → validador reutilizável | AP-14 | controllers |
| T10 | `try/except` por handler → error handler central | AP-15 | middlewares |
| T11 | Estado global e acoplamento → factory + injeção | AP-08, AP-11 | composition root |
| T12 | API deprecated → equivalente moderno | AP-19 | todas |
| T13 | Serialização solta → serializer com campos explícitos | AP-03, AP-24 | views |
| T14 | Endpoint privilegiado → remover ou proteger | AP-05 | views, middlewares |
| T15 | Remoção sem integridade → cascade explícito | AP-18 | models |
| T16 | Higiene: logging, constantes, código morto, nomes | AP-20 a AP-23 | todas |
| T17 | Listagem completa → paginação opcional | AP-17 | controllers, models |

## Princípios

1. **Mover antes de melhorar.** Primeiro leve o código para a camada certa sem mudar o que ele faz; depois melhore dentro da camada. Separar as duas coisas torna a causa de qualquer regressão óbvia.
2. **Comportamento observável é sagrado.** Mesmos status, mesmas chaves JSON, mesmas mensagens de erro, mesmo formato de datas e números — exceto Breaking Changes declarados.
3. **Preserve a semântica, inclusive a estranha.** `if preco_min:` ignora `0`; um `get` que devolve só a primeira linha; uma ordem de validação que decide qual erro aparece primeiro. Reproduza, e registre como recomendação no relatório se for um bug.
4. **Sem dependência nova sem necessidade.** Biblioteca padrão e dependências já declaradas primeiro.

---

## T01 · Concatenação SQL → query parametrizada

**Corrige:** AP-01 · **Contrato:** preservado

**Passos**
1. Troque cada valor concatenado por um placeholder do driver.
2. Passe os valores numa sequência separada, na mesma ordem dos placeholders.
3. Em consultas com filtros opcionais, acumule cláusulas e parâmetros juntos.

| Driver | Placeholder |
|---|---|
| Python `sqlite3` | `?` |
| `psycopg` / `pymysql` | `%s` |
| SQLAlchemy `text()` | `:nome` |
| Node `sqlite3` / `better-sqlite3` / `mysql2` | `?` |
| Node `pg` | `$1`, `$2` |

**Python — antes**

```python
def buscar_produtos(termo, categoria=None):
    query = "SELECT * FROM produtos WHERE 1=1"
    if termo:
        query += " AND (nome LIKE '%" + termo + "%' OR descricao LIKE '%" + termo + "%')"
    if categoria:
        query += " AND categoria = '" + categoria + "'"
    cursor.execute(query)
    return cursor.fetchall()
```

**Python — depois**

```python
def buscar(self, termo=None, categoria=None):
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    return self._database.connection().execute(query, params).fetchall()
```

**JavaScript — antes**

```js
db.get(`SELECT id FROM users WHERE email = '${email}'`, (err, user) => { /* ... */ });
```

**JavaScript — depois**

```js
db.get('SELECT id FROM users WHERE email = ?', [email], (err, user) => { /* ... */ });
```

**Armadilhas**
- Nomes de coluna, tabela e direção de `ORDER BY` não aceitam placeholder: valide contra uma lista fixa.
- `IN (...)` precisa de um placeholder por item: `",".join("?" * len(ids))`.
- Mantenha as condições de truthiness do original (`if preco_min:` ignora `0`).

---

## T02 · Segredos e flags → módulo de configuração

**Corrige:** AP-02, AP-10, AP-16 · **Contrato:** preservado

**Passos**
1. Crie um módulo de configuração que lê o ambiente uma única vez.
2. Segredos: obrigatórios em produção (falha no boot); em desenvolvimento, gere um valor aleatório efêmero. Nunca um literal.
3. Flags de execução (`debug`, `host`) com defaults seguros; porta com o **mesmo default** do original para preservar o comando documentado.
4. CORS: origens vindas do ambiente; `*` apenas fora de produção.
5. Crie `.env.example` só com os nomes das variáveis. Use `python-dotenv`/`dotenv` apenas se já estiverem declarados.
6. Substitua todos os literais pelo objeto de configuração, inclusive onde o segredo era devolvido em resposta ou log.

**Python — antes**

```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
CORS(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

**Python — depois**

```python
# src/config/settings.py
import os
import secrets
from dataclasses import dataclass


def _as_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    env: str
    debug: bool
    host: str
    port: int
    secret_key: str
    database_path: str
    cors_origins: object

    @classmethod
    def from_env(cls, environ=None):
        environ = os.environ if environ is None else environ
        env = environ.get("APP_ENV", "development")
        production = env == "production"

        secret_key = environ.get("SECRET_KEY")
        if not secret_key:
            if production:
                raise RuntimeError("SECRET_KEY é obrigatória em produção")
            secret_key = secrets.token_hex(32)

        origins = environ.get("CORS_ORIGINS")
        if origins:
            cors_origins = [origin.strip() for origin in origins.split(",") if origin.strip()]
        else:
            cors_origins = [] if production else "*"

        return cls(
            env=env,
            debug=_as_bool(environ.get("APP_DEBUG", "false")),
            host=environ.get("APP_HOST", "127.0.0.1"),
            port=int(environ.get("PORT", "5000")),
            secret_key=secret_key,
            database_path=environ.get("DATABASE_PATH", "app.db"),
            cors_origins=cors_origins,
        )
```

```python
# src/app.py
CORS(app, origins=settings.cors_origins)
```

**JavaScript — antes**

```js
const config = {
  dbPass: 'senha_super_secreta_prod_123',
  paymentGatewayKey: 'pk_live_1234567890abcdef',
  port: 3000,
};
```

**JavaScript — depois**

```js
// src/config/index.js
const env = process.env.NODE_ENV || 'development';

function secret(name) {
  const value = process.env[name];
  if (!value && env === 'production') {
    throw new Error(`Variável de ambiente obrigatória ausente: ${name}`);
  }
  return value || '';
}

module.exports = Object.freeze({
  env,
  port: Number(process.env.PORT || 3000),
  databaseFile: process.env.DATABASE_FILE || ':memory:',
  dbPassword: secret('DB_PASSWORD'),
  paymentGatewayKey: secret('PAYMENT_GATEWAY_KEY'),
});
```

```dotenv
# .env.example
NODE_ENV=development
PORT=3000
DB_PASSWORD=
PAYMENT_GATEWAY_KEY=
```

**Armadilhas**
- Um segredo aleatório por boot invalida sessões a cada restart. É o comportamento correto em desenvolvimento; documente a variável para produção.
- Mudar o default de `host` para `127.0.0.1` não afeta o smoke test local, mas afeta quem acessava de outra máquina: registre no relatório.
- Não deixe o valor antigo como fallback (`os.environ.get("SECRET_KEY", "minha-chave...")`). Isso não corrige nada.

---

## T03 · God Class/Module → models por domínio

**Corrige:** AP-06 · **Contrato:** preservado

**Passos**
1. Liste as funções/métodos do módulo e agrupe por domínio (entidade principal que cada um toca).
2. Crie um model por domínio com as operações de dados daquele domínio; mova o código sem alterar comportamento.
3. Separe o que **não** é acesso a dados: regras (descontos, estados, cálculos) vão para services (T04); rotas vão para views; integrações vão para services.
4. Isole conexão e schema em `models/database.py` / `models/database.js`.
5. Atualize os imports, confirme com `grep -rn "<modulo_antigo>"` que nada mais usa o módulo antigo e remova-o na etapa de limpeza.

**Python — antes**

```python
# models.py — 4 domínios, SQL, regra e formatação
from database import get_db

def get_todos_produtos(): ...
def criar_usuario(nome, email, senha): ...
def criar_pedido(usuario_id, itens): ...
def relatorio_vendas():
    ...
    if faturamento > 10000:
        desconto = faturamento * 0.1
```

**Python — depois**

```python
# src/models/produto_model.py
class ProdutoModel:
    def __init__(self, database):
        self._database = database

    def listar(self):
        rows = self._database.connection().execute(
            "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos"
        ).fetchall()
        return [dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._database.connection().execute(
            "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em "
            "FROM produtos WHERE id = ?",
            (produto_id,),
        ).fetchone()
        return dict(row) if row else None
```

```python
# src/services/relatorio_service.py — a regra de desconto sai do model
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))


class RelatorioService:
    def __init__(self, pedido_model):
        self._pedidos = pedido_model

    def vendas(self):
        totais = self._pedidos.totais_por_status()
        faturamento = totais["faturamento"]
        taxa = next((t for limite, t in FAIXAS_DESCONTO if faturamento > limite), 0)
        desconto = faturamento * taxa
        return {"faturamento_bruto": round(faturamento, 2), "desconto_aplicavel": round(desconto, 2)}
```

**JavaScript — antes**

```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { /* CREATE TABLE ... e INSERT de seed */ }
  setupRoutes(app) {
    app.post('/api/orders', (req, res) => { /* validação + SQL + pagamento + auditoria */ });
    app.get('/api/admin/report', (req, res) => { /* SQL em laço + agregação */ });
  }
}
```

**JavaScript — depois**

```js
// src/models/order.model.js
class OrderModel {
  constructor(db) {
    this.db = db;
  }

  async create({ userId, productId }) {
    const { lastID } = await this.db.run(
      'INSERT INTO orders (user_id, product_id) VALUES (?, ?)',
      [userId, productId],
    );
    return lastID;
  }
}

module.exports = OrderModel;
```

```js
// src/models/database.js — schema e seed saem da God Class
async function initSchema(db) {
  await db.exec(`
    CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER);
  `);
}

module.exports = { initSchema };
```

**Armadilhas**
- Se o schema e o seed rodavam no boot, continuam rodando no boot — agora chamados pelo composition root.
- Preserve colunas e ordem dos campos devolvidos quando a resposta depende de `SELECT *` + `dict(row)`.

---

## T04 · Regra na rota → controller + service

**Corrige:** AP-07 · **Contrato:** preservado

**Passos**
1. **Service:** tudo que é decisão do domínio (validar estoque, calcular total, disparar notificação) vira método de service, recebendo e devolvendo dados puros. Falhas viram erros de domínio.
2. **Controller:** extrai a entrada da requisição, chama o validador (T09), chama o service e monta a resposta com o status correto.
3. **View/route:** só associa método + path ao método do controller.
4. Efeitos colaterais simulados (`print("ENVIANDO EMAIL")`) viram chamadas a um serviço de notificação injetado.

**Python — antes**

```python
def criar_pedido():
    try:
        dados = request.get_json()
        if not dados.get("itens"):
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400
        resultado = models.criar_pedido(dados["usuario_id"], dados["itens"])
        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400
        print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]))
        return jsonify({"dados": resultado, "sucesso": True}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

**Python — depois**

```python
# src/services/pedido_service.py
from src.errors import ValidationError


class PedidoService:
    def __init__(self, pedido_model, produto_model, notificador):
        self._pedidos = pedido_model
        self._produtos = produto_model
        self._notificador = notificador

    def criar(self, usuario_id, itens):
        for item in itens:
            produto = self._produtos.buscar_por_id(item["produto_id"])
            if produto is None:
                raise ValidationError(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
        resultado = self._pedidos.criar(usuario_id, itens)
        self._notificador.pedido_criado(resultado["pedido_id"], usuario_id)
        return resultado
```

```python
# src/controllers/pedido_controller.py
from flask import jsonify, request

from src.controllers.validators import validar_pedido


class PedidoController:
    def __init__(self, pedido_service):
        self._service = pedido_service

    def criar(self):
        usuario_id, itens = validar_pedido(request.get_json(silent=True))
        resultado = self._service.criar(usuario_id, itens)
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201
```

**JavaScript — antes**

```js
app.post('/api/orders', (req, res) => {
  const { productId, card } = req.body;
  db.get('SELECT * FROM products WHERE id = ?', [productId], (err, product) => {
    if (!product) return res.status(404).send('Produto não encontrado');
    const status = card.startsWith('4') ? 'PAID' : 'DENIED';
    if (status === 'DENIED') return res.status(400).send('Pagamento recusado');
    db.run('INSERT INTO orders (product_id) VALUES (?)', [productId], function () {
      res.json({ msg: 'Sucesso', order_id: this.lastID });
    });
  });
});
```

**JavaScript — depois**

```js
// src/services/order.service.js
const { NotFoundError, ValidationError } = require('../errors');

class OrderService {
  constructor({ productModel, orderModel, paymentGateway }) {
    this.productModel = productModel;
    this.orderModel = orderModel;
    this.paymentGateway = paymentGateway;
  }

  async checkout({ productId, card }) {
    const product = await this.productModel.findById(productId);
    if (!product) throw new NotFoundError('Produto não encontrado');
    const approved = await this.paymentGateway.charge({ card, amount: product.price });
    if (!approved) throw new ValidationError('Pagamento recusado');
    return this.orderModel.create({ productId });
  }
}

module.exports = OrderService;
```

```js
// src/controllers/order.controller.js
class OrderController {
  constructor(orderService) {
    this.orderService = orderService;
  }

  checkout = async (req, res) => {
    const orderId = await this.orderService.checkout({
      productId: req.body.productId,
      card: req.body.card,
    });
    res.status(200).json({ msg: 'Sucesso', order_id: orderId });
  };
}

module.exports = OrderController;
```

```js
// src/services/payment.gateway.js — a simulação vira uma implementação substituível
class FakePaymentGateway {
  async charge({ card }) {
    return card.startsWith('4');
  }
}

module.exports = FakePaymentGateway;
```

**Armadilhas**
- A ordem das verificações define qual erro o cliente vê primeiro. Mantenha-a.
- Controllers devolvem exatamente o mesmo envelope de antes (`{"dados": ..., "sucesso": true}`), incluindo chaves de mensagem.

---

## T05 · Senha fraca → hash com KDF e salt

**Corrige:** AP-04 · **Contrato:** preservado (a senha já não deve sair em resposta — ver T13)

**Passos**
1. Centralize `hash_password` e `verify_password` num único módulo.
2. Use um KDF com salt: Werkzeug `generate_password_hash` (dependência do Flask), `bcrypt`/`argon2` se já declarados; em Node, `crypto.scrypt` nativo.
3. Login: busque o usuário pelo e-mail e verifique a senha em código. Nunca compare senha dentro do SQL.
4. Senhas já gravadas no formato antigo: verifique no formato legado e regrave com o hash novo no primeiro login bem-sucedido.
5. Seeds que criam usuários passam a gravar o hash.

**Python — antes**

```python
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

def check_password(self, pwd):
    return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

**Python — depois**

```python
# src/models/passwords.py
import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

_LEGACY_MD5 = re.compile(r"^[a-f0-9]{32}$")
METHOD = "pbkdf2:sha256:600000"


def hash_password(plain):
    return generate_password_hash(plain, method=METHOD)


def verify_password(stored, plain):
    """Retorna (senha_confere, precisa_regravar)."""
    if stored and _LEGACY_MD5.match(stored):
        legacy = hashlib.md5(plain.encode()).hexdigest()
        return hmac.compare_digest(legacy, stored), True
    return check_password_hash(stored, plain), False
```

```python
# no model de usuário
def check_password(self, plain):
    ok, needs_rehash = verify_password(self.password, plain)
    if ok and needs_rehash:
        self.password = hash_password(plain)
    return ok
```

**JavaScript — antes**

```js
function badCrypto(pwd) {
  let hash = '';
  for (let i = 0; i < 10000; i++) hash += Buffer.from(pwd).toString('base64').substring(0, 2);
  return hash.substring(0, 10);
}
```

**JavaScript — depois**

```js
// src/models/passwords.js
const crypto = require('node:crypto');
const { promisify } = require('node:util');

const scrypt = promisify(crypto.scrypt);
const KEY_LENGTH = 64;

async function hashPassword(plain) {
  const salt = crypto.randomBytes(16);
  const key = await scrypt(plain, salt, KEY_LENGTH);
  return `scrypt$${salt.toString('hex')}$${key.toString('hex')}`;
}

async function verifyPassword(stored, plain) {
  const [scheme, saltHex, keyHex] = String(stored).split('$');
  if (scheme !== 'scrypt' || !saltHex || !keyHex) return false;
  const expected = Buffer.from(keyHex, 'hex');
  const actual = await scrypt(plain, Buffer.from(saltHex, 'hex'), expected.length);
  return expected.length === actual.length && crypto.timingSafeEqual(expected, actual);
}

module.exports = { hashPassword, verifyPassword };
```

**Armadilhas**
- O método padrão do Werkzeug 3 é `scrypt`, que depende de `hashlib.scrypt`. Builds de Python ligados a LibreSSL (como o Python do Xcode no macOS) não o têm e `generate_password_hash` falha em runtime. Por isso o exemplo fixa `pbkdf2:sha256`; se quiser `scrypt`, teste antes com `python -c "import hashlib; print(hasattr(hashlib, 'scrypt'))"`.
- Banco com senhas em texto plano: a verificação legada é a comparação direta com `hmac.compare_digest`, seguida de regravação. Um banco de desenvolvimento recriado pelo seed dispensa isso.
- Default de senha quando o campo não vem (`pwd || "123456"`) deve virar erro de validação — se isso mudar o status de uma rota, declare como Breaking Change de segurança.

---

## T06 · Aninhamento profundo → async/await e guard clauses

**Corrige:** AP-12 · **Contrato:** preservado

**Passos (JavaScript)**
1. Crie um adaptador que expõe o driver de callbacks como Promises. Se o driver já tem API de Promises, use-a.
2. Reescreva o fluxo de cima para baixo com `await`; erros sobem por exceção até o middleware (T10).
3. Troque contadores manuais (`pending--`) por `Promise.all` ou, melhor, por uma única consulta (T08).

**Passos (Python)**
1. Inverta condições e retorne cedo (guard clauses).
2. Pirâmides que só produzem um booleano viram uma expressão.

**JavaScript — antes**

```js
db.get('SELECT * FROM courses WHERE id = ?', [courseId], (err, course) => {
  if (err || !course) return res.status(404).send('Curso não encontrado');
  db.get('SELECT id FROM users WHERE email = ?', [email], (err, user) => {
    if (err) return res.status(500).send('Erro DB');
    db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [user.id, courseId], function (err) {
      if (err) return res.status(500).send('Erro Matrícula');
      res.json({ enrollment_id: this.lastID });
    });
  });
});
```

**JavaScript — depois**

```js
// src/models/database.js — adaptador de Promises para o driver sqlite3
const sqlite3 = require('sqlite3');

function openDatabase(filename) {
  const raw = new sqlite3.Database(filename);
  return {
    run(sql, params = []) {
      return new Promise((resolve, reject) => {
        raw.run(sql, params, function onRun(err) {
          if (err) return reject(err);
          resolve({ lastID: this.lastID, changes: this.changes });
        });
      });
    },
    get(sql, params = []) {
      return new Promise((resolve, reject) => {
        raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
      });
    },
    all(sql, params = []) {
      return new Promise((resolve, reject) => {
        raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
      });
    },
    exec(sql) {
      return new Promise((resolve, reject) => {
        raw.exec(sql, (err) => (err ? reject(err) : resolve()));
      });
    },
  };
}

module.exports = { openDatabase };
```

```js
// src/services/enrollment.service.js
const { NotFoundError } = require('../errors');

class EnrollmentService {
  constructor({ courseModel, userModel, enrollmentModel }) {
    this.courseModel = courseModel;
    this.userModel = userModel;
    this.enrollmentModel = enrollmentModel;
  }

  async enroll({ courseId, email }) {
    const course = await this.courseModel.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');
    const user = await this.userModel.findByEmail(email);
    return this.enrollmentModel.create({ userId: user.id, courseId });
  }
}

module.exports = EnrollmentService;
```

**Python — antes**

```python
def is_overdue(self):
    if self.due_date:
        if self.due_date < datetime.utcnow():
            if self.status != 'done' and self.status != 'cancelled':
                return True
            else:
                return False
        else:
            return False
    else:
        return False
```

**Python — depois**

```python
CLOSED_STATUSES = frozenset({"done", "cancelled"})


def is_overdue(self, now=None):
    now = now or utcnow()
    return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_STATUSES
```

**Armadilhas**
- `function` (não arrow) no callback de `run`: é por `this` que o `sqlite3` entrega `lastID` e `changes`.
- No original, respostas de erro diferentes por etapa (`"Erro DB"`, `"Erro Matrícula"`) fazem parte do contrato; preserve-as com erros de domínio específicos quando o cliente depende delas.
- Express 4 não captura rejeições de handlers `async`: use `asyncHandler` (T10).

---

## T07 · Escritas soltas → transação

**Corrige:** AP-09 · **Contrato:** preservado

**Passos**
1. Valide **tudo** antes da primeira escrita.
2. Envolva as escritas relacionadas numa única transação com rollback em qualquer erro.
3. Troque "ler, verificar e depois escrever" por uma escrita condicional quando houver concorrência (`UPDATE ... WHERE estoque >= ?` + checagem de linhas afetadas).

**Python (`sqlite3`) — antes**

```python
cursor.execute("INSERT INTO pedidos (usuario_id, total) VALUES (" + str(usuario_id) + ", " + str(total) + ")")
pedido_id = cursor.lastrowid
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - " + str(item["quantidade"]) + " ...")
db.commit()
```

**Python (`sqlite3`) — depois**

```python
from src.errors import ValidationError


def criar(self, usuario_id, itens, total):
    conn = self._database.connection()
    with conn:  # COMMIT ao sair do bloco; ROLLBACK se uma exceção escapar
        pedido_id = conn.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        ).lastrowid
        for item in itens:
            conn.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                "VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
            )
            atualizado = conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            ).rowcount
            if atualizado == 0:
                raise ValidationError(f"Estoque insuficiente para o produto {item['produto_id']}")
    return pedido_id
```

**Python (Flask-SQLAlchemy)**

```python
try:
    db.session.add(order)
    db.session.add_all(items)
    db.session.commit()
except Exception:
    db.session.rollback()
    raise
```

**JavaScript — depois**

```js
// src/models/transaction.js
function createTransactionRunner(db) {
  let queue = Promise.resolve();

  return function withTransaction(work) {
    const result = queue.then(async () => {
      await db.run('BEGIN IMMEDIATE');
      try {
        const value = await work(db);
        await db.run('COMMIT');
        return value;
      } catch (err) {
        await db.run('ROLLBACK');
        throw err;
      }
    });
    queue = result.catch(() => {});
    return result;
  };
}

module.exports = { createTransactionRunner };
```

```js
// uso no service
const enrollmentId = await this.withTransaction(async () => {
  const enrollment = await this.enrollmentModel.create({ userId, courseId });
  await this.paymentModel.create({ enrollmentId: enrollment, amount: course.price, status: 'PAID' });
  await this.auditModel.log(`Checkout curso ${courseId} por ${userId}`);
  return enrollment;
});
```

**Armadilhas**
- `with conn:` do `sqlite3` faz commit/rollback, mas **não fecha** a conexão.
- Em Flask-SQLAlchemy a sessão inicia transação sozinha na primeira consulta; `with db.session.begin():` depois de uma consulta na mesma requisição lança "A transaction is already begun". Prefira `commit`/`rollback` explícitos.
- Com uma única conexão compartilhada em Node, instruções de outras requisições podem cair dentro da transação aberta. A fila do exemplo serializa as transações; todas as escritas relacionadas devem passar por ela.

---

## T08 · N+1 → JOIN, eager loading ou agregação

**Corrige:** AP-13 · **Contrato:** preservado

**Passos**
1. Identifique o laço e a consulta interna.
2. Traga os dados relacionados numa consulta (JOIN) ou em lote (`WHERE id IN (...)`), e agrupe em memória.
3. Contagens por categoria/status viram `GROUP BY`.
4. Reproduza os valores de fallback do original (`"Desconhecido"`, `0`, `None`) no SQL (`COALESCE`) ou no agrupamento.

**Python (SQL) — antes**

```python
for row in pedidos:
    itens = db.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"])).fetchall()
    for item in itens:
        prod = db.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"])).fetchone()
```

**Python (SQL) — depois**

```python
def listar_com_itens(self):
    rows = self._database.connection().execute(
        """
        SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
               i.produto_id, i.quantidade, i.preco_unitario,
               COALESCE(pr.nome, 'Desconhecido') AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = i.produto_id
        ORDER BY p.id, i.id
        """
    ).fetchall()

    pedidos = {}
    for row in rows:
        pedido = pedidos.setdefault(row["id"], {
            "id": row["id"], "usuario_id": row["usuario_id"], "status": row["status"],
            "total": row["total"], "criado_em": row["criado_em"], "itens": [],
        })
        if row["produto_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"], "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"], "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())
```

**Python (SQLAlchemy)**

```python
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

tasks = db.session.execute(
    select(Task).options(joinedload(Task.user), joinedload(Task.category))
).scalars().all()

counts_by_status = dict(db.session.execute(
    select(Task.status, func.count(Task.id)).group_by(Task.status)
).all())

tasks_per_category = db.session.execute(
    select(Category, func.count(Task.id))
    .outerjoin(Task, Task.category_id == Category.id)
    .group_by(Category.id)
).all()
```

**JavaScript — antes**

```js
courses.forEach((c) => {
  db.all('SELECT * FROM enrollments WHERE course_id = ?', [c.id], (err, enrollments) => {
    enrollments.forEach((enr) => {
      db.get('SELECT name FROM users WHERE id = ?', [enr.user_id], (err, user) => {
        db.get('SELECT amount, status FROM payments WHERE enrollment_id = ?', [enr.id], (err, payment) => {
          /* acumula e usa contadores para saber quando responder */
        });
      });
    });
  });
});
```

**JavaScript — depois**

```js
// src/models/report.model.js
class ReportModel {
  constructor(db) {
    this.db = db;
  }

  async financialReport() {
    const rows = await this.db.all(`
      SELECT c.id AS course_id, c.title, e.id AS enrollment_id,
             u.name AS student, p.amount, p.status
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u ON u.id = e.user_id
      LEFT JOIN payments p ON p.enrollment_id = e.id
      ORDER BY c.id, e.id
    `);

    const report = new Map();
    for (const row of rows) {
      if (!report.has(row.course_id)) {
        report.set(row.course_id, { course: row.title, revenue: 0, students: [] });
      }
      if (row.enrollment_id == null) continue;
      const entry = report.get(row.course_id);
      if (row.status === 'PAID') entry.revenue += row.amount;
      entry.students.push({ student: row.student || 'Unknown', paid: row.amount || 0 });
    }
    return [...report.values()];
  }
}

module.exports = ReportModel;
```

**Armadilhas**
- JOIN com relação 1:N multiplica linhas. Confira a cardinalidade que o original assumia: um `db.get`/`fetchone` por item pegava **só a primeira** linha relacionada.
- `LEFT JOIN` preserva itens sem relacionamento (curso sem matrícula, pedido sem itens); `INNER JOIN` os descarta silenciosamente.
- A ordem dos itens pode mudar. O smoke test não compara ordem, mas clientes podem depender dela: use `ORDER BY` que reproduza a ordem original quando ela era determinística.

---

## T09 · Validação inline → validador reutilizável

**Corrige:** AP-14 · **Contrato:** preservado

**Passos**
1. Extraia as regras duplicadas para um validador por entidade, com modo de criação e de atualização quando as regras diferirem.
2. Mantenha **as mesmas mensagens** e **a mesma ordem** de verificação do original.
3. O validador lança `ValidationError`; o middleware central devolve o status e o corpo de erro que o projeto já usa.
4. Converta tipos com tratamento (`int("abc")` não pode virar 500).
5. Use biblioteca de schema (marshmallow, pydantic, joi, zod) só se já estiver declarada — e só se as mensagens puderem ser preservadas.

**Python — antes**

```python
def criar_produto():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    if "nome" not in dados:
        return jsonify({"erro": "Nome é obrigatório"}), 400
    if dados["preco"] < 0:
        return jsonify({"erro": "Preço não pode ser negativo"}), 400

def atualizar_produto(id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    if "nome" not in dados:
        return jsonify({"erro": "Nome é obrigatório"}), 400
    # ... mesma lista, copiada
```

**Python — depois**

```python
# src/controllers/validators.py
from src.errors import ValidationError

OBRIGATORIOS_PRODUTO = (
    ("nome", "Nome é obrigatório"),
    ("preco", "Preço é obrigatório"),
    ("estoque", "Estoque é obrigatório"),
)


def validar_produto(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    for campo, mensagem in OBRIGATORIOS_PRODUTO:
        if campo not in dados:
            raise ValidationError(mensagem)
    if dados["preco"] < 0:
        raise ValidationError("Preço não pode ser negativo")
    if dados["estoque"] < 0:
        raise ValidationError("Estoque não pode ser negativo")
    return {
        "nome": dados["nome"],
        "descricao": dados.get("descricao", ""),
        "preco": dados["preco"],
        "estoque": dados["estoque"],
        "categoria": dados.get("categoria", "geral"),
    }
```

**JavaScript — antes**

```js
const u = req.body.usr;
const e = req.body.eml;
const cid = req.body.c_id;
const cc = req.body.card;
if (!u || !e || !cid || !cc) return res.status(400).send('Bad Request');
```

**JavaScript — depois**

```js
// src/controllers/validators.js
const { ValidationError } = require('../errors');

// Traduz as chaves públicas (contrato) para nomes internos num único lugar.
function parseCheckout(body = {}) {
  const input = {
    name: body.usr,
    email: body.eml,
    password: body.pwd,
    courseId: body.c_id,
    card: body.card,
  };
  if (!input.name || !input.email || !input.courseId || !input.card) {
    throw new ValidationError('Bad Request');
  }
  return input;
}

module.exports = { parseCheckout };
```

**Armadilhas**
- Um validador "melhor" que rejeita o que o original aceitava muda status code: só endureça regras quando o original deixava passar algo que causa erro 500 ou corrompe dados, e registre.
- Regras que o original aplicava só na criação não passam a valer na atualização (e vice-versa) sem registro.

---

## T10 · `try/except` por handler → error handler central

**Corrige:** AP-15 · **Contrato:** preservado

**Passos**
1. Defina erros de domínio com status associado (`errors.py` / `errors.js`).
2. Registre um handler central que traduz erros de domínio no **formato de erro que o projeto já usa** (`{"erro": ...}`, `{"error": ...}` ou texto).
3. Erros inesperados: logue com stack trace e responda uma mensagem genérica, sem `str(e)`.
4. Remova os `try/except` repetidos dos handlers.

**Python (Flask) — antes**

```python
def buscar_produto(id):
    try:
        produto = models.get_produto_por_id(id)
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

**Python (Flask) — depois**

```python
# src/middlewares/error_handler.py
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return err  # 404 de rota inexistente, 405 etc. seguem com o comportamento nativo

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
```

```python
# controller, sem try/except
def mostrar(self, produto_id):
    return jsonify({"dados": self._service.buscar(produto_id), "sucesso": True}), 200
```

**JavaScript (Express) — depois**

```js
// src/errors.js
class AppError extends Error {
  constructor(message, statusCode = 500) {
    super(message);
    this.statusCode = statusCode;
  }
}
class NotFoundError extends AppError {
  constructor(message) { super(message, 404); }
}
class ValidationError extends AppError {
  constructor(message) { super(message, 400); }
}

module.exports = { AppError, NotFoundError, ValidationError };
```

```js
// src/middlewares/asyncHandler.js
module.exports = (handler) => (req, res, next) =>
  Promise.resolve(handler(req, res, next)).catch(next);
```

```js
// src/middlewares/errorHandler.js
const { AppError } = require('../errors');

// Express reconhece middleware de erro pelos 4 parâmetros.
module.exports = function errorHandler(err, req, res, next) {
  if (res.headersSent) return next(err);
  if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
  const status = err.statusCode || err.status;  // ex.: JSON malformado no express.json() → 400
  if (status && status < 500) return res.status(status).send(err.message);
  console.error(err);
  return res.status(500).send('Erro interno do servidor');
};
```

**Armadilhas**
- `@app.errorhandler(Exception)` sozinho captura também `HTTPException` e transforma 404/405 em 500. O handler de `HTTPException` evita isso.
- No Flask 3, `request.get_json()` com Content-Type errado lança 415. Se o original transformava isso em 500 e o baseline registrou 500, preserve o status (use `get_json(silent=True)` e deixe o validador decidir) e recomende a correção no relatório.
- O corpo de erro segue o formato do projeto: `send(texto)` continua texto, `{"error": ...}` continua com a mesma chave.
- Express 4 não repassa rejeições de handlers `async` ao middleware: sem `asyncHandler`, a requisição fica pendurada.

---

## T11 · Estado global e acoplamento → factory + injeção de dependência

**Corrige:** AP-08, AP-11 · **Contrato:** preservado

**Passos**
1. Troque variáveis de módulo mutáveis por objetos criados no composition root.
2. Conexão com banco: uma por requisição/contexto (Flask) ou um adaptador único criado no boot e injetado (Node).
3. Integrações externas (SMTP, gateway, cache) recebem configuração pelo construtor e são injetadas nos services.
4. O composition root é o **único** lugar que conhece as implementações concretas.

**Python — antes**

```python
# database.py
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```

**Python — depois**

```python
# src/models/database.py
import sqlite3

from flask import g


class Database:
    def __init__(self, path):
        self._path = path

    def connection(self):
        if "db_connection" not in g:
            g.db_connection = sqlite3.connect(self._path)
            g.db_connection.row_factory = sqlite3.Row
        return g.db_connection

    def close(self, _exc=None):
        conn = g.pop("db_connection", None)
        if conn is not None:
            conn.close()
```

```python
# src/services/notification_service.py — configuração injetada, sem credencial literal
class NotificationService:
    def __init__(self, smtp_settings, smtp_factory):
        self._settings = smtp_settings
        self._smtp_factory = smtp_factory
```

**JavaScript — antes**

```js
// utils.js
let globalCache = {};
let totalRevenue = 0;
module.exports = { globalCache, totalRevenue };
```

**JavaScript — depois**

```js
// src/services/cache.js
class InMemoryCache {
  constructor() {
    this.entries = new Map();
  }

  set(key, value) {
    this.entries.set(key, value);
  }

  get(key) {
    return this.entries.get(key);
  }
}

module.exports = InMemoryCache;
```

```js
// src/app.js — composition root
const cache = new InMemoryCache();
const checkoutService = new CheckoutService({ db, cache, paymentGateway: new FakePaymentGateway() });
```

**Armadilhas**
- **Extensões projetadas para init tardio** (`db = SQLAlchemy()` + `db.init_app(app)`) não são estado global problemático: mantenha.
- **Seed no boot:** se o original populava o banco na primeira conexão, execute isso uma vez na factory, dentro de `app.app_context()`, e não a cada requisição.
- **Uma conexão por requisição com `g`** exige contexto de aplicação: scripts fora de requisição usam `with app.app_context():`.
- **Primitivo exportado por valor** (`totalRevenue`) nunca foi atualizado de fato. Se ninguém lê o valor, remova (T16) em vez de "consertar".

---

## T12 · API deprecated → equivalente moderno

**Corrige:** AP-19 · **Contrato:** preservado

**Passos**
1. Troque cada uso pela alternativa da tabela do catálogo (AP-19).
2. Confirme que os avisos sumiram: `python -W default ...` / `node --trace-deprecation ...`.
3. Dependências deprecated transitivas: `npm ls <pacote>` mostra a dependência direta responsável; atualize-a para uma versão que não as puxe, se existir e o smoke test continuar idêntico. Caso contrário, registre como finding parcial.

**Python — antes**

```python
created_at = db.Column(db.DateTime, default=datetime.utcnow)

task = Task.query.get(task_id)
tasks = Task.query.filter_by(user_id=user_id).all()
total = Task.query.count()
```

**Python — depois**

```python
# src/models/clock.py
from datetime import datetime, timezone


def utcnow():
    """UTC atual sem tzinfo, compatível com colunas DateTime sem timezone."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

```python
from sqlalchemy import func, select

created_at = db.Column(db.DateTime, default=utcnow)

task = db.session.get(Task, task_id)
tasks = db.session.execute(select(Task).filter_by(user_id=user_id)).scalars().all()
total = db.session.scalar(select(func.count()).select_from(Task))
```

**JavaScript — antes**

```js
const buf = new Buffer(text);
app.del('/api/items/:id', handler);
res.send(404);
app.use(bodyParser.json());
```

**JavaScript — depois**

```js
const buf = Buffer.from(text);
app.delete('/api/items/:id', handler);
res.sendStatus(404);
app.use(express.json());
```

**Armadilhas**
- **Naive × aware:** trocar `datetime.utcnow()` por `datetime.now(timezone.utc)` puro quebra comparações com colunas sem timezone (`TypeError: can't compare offset-naive and offset-aware datetimes`) e muda o texto das datas nas respostas (`+00:00`). O helper `utcnow()` evita os dois problemas.
- **Default de coluna** recebe a função (`default=utcnow`), não o resultado da chamada.
- **Upgrade de versão maior** de framework ou driver nativo (Express 4 → 5, troca de `sqlite3`) só entra se o smoke test ficar idêntico; senão, finding parcial com a recomendação.

---

## T13 · Serialização solta → serializer com campos explícitos

**Corrige:** AP-03, AP-24 · **Contrato:** preservado para campos públicos; **remover campo sensível é Breaking Change** (declare no relatório)

**Passos**
1. Um serializer por entidade, com lista explícita (whitelist) de campos públicos.
2. Todas as respostas daquela entidade passam pelo serializer; apague as montagens manuais duplicadas.
3. Campos sensíveis (senha, hash, token, segredo) não entram na whitelist.
4. Mantenha nome, tipo e formato de cada campo público.

**Python — antes**

```python
def to_dict(self):
    return {
        "id": self.id,
        "name": self.name,
        "email": self.email,
        "password": self.password,
        "created_at": str(self.created_at),
    }
```

**Python — depois**

```python
# src/views/serializers.py
def serialize_user(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created_at": str(user.created_at),
    }


def serialize_users(users):
    return [serialize_user(user) for user in users]
```

**JavaScript — depois**

```js
// src/views/serializers.js
const serializeUser = ({ id, name, email }) => ({ id, name, email });

module.exports = { serializeUser };
```

**Armadilhas**
- Um endpoint de health/debug que devolvia configuração interna mantém os campos não sensíveis (`status`, `database`) e perde os sensíveis — declare os removidos.
- `str(datetime)` e `datetime.isoformat()` produzem textos diferentes: mantenha o formato do original.

---

## T14 · Endpoint privilegiado → remover ou proteger

**Corrige:** AP-05 · **Contrato:** **Breaking Change** — declare sempre

Aplica-se ao AP-05 em CRITICAL **e** em HIGH (regra 3 do `SKILL.md`). O finding só fica corrigido quando nenhuma rota destrutiva ou privilegiada responde a um cliente anônimo.

| Situação | Ação |
|---|---|
| Executa SQL ou código enviado pelo cliente | **Remover** da API. Nenhuma proteção torna isso aceitável. |
| Destruição em massa (reset de banco) | **Remover** da API; se for útil em desenvolvimento, oferecer como comando de linha de comando. |
| Leitura ou gestão administrativa (relatórios financeiros, remoção de usuários) sem login no projeto | **Proteger** com middleware de credencial administrativa lida da configuração (`X-Admin-Token`). |
| Token de autenticação falso (o projeto tem login) | Duas partes, ambas obrigatórias: (a) emitir token assinado com biblioteca já disponível (`itsdangerous` vem com o Flask; `crypto.createHmac` no Node), mantendo a mesma chave JSON na resposta de login; (b) **exigir** esse token (`Authorization: Bearer <token>`) nas rotas destrutivas — no mínimo todo `DELETE` — e nas administrativas. Cada rota protegida é um `BC-xx` declarado. Só (a) deixa o finding **parcial**, o que é proibido para finding de segurança. |

**Python — depois (proteção)**

```python
# src/middlewares/admin_auth.py
import hmac
from functools import wraps

from flask import current_app, jsonify, request


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN") or ""
        provided = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(provided, expected):
            return jsonify({"erro": "Não autorizado"}), 401
        return view(*args, **kwargs)
    return wrapper
```

**Python — depois (token do login exigido nas rotas destrutivas)**

```python
# services/auth_service.py
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


class AuthService:
    def __init__(self, secret_key, max_age_seconds=86400):
        self._serializer = URLSafeTimedSerializer(secret_key, salt="auth-token")
        self._max_age = max_age_seconds

    def issue_token(self, user):
        return self._serializer.dumps({"user_id": user.id})

    def verify_token(self, token):
        try:
            return self._serializer.loads(token, max_age=self._max_age)
        except (BadSignature, SignatureExpired):
            return None
```

```python
# middlewares/auth.py
from functools import wraps

from flask import g, jsonify, request


def require_auth(auth_service):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            scheme, _, token = request.headers.get("Authorization", "").partition(" ")
            payload = auth_service.verify_token(token) if scheme == "Bearer" and token else None
            if payload is None:
                return jsonify({"error": "Não autorizado"}), 401
            g.user_id = payload["user_id"]
            return view(*args, **kwargs)
        return wrapper
    return decorator
```

```python
# routes/task_routes.py
bp.add_url_rule(
    "/tasks/<int:task_id>", "delete_task", require_auth(auth_service)(controller.delete), methods=["DELETE"]
)
```

Use a chave de erro que o projeto já usa (`error`, `erro`, texto puro).

**JavaScript — depois (proteção)**

```js
// src/middlewares/requireAdmin.js
const crypto = require('node:crypto');

module.exports = (config) => (req, res, next) => {
  const expected = Buffer.from(config.adminToken || '');
  const provided = Buffer.from(req.get('X-Admin-Token') || '');
  const valid = expected.length > 0
    && expected.length === provided.length
    && crypto.timingSafeEqual(expected, provided);
  if (!valid) return res.status(401).send('Não autorizado');
  return next();
};
```

**Armadilhas**
- Sem `ADMIN_TOKEN` configurado, a rota protegida recusa tudo (falha fechada). Nunca libere quando a variável estiver vazia.
- Para o smoke test continuar exercitando a rota, `smoke.sh` envia `X-Admin-Token: ${ADMIN_TOKEN}` nas duas execuções (o original ignora o header) e a validação sobe a aplicação com `ADMIN_TOKEN` definido — ver protocolo, seção A5.
- Com token de login, `smoke.sh` faz o `POST /login`, guarda o `token` da resposta e o envia como `Authorization: Bearer` nas rotas protegidas; o original ignora o header. Inclua uma chamada anônima a cada rota protegida com id inexistente: 404 no baseline, 401 depois — é a divergência declarada que prova a proteção.
- Token de login sem `max_age` vale para sempre; não use a mesma `SECRET_KEY` aleatória por processo se houver mais de um worker (tokens emitidos num não validam no outro) — leia-a da configuração (T02).

---

## T15 · Remoção sem integridade → cascade explícito

**Corrige:** AP-18 · **Contrato:** preservado (status e corpo); mensagens que descreviam o bug podem mudar

**Passos**
1. Decida a regra de domínio: remover dependentes em cascata ou impedir a remoção enquanto houver dependentes. Na dúvida, a que o original **pretendia**.
2. Implemente num único ponto (model ou service), dentro de transação (T07).
3. Respeite o erro do driver: remoção que falha não responde sucesso.

**SQL (SQLite) — depois**

```sql
PRAGMA foreign_keys = ON;  -- por conexão

CREATE TABLE IF NOT EXISTS enrollments (
  id INTEGER PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  course_id INTEGER REFERENCES courses(id)
);
```

**Python (SQLAlchemy) — antes**

```python
tasks = Task.query.filter_by(user_id=user_id).all()
for t in tasks:
    db.session.delete(t)
db.session.delete(user)
db.session.commit()
```

**Python (SQLAlchemy) — depois**

```python
# models/task.py
user = db.relationship("User", backref=db.backref("tasks", cascade="all, delete-orphan"))
```

```python
# service
db.session.delete(user)
db.session.commit()
```

**JavaScript — depois**

```js
// src/models/user.model.js
class UserModel {
  constructor({ withTransaction }) {
    this.withTransaction = withTransaction;
  }

  async deleteById(userId) {
    return this.withTransaction(async (db) => {
      await db.run(
        'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
        [userId],
      );
      await db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
      const { changes } = await db.run('DELETE FROM users WHERE id = ?', [userId]);
      return changes;
    });
  }
}

module.exports = UserModel;
```

**Armadilhas**
- SQLite não permite adicionar `FOREIGN KEY` a tabela existente com `ALTER TABLE`. Em banco já criado, prefira o cascade explícito no código.
- Se o original respondia 200 mesmo quando o registro não existia, mantenha o status. Anote a recomendação de 404 no relatório.

---

## T16 · Higiene: logging, constantes, código morto e nomes

**Corrige:** AP-20, AP-21, AP-22, AP-23 · **Contrato:** preservado

**Logging — Python**

```python
# antes
print("Produto criado com ID: " + str(id))

# depois
import logging

logger = logging.getLogger(__name__)
logger.info("Produto criado", extra={"produto_id": produto_id})
```

**Logging — JavaScript**

```js
// src/config/logger.js — ponto único, fácil de trocar por pino/winston
const logger = {
  info: (message, meta = {}) => console.info(JSON.stringify({ level: 'info', message, ...meta })),
  error: (message, meta = {}) => console.error(JSON.stringify({ level: 'error', message, ...meta })),
};

module.exports = logger;
```

**Constantes nomeadas**

```python
# antes (repetido em vários arquivos)
if status not in ['pending', 'in_progress', 'done', 'cancelled']:
    raise ValidationError("Status inválido")

# depois (definido uma vez, importado onde é usado)
TASK_STATUSES = ("pending", "in_progress", "done", "cancelled")
if status not in TASK_STATUSES:
    raise ValidationError("Status inválido")
```

**Código verboso**

```python
# antes
def is_admin(self):
    if self.role == 'admin':
        return True
    else:
        return False

# depois
def is_admin(self):
    return self.role == "admin"
```

**Código morto**
- Imports não usados: remova depois de conferir com `grep` que o nome não aparece no arquivo.
- Funções nunca chamadas: remova; se contiverem lógica útil que o código vivo duplica, use-as como base da T09 antes de remover a cópia.
- Dependências declaradas e não importadas: remova do manifesto **só** se nenhum script do projeto as usar.

**Nomes**
- Renomeie identificadores internos (`u` → `name`, `cc` → `card`).
- **Não** renomeie chaves JSON públicas, paths ou nomes de parâmetros de query.

**Armadilhas**
- Mensagens impressas por scripts de linha de comando (seed) são saída para o operador: `print` ali é aceitável.
- Logs não podem conter senha, token, cartão ou segredo (AP-03).

---

## T17 · Listagem completa → paginação opcional

**Corrige:** AP-17 · **Contrato:** preservado

Paginação obrigatória muda o conteúdo da resposta. A forma segura é **opt-in**: sem parâmetros, o endpoint responde como antes; com `limit`/`offset`, pagina.

**Python — depois**

```python
# model
def listar(self, limit=None, offset=0):
    query = "SELECT id, nome, preco FROM produtos ORDER BY id"
    params = []
    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params = [limit, offset]
    return [dict(row) for row in self._database.connection().execute(query, params).fetchall()]
```

```python
# controller
from src.errors import ValidationError

MAX_PAGE_SIZE = 100


def _pagination_args(args):
    if "limit" not in args:
        return None, 0
    try:
        limit = min(int(args["limit"]), MAX_PAGE_SIZE)
        offset = int(args.get("offset", 0))
    except ValueError:
        raise ValidationError("Parâmetros de paginação inválidos")
    return limit, offset
```

**JavaScript — depois**

```js
// src/models/course.model.js
class CourseModel {
  constructor(db) {
    this.db = db;
  }

  async list({ limit, offset = 0 } = {}) {
    if (limit === undefined) return this.db.all('SELECT id, title FROM courses ORDER BY id');
    return this.db.all('SELECT id, title FROM courses ORDER BY id LIMIT ? OFFSET ?', [limit, offset]);
  }
}

module.exports = CourseModel;
```

**Armadilhas**
- Adicionar `ORDER BY` onde não havia pode mudar a ordem: use a chave primária, que reproduz a ordem de inserção típica do SQLite.
- O envelope da resposta não ganha campos novos (`total`, `page`) sem necessidade.
