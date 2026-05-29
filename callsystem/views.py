import logging

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .services import CacheService, build_call_list_use_case

logger = logging.getLogger(__name__)


def call_list(request: HttpRequest) -> HttpResponse:
    """Lista os chamados aplicando o padrão Cache-Aside."""
    result = build_call_list_use_case().execute()

    redis_display_url = (
        settings.REDIS_URL.split("@")[-1]
        if "@" in settings.REDIS_URL
        else settings.REDIS_URL
    )

    context = {
        "calls": result.calls,
        "latency": f"{result.latency:.3f}",
        "cache_status": result.cache_status,
        "redis_url": redis_display_url,
        "error_message": result.error_message,
    }
    return render(request, "callsystem/call_list.html", context)


def clear_cache(request: HttpRequest) -> HttpResponse:
    """Limpa a chave de chamados do Redis."""
    try:
        CacheService().invalidate()
    except Exception as exc:
        logger.error("Falha ao limpar cache: %s", exc)

    return redirect("callsystem:call_list")
