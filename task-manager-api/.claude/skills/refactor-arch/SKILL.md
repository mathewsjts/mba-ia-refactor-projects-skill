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
3. **Contrato HTTP preservado.** Método, path, status code, tipo de corpo (JSON ou texto) e estrutura de chaves das respostas continuam iguais. A **única** exceção é a correção de um finding **de segurança** de severidade CRITICAL **ou HIGH** (AP-01 a AP-05, AP-10, AP-16) — e toda quebra desse tipo é declarada em `Breaking Changes propostos` no relatório, *antes* da confirmação. Para AP-05 isso significa aplicar a T14 por completo, qualquer que seja a severidade, seguindo a ação da tabela de situações para **cada rota**: rota que executa SQL ou código enviado pelo cliente, ou que destrói dados em massa, é **removida** da API — exigir credencial nela não corrige o finding; as demais rotas privilegiadas ou destrutivas passam a exigir credencial — e escrever campo de perfil, credencial ou estado da conta (`role`, senha, `ativo`) é privilegiado mesmo em `POST`/`PUT`, então "preservar o contrato" nunca justifica deixar essas rotas abertas; assinar um token falso sem exigi-lo não basta. Em projeto **com login**, isso vale para **toda rota de escrita** (`POST`, `PUT`, `PATCH`, `DELETE`), não só para o `DELETE`: ela exige token, e a T14 diz quem pode escrever — o dono do recurso ou um admin; num recurso compartilhado, sem dono, só um admin. Ficam públicos só o login, o cadastro público e os fluxos que o relatório declara públicos com o motivo.
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
5. Leia `template-relatorio.md` e monte o relatório, incluindo `Breaking Changes propostos` — toda mudança de contrato que a Fase 3 fará, com o finding que a justifica. Toda rota que a T14 passará a proteger **ou remover** é um Breaking Change e entra nessa tabela; a recomendação do finding AP-05 diz, rota a rota, qual linha da tabela da T14 se aplica (remover ou proteger). Em projeto com login, a recomendação percorre **todas** as rotas de escrita do inventário, não só as que o legado já tratava como sensíveis. Preencha também `Riscos residuais`, com o que a refatoração não elimina (ex.: efeito externo antes da transação, T07 passo 2), e a linha `Dependências` do plano, com toda dependência que a Fase 3 vai adicionar, remover, atualizar ou trocar.
6. Grave o relatório em `.refactor-arch/relatorio-auditoria.md` e imprima-o **completo** no terminal: a resposta da Fase 2 traz o conteúdo integral do arquivo, com todos os blocos `### F-`, sem resumir.
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
   5. **views/routes** — mapeamento de rotas e serialização (T13, T14, T17). Na T14, classifique cada rota do finding AP-05 pela tabela de situações e aplique a ação daquela linha: em "Remover", apagam-se a rota, o método do controller e o método do model/service que executa a entrada do cliente — proteger com token no lugar de remover deixa o finding **não corrigido**
   6. **middlewares** — tratamento centralizado de erros (T10)
   7. **composition root** — montagem das dependências e entry point (T11)
   8. **limpeza** — código morto, imports, logging, constantes (T16); remova os arquivos antigos que ficaram vazios
4. **Aplique a transformação inteira.** Para cada finding, abra a(s) transformação(ões) da recomendação (`Playbook Txx`) e execute **todos** os passos numerados — não só o que a camada da etapa sugere. Mover o código para a camada certa (princípio 1 do playbook) não aplica transformação nenhuma: depois de mover, volte à linha e aplique os passos. Um passo só fica de fora se for comprovadamente inaplicável ao código, com o motivo. Registre em `.refactor-arch/conformidade.md`, uma linha por passo:

   ```
   | Finding | Transformação | Passo | Evidência |
   | F-xx | T07 | 3 — escrita condicional + linhas afetadas | <arquivo>:<linhas> |
   | F-xx | Txx | <n> — <passo> | N/A: <motivo> |
   ```
