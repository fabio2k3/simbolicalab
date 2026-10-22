from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Evento:
    tipo: str
    datos: dict[str, Any] = field(default_factory=dict)

    def a_dict(self) -> dict[str, Any]:
        return {"tipo": self.tipo, **self.datos}

class Traza:
    def __init__(self, maximo: int = 100000) -> None:
        self.maximo = maximo
        self.eventos = list[Evento] = []
        self.truncada = False


    def emitir(self, tipo: str, /, **datos: Any) -> None:
        if "tipo" in datos:
            raise ValueError("'tipo' es reservado: usa otro nombre para ese dato")
        if len(self.eventos) >= self.maximo:
            self.truncada = True
            return
        self.eventos.append(Evento(tipo, datos))

    def a_lista(self) -> list[dict[str, Any]]:
        return [e.a_dict() for e in self.eventos]

    def a_json(self) -> str:
        return json.dumps({"truncada": self.truncada, "eventos": self.a_lista()}, ensure_ascii=False)

    def __len__(self) -> int:
        return len(self.eventos)

    def __bool__(self) -> bool:
        return True


class _TrazaNula:
    maximo = 0
    truncada = False
    eventos: list[Evento] = []

    def emitir(self, tipo:str, /, **datos: Any) -> None:
        pass

    def a_lista(self) -> list[dict[str, Any]]:
        return []

    def a_json(self) -> str:
        return '{"truncada": false, "eventos": []}'

    def __len__(self) -> int:
        return 0

    def __bool__(self) -> bool:
        return False

TRAZA_NULA = _TrazaNula()
        