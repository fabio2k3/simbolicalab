from __future__ import annotations

from typing import Sequence

from ..rs.datos import Datos
from ..rs.expresion import Const, Expr, Op, Var, a_cadena, evaluar


def datos_desde_expresion(e: Expr, xs: Sequence[float], nombre_x: str = "x", nombre: str | None = None) -> Datos:
    """Datos exactos (sin ruido) generados por una fórmula conocida."""
    ys = tuple(evaluar(e, {nombre_x: x}) for x in xs)
    return Datos(xs=tuple(float(x) for x in xs), ys=ys, nombre_x=nombre_x,
                 nombre=nombre or f"Ley construida: {a_cadena(e)}", ley_oculta=a_cadena(e))


def contraejemplo_de_la_poda() -> Datos:
    """y = sqrt(x + 1) en x = 1..8. Necesita la subexpresión x + 1, que no está entre las mejores por error de su tamaño."""
    ley = Op("sqrt", (Op("+", (Var("x"), Const(1.0))),))
    return datos_desde_expresion(ley, range(1, 9), "x", "Contraejemplo de la poda: y = sqrt(x + 1)")