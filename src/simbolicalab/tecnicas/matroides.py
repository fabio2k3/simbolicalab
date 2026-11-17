from __future__ import annotations

from ..nucleo.contador import Contador
from ..rs.invariantes import InvarianteViolado

import math
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from typing import Callable, Iterable, Sequence

Oraculo = Callable[[frozenset], bool]
MAX_ELEMENTOS_EXHAUSTIVO = 12


def producto(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def norma(a: Sequence[float]) -> float:
    return math.sqrt(producto(a, a))


class BaseOrtonormal:
    def __init__(self, tol: float = 1e-9, contador: Contador | None = None) -> None:
        if tol < 0:
            raise ValueError("tol no puede ser negativa")
        self.tol, self.contador, self.q = tol, contador, []

    def residuo(self, v: Sequence[float]) -> list[float]:
        r = list(v)
        for _ in range(2):
            for q in self.q:
                if self.contador is not None:
                    self.contador.tick(2 * len(r), "op_vectorial")
                d = producto(q, r)
                r = [a - d * b for a, b in zip(r, q)]
        return r

    def intentar(self, v: Sequence[float]) -> bool:
        n_v = norma(v)
        if n_v == 0.0:
            return False
        
        r = self.residuo(v)
        n_r = norma(r)

        if n_r <= self.tol * n_v:
            return False
        self.q.append([a / n_r for a in r])
        return True

    def __len__(self) -> int:
        return len(self.q)


class MatroideLineal:
    def __init__(self, columnas: Sequence[Sequence[float]], tol: float = 1e-9, contador: Contador | None = None) -> None:
        cols = [tuple(float(x) for x in c) for c in columnas]
        if cols and len({len(c) for c in cols}) != 1:
            raise ValueError("todas las columnas deben tener la misma longitud")
        if not all(math.isfinite(x) for c in cols for x in c):
            raise ValueError("las columnas deben ser finitas")
        self.columnas, self.tol, self.contador = cols, tol, contador

    @property
    def n(self) -> int:
        return len(self.columnas)

    def _base(self, S: Iterable[int]) -> tuple[BaseOrtonormal, bool]:
        b = BaseOrtonormal(self.tol, self.contador)
        for i in sorted(S):
            if not b.intentar(self.columnas[i]):
                return b, False
        return b, True

    def independiente(self, S: Iterable[int]) -> bool:
        return self._base(S)[1]

    def rango(self, S: Iterable[int]) -> int:
        b = BaseOrtonormal(self.tol, self.contador)
        for i in sorted(S):
            b.intentar(self.columnas[i])
        return len(b)

    def oraculo(self) -> Oraculo:
        return lambda S: self.independiente(S)


def rango_exacto(columnas: Sequence[Sequence[int | Fraction]]) -> int:
    filas = [[Fraction(c[i]) for c in columnas] for i in range(len(columnas[0]))] if columnas else []
    rango, n_col = 0, len(columnas)

    for j in range(n_col):
        piv = next((i for i in range(rango, len(filas)) if filas[i][j] != 0), None)
        if piv is None:
            continue
        filas[rango], filas[piv] = filas[piv], filas[rango]
        for i in range(len(filas)):
            if i != rango and filas[i][j] != 0:
                f = filas[i][j] / filas[rango][j]
                filas[i] = [a - f * b for a, b in zip(filas[i], filas[rango])]
        rango += 1

    return rango



def oraculo_exacto(columnas: Sequence[Sequence[int]]) -> Oraculo:
    return lambda S: rango_exacto([columnas[i] for i in sorted(S)]) == len(S)


def _memo(oraculo: Oraculo) -> Oraculo:
    cache: dict[frozenset, bool] = {}

    def f(S: frozenset) -> bool:
        if S not in cache:
            cache[S] = oraculo(S)
        return cache[S]
    return f


def _subconjuntos(n: int) -> list[frozenset]:
    return [frozenset(i for i in range(n) if m >> i & 1) for m in range(1 << n)]


def verificar_axiomas(oraculo: Oraculo, n: int) -> dict[str, int]:
    if n > MAX_ELEMENTOS_EXHAUSTIVO:
        raise ValueError(f"la verificación exhaustiva admite a lo sumo {MAX_ELEMENTOS_EXHAUSTIVO} elementos")
    ind = _memo(oraculo)
    if not ind(frozenset()):
        raise InvarianteViolado("el conjunto vacío no es independiente")
    independientes = [S for S in _subconjuntos(n) if ind(S)]
    for S in independientes:
        for e in S:
            if not ind(S - {e}):
                raise InvarianteViolado(f"no es hereditario: {sorted(S)} es independiente pero {sorted(S - {e})} no")
    por_tamano: dict[int, list[frozenset]] = {}
    for S in independientes:
        por_tamano.setdefault(len(S), []).append(S)
    for k, As in por_tamano.items():
        for A in As:
            for B in por_tamano.get(k + 1, []):
                if not any(ind(A | {x}) for x in B - A):
                    raise InvarianteViolado(
                        f"falla el intercambio: A={sorted(A)} y B={sorted(B)} son independientes, |A| < |B|, "
                        f"pero ningún x de B \\ A extiende A")
    rango = max(len(S) for S in independientes)
    bases = sum(1 for S in independientes if len(S) == rango)
    return {"subconjuntos": 1 << n, "independientes": len(independientes), "bases": bases, "rango": rango}


def discrepancia(a: Oraculo, b: Oraculo, n: int) -> frozenset | None:
    for S in _subconjuntos(n):
        if a(S) != b(S):
            return S
    return None


@dataclass(frozen=True)
class ResultadoGreedy:
    elegidos: tuple[int, ...]
    costo: float
    descartados: tuple[int, ...]


def _orden(costos: Sequence[float]) -> list[int]:
    return sorted(range(len(costos)), key=lambda i: (costos[i], i))


def greedy_base(oraculo: Oraculo, costos: Sequence[float]) -> ResultadoGreedy:
    S: set[int] = set()
    elegidos, descartados = [], []
    for e in _orden(costos):
        if oraculo(frozenset(S | {e})):
            S.add(e)
            elegidos.append(e)
        else:
            descartados.append(e)
    return ResultadoGreedy(tuple(elegidos), sum(costos[e] for e in elegidos), tuple(descartados))



def greedy_base_lineal(m: MatroideLineal, costos: Sequence[float]) -> ResultadoGreedy:
    if len(costos) != m.n:
        raise ValueError("hace falta un costo por columna")
    
    base = BaseOrtonormal(m.tol, m.contador)
    elegidos, descartados = [], []
    for e in _orden(costos):
        (elegidos if base.intentar(m.columnas[e]) else descartados).append(e)

    return ResultadoGreedy(tuple(elegidos), sum(costos[e] for e in elegidos), tuple(descartados))



def mejor_base_por_fuerza_bruta(oraculo: Oraculo, costos: Sequence[float]) -> tuple[float, list[frozenset]]:
    n = len(costos)
    if n > MAX_ELEMENTOS_EXHAUSTIVO:
        raise ValueError(f"la fuerza bruta admite a lo sumo {MAX_ELEMENTOS_EXHAUSTIVO} elementos")
    
    ind = _memo(oraculo)
    maximales = [S for S in _subconjuntos(n) if ind(S) and not any(ind(S | {e}) for e in range(n) if e not in S)]
    mejor = min(sum(costos[e] for e in S) for S in maximales)
    return mejor, [S for S in maximales if math.isclose(sum(costos[e] for e in S), mejor, rel_tol=1e-12, abs_tol=1e-12)]



def sistema_sin_intercambio() -> tuple[Oraculo, list[float], int]:
    maximales = [frozenset({0, 1}), frozenset({2, 3})]
    return (lambda S: any(S <= m for m in maximales)), [1.0, 5.0, 2.0, 2.0], 4


def clases_paralelas(columnas: Sequence[Sequence[float]], decimales: int = 9) -> list[list[int]]:
    grupos: dict[tuple[float, ...], list[int]] = {}

    for i, c in enumerate(columnas):
        nc = norma(c)
        if nc == 0.0 or not math.isfinite(nc):
            continue

        signo = next((1.0 if x > 0 else -1.0 for x in c if abs(x) > 1e-12 * nc), 1.0)
        clave = tuple(round(signo * x / nc, decimales) + 0.0 for x in c)
        grupos.setdefault(clave, []).append(i)
        
    return list(grupos.values())