import json
from unittest.mock import MagicMock, patch

import pytest
import redis
from django.test import Client
from django.urls import reverse

from callsystem.constants import CacheStatus
from callsystem.models import Call

from .factories import make_call, make_call_dto


@pytest.fixture(autouse=True)
def db_setup(db):
    """Garante banco limpo e 2 chamados pré-criados para cada teste."""
    Call.objects.all().delete()
    make_call(title="Chamado de Teste 1", status="pending")
    make_call(title="Chamado de Teste 2", status="resolved")


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def url_call_list() -> str:
    return reverse("callsystem:call_list")


@pytest.fixture
def url_clear_cache() -> str:
    return reverse("callsystem:clear_cache")


@pytest.mark.django_db
class TestCallListView:
    """Testes de integração para a view `call_list`."""

    @patch("callsystem.services.CacheService.get_calls", return_value=None)
    @patch("callsystem.services.CacheService.set_calls")
    @patch("callsystem.services.CacheService._build_client", return_value=MagicMock())
    @patch("time.sleep")
    def test_cache_miss_flow(
        self,
        mock_sleep: MagicMock,
        mock_build: MagicMock,
        mock_set: MagicMock,
        mock_get: MagicMock,
        client: Client,
        url_call_list: str,
    ) -> None:
        """
        CACHE MISS: deve buscar no banco (com delay), gravar no Redis e
        renderizar a tela com status CACHE_MISS e 2 chamados.
        """
        response = client.get(url_call_list)

        assert response.status_code == 200
        assert response.context["cache_status"] == CacheStatus.MISS
        assert len(response.context["calls"]) == 2

        mock_sleep.assert_called_once_with(1.5)

        mock_set.assert_called_once()

    @patch("callsystem.services.CacheService._build_client", return_value=MagicMock())
    @patch("callsystem.services.CacheService.get_calls")
    @patch("time.sleep")
    def test_cache_hit_flow(
        self,
        mock_sleep: MagicMock,
        mock_get: MagicMock,
        mock_build: MagicMock,
        client: Client,
        url_call_list: str,
    ) -> None:
        """
        CACHE HIT: deve retornar dados do Redis sem tocar no banco nem no sleep.
        """
        dto_cacheado = make_call_dto(call_id=99, title="Chamado Cacheado")
        mock_get.return_value = [dto_cacheado]

        response = client.get(url_call_list)

        assert response.status_code == 200
        assert response.context["cache_status"] == CacheStatus.HIT
        assert len(response.context["calls"]) == 1
        assert response.context["calls"][0].title == "Chamado Cacheado"

        mock_sleep.assert_not_called()

    @patch(
        "callsystem.services.CacheService.get_calls",
        side_effect=redis.exceptions.ConnectionError("Falha de DNS no Upstash"),
    )
    @patch("callsystem.services.CacheService._build_client", return_value=MagicMock())
    @patch("time.sleep")
    def test_fail_soft_resilience_flow(
        self,
        mock_sleep: MagicMock,
        mock_build: MagicMock,
        mock_get: MagicMock,
        client: Client,
        url_call_list: str,
    ) -> None:
        """
        FAIL-SOFT: Redis indisponível → app não crasha, busca do banco,
        exibe status FALLBACK_ATIVO e a mensagem de erro ao usuário.
        """
        response = client.get(url_call_list)

        assert response.status_code == 200
        assert response.context["cache_status"] == CacheStatus.FALLBACK
        assert "Falha de DNS" in response.context["error_message"]
        assert len(response.context["calls"]) == 2

        mock_sleep.assert_called_once_with(1.5)


@pytest.mark.django_db
class TestClearCacheView:
    """Testes de integração para a view `clear_cache`."""

    @patch("callsystem.views.CacheService")
    def test_clear_cache_redireciona_para_listagem(
        self,
        mock_cache_cls: MagicMock,
        client: Client,
        url_clear_cache: str,
    ) -> None:
        """clear_cache() deve chamar invalidate() e redirecionar para call_list."""
        mock_instance = MagicMock()
        mock_cache_cls.return_value = mock_instance

        response = client.get(url_clear_cache)

        assert response.status_code == 302
        mock_instance.invalidate.assert_called_once()

    @patch("callsystem.views.CacheService")
    def test_clear_cache_redireciona_mesmo_com_erro_redis(
        self,
        mock_cache_cls: MagicMock,
        client: Client,
        url_clear_cache: str,
    ) -> None:
        """clear_cache() não deve crashar se o Redis estiver indisponível."""
        mock_instance = MagicMock()
        mock_instance.invalidate.side_effect = redis.exceptions.ConnectionError("down")
        mock_cache_cls.return_value = mock_instance

        response = client.get(url_clear_cache)

        assert response.status_code == 302
