from __future__ import annotations

from ..nucleo.contador import Contador
from .ajuste_lineal import minimos_cuadrados
import math
from typing import Sequence

def piso_de_error(ys: Sequence[float], factor: float = 1e-12) -> float:
    n = len(ys)
    media = sum(ys) / n
    var = sum((y - media) ** 2 for y in ys) / n
    return max(factor * var, 1e-300)


def bic(ecm: float, n: int, k: int, piso: float = 1e-300, m: int = 0, gamma: float = 1.0) -> float:
    if n < 2 or k < 0:
        raise ValueError("hace falta n >= 2 y k >= 0")
    
    if m and not k <= m:
        raise ValueError("k no puede superar a m")
    
    extra = 2 * gamma * math.log(math.comb(m, k)) if m else 0.0
    return n * math.log(max(ecm, piso)) + k * math.log(n) + extra



def elegir_k(errores: Sequence[float], n: int, piso: float = 1e-300, m: int = 0, gamma: float = 1.0) -> tuple[int, list[float]]:
    if not errores:
        raise ValueError("hace falta al menos un error")
    
    values = [bic(e, n, k, piso, m, gamma) for k, e in enumerate(errores, start=1)]
    best = min(range(len(values)), key=lambda i: (values[i], i))
    return best + 1, values



def eliminacion_hacia_atras(columnas: Sequence[Sequence[float]], y: Sequence[float], indices: Sequence[int], piso: float = 1e-300, 
                            tol: float = 1e-9, contador: Contador | None = None, m: int = 0, gamma: float = 1.0) -> tuple[list[int], float]:
    if not indices:
        raise ValueError("hace falta al menos un índice")
    
    n = len(y)
    current = list(indices)
    _, ecm = minimos_cuadrados([columnas[i] for i in current], y, tol, contador)
    while len(current) > 1:
        referencia = bic(ecm, n, len(current), piso, m, gamma)
        mejor = None
        for pos in range(len(current)):
            resto = current[:pos] + current[pos + 1:]
            _, e = minimos_cuadrados([columnas[i] for i in resto], y, tol, contador)
            b = bic(e, n, len(resto), piso, m, gamma)
            if mejor is None or b < mejor[0]:
                mejor = (b, resto, e)
        if mejor is None or mejor[0] >= referencia:
            break
        _, current, ecm = mejor
    return current, ecm