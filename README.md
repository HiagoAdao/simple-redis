# Django + Redis Demo

Aplicação web simples em **Django** integrada ao **Redis**, demonstrando o padrão **Cache-Aside** sob a perspectiva de **DSM (Distributed Shared Memory)**.

---

## Requisitos

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) instalado
- Redis local ou conta no [Upstash Redis](https://upstash.com/)
- Docker (opcional)

---

## Instalação

```bash
uv sync
```

---

## Configuração

Por padrão, a aplicação conecta ao Redis local em `redis://127.0.0.1:6379/0`.

Para usar o Upstash ou outro Redis remoto, exporte a variável antes de subir:

```bash
# macOS / Linux
export REDIS_URL="rediss://default:senha@endpoint.upstash.io:port"

# Windows (PowerShell)
$env:REDIS_URL="rediss://default:senha@endpoint.upstash.io:port"
```

---

## Execução local

```bash
uv run task migrate
uv run task run
```

Acesse `http://127.0.0.1:8000/` e observe a diferença de latência entre **Cache Miss** (~1.5s) e **Cache Hit** (< 10ms).

---

## Testes

```bash
uv run task test
```

Para relatório de cobertura:

```bash
uv run pytest --cov=callsystem --cov-report=term-missing -v
```

---

## Docker Compose

Sobe Django + Redis em containers interconectados:

```bash
docker compose up --build
```

Para encerrar:

```bash
docker compose down
```

---

## Como funciona

| Situação | Comportamento |
|---|---|
| Cache Hit | Leitura do Redis em memória — latência < 10ms |
| Cache Miss | Acesso ao banco SQLite com delay simulado de 1.5s, seguido de escrita no Redis (TTL 30s) |
| Redis indisponível | Fallback resiliente (*Fail-Soft*) — continua servindo dados do banco |
