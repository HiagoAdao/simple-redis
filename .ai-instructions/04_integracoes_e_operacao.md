# 04 — Integrações, configuração e operação

Este documento separa as decisões de runtime das responsabilidades de domínio
descritas em `03_arquitetura_e_estado_final.md`. A base inicial sobe somente
Django; adicionar Redis ao Compose é uma missão, não uma funcionalidade já
disponível.

## Portão zero — diagnosticar e preparar o ambiente

Faça esta verificação antes da Missão 0 e antes de sugerir instalações.

### Perguntas de contexto

Confirme com o aluno:

1. sistema operacional e versão;
2. shell usado (PowerShell, Terminal macOS, shell Linux ou shell dentro do WSL);
3. arquitetura quando houver instaladores diferentes (por exemplo, Apple
   Silicon/Intel ou x86_64/ARM);
4. fluxo escolhido: executar tudo no Docker ou executar Python/testes no host;
5. se o Docker Desktop/daemon já está aberto, quando o CLI estiver instalado.

O ambiente do agente não comprova o ambiente do aluno. Nunca solicite a saída de
`env`, `.env`, `docker login`, tokens ou outras configurações secretas.

### Diagnóstico sem instalação

Peça somente o bloco adequado ao SO e shell. Se um executável não existir, o
aluno deve informar isso; não tratar a mensagem como falha do projeto.

**macOS (Terminal/zsh):**

```bash
sw_vers
uname -m
command -v uv || true
command -v python3 || true
command -v docker || true
```

Se `docker` existir, pedir também `docker --version`, `docker compose version`
e `docker info`. Se `uv` existir, pedir `uv --version`. Executar
`python3 --version` somente se `python3` foi encontrado.

**Linux (shell usado para trabalhar no repositório):**

```bash
cat /etc/os-release
uname -m
command -v uv || true
command -v python3 || true
command -v docker || true
```

Para executáveis encontrados, coletar as mesmas versões acima. `docker info`
verifica se o daemon responde; `docker --version`, sozinho, só confirma o CLI.

**Windows (PowerShell):**

```powershell
$PSVersionTable.PSVersion
Get-ComputerInfo -Property WindowsProductName,WindowsVersion,OsArchitecture
Get-Command uv,python,py,docker -ErrorAction SilentlyContinue
```

Se `docker` existir, pedir `docker --version`, `docker compose version` e
`docker info`. Se `uv` existir, pedir `uv --version`. Para cada interpretador
encontrado, pedir a versão usando o comando correspondente ao shell.
Não usar comandos de PowerShell em WSL. Se o aluno trabalha dentro do WSL,
confirmar a distro/shell e verificar a integração WSL do Docker Desktop quando
essa for a escolha dele.

### Escolher a instalação pelo fluxo

| Fluxo escolhido | Requisitos no host | O que já vem no projeto/container |
|---|---|---|
| Docker | Docker Desktop no macOS/Windows, ou Docker Engine e Compose plugin na distro Linux; daemon ativo. | Python, `uv`, Django e dependências de desenvolvimento são instalados pela imagem deste scaffold. Não exigir Python ou `taskipy` no host. |
| Local | `uv`; um Python 3.12+ disponível ou Python gerenciado por `uv`. | `uv sync` cria/sincroniza o ambiente do projeto e instala o grupo `dev`, incluindo `taskipy` e ferramentas de teste. |

Se o aluno pretende usar ambos, validar cada fluxo separadamente. Não instalar
Docker, Python e `uv` por rotina sem confirmar que serão usados.

### Consultar documentação atual antes de orientar instalação

Quando um requisito faltar ou estiver abaixo da versão necessária:

1. use Context7 para resolver o ID da ferramenta/biblioteca antes de consultar
   documentação;
2. faça uma consulta específica para instalação/atualização no SO, shell e
   arquitetura informados;
3. prefira a documentação oficial indicada abaixo e forneça o link junto dos
   comandos;
4. explique o que será alterado, se há elevação de privilégio, reinício do
   terminal/daemon ou requisito de reinicialização;
5. deixe o aluno executar e depois valide as versões; não execute instaladores
   automaticamente nem reaproveite comandos de outro SO.

Referências oficiais a consultar/confirmar no momento da orientação:

- [`uv` — instalação por plataforma](https://docs.astral.sh/uv/getting-started/installation/)
- [`uv` — instalar e escolher versões de Python](https://docs.astral.sh/uv/guides/install-python/)
- [Docker Desktop para macOS](https://docs.docker.com/desktop/setup/install/mac-install/)
- [Docker Desktop para Windows](https://docs.docker.com/desktop/setup/install/windows-install/)
- [Docker Engine para Linux — escolher a distro](https://docs.docker.com/engine/install/)
- [Docker Compose plugin para Linux](https://docs.docker.com/compose/install/linux/)

Não copie uma linha de instalação antiga para todos os sistemas. Em Linux,
primeiro identifique a distribuição e siga sua página oficial. Em macOS,
confirme Apple Silicon ou Intel para escolher o instalador. No Windows, confirme
PowerShell versus WSL e o backend/integração disponíveis para aquela instalação.

### Python e `uv`

- A exigência do projeto é Python `>=3.12` (`requires-python` em
  `pyproject.toml`); não assumir que o `python` do sistema atende.
- Se já houver Python 3.12+, sincronize o projeto com `uv sync` e confira a
  versão realmente selecionada dentro do ambiente via `uv run python --version`.
- Se estiver ausente/desatualizado e `uv` estiver instalado, oriente o aluno a
  instalar um interpretador gerenciado pela ferramenta (por exemplo,
  `uv python install 3.12`) em vez de modificar o Python global sem necessidade.
  Depois rode `uv sync` e valide `uv run python --version`; a versão selecionada
  precisa satisfazer `>=3.12`.
- Se `uv` estiver ausente, primeiro consulte a instalação oficial por SO/shell;
  só depois use comandos `uv`. Em Windows, não misture PowerShell e WSL.
- `taskipy` já pertence ao grupo `dev` do `pyproject.toml`; não deve ser
  instalado globalmente nem com `pip`. `uv sync` instala esse grupo neste fluxo.
  Confirme a disponibilidade executando uma tarefa do projeto, por exemplo
  `uv run task test`. Se `task` não for encontrado, confira diretório atual,
  saída de `uv sync`, grupo `dev` e lockfile antes de sugerir qualquer instalação.

### Docker e Compose

- `docker --version` verifica o cliente; `docker compose version` verifica o
  plugin Compose v2; `docker info` verifica se o daemon está ativo e acessível.
- Se o cliente existir, mas `docker info` falhar, descubra se Docker Desktop ou
  o serviço Linux está parado antes de propor reinstalação.
- No Windows/macOS, use as instruções oficiais de Docker Desktop da plataforma e
  arquitetura detectadas. No Linux, siga as instruções de Docker Engine e Compose
  plugin da distro; não presuma `apt`/Ubuntu.
- Explique que instalação de Docker pode exigir permissões administrativas,
  backend WSL/virtualização ou iniciar um daemon. Não sugira adicionar o aluno ao
  grupo `docker` nem usar `sudo` sem explicar as implicações e confirmar o SO.
- Quando instalado, validar `docker info`, `docker compose version` e
  `docker compose config` antes de tentar construir a aplicação.

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
