# Template do Relatório de Auditoria

Referência da **Fase 2**. O relatório é gravado em `.refactor-arch/relatorio-auditoria.md` e impresso completo no terminal. Siga a estrutura abaixo sem remover seções; seção sem conteúdo recebe `Nenhum`.

## Regras de preenchimento

1. **Ordenação.** CRITICAL → HIGH → MEDIUM → LOW. Na mesma severidade, pela ordem do ID do catálogo (AP-01, AP-02, …); em empate, pelo primeiro arquivo em ordem alfabética.
2. **Numeração.** Depois de ordenar, numere `F-01`, `F-02`, … A numeração é a referência usada na Fase 3 e em `Breaking Changes propostos`.
3. **Um finding por causa raiz.** Ocorrências repetidas do mesmo anti-pattern viram um único finding; a primeira vai em `Arquivo`, as demais em `Ocorrências`.
4. **Localização exata.** `caminho/relativo/arquivo.ext:linha` ou `:inicio-fim`, relativo à raiz do projeto, conferido no arquivo. Proibido `~`, "aprox." ou "linha N em diante".
5. **Contagens coerentes.** Os números do `Resumo` contam findings, não ocorrências. `Total` é a soma do resumo e bate com a quantidade de blocos `### F-`.
6. **Descrição concreta.** Cite nomes de funções, rotas e trechos reais. Segredos aparecem redigidos: mostre só os primeiros caracteres (`'minha-chave-****'`, `pk_live_****`).
7. **Recomendação acionável.** Diga o que fazer e aponte a transformação do playbook (`T01`…`T17`).
8. **Contrato.** Todo finding declara se a correção preserva o contrato HTTP ou qual quebra (`BC-xx`) ela exige. Quebras só são aceitas para findings de segurança CRITICAL ou HIGH (regra 3 do `SKILL.md`) — e, nesses, a quebra necessária é proposta, não evitada: um AP-05 HIGH cuja correção exige proteger rotas declara um `BC-xx` por rota protegida. No AP-05, a recomendação segue a tabela de situações da T14 rota a rota: rota que executa SQL/código do cliente ou destrói dados em massa é **removida** (um `BC-xx` por rota removida), nunca apenas protegida.
9. **APIs deprecated.** A seção é obrigatória. Sem ocorrências, escreva `Nenhuma API deprecated detectada` e diga como verificou (warnings em runtime, saída do instalador, busca pelos padrões do catálogo).

## Estrutura

````markdown
================================
RELATÓRIO DE AUDITORIA DE ARQUITETURA
================================
Projeto:  <nome do diretório>
Stack:    <linguagem> + <framework> <versão>
Arquivos: <N> analisados | ~<L> linhas de código
Data:     <AAAA-MM-DD>

## Resumo
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

| # | Severidade | Anti-pattern | Local principal |
|---|---|---|---|
| F-01 | CRITICAL | <nome> (AP-xx) | <arquivo>:<linha> |

## Findings

### F-01 [CRITICAL] <Nome do anti-pattern> (AP-xx)
Arquivo: <arquivo>:<linhas>
Ocorrências: <arquivo>:<linhas>, <arquivo>:<linhas> | Nenhuma adicional
Descrição: <o que acontece, citando o código concreto>
Impacto: <consequência concreta para segurança, dados, manutenção ou performance>
Recomendação: <o que fazer> — Playbook T<nn>
Contrato: preservado | exige BC-<nn>

<… um bloco por finding, na ordem definida …>

## APIs deprecated
| API ou dependência | Local | Substituto | Evidência |
|---|---|---|---|
| <api> | <arquivo>:<linha> | <substituto> | <warning, saída do instalador ou versão de remoção> |

## Breaking Changes propostos
| # | Rota | Mudança no contrato | Finding que justifica |
|---|---|---|---|
| BC-01 | <MÉTODO /path> | <o que muda na resposta> | F-<nn> — <motivo de segurança> |

## Plano de refatoração
<árvore resumida da estrutura-alvo>
<ordem das camadas e transformações principais por camada>

================================
Total: <N> findings
================================
````

Depois do bloco, a pergunta de confirmação definida no `SKILL.md`, Fase 2, passo 7.

## Exemplo de finding preenchido

```markdown
### F-03 [HIGH] Operação multi-passo sem transação (AP-09)
Arquivo: app/orders.py:41-78
Ocorrências: Nenhuma adicional
Descrição: `create_order()` insere em `orders` (linha 52), grava cada item em `order_items` (linhas 60-66) e decrementa `stock` (linhas 68-71) com `commit()` só na linha 77. A validação de estoque dentro do laço (linha 63) pode retornar no meio das escritas, deixando o pedido gravado sem parte dos itens.
Impacto: pedidos inconsistentes e estoque divergente em qualquer falha parcial; o erro não é detectável pela API, que responde 400.
Recomendação: validar todos os itens antes de escrever e envolver as escritas numa transação única, com rollback em exceção — Playbook T07.
Contrato: preservado
```

## Exemplo de Breaking Change bem declarado

```markdown
| BC-01 | GET /health | remove os campos `secret_key`, `debug` e `db_path` da resposta; `status` e `database` permanecem | F-02 — segredo exposto em endpoint público |
| BC-02 | POST /admin/query | rota removida da API (T14, "Executa SQL enviado pelo cliente"); passa a responder 404 com ou sem credencial | F-01 — execução de SQL arbitrário |
```

Uma quebra não declarada aqui e detectada na validação da Fase 3 é tratada como regressão.
