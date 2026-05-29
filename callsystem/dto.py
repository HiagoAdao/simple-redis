import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CallDTO:
    """DTO para transporte dos dados dos chamados."""
    id: int
    title: str
    description: str
    created_at: str
    status: str

    def as_dict(self) -> dict[str, Any]:
        """Retorna representação em dicionário via `dataclasses.asdict()`."""
        return asdict(self)

    def to_json(self) -> str:
        """Serializa o DTO para string JSON para gravação no Redis."""
        return json.dumps(self.as_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CallDTO":
        """Constrói um CallDTO a partir de um dicionário validando os tipos."""
        return cls(
            id=int(data["id"]),
            title=str(data["title"]),
            description=str(data["description"]),
            created_at=str(data["created_at"]),
            status=str(data["status"]),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "CallDTO":
        """Desserializa uma string JSON de volta para o objeto CallDTO."""
        return cls.from_dict(json.loads(json_str))
