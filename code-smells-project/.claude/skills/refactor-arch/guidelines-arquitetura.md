# Guidelines de Arquitetura — MVC Alvo

Referência da **Fase 3**. Define as camadas da arquitetura-alvo, o que cada uma pode e não pode conter, a regra de dependência entre elas e como chegar lá a partir de pontos de partida diferentes.

---

## 1. MVC aplicado a uma API HTTP

Numa API que responde JSON não há template HTML: a **View** é a representação pública da resposta — o mapeamento de rotas e a serialização das entidades. O MVC clássico tem três letras, mas a regra de negócio precisa de uma casa que não seja o controller (regra pesada em controller é finding HIGH, AP-07). Por isso a arquitetura-alvo tem uma camada de **services** entre controllers e models.

| Camada | Diretório | Responsabilidade | Pode depender de |
|---|---|---|---|
| **Config** | `config/` | Ler o ambiente, aplicar defaults seguros, falhar cedo quando faltar configuração obrigatória em produção | Nada do projeto |
| **Models** | `models/` | Entidades, acesso a dados (repositórios), transações, schema e mapeamento linha → entidade | Driver/ORM; configuração recebida por injeção |
| **Services** | `services/` | Regras de negócio, orquestração de vários models, integrações externas (e-mail, pagamento) | Models, erros de domínio |
| **Controllers** | `controllers/` | Traduzir requisição → chamada de serviço → resposta; extrair e validar entrada; escolher o status code | Services, validadores, serializers |
| **Views** | `views/` (ou `routes/` já existente) | Mapear método + path → controller; serializar entidades para o formato público | Controllers; serializers leem atributos de entidades |
| **Middlewares** | `middlewares/` | Preocupações transversais: tratamento de erros, autenticação, log de requisição | Config, erros de domínio |
| **Composition root** | `app.py` / `src/app.js` | Criar as dependências concretas, injetá-las, registrar rotas e middlewares, expor o entry point | Todas |

Erros de domínio (`AppError`, `NotFoundError`, `ValidationError`) ficam num módulo neutro (`errors.py` / `errors.js`) importado por services, controllers e middlewares.

---

## 2. Regra de dependência

```
cliente HTTP
    │
    ▼
views/routes ──► controllers ──► services ──► models ──► banco de dados
    │                │               │
    └────────────────┴───────────────┴──► errors (módulo neutro)

middlewares (erros, auth) envolvem o fluxo inteiro
composition root cria e conecta todas as peças
```

As setas apontam num único sentido. Uma camada **nunca** importa uma camada acima dela:

- models não conhecem requisição, resposta nem status code;
- services não recebem objetos de requisição nem devolvem respostas HTTP;
- controllers não escrevem SQL nem chamam o ORM diretamente;
- views não contêm regra de negócio.

---

## 3. O que cada camada não pode conter

Estes greps também são usados na varredura final da validação (protocolo, Parte B). Ajuste os caminhos à estrutura do projeto.

| Camada | Proibido | Verificação |
|---|---|---|
| models | Objeto de requisição/resposta, status HTTP, dicionários de erro HTTP, envio de e-mail, `print`/`console.log` | `grep -rnE "from flask import.*(request\|jsonify)\|\breq\.\|\bres\.\|status_code\|print\(\|console\.log" models/` |
| services | Objeto de requisição/resposta, SQL literal, montagem de resposta HTTP | `grep -rnE "request\.\|jsonify\|\breq\.\|\bres\.\|SELECT \|INSERT \|UPDATE \|DELETE " services/` |
| controllers | SQL, chamadas de ORM, cálculos de domínio, instanciação de infraestrutura | `grep -rnE "execute\(\|\.query\b\|db\.session\|SELECT \|INSERT \|sqlite3\.\|smtplib" controllers/` |
| views/routes | Regra de negócio, SQL, ORM, validação de domínio | `grep -rnE "execute\(\|\.query\b\|db\.session\|SELECT " views/ routes/` |
| config | Segredos literais, regra de negócio | catálogo, AP-02 |
| qualquer camada | Estado global mutável, segredos literais | catálogo, AP-02 e AP-08 |

---

## 4. Convenções

