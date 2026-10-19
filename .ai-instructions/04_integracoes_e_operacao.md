# 04 — Integrações, configuração e operação

Este documento separa as decisões de runtime das responsabilidades de domínio
descritas em `03_arquitetura_e_estado_final.md`. A base inicial sobe somente
Django; adicionar Redis ao Compose é uma missão, não uma funcionalidade já
disponível.

## Configuração Django

- Projeto: `django_redis_demo`.
- Banco didático: SQLite em `BASE_DIR / "db.sqlite3"`.
- Idioma: `pt-br`; fuso: `America/Sao_Paulo`.
- `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` devem ser lidos de variáveis de
  ambiente. Defaults permissivos são exclusivamente locais e devem ser
  identificados como tais.
- A base inicial fornece `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` e
  `DJANGO_ALLOWED_HOSTS`. Ao adicionar Redis, introduza `REDIS_URL` e explique
  que seu valor muda conforme o processo está no host ou no Compose.
- Nunca versionar `.env`, imprimir configurações secretas ou exibir a URL Redis
  com usuário/senha na interface. Se a UI mostrar o destino Redis, sanitizar a
  informação na fronteira e testar que credenciais não aparecem.
- `runserver` é apenas para desenvolvimento; não orientar implantação pública
  com `DEBUG=true`, hosts abertos, chave de exemplo ou servidor de desenvolvimento.

## SQLite, migrations e inicialização

- O SQLite é a fonte persistente de chamados; Redis é uma cópia temporária de
  leitura, não a fonte de verdade.
- Toda mudança de modelo gera migration versionada com `uv run task
  makemigrations` e é aplicada por `uv run task migrate`.
- No Compose completo, a aplicação aplica migrations antes de iniciar o servidor.
  Explique que isso é conveniente em laboratório; implantação com múltiplas
  réplicas pede uma estratégia de migration controlada para evitar concorrência.
- A chamada atual para semear dados é executada dentro do caso de uso de leitura.
  Ela faz uma consulta `exists()` ao SQLite antes de tentar o Redis. Registre essa
  nuance ao explicar hit/miss e não afirme que o caminho hit não toca o banco.

## Compose inicial e Compose final

### Inicial

O `docker-compose.yml` tem somente `web`, uma porta HTTP publicada em loopback,
bind mount do código e health check HTTP baseado em `/health/`. O health check
comprova que o processo web respondeu à rota, não que Redis exista ou esteja
conectado.

O ambiente virtual do container fica fora do bind mount do código. Isso evita
que o diretório `.venv` do macOS/Linux hospedeiro sombreie ou invalide o ambiente
construído na imagem.

### Depois da missão Redis

Ao incluir o Redis, o aluno deve justificar e validar:

- imagem Redis 7 Alpine ou versão explícita equivalente;
- health check de Redis usando `redis-cli ping`;
- comunicação pela rede Compose;
- `depends_on` com `condition: service_healthy` no serviço web;
- `REDIS_URL=redis://redis:6379/0` dentro do container web;
- não publicar a porta Redis no host sem uma necessidade didática explícita;
- migrations antes do servidor, depois que o modelo e a migration existirem.

Dentro do Compose, `redis` é o DNS do serviço. `localhost` dentro do container
web aponta para o próprio container web; `127.0.0.1:6379` só faz sentido para um
processo executado no host quando Redis está publicado localmente.

Evite `container_name` fixo sem justificativa: o nome do serviço já é o endereço
estável da rede e nomes fixos atrapalham múltiplas instâncias do mesmo Compose.

## HTTP e health check

- Preserve `GET /health/` durante toda a jornada. Ele retorna JSON de saúde do
  processo web e aceita apenas GET.
- A referência completa em `feature/django-redis` (antiga `main`) não contém essa rota; sua presença no
  resultado da jornada é intencional porque ela já vem no scaffold e deve ser
  preservada.
- A listagem usa `GET /calls/`; a raiz pode redirecionar para essa tela.
- Limpar cache altera estado: implemente a ação por POST e use um formulário com
  CSRF, não um link GET.
- Teste o status, o payload, método não permitido, nomes de URL e redirect.
- Uma rota health verde não verifica dependências externas. Se futuramente for
  criada uma readiness que consulte Redis, documente a diferença entre
  liveness (processo responde) e readiness (dependências essenciais disponíveis).

## Dependências e imagem

- Python 3.12+ e `uv` são o fluxo do projeto. Alterações de dependências são
  feitas em `pyproject.toml` e refletidas com `uv lock`; nunca editar `uv.lock`
  manualmente.
- `redis` só entra no grupo de dependências de runtime na missão de integração.
- A imagem deste scaffold é de desenvolvimento e inclui ferramentas de teste para
  que `docker compose run --rm web uv run task test` funcione.
- Fixe uma versão de `uv` na imagem em vez de `latest`, mantenha dependências
  reproduzíveis com `uv sync --frozen` e exclua `.env`, `.venv`, `.git`, banco e
  cache de teste do build context via `.dockerignore`.
- Se separar imagem de desenvolvimento e produção, torne explícito qual grupo de
  dependências está instalado; `uv run` pode sincronizar o projeto e não se deve
  depender de um ambiente virtual do host montado no container.

## Execução observável

Com Compose inicial:

```bash
docker compose config
docker compose up --build -d --wait
docker compose ps
curl --fail --show-error http://127.0.0.1:8000/health/
docker compose logs web
```

Após a missão Redis, verificar separadamente o health check Redis e executar um
PING originado do serviço web. Não registrar credenciais nem afirmar conectividade
com base somente em `docker compose config`.
