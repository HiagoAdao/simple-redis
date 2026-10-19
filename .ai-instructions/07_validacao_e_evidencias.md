# 07 — Fluxo de validação e evidências

## Ordem por missão

1. confirmar objetivo e etapa atual;
2. localizar os arquivos/camada envolvidos;
3. explicar o conceito, o menor plano e os riscos;
4. pedir uma tentativa pequena e aguardar o aluno;
5. revisar código/diff e executar ou solicitar a validação indicada;
6. classificar evidência e apontar limites;
7. fazer pergunta adaptada de entendimento;
8. atualizar registros separados de tarefa e aprendizagem;
9. avançar somente depois de resposta e evidência suficientes.

## Comandos do projeto

### Scaffold

```bash
uv sync
uv run task test
uv run task test-cov
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
docker compose config
docker compose up --build -d --wait
docker compose ps
curl --fail --show-error http://127.0.0.1:8000/health/
docker compose run --rm web uv run task test
```

### Depois de criar modelo e Redis

```bash
uv lock
uv run task makemigrations
uv run task migrate
uv run task test
uv run task test-cov
docker compose up --build -d --wait
docker compose logs web redis
docker compose down
```

Use `docker compose down -v` somente se houver motivo explicado: `-v` apaga
volumes. Não apague o banco para “resolver” uma migration sem diagnóstico.

## Categorias de evidência

- **Estática:** arquivo, diff ou configuração.
- **Automatizada:** teste, `manage.py check`, migration check, cobertura ou
  `docker compose config`.
- **Operacional:** container saudável, rota HTTP ou conexão Redis observada.
- **Compreensão:** explicação do aluno sobre fluxo, escolha ou limite.

Uma categoria não substitui outra: mock não prova DNS Compose; Compose config
não prova que o container iniciou; health web não prova conexão Redis; cobertura
não prova que as assertivas são significativas.

## Critérios para declarar sucesso

- O status saudável do Compose deve vir de `docker compose ps` observado.
- A resposta HTTP deve ser realmente consultada; teste automatizado sozinho não
  vira evidência de navegador/cliente.
- Redis real só é declarado acessível após PING/uso observado no ambiente Compose.
- Testes unitários não dependem de Redis real; use doubles para Redis e tempo.
- Falhas de teste devem ser classificadas antes de mudar código: settings, URL,
  migration, Redis/DNS, serialização, template ou Compose.
- Não esconda falha com `except Exception`, retry infinito ou timeout exagerado.
- Não logue segredos; registre somente trechos necessários e redigidos.

## Registros pedagógicos

- `.mestre-jedi/tasks.md`: apenas checklist e próximos passos práticos.
- `.mestre-jedi/acompanhamento_academico.md`: apenas conceitos, dúvidas,
  respostas e evidências de aprendizagem, sem segredos/dados pessoais.

Ao concluir, informe missões e evidências que foram verificadas, compreensão
demonstrada e limitações ainda não validadas. Não marque progresso por volume de
código ou por “pronto”.
