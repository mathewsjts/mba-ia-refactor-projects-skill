# Protocolo de Validação

Referência da **Fase 1** (Parte A — Baseline) e da **Fase 3** (Parte B — Validação).

"Os endpoints continuam respondendo" só é verificável se o comportamento anterior foi registrado **antes** da primeira mudança. Este protocolo congela o contrato HTTP da aplicação original, reexecuta as mesmas requisições depois da refatoração e compara.

## O que é comparado

Para cada requisição do smoke test:

| Elemento | Exemplo |
|---|---|
| Método e path | `GET /produtos/1` |
| Status code | `200` |
| Tipo de corpo | `json:objeto`, `json:lista`, `texto`, `vazio` |
| Estrutura de chaves | todos os caminhos de chave até 4 níveis, unindo os elementos de listas: `dados,dados[].id,dados[].nome,sucesso` |

**Valores não são comparados** — ids, datas e totais variam legitimamente. Uma chave que some ou aparece, um status diferente ou JSON que vira texto é divergência.

## Artefatos

Tudo fica em `.refactor-arch/`, na raiz do projeto:

| Arquivo | Conteúdo |
|---|---|
| `install.log` | Saída da instalação de dependências (evidência para AP-19) |
| `rotas.md` | Inventário de rotas e requisições planejadas |
| `smoke.sh` | Script de replay das requisições |
| `boot-antes.log` / `boot-depois.log` | Saída da aplicação em cada execução |
| `baseline.txt` / `depois.txt` | Resultado do smoke test antes e depois |
| `diff.txt` | `diff -u` entre os dois |
| `db-backup/` | Bancos de arquivo movidos para garantir estado inicial limpo |
| `relatorio-auditoria.md` | Relatório da Fase 2 |
| `validacao.md` | Evidências consolidadas da Fase 3 |

---

## Parte A — Baseline (fim da Fase 1)

### A1. Ambiente

