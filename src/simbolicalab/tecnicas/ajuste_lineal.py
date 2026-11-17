from __future__ import annotations
import math
from dataclasses import dataclass
from itertools import combinations

from ..nucleo.contador import Contador
from .matroides import norma, producto

from math import comb
from typing import Sequence
MAX_COMBINACIONES = 200_000


def minimos_cuadrados(columnas: Sequence[Sequence[float]], y: Sequence[float], tol: float = 1e-9, contador: Contador | None = None) -> tuple[list[float], float]:
    n, k = len(y), len(columnas)
    Q: list[list[float]] = []
    R = [[0.0] * k for _ in range(k)]

    for j, c in enumerate(columnas):
        v = [float(a) for a in c]
        for _ in range(2):
            for i, q in enumerate(Q):
                if contador is not None:
                    contador.tick(2 * n, "op_vectorial")
                d = producto(q, v)
                R[i][j] += d
                v = [a - d * b for a, b in zip(v, q)]
        nr = norma(v)
        if nr <= tol * norma(c):
            raise ValueError("las columnas son linealmente dependientes")
        R[j][j] = nr
        Q.append([a / nr for a in v])

    qty = [producto(q, y) for q in Q]
    coefs = [0.0] * k
    for i in reversed(range(k)):
        coefs[i] = (qty[i] - sum(R[i][j] * coefs[j] for j in range(i + 1, k))) / R[i][i]
    ecm = sum((yy - sum(cf * col[t] for cf, col in zip(coefs, columnas))) ** 2 for t, yy in enumerate(y)) / n
    return coefs, ecm



class Proyector:
    def __init__(self, y: Sequence[float], tol: float = 1e-9, contador: Contador | None = None) -> None:
        self.y, self.tol, self.contador = list(y), tol, contador
        self.q: list[list[float]] = []
        self.residuo = list(y)

    @property
    def error(self) -> float:
        return sum(r * r for r in self.residuo) / len(self.y)

    def _ortogonal(self, col: Sequence[float]) -> tuple[list[float], float] | None:
        nc = norma(col)
        if nc == 0.0:
            return None
        r = list(col)
        for _ in range(2):
            for q in self.q:
                if self.contador is not None:
                    self.contador.tick(2 * len(r), "op_vectorial")
                d = producto(q, r)
                r = [a - d * b for a, b in zip(r, q)]
        nr = norma(r)
        if nr <= self.tol * nc:
            return None
        return [a / nr for a in r], nr

    def ganancia(self, col: Sequence[float]) -> float:
        o = self._ortogonal(col)
        if o is None:
            return 0.0
        return producto(o[0], self.residuo) ** 2

    def agregar(self, col: Sequence[float]) -> bool:
        o = self._ortogonal(col)
        if o is None:
            return False
        q = o[0]
        d = producto(q, self.residuo)
        self.residuo = [a - d * b for a, b in zip(self.residuo, q)]
        self.q.append(q)
        return True



@dataclass(frozen=True)
class Seleccion:
    indices: tuple[int, ...]
    errores: tuple[float, ...]          

    @property
    def error(self) -> float:
        return self.errores[-1] if self.errores else math.inf



def seleccion_hacia_adelante(columnas: Sequence[Sequence[float]], y: Sequence[float], k: int, costos: Sequence[float] | None = None, tol: float = 1e-9,
                             contador: Contador | None = None) -> Seleccion:
    if k < 1:
        raise ValueError("k debe ser al menos 1")
    
    costos = costos if costos is not None else [0.0] * len(columnas)
    p = Proyector(y, tol, contador)
    elegidos: list[int] = []
    errores: list[float] = []
    escala = sum(v * v for v in y) or 1.0

    for _ in range(min(k, len(columnas))):
        mejor, mejor_g = None, 0.0
        for j, c in enumerate(columnas):
            if j in elegidos:
                continue
            g = p.ganancia(c)
            if mejor is None and g > 1e-14 * escala:
                mejor, mejor_g = j, g
            elif mejor is not None and (g > mejor_g * (1 + 1e-12) or
                                        (abs(g - mejor_g) <= 1e-12 * mejor_g and costos[j] < costos[mejor])):
                mejor, mejor_g = j, g
        if mejor is None:
            break
        p.agregar(columnas[mejor])
        elegidos.append(mejor)
        errores.append(p.error)
    return Seleccion(tuple(elegidos), tuple(errores))



def mejor_subconjunto(columnas: Sequence[Sequence[float]], y: Sequence[float], k: int, tol: float = 1e-9) -> tuple[tuple[int, ...], float]:
    if comb(len(columnas), k) > MAX_COMBINACIONES:
        raise ValueError(f"C({len(columnas)}, {k}) supera {MAX_COMBINACIONES} combinaciones")
    
    mejor: tuple[int, ...] | None = None
    mejor_e = math.inf

    for S in combinations(range(len(columnas)), k):
        try:
            _, e = minimos_cuadrados([columnas[i] for i in S], y, tol)
        except ValueError:
            continue
        if e < mejor_e:
            mejor, mejor_e = S, e

    if mejor is None:
        raise ValueError("ningún subconjunto de ese tamaño es independiente")
    return mejor, mejor_e