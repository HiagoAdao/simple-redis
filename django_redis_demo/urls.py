"""
Configuração de URLs raiz do projeto.

Delega as rotas de cada app via `include()` — padrão Django recomendado
para projetos escaláveis com múltiplos apps.
"""
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    # Redireciona a raiz para a listagem de chamados
    path("", lambda request: redirect("callsystem:call_list")),

    # Rotas do app callsystem (delegadas via include)
    path("calls/", include("callsystem.urls", namespace="callsystem")),
]
