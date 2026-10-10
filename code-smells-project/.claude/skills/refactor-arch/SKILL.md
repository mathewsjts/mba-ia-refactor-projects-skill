---
name: refactor-arch
description: Analisa, audita e refatora uma API backend legada para o padrão MVC em três fases sequenciais — detecção de stack e arquitetura, relatório de anti-patterns classificados por severidade com arquivo e linha, e refatoração validada por boot e replay dos endpoints originais. Agnóstica de linguagem e framework. Use quando o usuário pedir para auditar ou refatorar a arquitetura de um projeto.
argument-hint: "[caminho-do-projeto]"
disable-model-invocation: true
---

# refactor-arch — Refatoração Arquitetural Automatizada

Você vai atuar como arquiteto de software sênior conduzindo a auditoria e a refatoração de uma codebase legada. O trabalho acontece em **três fases sequenciais**, com uma confirmação humana obrigatória entre a auditoria e qualquer modificação.

Raiz do projeto-alvo: o caminho passado como argumento, se houver (`$ARGUMENTS`); caso contrário, o diretório de trabalho atual. Todos os caminhos abaixo são relativos a essa raiz.

## Arquivos de referência

Ficam no mesmo diretório deste `SKILL.md` — a partir da raiz do projeto, `.claude/skills/refactor-arch/`. Leia cada um **no momento indicado**, não todos de uma vez.

| Arquivo | Conteúdo | Quando ler |
|---|---|---|
| `analise-de-projeto.md` | Heurísticas de detecção de linguagem, framework, banco, rotas, domínio e arquitetura | Início da Fase 1 |
| `protocolo-validacao.md` | Ambiente, boot, inventário de rotas, smoke test e comparação com baseline | Fim da Fase 1 e fim da Fase 3 |
| `catalogo-anti-patterns.md` | Anti-patterns com sinais de detecção, severidade e APIs deprecated | Início da Fase 2 |
| `template-relatorio.md` | Formato obrigatório do relatório de auditoria | Antes de escrever o relatório |
| `guidelines-arquitetura.md` | Camadas do MVC alvo, responsabilidades e regra de dependência | Início da Fase 3 |
| `playbook-refatoracao.md` | Transformações concretas com código antes/depois | Durante a Fase 3, por finding |

## Regras invioláveis

1. **Nenhuma modificação antes da confirmação.** Até o usuário aprovar explicitamente no fim da Fase 2, você não cria, altera, move nem apaga arquivo algum do projeto. Exceções: escrever dentro de `.refactor-arch/` (diretório de trabalho da skill), instalar dependências declaradas e subir a aplicação para capturar o baseline.
2. **Evidência, não estimativa.** Todo finding cita arquivo e linha(s) conferidos lendo o arquivo. Toda afirmação de sucesso na Fase 3 corresponde a uma saída real de comando. O que não pôde ser verificado é declarado como não verificado.
3. **Contrato HTTP preservado.** Método, path, status code, tipo de corpo (JSON ou texto) e estrutura de chaves das respostas continuam iguais. A **única** exceção é a correção de um finding CRITICAL de segurança — e toda quebra desse tipo é declarada em `Breaking Changes propostos` no relatório, *antes* da confirmação.
4. **Comandos de execução preservados.** Os comandos documentados para instalar, popular e subir a aplicação (README, `scripts` do manifesto, bloco `__main__`, scripts de seed) continuam funcionando depois da refatoração.
5. **Adapte-se ao ponto de partida.** Um monolito é reestruturado; um projeto que já tem camadas é refinado. Não renomeie nem mova o que já cumpre o papel certo.
6. **Não faça commit** nem altere o histórico git. Versionar é decisão do usuário.
7. **Idioma.** Toda saída para o usuário — resumos, relatório, perguntas — é em português do Brasil. No código, siga o idioma dos identificadores que o projeto já usa.

## Fase 1 — Análise

Objetivo: entender o projeto e congelar o comportamento atual antes de qualquer mudança.

1. Leia `analise-de-projeto.md`.
2. Faça o inventário de arquivos-fonte (seção 1) e leia **todos por completo**. A auditoria depende de conhecer cada linha.
3. Detecte linguagem, framework com versão, dependências relevantes, banco de dados e tabelas, entry point, comando de execução e porta (seções 2 a 6).
4. Mapeie as rotas (seção 7) e classifique a arquitetura atual com a matriz de responsabilidades (seção 8).
5. Descreva o domínio em uma linha, com as entidades principais entre parênteses (seção 9).
6. Leia `protocolo-validacao.md` e execute a **Parte A — Baseline**: preparar o ambiente, garantir estado inicial reprodutível, subir a aplicação original, gerar `.refactor-arch/smoke.sh`, gravar `.refactor-arch/baseline.txt` e derrubar a aplicação.
   - Se a aplicação original não subir, registre o erro exato em `.refactor-arch/boot-antes.log`, siga para a Fase 2 sem baseline e deixe isso explícito no resumo. Não conserte nada ainda.
7. Imprima o resumo exatamente neste formato:

```
================================
FASE 1: ANÁLISE DO PROJETO
================================
Linguagem:      <linguagem> <versão do runtime em uso>
Framework:      <framework> <versão instalada>
Dependências:   <dependências relevantes além do framework>
Domínio:        <descrição curta> (<entidades principais>)
Arquitetura:    <classificação> — <evidência em uma frase>
Arquivos-fonte: <N> arquivos analisados | ~<L> linhas de código
Banco de dados: <engine e modo> — tabelas: <lista>
Entry point:    <arquivo> (<comando de execução>)
Endpoints:      <N> rotas mapeadas
Baseline:       <N> requisições em .refactor-arch/baseline.txt | NÃO CAPTURADO: <motivo>
================================
```

## Fase 2 — Auditoria

Objetivo: produzir um relatório confiável e obter autorização para modificar o projeto.

1. Leia `catalogo-anti-patterns.md`.
2. Para **cada** anti-pattern do catálogo, aplique os sinais de detecção sobre os arquivos-fonte (busca textual e leitura do trecho). Confirme cada ocorrência lendo o código ao redor e descarte os falsos positivos descritos no catálogo.
3. Consolide por causa raiz: várias ocorrências do mesmo anti-pattern com a mesma causa viram **um** finding com todas as localizações.
4. Classifique a severidade pelo catálogo e aplique as regras de escalonamento.
5. Leia `template-relatorio.md` e monte o relatório, incluindo `Breaking Changes propostos` — toda mudança de contrato que a Fase 3 fará, com o finding que a justifica.
6. Grave o relatório em `.refactor-arch/relatorio-auditoria.md` e imprima-o **completo** no terminal.
7. **PARE e peça confirmação** antes de qualquer modificação:
   - Se a ferramenta `AskUserQuestion` estiver disponível, use-a com as opções "Sim, prosseguir com a refatoração" e "Não, encerrar aqui".
   - Caso contrário, termine a resposta com a linha `Fase 2 concluída. Prosseguir com a refatoração (Fase 3)? [s/n]` e aguarde a próxima mensagem do usuário.
   - Qualquer resposta que não seja uma aprovação inequívoca encerra a skill sem modificar arquivos. Em execução não interativa, sem como receber resposta, encerre aqui.

## Fase 3 — Refatoração

Objetivo: reestruturar para MVC, eliminar os findings e provar que a aplicação continua funcionando.

1. Leia `guidelines-arquitetura.md` e `playbook-refatoracao.md`.
2. Desenhe a estrutura-alvo a partir do ponto de partida (guidelines, seção 5) e imprima a árvore planejada antes de começar a editar.
3. Execute por camadas, nesta ordem. Ao fim de cada etapa, faça uma verificação barata de que o código ainda carrega, sem subir o servidor — por exemplo `python -m compileall -q <pastas>` ou `node --check <arquivo>`.
   1. **config** — configuração e segredos (T02)
   2. **models** — entidades e acesso a dados por domínio (T01, T03, T05, T07, T08, T11, T12, T15)
   3. **services** — regras de negócio e integrações externas (T04, T06, T09)
   4. **controllers** — fluxo de requisição e resposta (T04, T09)
   5. **views/routes** — mapeamento de rotas e serialização (T13, T14, T17)
   6. **middlewares** — tratamento centralizado de erros (T10)
   7. **composition root** — montagem das dependências e entry point (T11)
   8. **limpeza** — código morto, imports, logging, constantes (T16); remova os arquivos antigos que ficaram vazios
4. Todo finding do relatório termina em um de três estados: **corrigido**, **parcial** (dizendo o que falta) ou **não corrigido** (dizendo o motivo, ex.: exigiria quebra de contrato não autorizada). Nenhum finding é omitido.
5. Prefira bibliotecas já declaradas no manifesto e a biblioteca padrão. Se adicionar uma dependência, atualize o manifesto e instale-a.
6. Leia de novo `protocolo-validacao.md` e execute a **Parte B — Validação**: mesmo estado inicial do baseline, boot pelo comando documentado, replay de `smoke.sh`, `diff` contra `baseline.txt` e varredura de anti-patterns remanescentes.
7. Toda divergência que **não** esteja em `Breaking Changes propostos` é regressão: corrija e valide de novo. Limite de 5 ciclos; se não convergir, pare e reporte exatamente o que diverge.
8. Grave `.refactor-arch/validacao.md` com as evidências e derrube a aplicação.
9. Imprima:

```
================================
FASE 3: REFATORAÇÃO CONCLUÍDA
================================
## Nova estrutura do projeto
<árvore de diretórios e arquivos-fonte, anotando a camada de cada um>

## Findings
CRITICAL: <corrigidos>/<total> | HIGH: <c>/<t> | MEDIUM: <c>/<t> | LOW: <c>/<t>
<findings parciais ou não corrigidos, com o motivo>

## Breaking Changes aplicados
<lista, ou "Nenhum">

## Validação
  ✓ Aplicação inicia sem erros (<comando usado>)
  ✓ Endpoints originais respondem: <iguais>/<total> idênticos ao baseline, <K> divergências declaradas
  ✓ Nenhum anti-pattern CRITICAL ou HIGH remanescente
Evidências: .refactor-arch/validacao.md
================================
```

Use `✗` no lugar de `✓` para qualquer verificação que falhou ou não pôde ser executada, com o motivo na mesma linha. Não suavize falhas.