- **Um arquivo por domínio em cada camada.** Siga a convenção de nomes que o projeto já usa; na ausência dela, `<dominio>_<camada>.py` em Python (`produto_model.py`, `produto_controller.py`) e `<dominio>.<camada>.js` em JavaScript (`order.model.js`, `order.controller.js`).
- **Idioma.** Identificadores seguem o idioma já usado no código do projeto.
- **Injeção de dependência.** Dependências entram pelo construtor ou por parâmetros de factory; só o composition root instancia banco, clientes SMTP e gateways.
- **Configuração.** Um único objeto de configuração, criado uma vez no composition root. Nenhuma leitura de `os.environ` ou `process.env` espalhada pelo código.
- **Serialização.** Uma função ou método por entidade, com lista explícita de campos públicos (T13).
- **Erros.** Services lançam erros de domínio; o middleware central os traduz para HTTP (T10). Controllers não precisam de `try/except` para erros esperados.
- **Contrato público intocado.** Paths, métodos, nomes de campos JSON e mensagens de erro continuam os mesmos, mesmo quando mal nomeados. Traduza nomes públicos para nomes internos num único ponto (controller ou validador).

---

## 5. Ponto de partida → estrutura-alvo

Use a classificação da Fase 1 (`analise-de-projeto.md`, seção 8.2) para escolher o caminho.

### 5.1 Monolito ou God Class

Crie a estrutura canônica completa.

- Se o projeto **já tem** `src/`, as camadas vão dentro dele.
- Se o projeto é **flat** (código na raiz), crie as camadas num pacote `src/` e mantenha o entry point documentado na raiz como um invólucro fino que chama a factory. Isso evita colisão entre pacotes novos e módulos antigos com o mesmo nome (`models/` e `models.py`) e preserva o comando de execução.

**Python (projeto flat):**

```
<raiz>/
├── app.py                         # entry point documentado — só chama create_app() e roda
├── requirements.txt
└── src/
    ├── __init__.py
    ├── app.py                     # composition root: create_app()
    ├── errors.py                  # erros de domínio
    ├── config/
    │   ├── __init__.py
    │   └── settings.py
    ├── models/
    │   ├── __init__.py
    │   ├── database.py            # conexão, schema, seed automático (se o original fazia)
    │   └── <dominio>_model.py
    ├── services/
    │   ├── __init__.py
    │   └── <dominio>_service.py
    ├── controllers/
    │   ├── __init__.py
    │   └── <dominio>_controller.py
    ├── views/
    │   ├── __init__.py
    │   ├── routes.py              # registro de rotas → controllers
    │   └── serializers.py
    └── middlewares/
        ├── __init__.py
        └── error_handler.py
```

**JavaScript (projeto com `src/`):**

```
<raiz>/
├── package.json                   # scripts.start e main continuam válidos
└── src/
    ├── app.js                     # composition root + listen quando executado diretamente
    ├── errors.js
    ├── config/index.js
    ├── models/
    │   ├── database.js            # conexão promisificada, schema, seed
    │   └── <dominio>.model.js
    ├── services/<dominio>.service.js
    ├── controllers/<dominio>.controller.js
    ├── views/routes.js
    └── middlewares/errorHandler.js
```

### 5.2 Camadas parciais

Evolua no lugar. Não mova pastas que já cumprem um papel só para bater com os nomes canônicos.

| Pasta existente | Papel na arquitetura-alvo | O que fazer |
|---|---|---|
| `routes/` | Views | Manter; esvaziar os handlers para que só mapeiem rota → controller |
| `models/` | Models | Manter; receber consultas que hoje estão nas rotas (métodos de classe ou repositório) |
| `services/` | Services | Manter; receber regras hoje nas rotas; integrações recebem configuração por injeção |
| `utils/` | — | Distribuir: validação → validadores usados pelos controllers; regra de domínio → services ou models; constantes → config ou módulo de constantes do domínio. Remover se esvaziar |
| — | Controllers | Criar `controllers/` |
| — | Config | Criar `config/` |
| — | Middlewares | Criar `middlewares/` |

Preserve os nomes importados por scripts auxiliares. Se `seed.py` faz `from app import app, db`, o `app.py` refatorado continua expondo `app` e `db`, por exemplo com `app = create_app()` no nível do módulo.

Na saída da Fase 3, declare o mapeamento — ex.: "`routes/` cumpre o papel de Views".

### 5.3 Já em camadas

Não reestruture. Aplique apenas as transformações dos findings dentro das camadas existentes.

---

## 6. Fatia vertical de referência

Uma rota completa atravessando todas as camadas. Serve de molde para as demais.

**Python / Flask**

```python
# src/errors.py
class AppError(Exception):
    status_code = 500

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class ValidationError(AppError):
    status_code = 400
```

