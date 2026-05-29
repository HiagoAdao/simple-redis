from enum import StrEnum


class CacheStatus(StrEnum):
    """Estados possíveis do cache Redis na camada DSM."""
    HIT = "CACHE_HIT"
    MISS = "CACHE_MISS"
    FALLBACK = "FALLBACK_ATIVO"


class CallStatus(StrEnum):
    """Status válidos para um chamado no banco relacional."""
    PENDING = "pending"
    RESOLVED = "resolved"


CACHE_KEY_ALL_CALLS: str = "calls:all"
CACHE_TTL_SECONDS: int = 30

SLOW_QUERY_DELAY_SECONDS: float = 1.5
