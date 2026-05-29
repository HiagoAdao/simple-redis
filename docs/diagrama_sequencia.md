# Diagrama de Sequência — Aula de Redis com Django & Python

Este documento apresenta o diagrama de sequência detalhado que representa a arquitetura refatorada do projeto `django-redis-demo` seguindo os princípios de **Clean Code**, **SOLID** (SRP, DIP) e a separação clara de responsabilidades com o padrão **Cache-Aside** (Lazy Loading) e suporte a **Fail-Soft (Fallback)**.

## 📊 Diagrama de Sequência da Listagem de Chamados

```mermaid
sequenceDiagram
    actor C as "Cliente"
    participant V as "View (call_list)"
    participant UC as "CallListUseCase"
    participant CS as "CacheService"
    participant R as "Redis (DSM)"
    participant RP as "CallRepository"
    participant DB as "Banco de Dados (SQLite)"

    C->>V: GET /calls/
    V->>UC: execute()
    
    rect rgb(240, 248, 255)
        Note over UC,CS: Tentativa de leitura do Cache (Cache-Aside)
        UC->>CS: get_calls()
        
        alt Sucesso na Conexão com Redis
            CS->>R: GET calls:all
            
            alt Cache Hit (Dados presentes)
                R-->>CS: JSON estruturado
                Note over CS: Desserializa JSON para list[CallDTO]
                CS-->>UC: list[CallDTO] (CACHE_HIT)
            else Cache Miss (Dados ausentes ou expirados)
                R-->>CS: None
                CS-->>UC: None (CACHE_MISS)
                
                Note over UC,RP: Busca no Banco de Dados
                UC->>RP: get_all()
                RP->>DB: SELECT * FROM callsystem_call
                DB-->>RP: Lista de instâncias Call (Models)
                Note over RP: Mapeia Models para list[CallDTO]
                RP-->>UC: list[CallDTO]
                
                Note over UC,CS: Atualiza o Cache assincronamente
                UC->>CS: set_calls(calls)
                CS->>R: SETEX calls:all (TTL=30s)
                R-->>CS: OK
            end
            
        else Falha na Conexão com Redis (Fail-Soft)
            CS-xR: Falha de conexão / Timeout
            Note over CS: Captura ConnectionError / TimeoutError
            CS-->>UC: Lança exceção de cache/conexão
            Note over UC: Captura erro e ativa Fallback
            
            UC->>RP: get_all()
            RP->>DB: SELECT * FROM callsystem_call
            DB-->>RP: Lista de instâncias Call (Models)
            Note over RP: Mapeia Models para list[CallDTO]
            RP-->>UC: list[CallDTO] (FALLBACK_ATIVO)
        end
    end

    Note over UC: Constrói CallListResult (calls, cache_status, latency)
    UC-->>V: CallListResult
    Note over V: Renderiza callsystem/call_list.html
    V-->>C: HTML renderizado (HTTP 200)
```

## 🔍 Explicação dos Componentes no Fluxo

1. **`View (call_list)`**: Tem responsabilidade única baseada no protocolo HTTP (SRP). Recebe o request, delega toda a orquestração de lógica para o caso de uso e renderiza o template HTML correspondente.
2. **`CallListUseCase`**: Orquestrador central que implementa as regras de negócio distribuídas (Cache-Aside + Fail-Soft). Recebe `CacheService` e `CallRepository` via injeção de dependências (DIP).
3. **`CacheService`**: Encapsula totalmente a conexão física e lógica com o **Upstash Redis**. Responsável por serializar/desserializar a lista de `CallDTO` utilizando representações em JSON.
4. **`CallRepository`**: Responsável exclusivo por se comunicar com o banco de dados SQLite. Converte o resultado bruto retornado pelas queries do ORM Django para objetos imutáveis e padronizados `CallDTO` antes de trafegá-los para outras camadas.
5. **`CallDTO`**: Nosso contrato estruturado e imutável que trafega os dados de forma limpa pela aplicação e pelo cache compartilhado distribuído.