```python
# src/models/item_model.py
class ItemModel:
    def __init__(self, database):
        self._database = database

    def find_by_id(self, item_id):
        row = self._database.connection().execute(
            "SELECT id, name, price FROM items WHERE id = ?", (item_id,)
        ).fetchone()
        return dict(row) if row else None
```

```python
# src/services/item_service.py
from src.errors import NotFoundError


class ItemService:
    def __init__(self, item_model):
        self._items = item_model

    def get(self, item_id):
        item = self._items.find_by_id(item_id)
        if item is None:
            raise NotFoundError("Item não encontrado")
        return item
```

```python
# src/controllers/item_controller.py
from flask import jsonify

from src.views.serializers import serialize_item


class ItemController:
    def __init__(self, item_service):
        self._service = item_service

    def show(self, item_id):
        item = self._service.get(item_id)
        return jsonify({"data": serialize_item(item)}), 200
```

```python
# src/views/routes.py
from flask import Blueprint


def create_routes(item_controller):
    bp = Blueprint("api", __name__)
    bp.add_url_rule("/items/<int:item_id>", "show_item", item_controller.show, methods=["GET"])
    return bp
```

```python
# src/app.py — composition root
from flask import Flask

from src.config.settings import Settings
from src.controllers.item_controller import ItemController
from src.middlewares.error_handler import register_error_handlers
from src.models.database import Database
from src.models.item_model import ItemModel
from src.services.item_service import ItemService
from src.views.routes import create_routes


def create_app(settings=None):
    settings = settings or Settings.from_env()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key

    database = Database(settings.database_path)
    app.teardown_appcontext(database.close)

    item_controller = ItemController(ItemService(ItemModel(database)))
    app.register_blueprint(create_routes(item_controller))
    register_error_handlers(app)
    return app
```

```python
# app.py (raiz) — entry point documentado
from src.app import create_app
from src.config.settings import Settings

settings = Settings.from_env()
app = create_app(settings)

if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
```

**JavaScript / Express**

```js
// src/models/item.model.js
class ItemModel {
  constructor(db) {
    this.db = db;
  }

  findById(id) {
    return this.db.get('SELECT id, name, price FROM items WHERE id = ?', [id]);
  }
}

module.exports = ItemModel;
```

```js
// src/services/item.service.js
const { NotFoundError } = require('../errors');

class ItemService {
  constructor(itemModel) {
    this.itemModel = itemModel;
  }

  async get(id) {
    const item = await this.itemModel.findById(id);
    if (!item) throw new NotFoundError('Item não encontrado');
    return item;
  }
}

module.exports = ItemService;
```

```js
// src/controllers/item.controller.js
class ItemController {
  constructor(itemService) {
    this.itemService = itemService;
  }

  show = async (req, res) => {
    const item = await this.itemService.get(Number(req.params.id));
    res.status(200).json(item);
  };
}

module.exports = ItemController;
```

```js
// src/views/routes.js
const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

function buildRoutes({ itemController }) {
  const router = express.Router();
  router.get('/items/:id', asyncHandler(itemController.show));
  return router;
}

module.exports = buildRoutes;
```

```js
// src/app.js — composition root e entry point
const express = require('express');
const config = require('./config');
const { openDatabase } = require('./models/database');
const ItemModel = require('./models/item.model');
const ItemService = require('./services/item.service');
const ItemController = require('./controllers/item.controller');
const buildRoutes = require('./views/routes');
const errorHandler = require('./middlewares/errorHandler');

function createApp({ db }) {
  const itemController = new ItemController(new ItemService(new ItemModel(db)));
  const app = express();
  app.use(express.json());
  app.use(buildRoutes({ itemController }));
  app.use(errorHandler);
  return app;
}

if (require.main === module) {
  const db = openDatabase(config.databaseFile);
  createApp({ db }).listen(config.port, () => {
    console.info(`API ouvindo na porta ${config.port}`);
  });
}

module.exports = createApp;
```

---

## 7. Critérios de pronto da Fase 3

- [ ] Estrutura de diretórios com config, models, views/routes, controllers, middlewares e entry point claros
- [ ] Nenhum segredo literal; configuração centralizada e lida do ambiente
- [ ] Todo acesso a dados está em models
- [ ] Views/routes apenas mapeiam rotas e serializam
- [ ] Controllers finos concentram o fluxo; regras de negócio em services
- [ ] Tratamento de erros centralizado num middleware
- [ ] Comandos documentados de instalação, seed e execução funcionam
- [ ] Greps da seção 3 sem ocorrências (ou falsos positivos justificados)
- [ ] Smoke test idêntico ao baseline, exceto Breaking Changes declarados
