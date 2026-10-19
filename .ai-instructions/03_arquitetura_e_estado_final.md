# 03 — Arquitetura e contrato do estado final

Este arquivo é a fonte de verdade da jornada. A estrutura abaixo descreve o
resultado funcional a ser construído a partir do scaffold. Oriente a
implementação por etapas; não entregue o sistema completo para cópia.

## Estado inicial do checkout

```text
manage.py
django_redis_demo/
├── settings.py
├── urls.py
├── views.py             # GET /health/
└── wsgi.py
tests/
└── test_health.py
Dockerfile
docker-compose.yml       # somente web, ainda sem Redis
pyproject.toml
uv.lock
```

O health check é uma rota operacional do scaffold. Ele não é a funcionalidade de
negócio e deve continuar disponível durante a evolução.

## Estrutura-alvo

```text
django_redis_demo/
├── settings.py          # Django, SQLite e configuração via ambiente
├── urls.py              # health e montagem das rotas de chamados
├── views.py             # health check
└── wsgi.py
callsystem/
├── apps.py
├── constants.py         # estados, chave e TTL
├── dto.py               # CallDTO imutável e serialização
├── models.py            # modelo Call
├── services.py          # cache, repositório e caso de uso
├── urls.py
├── views.py             # adaptação HTTP → caso de uso/template
├── migrations/
├── templates/callsystem/call_list.html
└── tests/
    ├── factories.py
    ├── test_dto.py
    ├── test_cache_service.py
    └── test_views.py
tests/
└── test_health.py         # contrato operacional já existente no scaffold
docs/
└── diagrama_sequencia.md   # diagrama sincronizado com chamadas reais
```

Os testes podem ser reorganizados se o aluno justificar a estrutura e mantiver
os mesmos contratos de validação.

## Fluxo funcional

```text
GET /calls/
  → URL Django
  → view chama o caso de uso
  → caso de uso verifica/semeia dados iniciais no SQLite
  → CacheService tenta ler a chave calls:all no Redis
      ├─ HIT: desserializa DTOs e retorna sem consulta lenta
      ├─ MISS: repositório consulta SQLite, simula latência e grava JSON no Redis
      └─ Redis indisponível: busca SQLite e retorna FALLBACK sem derrubar a página
  → view envia os dados e métricas ao template
```

Uma ação de limpeza remove a chave de cache; a próxima leitura deve demonstrar
um miss. As métricas e mensagens exibidas devem vir do resultado do caso de uso,
não de lógica de cache colocada na view.

O comportamento atual de referência chama `ensure_initial_data()` antes de
consultar o cache. Como esse método executa `Call.objects.exists()`, um cache hit
evita a leitura completa do repositório e o atraso simulado, mas ainda toca o
SQLite. Não descreva esse hit como “zero acesso ao banco”. A avaliação dessa
decisão e uma alternativa de seed fora do caminho HTTP estão em
`06_qualidade_e_pontos_de_atencao.md`.

## Contratos principais do código

### `callsystem.constants`

- `CacheStatus(StrEnum)`: `HIT="CACHE_HIT"`, `MISS="CACHE_MISS"` e
  `FALLBACK="FALLBACK_ATIVO"`.
- `CallStatus(StrEnum)`: `PENDING="pending"` e `RESOLVED="resolved"`.
- Constantes: `CACHE_KEY_ALL_CALLS="calls:all"`, TTL de 30 segundos e atraso
  didático de 1,5 segundo.

Centralize valores usados em mais de uma camada; não crie abstrações ou
enumerações para valores que não tenham um contrato real.

## Modelo e estados

Implemente `Call` em `callsystem/models.py` com:

| Campo | Tipo/conceito | Regra esperada |
|---|---|---|
| `id` | chave primária Django | gerada automaticamente |
| `title` | texto curto | até 150 caracteres |
| `description` | texto | descrição do chamado |
| `created_at` | data/hora | preenchida automaticamente na criação |
| `status` | escolha finita | `pending` ou `resolved`, padrão `pending` |

Ordene a lista por id decrescente e configure nomes de exibição em português.
Crie e versiona a migration; não dependa de criação manual de tabela.

Declare em `constants.py` enums `StrEnum` para status de cache (`CACHE_HIT`,
`CACHE_MISS`, `FALLBACK_ATIVO`) e de chamado (`pending`, `resolved`). Centralize
a chave do cache `calls:all`, TTL de 30 segundos e atraso didático de cache miss
de 1,5 segundo. Não espalhe strings mágicas pela lógica.

## DTO e serialização

`CallDTO` é um `dataclass(frozen=True)` com os campos transportados para o
template/cache: `id`, `title`, `description`, `created_at` formatado e `status`
de exibição.

O contrato público deve permitir:

