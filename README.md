# Simple Redis — laboratório de aprendizado com Django

Este repositório começa com uma aplicação **Django mínima**, uma rota de health
check e um container web. A partir dessa base, um agente de mentoria guia a
construção de uma demonstração de **Cache-Aside com Redis**, SQLite e conceitos
de **DSM (Distributed Shared Memory)**.

O objetivo é aprender a projetar, implementar e validar o sistema em etapas —
não receber uma solução pronta para copiar. O agente e sua sequência de ensino
estão descritos em [`AGENTS.md`](AGENTS.md) e em `.ai-instructions/`.

## A jornada

Ao concluir as missões, a aplicação deverá permitir observar:

- **Cache miss:** leitura dos chamados no SQLite, simulação de uma consulta mais
  lenta e gravação do resultado no Redis com TTL;
- **Cache hit:** leitura da resposta serializada no Redis, sem repetir a consulta
  lenta;
- **Redis indisponível:** fallback para o SQLite, mantendo a aplicação útil;
- **Invalidação:** remoção da chave para que uma nova leitura volte a ser cache
  miss.

O resultado esperado é uma aplicação Django organizada em uma aplicação
`callsystem`, com modelo, DTO, serviços, caso de uso, views, template e testes.
As instruções definem as responsabilidades e os contratos de cada parte sem
substituir o raciocínio e a implementação do aluno.

## Estrutura inicial

```text
simple-redis/
├── .ai-instructions/       # roteiro pedagógico, arquitetura e critérios
├── .mestre-jedi/           # tarefas práticas e evidências de aprendizagem
├── AGENTS.md               # inicialização e política do agente mentor
├── django_redis_demo/      # projeto Django e rota /health/
├── tests/                  # testes iniciais da rota de health
├── Dockerfile              # imagem da aplicação web
├── docker-compose.yml      # somente o serviço web na etapa inicial
├── manage.py
├── pyproject.toml          # dependências, pytest e comandos taskipy
└── uv.lock
```

**O Redis ainda não está no `docker-compose.yml` desta base.** Adicioná-lo,
configurar a rede e fazer a aplicação aguardar seu health check são missões
deliberadas da jornada.

## Requisitos

- Docker Engine e Docker Compose v2 (ou Docker Desktop com Compose);
- `uv` é opcional para executar testes fora do container;
- Python 3.12+ é necessário somente para o fluxo local fora do Docker.

## Comece pelo container

Na raiz do projeto:

```bash
docker compose up --build -d
docker compose ps
```

Quando o serviço estiver saudável, acesse [`http://localhost:8000/health/`](http://localhost:8000/health/).
A resposta inicial é JSON com status `ok`. Para acompanhar a inicialização:

```bash
docker compose logs -f web
```

Encerre os containers com:

```bash
docker compose down
```

A porta está publicada somente no loopback da máquina local. O servidor Django
`runserver` e a chave padrão são destinados ao desenvolvimento, não a uma
implantação pública.

## Testes da base

Com `uv` instalado:

```bash
uv sync
uv run task test
uv run task test-cov
```

Ou execute os testes no container:

```bash
docker compose run --rm web uv run task test
```

O health check do Compose confirma que a aplicação responde por HTTP dentro do
container; os testes verificam o contrato da rota. Nenhum desses resultados, por
si só, prova o comportamento futuro do Redis.

## Ative a mentoria

Abra a raiz deste repositório em uma IDE com agente de código e envie uma
mensagem inicial, por exemplo: **“Olá, vamos começar pela primeira missão.”**
O agente deve ler `AGENTS.md` e a sequência de `.ai-instructions/`, descobrir a
etapa atual, orientar uma tarefa de cada vez e solicitar evidências e uma
explicação de entendimento antes de avançar.

Os arquivos de instrução funcionam como o guia do mentor. Para uma experiência
de descoberta, comece pela conversa com o agente antes de estudá-los diretamente.

## O que você vai praticar

- roteamento, views, configuração e testes no Django;
- modelagem relacional simples com SQLite e migrations;
- separação entre view, caso de uso, repositório e serviço de cache;
- serialização explícita e contratos de dados;
- Cache-Aside, TTL, invalidação e comportamento em falha;
- DNS interno do Docker Compose, health checks e ordem de inicialização;
- testes unitários com dependências externas isoladas e testes de integração;
- validação de qualidade apoiada por evidências, não apenas pela aplicação
  “parecer funcionar”.

## Referências do método

- [Pongino Raspberry](https://github.com/HiagoAdao/pongino-rasp) — estrutura do
  `AGENTS.md`, papel do mentor e instruções modulares;
- [Jogo da Velha via WebSockets](https://github.com/HiagoAdao/websocket-jogo-da-velhia)
  — apresentação da jornada pedagógica e primeiros passos no README.
