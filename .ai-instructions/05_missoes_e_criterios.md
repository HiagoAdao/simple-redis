# 05 — Missões e critérios de avaliação

Apresente uma missão por vez. Use a sequência para escolher o próximo passo,
não como um bloco de instruções para colar e executar em lote.

## Missão 0 — compreender o scaffold

**Objetivo:** entender o container web, o roteamento Django e a diferença entre
health HTTP e dependências de negócio.

**Pré-requisito:** concluir o Portão zero de ambiente: SO/shell identificados e
Docker validado para fluxo container, ou `uv sync`/Python 3.12+/taskipy validados
para fluxo local.

**Trabalho:** rodar testes, subir o Compose, consultar `/health/` e localizar o
caminho URLconf → view → `JsonResponse`.

**Critérios:** HTTP 200 com JSON correto, POST recusado com 405, serviço web
saudável; o aluno explica o que o health check confirma e por que a porta está
limitada ao loopback.

**Evidência:** saída dos testes, `docker compose ps` e resposta HTTP observada.

## Missão 1 — modelo `Call` e migration

**Objetivo:** representar chamados persistidos e estados permitidos em SQLite.

**Trabalho:** criar `callsystem`, registrá-la no settings, modelar `Call` e gerar
uma migration.

**Critérios:** campos, choices, default, ordenação e rótulos atendem ao contrato
de `03_arquitetura_e_estado_final.md`; `manage.py check` e migration check passam.
Explicar que migration é uma alteração de esquema reproduzível, não um banco
comitado.

**Evidência:** diff da app/migration e saída dos comandos Django.

## Missão 2 — estados e DTO

**Objetivo:** distinguir modelo ORM de formato portátil enviado ao cache e à UI.

**Trabalho:** definir enums/constantes e `CallDTO` congelado com conversões
explícitas para dicionário e JSON.

**Critérios:** teste de round-trip, campos/tipos, imutabilidade com exceção
específica e comportamento claro para dicionário malformado. Não serializar
Model/QuerySet nem tratar `Any` como validação.

**Evidência:** testes e explicação sobre por que o Redis precisa de dados
serializados.

## Missão 3 — adicionar Redis ao Compose

**Objetivo:** compreender rede Docker, descoberta de serviço e ordem de startup.

**Trabalho:** adicionar serviço Redis, health check, DNS interno e dependência
`service_healthy`; adicionar o cliente `redis` em `pyproject.toml` e atualizar o
lock usando `uv lock`.

**Critérios:** `docker compose config` válido; `docker compose ps` mostra Redis
saudável; PING real originado de web funciona; segredo/porta não é exposto sem
motivo; o aluno explica por que hostname é `redis` e não localhost.

**Evidência:** diff, status dos serviços e PING. Mock não comprova rede real.

## Missão 4 — serviço de cache

**Objetivo:** encapsular operações Redis e serialização em uma fronteira testável.

**Trabalho:** criar cliente via `settings.REDIS_URL`, timeouts, `get_calls`,
`set_calls` com TTL e `invalidate`.

**Critérios:** testes de hit/miss, chave/TTL, payload, invalidação e política para
payload JSON inválido; mocks isolam Redis. A política não deve mascarar erros de
programação como cache miss.

**Evidência:** testes automatizados e explicação do TTL.

## Missão 5 — repositório e seed

**Objetivo:** isolar ORM e gerar dados de demonstração sem duplicação.

**Trabalho:** implementar `fetch_all()` e a inicialização dos três chamados
didáticos.

**Critérios:** repositório não conhece Redis/views; chamadas repetidas não
duplicam dados; cobrir banco vazio e populado. Explicar que check-then-create pode
ter race em inicializações concorrentes e avaliar se seed deve sair do caminho de
cada request.

**Evidência:** testes com banco isolado e análise do efeito de seed.

## Missão 6 — caso de uso Cache-Aside

**Objetivo:** orquestrar hit, miss, população, latência e fallback fora da view.

**Trabalho:** implementar `CallListResult`, `CallListUseCase.execute()`, factory
de composição e tratamento de conexão/timeout Redis.

**Critérios:** teste unitário direto do caso de uso com repositório/cache fake;
hit evita `fetch_all()` e atraso; miss consulta e grava; falha de conexão usa
SQLite sem segunda tentativa de Redis; JSON/programação inesperados não são
silenciados. Registrar que a referência atual semeia antes da leitura cacheada e,
portanto, consulta SQLite via `exists()` mesmo no hit.

**Evidência:** testes diretos dos cenários e diagrama do caminho de execução.

## Missão 7 — HTTP, view e interface

**Objetivo:** adaptar o resultado do caso de uso para HTTP sem mover regras de
cache para a view.

**Trabalho:** URLs nomeadas, view da listagem, template observável e ação de
limpeza.

**Critérios:** template mostra chamados, status, latência, fallback e destino
Redis sanitizado; UI usa POST + CSRF para invalidar; não há Redis/ORM complexo na
view; testes cobrem conteúdo/status/redirect/métodos.

**Evidência:** testes Django e comportamento local observado.

## Missão 8 — documentação de sequência

**Objetivo:** ensinar a manter documentação arquitetural sincronizada com as
chamadas reais.

**Trabalho:** revisar `docs/diagrama_sequencia.md` junto com o grafo e o código.

**Critérios:** nomes correspondem a `fetch_all`, `set_calls` e `execute`; o
diagrama não descreve cache assíncrono quando o caminho é síncrono; registra onde
o seed acontece (antes do Redis no fluxo atual, ou fora do request se o aluno
justificou a melhoria), hit/miss, fallback, renderização e invalidação; estudante
aponta uma limitação que o desenho não representa.

**Evidência:** diff do diagrama e walkthrough do fluxo.

## Missão 9 — integração e indisponibilidade

**Objetivo:** validar em Compose o que os doubles não podem provar.

**Trabalho:** observar primeira leitura, hit, invalidação e comportamento com
Redis parado de forma controlada; restaurar o serviço após o experimento.

**Critérios:** SQLite continua sendo fonte; fallback é visível; estado de cada
container é lido; não há credenciais em logs; o aluno diferencia resultado
automatizado de operacional.

**Evidência:** saída de Compose/HTTP e descrição do cenário de falha reproduzido.

## Missão 10 — qualidade final

**Objetivo:** revisar correção, testes, segurança, config e documentação.

**Critérios:**

- testes unitários isolam Redis e tempo;
- há testes diretos de use case e repository, além dos testes HTTP;
- cobertura configurada mede apenas código de aplicação, excluindo testes e
  migrations, com limite mínimo de 90%;
- `uv run task test`, `uv run task test-cov`, `uv run python manage.py check` e
  `uv run python manage.py makemigrations --check --dry-run` passam;
- `docker compose config` é válido e a stack fica saudável;
- README e diagrama descrevem exatamente o comportamento executado;
- o aluno explica qual evidência prova cada requisito e quais riscos permanecem.

Cobertura percentual não substitui assertivas significativas. Use a lista de
revisão de `06_qualidade_e_pontos_de_atencao.md`.
