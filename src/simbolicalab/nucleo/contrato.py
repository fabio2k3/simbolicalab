from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, TypeAlias, runtime_checkable

from .contador import Contador
from .traza import Traza


Datos: TypeAlias = Any
Gramatica: TypeAlias = Any

@dataclass(frozen=True)
class Presupuesto:
    operaciones: int | None = None

    def nuevo_contador(self) -> Contador:
        return Contador(self.operaciones)

@dataclass
class Resultado:
    expression: Any
    error: float
    operaciones: int
    agotado: bool = False
    detalle: dict[str, Any]

@runtime_checkable
class Solver(Protocol):
    nombre: str

    def resolver(self, datos: Datos, gramatica: Gramatica, presupuesto: Presupuesto, traza: Traza | None = None) -> Resultado:
        ...