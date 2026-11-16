from __future__ import annotations

from fractions import Fraction

from ..nucleo.contador import Contador
from ..rs.expresion import Const, Expr, Op, Var

OPERADORES_POLINOMIALES = frozenset({"+", "-", "*", "neg"})
Polinomio = tuple[Fraction, ...]       


def es_polinomio(e: Expr) -> bool:
    match e:
        case Const(_) | Var(_):
            return True
        case Op(nombre, hijos):
            return nombre in OPERADORES_POLINOMIALES and all(es_polinomio(h) for h in hijos)
    return False


def grado(e: Expr) -> int:
    match e:
        case Const(_):
            return 0
        case Var(_):
            return 1
        case Op("*", (a, b)):
            return grado(a) + grado(b)
        case Op("+" | "-", (a, b)):
            return max(grado(a), grado(b))
        case Op("neg", (a,)):
            return grado(a)
    raise ValueError("grado solo está definido para el fragmento polinomial (+, -, *, neg)")


def _limpiar(c: list[Fraction]) -> Polinomio:
    while c and c[-1] == 0:
        c.pop()
    return tuple(c)


def _sumar(a: Polinomio, b: Polinomio, signo: int, contador: Contador | None) -> Polinomio:
    n = max(len(a), len(b))
    if contador is not None:
        contador.tick(n, "suma_coef")
    return _limpiar([(a[i] if i < len(a) else Fraction(0)) + signo * (b[i] if i < len(b) else Fraction(0))
                     for i in range(n)])


def _multiplicar(a: Polinomio, b: Polinomio, contador: Contador | None) -> Polinomio:
    if not a or not b:
        return ()
    if contador is not None:
        contador.tick(len(a) * len(b), "mult_coef")
    res = [Fraction(0)] * (len(a) + len(b) - 1)

    for i, x in enumerate(a):
        for j, y in enumerate(b):
            res[i + j] += x * y
    return _limpiar(res)



def polinomio_canonico(e: Expr, nombre_x: str = "x", contador: Contador | None = None) -> Polinomio:
    match e:
        case Const(v):
            return _limpiar([Fraction(v)])
        case Var(n):
            if n != nombre_x:
                raise ValueError(f"variable inesperada {n!r}; se esperaba {nombre_x!r}")
            return (Fraction(0), Fraction(1))
        case Op("+", (a, b)):
            return _sumar(polinomio_canonico(a, nombre_x, contador), polinomio_canonico(b, nombre_x, contador), 1, contador)
        case Op("-", (a, b)):
            return _sumar(polinomio_canonico(a, nombre_x, contador), polinomio_canonico(b, nombre_x, contador), -1, contador)
        case Op("*", (a, b)):
            return _multiplicar(polinomio_canonico(a, nombre_x, contador), polinomio_canonico(b, nombre_x, contador), contador)
        case Op("neg", (a,)):
            return _sumar((), polinomio_canonico(a, nombre_x, contador), -1, contador)
    raise ValueError("la forma canónica solo está definida para el fragmento polinomial (+, -, *, neg)")