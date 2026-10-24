from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, TYPE_CHECKING, runtime_checkable

from .contador import Contador
from .traza import Traza

if TYPE_CHECKING:
    from ..rs.datos import Datos
    from ..rs.expresion import Expr
    from ..rs.gramatica import Gramatica

@dataclass(frozen=True)
class Presupuesto:
    operaciones: int | None = None

    def nuevo_contador(self) -> Contador:
        return Contador(self.operaciones)

@dataclass
class Resultado:
    expresion: Expr | None
    error: float
    operaciones: int
    detalle: dict[str, Any] =field(default_factory=dict)
    agotado: bool = False
    

@runtime_checkable
class Solver(Protocol):
    nombre: str

    def resolver(self, datos: Datos, gramatica: Gramatica, presupuesto: Presupuesto, traza: Traza | None = None) -> Resultado:
        ...