| Stack | Preparação |
|---|---|
| Python | Se existir `.venv/`, use-o. Senão: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>&1 \| tee .refactor-arch/install.log`. Execute sempre com `.venv/bin/python`. |
| Node | Se existir `node_modules/`, use-o. Senão: `npm ci` (com lockfile) ou `npm install`, com saída em `.refactor-arch/install.log`. Se `node_modules/` já existia, rode `npm ls --depth=0` e, para evidência de depreciação, consulte `npm audit`. |
| Outras | O comando de instalação documentado. |

Confira a compatibilidade do runtime (`analise-de-projeto.md`, seção 2). Se a instalação falhar, registre o erro e marque o baseline como não capturado. **Não altere o manifesto na Fase 1.**

### A2. Estado inicial reprodutível

A comparação só vale se as duas execuções partirem do mesmo estado.

| Persistência | Como garantir estado idêntico antes de cada boot |
|---|---|
| SQLite em arquivo | Se o arquivo existir, **mova** para `.refactor-arch/db-backup/<AAAAMMDD-HHMMSS>/` — nunca apague. Localize o arquivo real (Flask-SQLAlchemy 3.x usa `instance/`). |
| SQLite em memória | Nada: cada boot começa limpo. |
| Seed em script separado | Depois de mover o banco, rode o seed documentado antes do boot. |
| Seed automático no boot | Nada além de mover o banco. |
| Banco externo (PostgreSQL, MongoDB…) | Não resete. Pergunte ao usuário por uma instância descartável; sem ela, o smoke test inclui só requisições de leitura e a validação é marcada como parcial. |

### A3. Porta e boot

1. **Descubra a porta** (`analise-de-projeto.md`, seção 6).
2. **Verifique se está livre:**
   ```bash
   lsof -nP -iTCP:<porta> -sTCP:LISTEN
   ```
   Se outro programa ocupa a porta, uma checagem só por `curl` dá falso positivo. Exemplo real: no macOS, o AirPlay Receiver (`ControlCenter`) escuta a porta 5000 e responde `403` com `Server: AirTunes`. Escolha uma porta livre e suba **sem editar código**:

   | Stack | Override de porta sem editar código |
   |---|---|
   | Flask | `.venv/bin/flask --app <modulo> run --port <porta> --no-reload` — não executa o bloco `__main__`; confirme na análise que nada essencial acontece só ali |
   | FastAPI / Uvicorn | `.venv/bin/uvicorn <modulo>:app --port <porta>` |
   | Django | `.venv/bin/python manage.py runserver <porta> --noreload` |
   | Node lendo `process.env.PORT` | `PORT=<porta> npm start` |
   | Porta literal sem override | Não edite na Fase 1: informe o conflito e peça ao usuário para liberar a porta. Sem isso, baseline não capturado. |

   Depois da refatoração, a porta vem da configuração (T02), e o comando documentado aceita `PORT=<porta>`.

3. **Suba em segundo plano**, com log:
   ```bash
   nohup <comando> > .refactor-arch/boot-antes.log 2>&1 &
   ```

4. **Espere a aplicação ficar pronta** sem `sleep` fixo — o `curl` repete até a porta aceitar conexão:
   ```bash
   curl --retry 30 --retry-delay 1 --retry-connrefused -s -o /dev/null \
        -w 'status=%{http_code}\n' 'http://127.0.0.1:<porta><rota GET simples>'
   lsof -nP -iTCP:<porta> -sTCP:LISTEN
   ```
   O processo escutando precisa ser o runtime da aplicação (`python`, `node`…). Se o `curl` esgotar as tentativas, leia `boot-antes.log`.

5. **Modo debug com reloader** (`debug=True` no Flask, `nodemon`) cria processo filho: o PID do comando não é quem escuta a porta. Por isso o encerramento é sempre pela porta (A7).

### A4. Inventário de rotas → `.refactor-arch/rotas.md`

Parta da tabela de rotas da Fase 1 e planeje, para cada rota:

- **caminho feliz** com dados válidos (ids conhecidos do seed ou criados antes no próprio script);
- **não encontrado**, para rotas com id (`/recurso/999999`);
- **entrada inválida**, para rotas de escrita (corpo vazio `{}` ou campo obrigatório ausente).

Os casos de erro são obrigatórios: o tratamento de erros é uma das coisas que a Fase 3 mais altera.

### A5. Gerar `.refactor-arch/smoke.sh`

Copie o modelo e preencha apenas a seção de requisições.

**Regras para as requisições**
- **Ordem:** leituras → criações → atualizações → leituras que dependem das escritas → remoções → operações destrutivas em massa (sempre por último).
- **Paths entre aspas simples.** Shells como o zsh expandem `?` e `*` e abortam o comando.
- Todo corpo JSON é enviado com `Content-Type: application/json` (o modelo já faz isso).
- **Rotas administrativas** enviam `-H "X-Admin-Token: ${ADMIN_TOKEN:-}"` nas duas execuções. O original ignora o header; a versão protegida (T14) o exige.
- **Projeto com login:** logo depois do `call POST '/login'` com credenciais válidas do seed, guarde o token da resposta (`TOKEN="$(token_from_body)"`) e envie `-H "Authorization: Bearer ${TOKEN:-}"` em toda rota destrutiva (`DELETE`) e administrativa, nas duas execuções. O original ignora o header; a versão protegida (T14) o exige.
- **Prova de proteção:** para cada rota que a T14 vai proteger, inclua uma chamada **anônima** com id inexistente (`/recurso/999999`, sem header). No baseline ela responde 404 sem apagar nada; depois, 401 — divergência declarada no `BC-xx` correspondente.

```bash
#!/usr/bin/env bash
# Gerado pela skill refactor-arch.
# Uso: bash .refactor-arch/smoke.sh http://127.0.0.1:<porta>
set -u
BASE_URL="${1:?informe a URL base, ex.: http://127.0.0.1:5000}"
BODY_FILE="$(mktemp)"
trap 'rm -f "$BODY_FILE"' EXIT

