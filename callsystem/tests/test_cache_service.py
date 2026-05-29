"""
Testes unitários do `CacheService`.

Verifica operações de cache (get / set / invalidate) em completo isolamento
do Redis real, usando mocks. Não toca em banco de dados.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from callsystem.constants import CACHE_KEY_ALL_CALLS, CACHE_TTL_SECONDS
from callsystem.services import CacheService

from .factories import make_call_dto


class TestCacheService:
    """Testes unitários do serviço de cache Redis."""

    @patch("callsystem.services.redis.Redis.from_url")
    def test_get_calls_retorna_none_em_cache_miss(
        self, mock_from_url: MagicMock
    ) -> None:
        """get_calls() deve retornar None quando o Redis não tiver a chave."""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_from_url.return_value = mock_client

        service = CacheService()
        resultado = service.get_calls()

        assert resultado is None
        mock_client.get.assert_called_once_with(CACHE_KEY_ALL_CALLS)

    @patch("callsystem.services.redis.Redis.from_url")
    def test_get_calls_desserializa_em_cache_hit(
        self, mock_from_url: MagicMock
    ) -> None:
        """get_calls() deve retornar lista de DTOs desserializados do cache."""
        dto = make_call_dto(call_id=10, title="Chamado Cacheado")
        payload = json.dumps([dto.as_dict()])

        mock_client = MagicMock()
        mock_client.get.return_value = payload
        mock_from_url.return_value = mock_client

        service = CacheService()
        resultado = service.get_calls()

        assert resultado is not None
        assert len(resultado) == 1
        assert resultado[0].id == 10
        assert resultado[0].title == "Chamado Cacheado"

    @patch("callsystem.services.redis.Redis.from_url")
    def test_set_calls_serializa_e_chama_setex(
        self, mock_from_url: MagicMock
    ) -> None:
        """set_calls() deve serializar DTOs e chamar setex com a chave e TTL corretos."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        dto1 = make_call_dto(call_id=1, title="Chamado A")
        dto2 = make_call_dto(call_id=2, title="Chamado B")

        service = CacheService()
        service.set_calls([dto1, dto2])

        mock_client.setex.assert_called_once()
        args, _ = mock_client.setex.call_args
        assert args[0] == CACHE_KEY_ALL_CALLS
        assert args[1] == CACHE_TTL_SECONDS

        dados_gravados = json.loads(args[2])
        assert len(dados_gravados) == 2
        assert dados_gravados[0]["title"] == "Chamado A"

    @patch("callsystem.services.redis.Redis.from_url")
    def test_invalidate_chama_delete_com_chave_correta(
        self, mock_from_url: MagicMock
    ) -> None:
        """invalidate() deve chamar delete() com a chave exata do cache."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        service = CacheService()
        service.invalidate()

        mock_client.delete.assert_called_once_with(CACHE_KEY_ALL_CALLS)
