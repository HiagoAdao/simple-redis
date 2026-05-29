import json
import logging
import time
from dataclasses import dataclass, field

import redis
from django.conf import settings

from .constants import (
    CACHE_KEY_ALL_CALLS,
    CACHE_TTL_SECONDS,
    SLOW_QUERY_DELAY_SECONDS,
    CacheStatus,
)
from .dto import CallDTO
from .models import Call

logger = logging.getLogger(__name__)


@dataclass
class CallListResult:
    """
    Agrega o resultado completo da listagem de chamados para a view.
    Evita que a view precise conhecer detalhes da orquestração interna.
    """
    calls: list[CallDTO] = field(default_factory=list)
    cache_status: CacheStatus = CacheStatus.MISS
    error_message: str | None = None
    latency: float = 0.0


class CacheService:
    """
    Encapsula todas as operações com o Redis.

    Responsabilidade única: ler, gravar e invalidar entradas de cache.
    Não sabe nada sobre chamados — apenas sobre serialização/desserialização.
    """

    def __init__(self) -> None:
        self._client: redis.Redis = self._build_client()

    @staticmethod
    def _build_client() -> redis.Redis:
        """Constrói o cliente Redis com timeouts estritos para resiliência."""
        return redis.Redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=1.5,
            socket_timeout=1.0,
            decode_responses=True,
        )

    def get_calls(self) -> list[CallDTO] | None:
        """
        Retorna a lista de chamados do cache, ou `None` em caso de miss.
        """
        raw = self._client.get(CACHE_KEY_ALL_CALLS)
        if raw is None:
            return None
        items: list[dict] = json.loads(raw)
        return [CallDTO.from_dict(item) for item in items]

    def set_calls(self, calls: list[CallDTO]) -> None:
        """Serializa e grava a lista de chamados no Redis com TTL configurado."""
        payload = json.dumps([dto.as_dict() for dto in calls])
        self._client.setex(CACHE_KEY_ALL_CALLS, CACHE_TTL_SECONDS, payload)

    def invalidate(self) -> None:
        """Expurga a chave de chamados do cache (cache eviction)."""
        self._client.delete(CACHE_KEY_ALL_CALLS)
        logger.info("REDIS CACHE EVICTED: chave '%s' removida.", CACHE_KEY_ALL_CALLS)


class CallRepository:
    """
    Abstrai o acesso ao banco de dados relacional.

    Responsabilidade única: buscar entidades `Call` e converter para DTOs.
    A ordenação padrão vem da `class Meta` do modelo (ordering = ["-id"]).
    """

    @staticmethod
    def fetch_all() -> list[CallDTO]:
        """Busca todos os chamados do banco e retorna como lista de DTOs."""
        return [
            CallDTO(
                id=call.id,
                title=call.title,
                description=call.description,
                created_at=call.created_at.strftime("%d/%m/%Y %H:%M"),
                status=call.get_status_display(),
            )
            for call in Call.objects.all()
        ]

    @staticmethod
    def ensure_initial_data() -> None:
        """
        Garante a existência de dados iniciais para fins didáticos.
        Executado apenas quando o banco está completamente vazio.
        """
        if Call.objects.exists():
            return
        Call.objects.bulk_create([
            Call(
                title="Queda de conexão com gateway",
                description="Chamados de rede reportando perda de pacotes na filial sul.",
                status="pending",
            ),
            Call(
                title="Atualização de patch do SO",
                description="Agendar a atualização dos patches nos servidores Linux de homologação.",
                status="pending",
            ),
            Call(
                title="Restaurar backup base de relatórios",
                description="Solução de backup concluída com sucesso na base histórica.",
                status="resolved",
            ),
        ])


class CallListUseCase:
    """
    Orquestra a lógica de leitura de chamados com padrão Cache-Aside.

    Implementa o Princípio de Inversão de Dependência (DIP) ao receber
    `CacheService` e `CallRepository` como dependências injetáveis —
    o que facilita a substituição por mocks nos testes.

    Fluxo:
        1. Garante dados iniciais no banco.
        2. Tenta ler do cache (Redis/DSM).
        3. Se MISS: lê do banco lento, popula o cache.
        4. Se ERRO de conexão: fallback gracioso para o banco (Fail-Soft).
    """

    def __init__(
        self,
        cache: CacheService,
        repository: CallRepository,
    ) -> None:
        self._cache = cache
        self._repository = repository

    def execute(self) -> CallListResult:
        """Executa o caso de uso e retorna um `CallListResult` para a view."""
        start = time.perf_counter()
        self._repository.ensure_initial_data()

        try:
            result = self._try_from_cache()
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as exc:
            result = self._fallback(exc)

        result.latency = time.perf_counter() - start
        return result

    def _try_from_cache(self) -> CallListResult:
        """Tenta cache hit; em caso de miss, lê do banco e popula o cache."""
        cached = self._cache.get_calls()

        if cached is not None:
            logger.info("REDIS CACHE HIT: dados lidos da memória compartilhada.")
            return CallListResult(calls=cached, cache_status=CacheStatus.HIT)

        logger.info("REDIS CACHE MISS: acessando banco de dados em disco...")
        time.sleep(SLOW_QUERY_DELAY_SECONDS)

        calls = self._repository.fetch_all()
        self._cache.set_calls(calls)
        logger.info("REDIS CACHE POPULATED: gravado com TTL de %ds.", CACHE_TTL_SECONDS)

        return CallListResult(calls=calls, cache_status=CacheStatus.MISS)

    def _fallback(self, exc: Exception) -> CallListResult:
        """Fallback Fail-Soft: busca do banco sem Redis em caso de falha."""
        logger.error("REDIS CONNECTION ERROR: %s", exc)
        logger.info("FALLBACK: lendo diretamente do banco SQLite...")

        time.sleep(SLOW_QUERY_DELAY_SECONDS)
        calls = self._repository.fetch_all()

        return CallListResult(
            calls=calls,
            cache_status=CacheStatus.FALLBACK,
            error_message=str(exc),
        )


def build_call_list_use_case() -> CallListUseCase:
    """
    Factory function que monta o caso de uso com suas dependências reais.
    Centraliza a injeção de dependências para evitar acoplamento nas views.
    """
    return CallListUseCase(
        cache=CacheService(),
        repository=CallRepository(),
    )