# Resume o corpo da resposta: tipo + caminhos de chave (sem valores).
shape() {
  python3 - "$1" <<'PY'
import json
import sys

def walk(value, prefix, depth, out):
    if depth > 4:
        return
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.add(path)
            walk(child, path, depth + 1, out)
    elif isinstance(value, list):
        for item in value:
            walk(item, prefix + "[]", depth + 1, out)

raw = open(sys.argv[1], "rb").read()
if not raw.strip():
    print("vazio")
    sys.exit(0)
try:
    data = json.loads(raw)
except ValueError:
    print("texto")
    sys.exit(0)
if isinstance(data, (dict, list)):
    paths = set()
    walk(data, "", 0, paths)
    kind = "objeto" if isinstance(data, dict) else "lista"
    print("json:" + kind + "{" + ",".join(sorted(paths)) + "}")
else:
    print("json:" + type(data).__name__)
PY
}

# call MÉTODO PATH [CORPO_JSON] [argumentos extras do curl...]
call() {
  local method="$1" path="$2" body="${3:-}"
  if [ "$#" -ge 3 ]; then shift 3; else shift "$#"; fi
  local args=(-s -o "$BODY_FILE" -w '%{http_code}' -X "$method")
  if [ -n "$body" ]; then
    args+=(-H 'Content-Type: application/json' --data "$body")
  fi
  local status
  status="$(curl "${args[@]}" "$@" "$BASE_URL$path")"
  printf '%-7s %-45s %s %s\n' "$method" "$path" "$status" "$(shape "$BODY_FILE")"
}

# Lê o token da última resposta (chave `token` na raiz; ajuste se o login usa outra).
token_from_body() {
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("token", ""))' "$BODY_FILE" 2>/dev/null
}

# ---------------- requisições (a ordem importa) ----------------
call GET    '/health'
call GET    '/recursos'
call GET    '/recursos/1'
call GET    '/recursos/999999'
call GET    '/recursos/busca?q=exemplo'
call POST   '/recursos' '{"nome":"Exemplo","valor":10}'
call POST   '/recursos' '{}'
call PUT    '/recursos/1' '{"nome":"Alterado","valor":20}'
call POST   '/login' '{"email":"admin@exemplo.com","password":"senha-do-seed"}'
TOKEN="$(token_from_body)"
call GET    '/admin/relatorio' '' -H "X-Admin-Token: ${ADMIN_TOKEN:-}"
call DELETE '/recursos/999999'
call DELETE '/recursos/2' '' -H "Authorization: Bearer ${TOKEN:-}"
```

A linha `DELETE '/recursos/999999'` sem header é a prova de proteção; `DELETE '/recursos/2'` com o token é o caminho feliz. Em projeto sem login, remova o bloco do `/login` e o header `Authorization`.

O modelo depende de `bash`, `curl` e `python3`. Sem `python3`, substitua a função `shape` por um equivalente em `node -e` com a mesma saída.

### A6. Capturar o baseline

```bash
bash .refactor-arch/smoke.sh 'http://127.0.0.1:<porta>' | tee .refactor-arch/baseline.txt
```

Revise a saída: status `000` indica que a aplicação caiu no meio do script (veja o log). Linhas com `500` em caminho feliz indicam request mal montado — corrija o request, não a aplicação, e capture de novo a partir de A2.

Se alguma rota tiver resposta não determinística (ordem de callbacks assíncronos, aleatoriedade), capture duas vezes a partir de A2 e marque em `rotas.md` as linhas que variam entre execuções do próprio original.

### A7. Encerrar

```bash
for pid in $(lsof -ti tcp:<porta> -sTCP:LISTEN); do kill "$pid"; done
lsof -nP -iTCP:<porta> -sTCP:LISTEN || echo "porta <porta> livre"
```

Use o laço `for`: ele se comporta igual em bash e zsh. A forma `kill $pids` falha no zsh quando há mais de um PID, porque o zsh não divide variáveis em palavras.

---

## Parte B — Validação (fim da Fase 3)

### B1. Ambiente

Se o manifesto mudou, reinstale as dependências e anexe a saída a `install.log`.

### B2. Mesmo estado inicial

Repita A2: mova para `db-backup/` o banco gerado pela execução anterior e rode o seed documentado, se houver.

### B3. Boot pelo comando documentado

Use o comando documentado do projeto — é ele que prova que o entry point funciona. Se houve conflito de porta em A3, passe a porta pela configuração criada na T02 (`PORT=<porta>`). Defina as variáveis que a refatoração passou a exigir (ex.: `ADMIN_TOKEN` para rotas protegidas). Ative avisos de depreciação para confirmar a correção de AP-19:

```bash
# Python
PORT=<porta> PYTHONWARNINGS=default nohup .venv/bin/python app.py > .refactor-arch/boot-depois.log 2>&1 &
# Node
PORT=<porta> NODE_OPTIONS=--trace-deprecation nohup npm start > .refactor-arch/boot-depois.log 2>&1 &
```

Espere a prontidão como em A3.4 e verifique o log:

```bash
grep -nE "Traceback|Error|Exception|DeprecationWarning|LegacyAPIWarning|DEP0" .refactor-arch/boot-depois.log || echo "log limpo"
```

### B4. Replay e diff

```bash
bash .refactor-arch/smoke.sh 'http://127.0.0.1:<porta>' > .refactor-arch/depois.txt
diff -u .refactor-arch/baseline.txt .refactor-arch/depois.txt > .refactor-arch/diff.txt \
  && echo "idêntico ao baseline" \
  || grep -E '^[-+][^-+]' .refactor-arch/diff.txt