5. **Comentário não substitui código.** Docstring ou comentário que cita uma transformação (`T07`) ou promete uma garantia ("condicional", "atômico", "em transação", "protegido", "validado") precisa apontar para código que a cumpre. Se o código não cumpre, aplique o passo que falta — não ajuste o comentário para esconder a falta.
6. Todo finding do relatório termina em um de três estados: **corrigido** (todos os passos da transformação aplicados ou justificados como N/A em `conformidade.md`), **parcial** (dizendo qual passo falta) ou **não corrigido** (dizendo o motivo, ex.: exigiria quebra de contrato não autorizada). Nenhum finding é omitido. Finding de segurança CRITICAL ou HIGH nunca termina parcial ou não corrigido por motivo de contrato — a quebra necessária é declarada e aplicada (regra 3). Finding HIGH ou CRITICAL com passo faltando não é entregue parcial: aplique o passo.
7. Prefira bibliotecas já declaradas no manifesto e a biblioteca padrão. Se adicionar uma dependência, atualize o manifesto e instale-a.
   - **O plano aprovado manda.** Toda dependência adicionada, removida, atualizada ou trocada (ex.: trocar o driver do banco) precisa estar na linha `Dependências` do plano, e a versão escolhida precisa ser a que o relatório recomenda. Se a Fase 3 descobrir que precisa de outra coisa, a mudança vira um **desvio**: registre em `.refactor-arch/validacao.md` e na seção `Desvios do plano aprovado` da saída final o que foi aprovado, o que foi feito, o motivo e a evidência. O mesmo vale para qualquer outra decisão que contrarie o relatório. Desvio silencioso é falha da Fase 3.
8. Leia de novo `protocolo-validacao.md` e execute a **Parte B — Validação**: mesmo estado inicial do baseline, boot pelo comando documentado, replay de `smoke.sh`, `diff` contra `baseline.txt`, varredura de anti-patterns remanescentes, conferência passo a passo de `conformidade.md` contra o código, a prova de concorrência (escrita condicional e unicidade da T07), as entradas de tipo inválido (`tipos.sh`) e, em projeto com login, a matriz de autorização (`autorizacao.sh`).
9. Toda divergência que **não** esteja em `Breaking Changes propostos` é regressão, e todo passo de `conformidade.md` sem código correspondente também: corrija e valide de novo. Limite de 5 ciclos; se não convergir, pare e reporte exatamente o que diverge.
10. Grave `.refactor-arch/validacao.md` com as evidências e derrube a aplicação.
11. Imprima:

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

## Desvios do plano aprovado
<aprovado → feito, motivo e evidência; ou "Nenhum">

## Riscos residuais
<os do relatório, com o estado de cada um; ou "Nenhum">

## Validação
  ✓ Aplicação inicia sem erros (<comando usado>)
  ✓ Endpoints originais respondem: <iguais>/<total> idênticos ao baseline, <K> divergências declaradas
  ✓ Nenhum anti-pattern CRITICAL ou HIGH remanescente
  ✓ Passos do playbook conferidos: <X>/<Y> findings com a transformação completa (.refactor-arch/conformidade.md)
  ✓ Prova de concorrência: <invariante conferido> | N/A: <motivo>
  ✓ Entradas de tipo inválido: <N> casos, nenhum 5xx (.refactor-arch/tipos.txt)
  ✓ Matriz de autorização: <N> rotas de escrita, anônimo → 401 e outra conta → 403 (.refactor-arch/autorizacao.txt) | N/A: <projeto sem login>
  ✓ Dependências conforme o plano aprovado | <K> desvios declarados acima
Evidências: .refactor-arch/validacao.md
================================
```

Use `✗` no lugar de `✓` para qualquer verificação que falhou ou não pôde ser executada, com o motivo na mesma linha. Não suavize falhas.
