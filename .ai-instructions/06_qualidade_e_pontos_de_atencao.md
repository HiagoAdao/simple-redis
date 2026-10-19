# 06 — Qualidade, auditoria da referência e lacunas a ensinar

Este guia foi atualizado após inspeção do código completo em `feature/django-redis` (antiga `main`) via
codebase-memory-mcp e leitura direta dos trechos sinalizados como parcialmente
indexados. A implementação dessa branch é a referência funcional do laboratório,
mas contém atalhos didáticos e pontos que não devem ser apresentados como boas
práticas de produção. Preserve o conceito/contrato útil e conduza o aluno a
entender ou corrigir as limitações abaixo.

## Achados concretos na referência completa

| Fonte | Comportamento encontrado | Orientação ao agente |
|---|---|---|
| `django_redis_demo/settings.py` | `SECRET_KEY` fixa no fonte, `DEBUG=True` e `ALLOWED_HOSTS=['*']`; só `REDIS_URL` vem do ambiente. | Não reproduzir defaults de produção. Usar configuração por ambiente e explicar os valores locais. |
| `callsystem/views.py::clear_cache` | Limpa Redis por uma view chamada via link GET e captura `Exception`. | Mutação deve ser POST protegido por CSRF; capturar apenas falhas Redis esperadas e não esconder bugs. |
| `callsystem/templates/callsystem/call_list.html` | O botão de limpeza é um link GET; a UI mostra métricas e um destino Redis. | Trocar para formulário POST; testar sanitização e não renderizar erro/URL com credenciais. |
| `callsystem/services.py::CallListUseCase.execute` | Chama `ensure_initial_data()` antes da leitura Redis; depois captura ConnectionError/TimeoutError. | Cache hit evita `fetch_all()` e `sleep`, mas a verificação de seed consulta SQLite. Não alegar zero acesso ao banco. |
| `callsystem/services.py::CallRepository.ensure_initial_data` | Usa `exists()` seguido de `bulk_create()` no caminho de request. | É idempotente em chamadas sequenciais, mas check-then-create pode correr; discutir seed em comando/migration e evitar trabalho DB por request. |
| `GET /calls/` + seed | A primeira leitura pode gravar os chamados de exemplo durante uma requisição GET. | Um GET deve ser seguro; preferir preparar dados fora do request (migration/command/fixture) e testar a tela com DB já preparado. |
| `callsystem/services.py::_fallback` | Recebe `Exception`, loga sua mensagem e copia `str(exc)` para `error_message`. | Tipar para as exceções esperadas; logs/contexto não devem vazar endpoint ou credenciais. UI deve usar um indicador seguro, não texto bruto. |
| `callsystem/services.py::_try_from_cache` | Faz `time.sleep(1.5)` síncrono para simular lentidão. | É atraso didático e bloqueia um worker síncrono; mockar em testes e declarar que não modela latência real de banco. |
| `callsystem/dto.py::CallDTO` | Usa `Any` em mapas e converte campos com `int()`/`str()` sem validar a forma inteira do payload. | Explicar coercion versus validação; tipar o contrato e testar campos ausentes/tipos/payload inválido. |
| `callsystem/tests/test_dto.py` | Imutabilidade usa `pytest.raises(Exception)`. | Asserir a exceção específica de dataclass congelado (`FrozenInstanceError`). |
| `pyproject.toml` | `--cov=callsystem` também inclui `callsystem/tests` na medição; não há `--cov-fail-under`. | Medir produção, excluir testes/migrations e tornar o limite explícito; cobertura dos testes não pode inflar a da aplicação. |
| `callsystem/tests/` | Há 14 testes: 4 de `CacheService`, 5 de DTO, 5 de views. Hit/miss/fallback são exercitados pela view; não há teste unitário direto do caso de uso/repositório. | Adicionar testes isolados do caso de uso e repository; manter os testes HTTP como integração entre Django e camadas. |
| `docs/diagrama_sequencia.md` | Usa nome `get_all()` que não existe e chama atualização do cache de assíncrona, embora `fetch_all()` e `set_calls()` ocorram sincronamente. | Atualizar o diagrama junto da implementação; documentação antiga é fonte de divergência, não contrato. |
| `README.md` | Apresenta latências exemplificativas como `<10ms`/`~1.5s`, que variam por ambiente e não são garantias. | Marcar números como medições observadas ou valores didáticos, nunca como SLO universal. |
| `docker-compose.yml` | Publica Redis em `6379`, usa nomes de container fixos, dependência Redis saudável; web não tem health check HTTP. | Não expor Redis sem necessidade; preferir DNS do serviço; manter health de Redis distinto do endpoint web. |
| `Dockerfile` | Usa imagem `uv:latest`, `uv sync --no-dev` e o projeto executa com bind mount em `/app`. | Fixar `uv`, esclarecer grupo de deps da imagem e manter o virtualenv fora da árvore montada. |