```

Depois do replay, verifique de novo o log (B3): avisos de depreciação costumam aparecer só quando a rota é exercitada.

### B5. Classificar divergências

| Divergência | Classificação | Ação |
|---|---|---|
| Listada em `Breaking Changes propostos` e aprovada | Esperada | Registrar em `validacao.md` com o `BC-xx` |
| Qualquer outra | **Regressão** | Corrigir o código e voltar a B2 |

Exemplos típicos de regressão: 404 virou 500 porque o handler de `Exception` captura `HTTPException`; lista virou `vazio` porque o seed não rodou; chave renomeada ao "melhorar" um serializer.

### B6. Varredura de anti-patterns remanescentes

1. Reaplique os sinais de detecção de **todos** os anti-patterns CRITICAL e HIGH do catálogo sobre o código novo.
2. Rode os greps de proibições por camada (`guidelines-arquitetura.md`, seção 3).
3. Cada ocorrência é corrigida ou justificada como falso positivo em `validacao.md`.

### B7. Encerrar e registrar

1. Encerre a aplicação como em A7 e confirme a porta livre.
2. Se o projeto usa git e `.refactor-arch/` não está ignorado (`git check-ignore -q .refactor-arch || echo "não ignorado"`), adicione `.refactor-arch/` ao `.gitignore`.
3. Grave `.refactor-arch/validacao.md`:

```markdown
# Validação — <projeto>

## Boot
Comando: `<comando exato>`
Resultado: ✓ | ✗ — <trecho relevante do log>
Avisos de depreciação após o replay: <nenhum | lista>

## Smoke test
Requisições: <N> | Idênticas ao baseline: <X> | Divergências declaradas: <K> | Regressões: <R>

| Requisição | Antes | Depois | Classificação |
|---|---|---|---|
| GET /health | 200 json:objeto{…,secret_key,…} | 200 json:objeto{…} | BC-01 |

## Anti-patterns remanescentes
| Verificação | Comando | Resultado |
|---|---|---|
| AP-01 SQL concatenado | `grep …` | nenhuma ocorrência |

## Estado deixado
Porta <porta> livre. Bancos originais preservados em `.refactor-arch/db-backup/`.
```

A Fase 3 só é declarada concluída com **zero regressões**. Qualquer outro resultado é reportado com `✗` na saída final.
