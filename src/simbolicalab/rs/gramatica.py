from __future__ import annotations

import math
from dataclasses import dataclass

from .expresion import Const, Expr, Var
from .operadores import OPERADORES

@dataclass(frozen=True)
class Gramatica:
    variables: tuple[str, ...] = ("x",)
    constants: tuple[float,...] = (1.0, 2.0)
    unarios: tuple[str, ...] = ("sqrt",)
    binarios: tuple[str, ...] = ("+", "-", "*", "/")

    def __post_init__(self) -> None:
        if len(self.variables) + len(self.constants) == 0:
            raise ValueError("la gramatica necesita al menos un terminal (varaible o contante)")

        for nombre, esperada in [(n , 1) for n in self.unarios] + [(n,2) for n in self.binarios]:
            if nombre not in OPERADORES:
                raise ValueError(f"operador desconocido: {nombre !r}")
            if OPERADORES[nombre].aridad != esperada:
                raise ValueError(f"{nombre!r} no tiene aridad {esperada}")

        for lista, q in [(self.variables, "variables"), (self.constants, "constantes"), (self.unarios, "unarios"), (self.binarios, " binarios")]:
            if len(set(lista)) != len(lista):
                raise ValueError(f"hay elementos repetidos en {q}")

        if not all(math.isfinite(c) for c in self.constants):
            raise ValueError("las constantes deben ser finitas")

    @property
    def terminales(self) -> tuple[Expr, ...]:
        return tuple(Var(v) for v in self.variables) + tuple(Const(c) for c in self.constants)

    @property
    def n_terminales(self) -> int:
        return len(self.variables) + len(self.constants) 