- criar o DTO a partir dos campos do modelo;
- converter para dicionário com chaves explícitas;
- serializar/desserializar JSON de forma reversível;
- reconstruir uma lista de DTOs a partir do payload armazenado no Redis;
- impedir alteração acidental dos campos depois da criação.

Não serializar instâncias de Model ou QuerySets diretamente. O teste deve
verificar round-trip, tipos, campos e imutabilidade com a exceção específica
esperada.

## Camadas em `callsystem/services.py`

Comece com poucas classes coesas no módulo existente; novos módulos só são
necessários se a responsabilidade ou o tamanho justificar.

### `CacheService`

- Cria cliente Redis a partir de `settings.REDIS_URL`.
- Define timeout de conexão e de socket para que uma falha não bloqueie a
  aplicação indefinidamente; decodifica respostas em texto.
- `get_calls()` retorna `None` para cache miss e lista de `CallDTO` para hit.
- `set_calls()` serializa os DTOs e grava com TTL de 30 segundos.
- `invalidate()` apaga somente a chave correspondente à listagem.
- Não deve converter falhas de JSON/programação em “cache miss” silencioso.

### `CallRepository`

- `fetch_all()` busca os chamados usando ORM e converte resultados em DTOs.
- `ensure_initial_data()` garante os três registros didáticos iniciais somente
  quando a tabela está vazia; repetir a chamada não deve duplicar dados.
- Não conhece Redis nem detalhes HTTP.

### Resultado e caso de uso

`CallListResult` deve carregar `calls: list[CallDTO]`, `cache_status:
CacheStatus`, `error_message: str | None` e `latency: float`. Use
`default_factory` para coleções mutáveis. A referência atual altera `latency`
após construir o resultado; avalie se prefere construir o resultado final sem
essa mutação e cubra o contrato em teste.

`CallListUseCase` recebe `CacheService` e `CallRepository` por dependência. Ao
executar, mede latência, tenta cache hit, trata miss, popula cache após leitura
do SQLite e, se ocorrer falha de conexão/timeout Redis prevista, executa
fallback SQLite. A falha Redis deve ser estreitamente capturada: erros
inesperados continuam visíveis. Uma factory pode montar as implementações reais
para a view sem esconder as dependências nos testes.

O resultado deve ter os campos tipados `calls: list[CallDTO]`,
`cache_status: CacheStatus`, `error_message: str | None` e `latency: float`.
`CallListUseCase.execute()` é a entrada do caso de uso. Extraia a tentativa de
cache e o fallback em métodos privados pequenos se isso tornar os fluxos mais
fáceis de testar e explicar.

O cache hit não deve executar o atraso de miss. O fallback não deve tentar
gravar no Redis indisponível novamente no mesmo caminho.

## Views, URLs e template

- `django_redis_demo/urls.py` redireciona `/` para a listagem e inclui as rotas
  `callsystem` sob `/calls/`.
- `callsystem/urls.py` define namespace `callsystem`, uma rota de listagem e uma
  ação de invalidação com nomes claros.
- Preserve também o `GET /health/` fornecido pelo scaffold. Ele é um contrato
  inicial deste laboratório, embora não exista no código de referência atual em
  `feature/django-redis` (antiga `main`).
- `call_list` converte o resultado do caso de uso em contexto e renderiza
  `callsystem/call_list.html`.
- A página apresenta os chamados, status HIT/MISS/FALLBACK, latência, indicação
  de endpoint Redis sanitizada e ação de limpar cache.
- Escape de template do Django deve permanecer ativo. Não renderize stack traces,
  segredos ou payload bruto.
- A invalidação precisa ter comportamento verificável e mensagem/redirect
  previsível. Como altera estado, a interface deve enviar POST e a aplicação
  deve manter a proteção CSRF; a referência atual usa um link GET e isso não deve
  ser reproduzido sem discussão.
- As views não devem dormir, serializar payloads, fazer consultas de domínio
  complexas ou instanciar cliente Redis diretamente.

Detalhes de ambiente, settings, migrations, Docker e DNS entre serviços ficam em
`04_integracoes_e_operacao.md` para não misturar contratos de aplicação com
execução operacional.

## Contratos observáveis do resultado final

1. `/health/` responde HTTP 200 com JSON `{"status":"ok"}` e só aceita GET.
2. `/calls/` renderiza os registros persistidos em SQLite.
3. Primeira leitura sem chave faz miss, consulta banco, grava com TTL e mostra
   `CACHE_MISS`.
4. Leitura seguinte antes da expiração faz hit sem atraso didático e mostra
   `CACHE_HIT`.
5. Invalidação seguida de leitura volta a fazer miss.
6. Redis indisponível não impede a leitura no SQLite; a resposta sinaliza
   `FALLBACK_ATIVO` sem expor segredo.
7. Dados e estados são testáveis sem conexão real com Redis nos testes unitários.
8. O ambiente Compose completo inicia web e Redis; os critérios operacionais
   estão em `04_integracoes_e_operacao.md`.
