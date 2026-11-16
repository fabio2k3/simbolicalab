from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

def _div(a: float, b: float) -> float:
    return a / b if b != 0 else math.nan

def _sqrt(a: float) -> float:
    return math.sqrt(a) if a >= 0 else math.nan

def _log(a: float) -> float:
    return math.log(a) if a > 0 else math.nan

def _sin(a: float) -> float:
    return math.sin(a) if math.isfinite(a) else math.nan

def _cos(a: float) -> float:
    return math.cos(a) if math.isfinite(a) else math.nan

def _exp(a: float) -> float:
    try:
        return math.exp(a)
    except OverflowError:
        return math.inf

@dataclass(frozen=True)
class Operador:
    nombre: str
    aridad: int
    function: Callable[..., float]
    infijo: bool = False
    conmutativo: bool = False

OPERADORES: dict[str, Operador] = {
    "+": Operador("+", 2, lambda a, b: a + b, infijo=True, conmutativo=True),
    "-": Operador("-", 2, lambda a, b: a - b, infijo=True),
    "*": Operador("*", 2, lambda a, b: a*b, infijo= True, conmutativo=True),
    "/": Operador("/", 2, _div, infijo=True),
    "sqrt": Operador("sqrt", 1, _sqrt),
    "log": Operador("log", 1, _log),
    "exp": Operador("exp", 1, _exp),
    "neg": Operador("neg", 1, lambda a: -a),
    "sin": Operador("sin", 1, _sin),
    "cos": Operador("cos", 1, _cos),
}