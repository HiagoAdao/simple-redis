"""
Fábricas e fixtures centralizadas para os testes do app `callsystem`.

Centralizar a criação de dados de teste (padrão Factory) garante:
- DRY: evita repetição de `Call.objects.create(...)` em cada teste
- Consistência: dados padronizados e legíveis
- Flexibilidade: parâmetros sobrescritíveis por teste
"""
from callsystem.dto import CallDTO
from callsystem.models import Call


def make_call(
    title: str = "Chamado de Teste",
    description: str = "Descrição padrão do chamado de teste",
    status: str = "pending",
) -> Call:
    """
    Cria e persiste um `Call` no banco de testes (SQLite in-memory).
    Parâmetros são sobrescritíveis para variações de cenário.
    """
    return Call.objects.create(
        title=title,
        description=description,
        status=status,
    )


def make_call_dto(
    call_id: int = 1,
    title: str = "Chamado DTO",
    description: str = "Descrição do DTO de teste",
    created_at: str = "29/05/2026 16:00",
    status: str = "Pendente",
) -> CallDTO:
    """
    Constrói um `CallDTO` sem tocar no banco de dados.
    Útil para testar serialização/desserialização em isolamento.
    """
    return CallDTO(
        id=call_id,
        title=title,
        description=description,
        created_at=created_at,
        status=status,
    )
