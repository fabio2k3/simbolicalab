from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, TypeAlias

from ..nucleo.contador import Contador
from .operadores import OPERADORES

@dataclass(frozen=False, slots=True)
class Const:
    valor: float

@dataclass(frozen=True, slots=True)
class Var:
    nombre: str

@dataclass(frozen=True, slots=True)
class Op:
    nombre: str
    hijos: tuple["Expr", ...]

Expr: TypeAlias = Const | Var | Op

def tamano(e: Expr) -> int:
    match e:
        case Op(_, hijos):
            return 1 + sum(tamano(h) for h in hijos)
        case _:
            return 1

def a_cadena(e: Expr) -> str:

    def contar_parentesis(e: Expr) -> str:
        match e:
            case Const(v):
                return f"{v:g}"
            case Var(n):
                return n
            case Op(nombre, (a,b)) if OPERADORES[nombre].infijo:
                return f"({contar_parentesis(a)} {nombre} {contar_parentesis(b)})"

            case Op(nombre, hijos):
                return f"{nombre}({', '.join(contar_parentesis(h) for h in hijos)})"

    s = contar_parentesis(e)
    if isinstance(e, Op) and OPERADORES[e.nombre].infijo:
        s = s[1:-1]
    return s

def evaluar (e: Expr, entorno: Mapping[str, float], contador: Contador | None = None) -> float:
    if contador is not  None:
        contador.tick(1, "nodo")
    match e:
        case Const(v):
            return v
        case Var(n):
            return entorno[n]
        case Op(nombre, hijos):
            args = [evaluar(h, entorno, contador) for h in hijos]

            try: 
                return OPERADORES[nombre].function(*args)
            except (OverflowError, ZeroDivisionError, ValueError):
                return math.nan