"""
Testes unitários do `CallDTO`.

Verifica serialização, desserialização e encapsulamento do DTO
sem dependência de banco de dados ou Redis.
"""
import json

import pytest

from callsystem.dto import CallDTO

from .factories import make_call_dto


@pytest.mark.django_db
class TestCallDTO:
    """Testes unitários do Data Transfer Object de Chamado."""

    def test_as_dict_retorna_todas_as_chaves(self) -> None:
        """as_dict() deve retornar dicionário com todos os campos do DTO."""
        dto = make_call_dto(call_id=42, title="Título Teste")

        resultado = dto.as_dict()

        assert resultado["id"] == 42
        assert resultado["title"] == "Título Teste"
        assert "description" in resultado
        assert "created_at" in resultado
        assert "status" in resultado

    def test_to_json_serializa_corretamente(self) -> None:
        """to_json() deve retornar string JSON válida com os dados do DTO."""
        dto = make_call_dto(call_id=1, title="Chamado JSON")

        json_str = dto.to_json()
        dados = json.loads(json_str)

        assert dados["id"] == 1
        assert dados["title"] == "Chamado JSON"

    def test_from_json_roundtrip(self) -> None:
        """from_json(to_json()) deve reconstituir um DTO idêntico ao original."""
        original = make_call_dto(call_id=7, status="Resolvido")

        reconstruido = CallDTO.from_json(original.to_json())

        assert reconstruido == original

    def test_from_dict_converte_tipos_corretamente(self) -> None:
        """from_dict() deve coercionar id para int mesmo se vier como string."""
        data = {
            "id": "99",
            "title": "Teste",
            "description": "Desc",
            "created_at": "29/05/2026 00:00",
            "status": "Pendente",
        }

        dto = CallDTO.from_dict(data)

        assert isinstance(dto.id, int)
        assert dto.id == 99

    def test_imutabilidade_frozen(self) -> None:
        """CallDTO é frozen=True: qualquer tentativa de mutação deve lançar erro."""
        dto = make_call_dto()

        with pytest.raises(Exception):
            dto.title = "Modificado"  # type: ignore[misc]
