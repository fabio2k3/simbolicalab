from __future__ import annotations

import math
from typing import Callable

from ..nucleo.contador import Contador
from .datos import Datos
from .expresion import Expr, evaluar

def error_cuadratico_medio(e: Expr, datos: Datos, contador: Contador | None = None) -> float:
    total = 0.0

    for x, y in datos:
        d = evaluar(e, {datos.nombre_x: x}, contador) - y
        total += d * d
    ecm = total / len(datos)
    return ecm if math.isfinite(ecm) else math.inf

def error_relativo_medio(e:Expr, datos: Datos, contador: Contador | None = None) -> float:
    if any(y == 0 for y in datos.ys):
        raise ValueError("el error relativo no está definido si algún y es 0")
    total = 0.0

    for x, y in datos:
        total += abs(evaluar(e, {datos.nombre_x: x}, contador) - y)
    err = total / len(datos)
    return err if math.isfinite(err) else math.inf

METRICAS: dict[str, Callable[[Expr, Datos, Contador | None], float]] = { 
    "ecm" : error_cuadratico_medio,
    "relativo": error_relativo_medio,
}