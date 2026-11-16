"""Verificación de equivalencia de fórmulas por evaluación en puntos aleatorios (Monte Carlo, error de un lado).

Aritmética exacta módulo un primo p. Si dos polinomios distintos P y Q tienen grado <= d y se evalúan en un punto
uniforme de Z_p, entonces Pr[P(r) = Q(r)] <= d / p (Schwartz-Zippel). Con k puntos independientes la
probabilidad de que coincidan en todos es <= (d / p)^k. Dos fórmulas equivalentes coinciden siempre.
La garantía vale solo en el fragmento polinomial (+, -, *, neg); fuera de él no hay cota.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from ..nucleo.contador import Contador
from ..rs.expresion import Const, Expr, Op, Var
from .polinomios import es_polinomio, grado

Huella = tuple[int, ...]
PRIMOS_SUGERIDOS = (101, 1009, 10007, 2 ** 31 - 1, 2 ** 61 - 1)


def es_primo(n: int) -> bool:
    if n < 2:
        return False
    pequenos = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for q in pequenos:
        if n % q == 0:
            return n == q
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in pequenos:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _constante_mod(v: float, p: int) -> int:
    f = Fraction(v)
    if f.denominator % p == 0:
        raise ValueError(f"la constante {v!r} no es invertible módulo {p}")
    return f.numerator * pow(f.denominator, -1, p) % p


def evaluar_mod(e: Expr, nombre_x: str, r: int, p: int, contador: Contador | None = None) -> int:
    if contador is not None:
        contador.tick(1, "nodo_mod")
    match e:
        case Const(v):
            return _constante_mod(v, p)
        case Var(n):
            if n != nombre_x:
                raise ValueError(f"variable inesperada {n!r}; se esperaba {nombre_x!r}")
            return r % p
        case Op("+", (a, b)):
            return (evaluar_mod(a, nombre_x, r, p, contador) + evaluar_mod(b, nombre_x, r, p, contador)) % p
        case Op("-", (a, b)):
            return (evaluar_mod(a, nombre_x, r, p, contador) - evaluar_mod(b, nombre_x, r, p, contador)) % p
        case Op("*", (a, b)):
            return (evaluar_mod(a, nombre_x, r, p, contador) * evaluar_mod(b, nombre_x, r, p, contador)) % p
        case Op("neg", (a,)):
            return (-evaluar_mod(a, nombre_x, r, p, contador)) % p
    raise ValueError("evaluar_mod solo está definido para el fragmento polinomial (+, -, *, neg)")



def _validar(exprs: Sequence[Expr], p: int) -> int:
    if not es_primo(p):
        raise ValueError(f"el módulo {p} no es primo")
    if not all(es_polinomio(e) for e in exprs):
        raise ValueError("el Monte Carlo con garantía solo vale en el fragmento polinomial (+, -, *, neg)")
    
    d = max((grado(e) for e in exprs), default=0)

    if p <= d:
        raise ValueError(f"se necesita p > grado (p={p}, grado={d}): Schwartz-Zippel exige |S| > d")
    return d



def puntos_aleatorios(rondas: int, p: int, rng: random.Random) -> list[int]:
    if rondas < 1:
        raise ValueError("rondas debe ser al menos 1")
    return [rng.randrange(p) for _ in range(rondas)]


def huella(e: Expr, nombre_x: str, puntos: Sequence[int], p: int, contador: Contador | None = None) -> Huella:
    return tuple(evaluar_mod(e, nombre_x, r, p, contador) for r in puntos)


@dataclass(frozen=True)
class Veredicto:
    equivalentes: bool
    testigo: int | None
    rondas: int


def equivalentes_mc(e1: Expr, e2: Expr, nombre_x: str, rondas: int, p: int, rng: random.Random, contador: Contador | None = None) -> Veredicto:
    if rondas < 1:
        raise ValueError("rondas debe ser al menos 1")
    
    _validar((e1, e2), p)
    for i in range(1, rondas + 1):
        r = rng.randrange(p)
        if evaluar_mod(e1, nombre_x, r, p, contador) != evaluar_mod(e2, nombre_x, r, p, contador):
            return Veredicto(False, r, i)
        
    return Veredicto(True, None, rondas)



def deduplicar_huella(exprs: Sequence[Expr], nombre_x: str, puntos: Sequence[int], p: int, contador: Contador | None = None) -> list[int]:
    _validar(exprs, p)
    c = contador if contador is not None else Contador()
    vistas: set[Huella] = set()
    conservados: list[int] = []

    for i, e in enumerate(exprs):
        h = huella(e, nombre_x, puntos, p, c)
        c.tick(1, "acceso_hash")
        if h not in vistas:
            vistas.add(h)
            conservados.append(i)

    return conservados


def cota_falsa_fusion(grado_max: int, p: int, rondas: int) -> float:
    return min(1.0, grado_max / p) ** rondas


def rondas_necesarias(grado_max: int, p: int, delta: float) -> int:
    if not 0 < delta < 1:
        raise ValueError("delta debe estar en (0, 1)")
    if p <= grado_max:
        raise ValueError("se necesita p > grado")
    if grado_max == 0:
        return 1
    return max(1, math.ceil(math.log(delta) / math.log(grado_max / p)))