Os 14 testes da referência passam no ambiente analisado. O comando original de
cobertura reporta 99%, mas inclui os próprios testes em `callsystem`; esse número
não é cobertura isolada do código de produção. No relatório, a criação do seed e
`Call.__str__` também ficam sem execução. Isso demonstra por que se deve
inspecionar os arquivos/linhas medidos, não somente repetir o percentual.

## Política de tratamento dos pontos

### Corrigir no resultado didático

- Configuração local vem do ambiente e tem fallback explicitamente local; nunca
  recomendar a chave fixa/hosts `*` como produção.
- Limpeza de cache usa POST + CSRF.
- Fallback captura somente erros Redis previstos. Falha de JSON, tipo inválido,
  erro de programação ou ORM não vira “Redis fora do ar”.
- Logs e HTML não contêm segredo, URL com credencial, stack trace ou exceção bruta.
- Testes usam tipos de exceção específicos e medem módulos de aplicação, não
  arquivos de teste.
- Diagrama e README são atualizados quando método, fluxo ou comando mudar.

### Tornar explícito como limitação do laboratório

- `sleep(1.5)` é uma simulação visual de custo, não benchmark de SQLite/Redis.
- O cache é uma única chave `calls:all` para todos os registros; TTL é 30s e não
  há operações CRUD que invalidem por entidade.
- Seed atual ocorre no caminho de leitura e não é atomicamente seguro contra
  múltiplos processos concorrentes.
- `runserver`, DEBUG e composição local não são receita de produção.
- O serviço Redis saudável no Compose não garante que toda chamada da app vá
  funcionar; timeout, autenticação, DNS e operação da chave devem ser testados.

Não aumente o escopo para resolver todos os cenários distribuídos de produção.
O aluno deve conseguir explicar as simplificações e os riscos, e implementar as
correções mínimas pedidas pelas missões.

## Matriz mínima de testes de qualidade

### DTO/modelo/repositório

- DTO: chaves, round-trip, coerção/validação, campos ausentes e imutabilidade;
- conversão de `created_at` e status do modelo para a representação esperada;
- modelo: choices/default/ordenação e `__str__`;
- seed com banco vazio, já populado e repetição; discutir concorrência;
- repository não constrói cliente Redis nem resposta HTTP.

### CacheService

- miss (`None`) e hit com payload completo;
- `setex` recebe a chave/TTL certos e JSON esperado;
- invalidação apaga só a chave que pertence à listagem;
- parâmetros de cliente (URL, timeouts, `decode_responses`) são verificáveis;
- payload JSON inválido/estrutura inválida segue política explícita, distinta de
  falha de conexão;
- ConnectionError e TimeoutError não exigem servidor real nos testes unitários.

### Caso de uso

- teste direto com cache e repositório doubles;
- hit não chama `fetch_all` nem o atraso;
- miss busca, grava e retorna status correto;
- falha Redis usa repositório e marca fallback;
- erro inesperado continua propagando;
- mede a latência de ponta a ponta; se `perf_counter`/sleep for patchado, validar
  o resultado sem depender do relógio real.

### HTTP/integração

- view renderiza resultado e não contém lógica de cache;
- POST de invalidação chama `invalidate`, aplica CSRF conforme contrato e
  redireciona; GET não altera cache;
- mensagem de fallback não revela exceção nem segredo;
- mocks cobrem lógica local; Compose separado verifica DNS e Redis real.

### Cobertura

Configurar `coverage` para `django_redis_demo` e `callsystem`, omitindo
`*/tests/*`, `*/migrations/*` e boilerplate sem comportamento relevante. A tarefa
de cobertura deve ter mínimo de 90% e cobrir ramos importantes; não exclua um
módulo porque sua cobertura está baixa sem justificar.
