# code-smells-project

API de E-commerce em Python/Flask, refatorada para MVC em camadas pela skill `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado
automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração

As variáveis de ambiente estão documentadas em `.env.example` (porta, host, debug,
`SECRET_KEY`, CORS). Todas têm defaults seguros para desenvolvimento; `SECRET_KEY`
é obrigatória quando `APP_ENV=production`. Para subir em outra porta:

```bash
PORT=5055 python app.py
```

## Comandos de administração

O reset de dados, antes exposto como rota HTTP, agora é um comando de linha (uso local):

```bash
flask --app app reset-db
```

## Estrutura

```
app.py            # entry point (create_app + run)
src/
  app.py          # composition root
  config/         # configuração (ambiente, defaults seguros)
  models/         # acesso a dados por domínio, conexão, schema, seed
  services/       # regras de negócio e integrações
  controllers/    # fluxo de requisição/resposta + validação
  views/          # rotas e serializers
  middlewares/    # tratamento de erros centralizado
```
